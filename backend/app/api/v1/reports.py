from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from fastapi.responses import StreamingResponse
from bson import ObjectId
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser
from app.schemas.reports import ReportQuestionRequest, ReportQuestionResponse, ReportListItem
from app.services.sharing.family_service import redact_analysis_for_recipient
from app.services.reports.pdf_exporter import generate_report_pdf
from app.services.reports.qa_service import ask_report_question


router = APIRouter(tags=["Reports & Evidence"])


async def resolve_report_with_permissions(report_type: str, report_id: str, user: AuthenticatedUser):
    db = get_db()
    try:
        obj_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID format.")

    if report_type == "document_analysis":
        doc = await db.analyses.find_one({"_id": obj_id})
    elif report_type == "url_check":
        doc = await db.url_checks.find_one({"_id": obj_id})
    else:
        raise HTTPException(status_code=400, detail="Invalid reportType. Use 'document_analysis' or 'url_check'.")

    if not doc:
        raise HTTPException(status_code=404, detail="Report not found.")

    is_owner = (doc["ownerId"] == user.id)
    permissions = None

    if not is_owner:
        now = datetime.now(timezone.utc)
        share = await db.report_shares.find_one({
            "recipientId": user.id,
            "reportId": report_id,
            "revokedAt": None,
            "expiresAt": {"$gt": now}
        })
        if not share:
            raise HTTPException(status_code=403, detail="Unauthorized to view this report.")
        permissions = share.get("permissions", {})

    report_dict = dict(doc)
    report_dict["id"] = str(report_dict["_id"])
    del report_dict["_id"]

    if not is_owner and permissions and report_type == "document_analysis":
        report_dict = redact_analysis_for_recipient(report_dict, permissions)
        report_dict["isSharedView"] = True
        report_dict["permissions"] = permissions
    else:
        report_dict["isSharedView"] = False

    return report_dict, is_owner, permissions


@router.get("/reports", response_model=List[ReportListItem])
async def list_reports(user: AuthenticatedUser = Depends(get_current_user)):
    """List all available reports: both owned and shared with the user."""
    db = get_db()
    items: List[ReportListItem] = []

    # 1. Owned document analyses
    analyses = await db.analyses.find({"ownerId": user.id}).sort("createdAt", -1).to_list(50)
    for a in analyses:
        items.append(ReportListItem(
            id=str(a["_id"]),
            reportType="document_analysis",
            title=f"Document Analysis ({a.get('summaryStatement', 'Completed')[:50]}...)",
            createdAt=a["createdAt"],
            status=a.get("status", "completed"),
            isSharedWithMe=False
        ))

    # 2. Owned URL checks
    url_checks = await db.url_checks.find({"ownerId": user.id}).sort("createdAt", -1).to_list(50)
    for u in url_checks:
        items.append(ReportListItem(
            id=str(u["_id"]),
            reportType="url_check",
            title=f"URL Check: {u.get('submittedUrl', '')[:40]}",
            createdAt=u["createdAt"],
            status="completed" if u.get("completedAt") else "processing",
            isSharedWithMe=False
        ))

    # 3. Reports shared with me
    now = datetime.now(timezone.utc)
    shares = await db.report_shares.find({
        "recipientId": user.id,
        "revokedAt": None,
        "expiresAt": {"$gt": now}
    }).to_list(50)

    for s in shares:
        owner = await db.users.find_one({"_id": ObjectId(s["ownerId"])})
        items.append(ReportListItem(
            id=s["reportId"],
            reportType=s["reportType"],
            title=f"Family Shared Report ({s['reportType']})",
            createdAt=s["createdAt"],
            status="shared",
            isSharedWithMe=True,
            permissions=s.get("permissions"),
            ownerDisplayName=owner.get("displayName", "Family Member") if owner else None
        ))

    return items


@router.get("/reports/{report_type}/{report_id}")
async def get_single_report(
    report_type: str,
    report_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieve full report content, with backend permission enforcement."""
    report_dict, _, _ = await resolve_report_with_permissions(report_type, report_id, user)
    return report_dict


@router.get("/reports/{report_type}/{report_id}/export")
async def export_report(
    report_type: str,
    report_id: str,
    format: str = Query(default="pdf", regex="^(pdf|json)$"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Export report as PDF or JSON, strictly respecting caller's permissions."""
    report_dict, _, _ = await resolve_report_with_permissions(report_type, report_id, user)

    if format == "json":
        import json
        json_bytes = json.dumps(report_dict, default=str, indent=2).encode("utf-8")
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=truth_report_{report_id}.json"}
        )
    else:
        pdf_buffer = generate_report_pdf(
            report_dict,
            title=f"Truth Clarity Report ({report_type.replace('_', ' ').title()})"
        )
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=truth_report_{report_id}.pdf"}
        )


@router.post("/reports/{report_type}/{report_id}/questions", response_model=ReportQuestionResponse)
async def ask_question_about_report(
    report_type: str,
    report_id: str,
    req: ReportQuestionRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Ask questions strictly scoped to the accessible report evidence."""
    report_dict, _, _ = await resolve_report_with_permissions(report_type, report_id, user)
    return await ask_report_question(req.question, report_dict)
