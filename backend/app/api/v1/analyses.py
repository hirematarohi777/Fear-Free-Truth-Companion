from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser
from app.schemas.analyses import LoanAnalysisResponse
from app.services.sharing.family_service import redact_analysis_for_recipient


router = APIRouter(tags=["Document Analyses"])


@router.post("/documents/{document_id}/analyses", status_code=status.HTTP_202_ACCEPTED)
async def trigger_document_analysis(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Trigger a new analysis job for an existing uploaded document."""
    db = get_db()
    try:
        obj_id = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    doc = await db.documents.find_one({"_id": obj_id, "ownerId": user.id, "pendingDeletion": {"$ne": True}})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    now = datetime.now(timezone.utc)
    job_doc = {
        "ownerId": user.id,
        "type": "document_analysis",
        "resourceId": document_id,
        "status": "queued",
        "stage": "uploading",
        "attemptCount": 0,
        "leaseOwner": None,
        "leaseExpiresAt": None,
        "errorCode": None,
        "createdAt": now,
        "updatedAt": now
    }
    job_res = await db.jobs.insert_one(job_doc)

    return {
        "jobId": str(job_res.inserted_id),
        "status": "queued",
        "message": "Document analysis job started."
    }


@router.get("/analyses/{analysis_id}")
async def get_analysis_result(
    analysis_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Retrieve document analysis findings.
    Enforces owner or active family share access.
    Strictly redacts unauthorized fields for family recipients on the backend.
    """
    db = get_db()
    try:
        obj_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format.")

    analysis = await db.analyses.find_one({"_id": obj_id})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    analysis_owner_id = analysis["ownerId"]
    is_owner = (analysis_owner_id == user.id)
    granted_permissions = None

    if not is_owner:
        # Check active family share
        now = datetime.now(timezone.utc)
        share = await db.report_shares.find_one({
            "recipientId": user.id,
            "reportId": analysis_id,
            "revokedAt": None,
            "expiresAt": {"$gt": now}
        })
        if not share:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this analysis report."
            )
        granted_permissions = share.get("permissions", {})

    analysis_dict = dict(analysis)
    analysis_dict["id"] = str(analysis_dict["_id"])
    del analysis_dict["_id"]

    # Redact for family recipient
    if not is_owner and granted_permissions:
        analysis_dict = redact_analysis_for_recipient(analysis_dict, granted_permissions)
        analysis_dict["isSharedView"] = True
        analysis_dict["grantedPermissions"] = granted_permissions
        await db.audit_events.insert_one({
            "actorId": user.id,
            "resourceType": "document_analysis",
            "resourceId": analysis_id,
            "action": "report_viewed",
            "timestamp": datetime.now(timezone.utc),
            "safeMetadata": {"ownerId": analysis_owner_id},
        })
    else:
        analysis_dict["isSharedView"] = False

    return analysis_dict
