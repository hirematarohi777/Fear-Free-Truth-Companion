import copy
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from app.db.mongo import get_db
from app.schemas.family import SharingPermissions, ReportShareItem
from app.core.logging_config import logger


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalize MongoDB timestamps before comparing them with timezone-aware UTC values."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def generate_invitation_token() -> Tuple[str, str]:
    """Generate (raw_token, hashed_token). Raw token is sent to recipient; hash is stored in DB."""
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, hashed


async def create_invitation(
    owner_id: str,
    recipient_email: str,
    report_id: str,
    report_type: str,
    permissions: SharingPermissions,
    expires_in_hours: int = 72
) -> Dict[str, Any]:
    """Create a cryptographically secure family sharing invitation."""
    db = get_db()
    raw_token, hashed_token = generate_invitation_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_in_hours)

    inv_doc = {
        "ownerId": owner_id,
        "recipientEmailNormalized": recipient_email.strip().lower(),
        "reportId": report_id,
        "reportType": report_type,
        "permissions": permissions.model_dump(),
        "tokenHash": hashed_token,
        "expiresAt": expires_at,
        "acceptedAt": None,
        "revokedAt": None,
        "createdAt": now
    }

    res = await db.family_invitations.insert_one(inv_doc)

    # Log audit event
    await db.audit_events.insert_one({
        "actorId": owner_id,
        "resourceType": "family_invitation",
        "resourceId": str(res.inserted_id),
        "action": "invitation_created",
        "timestamp": now,
        "safeMetadata": {
            "recipientEmail": recipient_email.strip().lower(),
            "reportId": report_id,
            "permissions": permissions.model_dump()
        }
    })

    return {
        "invitationId": str(res.inserted_id),
        "token": raw_token,
        "recipientEmail": recipient_email.strip().lower(),
        "reportId": report_id,
        "reportType": report_type,
        "permissions": permissions,
        "expiresAt": expires_at
    }


async def accept_invitation(raw_token: str, recipient_id: str, recipient_email: str) -> Dict[str, Any]:
    """Accept an invitation, creating an active report_shares record."""
    db = get_db()
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    inv = await db.family_invitations.find_one({"tokenHash": hashed_token})
    if not inv:
        raise ValueError("Invalid or unrecognized invitation link.")

    if inv.get("revokedAt"):
        raise ValueError("This invitation has been revoked by the owner.")

    if as_utc(inv.get("expiresAt")) and as_utc(inv["expiresAt"]) < now:
        raise ValueError("This invitation link has expired.")

    # Email address check
    if inv["recipientEmailNormalized"] != recipient_email.strip().lower():
        raise ValueError(
            f"This invitation was sent specifically to {inv['recipientEmailNormalized']}. "
            f"You are currently logged in as {recipient_email}."
        )

    # Check if share already exists or update it
    share_filter = {
        "ownerId": inv["ownerId"],
        "recipientId": recipient_id,
        "reportId": inv["reportId"]
    }
    share_doc = {
        "ownerId": inv["ownerId"],
        "recipientId": recipient_id,
        "reportId": inv["reportId"],
        "reportType": inv["reportType"],
        "permissions": inv["permissions"],
        "expiresAt": inv["expiresAt"],
        "revokedAt": None,
        "createdAt": now
    }

    share_res = await db.report_shares.update_one(share_filter, {"$set": share_doc}, upsert=True)
    await db.family_invitations.update_one({"_id": inv["_id"]}, {"$set": {"acceptedAt": now}})

    # Audit log
    await db.audit_events.insert_one({
        "actorId": recipient_id,
        "resourceType": "report_share",
        "resourceId": inv["reportId"],
        "action": "invitation_accepted",
        "timestamp": now,
        "safeMetadata": {"ownerId": inv["ownerId"]}
    })

    return {"message": "Invitation accepted successfully", "reportId": inv["reportId"]}


async def revoke_share(share_id: str, actor_id: str) -> bool:
    """Immediately revoke a family share record."""
    db = get_db()
    now = datetime.now(timezone.utc)
    res = await db.report_shares.update_one(
        {"_id": ObjectId(share_id), "ownerId": actor_id},
        {"$set": {"revokedAt": now}}
    )
    if res.modified_count > 0:
        await db.audit_events.insert_one({
            "actorId": actor_id,
            "resourceType": "report_share",
            "resourceId": share_id,
            "action": "share_revoked",
            "timestamp": now,
            "safeMetadata": {}
        })
        return True
    return False


def redact_analysis_for_recipient(analysis_dict: Dict[str, Any], permissions: Dict[str, bool]) -> Dict[str, Any]:
    """
    Strict backend field-level redaction based on granted permissions.
    Unauthorized fields are never sent across the wire.
    """
    redacted = copy.deepcopy(analysis_dict)

    # 1. Summary permission
    if not permissions.get("shareSummary", False):
        redacted["summaryStatement"] = "Report summary has been kept private by the owner."

    # 2. Findings permission
    if not permissions.get("shareFindings", False):
        redacted["findings"] = []

    # 3. Financial amounts permission
    if not permissions.get("shareFinancialAmounts", False):
        redacted["calculations"] = None
        if "extractedTerms" in redacted and isinstance(redacted["extractedTerms"], dict):
            for field_name, field_obj in redacted["extractedTerms"].items():
                if isinstance(field_obj, dict):
                    if field_obj.get("value") is not None:
                        field_obj["value"] = "[Private Amount]"
                    field_obj["numericValue"] = None

        if "findings" in redacted and isinstance(redacted["findings"], list):
            for finding in redacted["findings"]:
                if finding.get("amountOrCalculationBasis"):
                    finding["amountOrCalculationBasis"] = "[Private Amount]"

    # 4. Source excerpts permission
    if not permissions.get("shareSourceExcerpts", False):
        if "extractedTerms" in redacted and isinstance(redacted["extractedTerms"], dict):
            for field_name, field_obj in redacted["extractedTerms"].items():
                if isinstance(field_obj, dict):
                    field_obj["supportingQuote"] = None

        if "findings" in redacted and isinstance(redacted["findings"], list):
            for finding in redacted["findings"]:
                finding["supportingQuote"] = None

    return redacted
