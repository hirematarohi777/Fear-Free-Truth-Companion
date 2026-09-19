from datetime import datetime, timezone
from typing import List
from urllib.parse import parse_qs, urlparse
import hashlib
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser
from app.schemas.family import (
    CreateInvitationRequest,
    InvitationCreatedResponse,
    AcceptInvitationRequest,
    ReportShareItem,
    UpdateSharePermissionsRequest
    , WhatsAppShareRequest, WhatsAppShareResponse
)
from app.services.sharing.family_service import create_invitation, accept_invitation, revoke_share, as_utc
from app.services.sharing.whatsapp_service import build_safe_whatsapp_payload, send_whatsapp_share
from app.core.config import settings


router = APIRouter(prefix="/family", tags=["Family Circle Sharing"])


@router.post("/invitations", response_model=InvitationCreatedResponse)
async def invite_family_member(
    req: CreateInvitationRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a secure, consent-first invitation for a specific family member email address.
    Default permissions require explicit user selection.
    """
    db = get_db()
    
    # Verify owner owns the report
    if req.reportType == "document_analysis":
        report = await db.analyses.find_one({"_id": ObjectId(req.reportId), "ownerId": user.id})
    else:
        report = await db.url_checks.find_one({"_id": ObjectId(req.reportId), "ownerId": user.id})

    if not report:
        raise HTTPException(status_code=404, detail="Target report not found or unauthorized.")

    inv_result = await create_invitation(
        owner_id=user.id,
        recipient_email=req.recipientEmail,
        report_id=req.reportId,
        report_type=req.reportType,
        permissions=req.permissions,
        expires_in_hours=req.expiresInHours
    )

    # In local development or production, generate clean invitation link
    invitation_link = f"{settings.APP_BASE_URL}/family/accept?token={inv_result['token']}"

    return InvitationCreatedResponse(
        invitationId=inv_result["invitationId"],
        recipientEmail=inv_result["recipientEmail"],
        reportId=inv_result["reportId"],
        reportType=inv_result["reportType"],
        permissions=inv_result["permissions"],
        expiresAt=inv_result["expiresAt"],
        invitationLink=invitation_link
    )


@router.post("/whatsapp", response_model=WhatsAppShareResponse)
async def share_family_invitation_via_whatsapp(
    req: WhatsAppShareRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Validate an owner-created invitation, then submit safe metadata to n8n."""
    db = get_db()
    try:
        invitation_id = ObjectId(req.invitationId)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invitation ID format.")

    parsed_link = urlparse(req.invitationLink)
    raw_token = parse_qs(parsed_link.query).get("token", [""])[0].strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Invitation link is invalid.")

    invitation = await db.family_invitations.find_one({"_id": invitation_id, "ownerId": user.id})
    now = datetime.now(timezone.utc)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or unauthorized.")
    if invitation.get("revokedAt"):
        raise HTTPException(status_code=400, detail="This invitation has been revoked.")
    if as_utc(invitation.get("expiresAt")) and as_utc(invitation.get("expiresAt")) <= now:
        raise HTTPException(status_code=400, detail="This invitation has expired.")
    if invitation.get("tokenHash") != hashlib.sha256(raw_token.encode("utf-8")).hexdigest():
        raise HTTPException(status_code=400, detail="Invitation link does not match the invitation.")

    if invitation["reportType"] == "document_analysis":
        report = await db.analyses.find_one({"_id": ObjectId(invitation["reportId"]), "ownerId": user.id})
        document = await db.documents.find_one({"_id": ObjectId(report["documentId"])}) if report and report.get("documentId") else None
        document_name = document.get("originalFilename", "Loan report") if document else "Loan report"
    else:
        report = await db.url_checks.find_one({"_id": ObjectId(invitation["reportId"]), "ownerId": user.id})
        document_name = "Loan link report"
    if not report:
        raise HTTPException(status_code=404, detail="Target report not found or unauthorized.")

    try:
        payload = build_safe_whatsapp_payload(
            recipient_phone=req.recipientPhone,
            document_name=document_name,
            permissions=invitation.get("permissions", {}),
            share_url=f"{settings.APP_BASE_URL}/family/accept?token={raw_token}",
        )
        await send_whatsapp_share(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error))

    return WhatsAppShareResponse(
        status="workflow_accepted",
        message="The invitation was accepted by the WhatsApp workflow. Delivery status is managed by n8n and WhatsApp.",
    )


@router.post("/invitations/accept")
async def accept_family_invitation(
    req: AcceptInvitationRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Authenticated recipient accepts a family share invitation."""
    try:
        res = await accept_invitation(
            raw_token=req.token.strip(),
            recipient_id=user.id,
            recipient_email=user.email
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/shares")
async def list_shares(user: AuthenticatedUser = Depends(get_current_user)):
    """List shares both created by the user (shared with others) and received by the user."""
    db = get_db()
    
    # 1. Shares created by user
    created_cursor = db.report_shares.find({"ownerId": user.id, "revokedAt": None})
    created_shares = await created_cursor.to_list(100)
    
    # 2. Shares received by user
    received_cursor = db.report_shares.find({"recipientId": user.id, "revokedAt": None})
    received_shares = await received_cursor.to_list(100)

    # Format list
    async def format_share(s, role):
        owner = await db.users.find_one({"_id": ObjectId(s["ownerId"])})
        recipient = await db.users.find_one({"_id": ObjectId(s["recipientId"])})
        return {
            "id": str(s["_id"]),
            "role": role,
            "ownerId": s["ownerId"],
            "ownerEmail": owner["emailNormalized"] if owner else "Unknown",
            "ownerName": owner.get("displayName", "User") if owner else "Unknown",
            "recipientId": s["recipientId"],
            "recipientEmail": recipient["emailNormalized"] if recipient else "Unknown",
            "reportId": s["reportId"],
            "reportType": s["reportType"],
            "permissions": s["permissions"],
            "expiresAt": s.get("expiresAt"),
            "createdAt": s["createdAt"]
        }

    out_created = [await format_share(s, "owner") for s in created_shares]
    out_received = [await format_share(s, "recipient") for s in received_shares]

    return {
        "sharedByMe": out_created,
        "sharedWithMe": out_received
    }


@router.patch("/shares/{share_id}")
async def update_share_permissions(
    share_id: str,
    req: UpdateSharePermissionsRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Update permissions of an existing family share."""
    db = get_db()
    try:
        obj_id = ObjectId(share_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid share ID format.")

    res = await db.report_shares.update_one(
        {"_id": obj_id, "ownerId": user.id},
        {"$set": {"permissions": req.permissions.model_dump()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Share record not found or unauthorized.")

    return {"message": "Permissions updated successfully."}


@router.delete("/shares/{share_id}")
async def revoke_family_share(
    share_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Immediately revoke a family member's access to a shared report."""
    success = await revoke_share(share_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Share record not found or already revoked.")
    return {"message": "Family member access revoked immediately."}


@router.get("/audit")
async def list_family_audit_events(user: AuthenticatedUser = Depends(get_current_user)):
    """Return invitation, view, and revocation events involving this user's family shares."""
    db = get_db()
    cursor = db.audit_events.find(
        {
            "$or": [
                {"actorId": user.id},
                {"safeMetadata.ownerId": user.id},
            ]
        }
    ).sort("timestamp", -1)
    events = await cursor.to_list(100)
    return [
        {
            "id": str(e["_id"]),
            "actorId": e.get("actorId"),
            "resourceType": e.get("resourceType"),
            "resourceId": e.get("resourceId"),
            "action": e.get("action"),
            "timestamp": e.get("timestamp"),
            "safeMetadata": e.get("safeMetadata", {}),
        }
        for e in events
    ]
