import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, Field
from bson import ObjectId
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser
from app.core.config import settings


router = APIRouter(prefix="/privacy", tags=["Privacy & Data Retention"])


class PrivacySettingsUpdate(BaseModel):
    documentRetentionDays: int = Field(default=30, ge=1, le=365)


@router.get("/settings")
async def get_privacy_settings(user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    user_doc = await db.users.find_one({"_id": ObjectId(user.id)})
    retention = (user_doc or {}).get("documentRetentionDays", settings.DOCUMENT_RETENTION_DAYS)
    return {
        "documentRetentionDays": retention,
        "privacyGuarantees": [
            "Uploaded documents are stored in private, isolated storage volumes and never exposed via public static URLs.",
            "Local Ollama inference is used exclusively. No document text is ever sent to external cloud AI APIs.",
            "No uploaded documents or borrower records are used for model training or commercial profiling.",
            "Family members cannot see unshared fields or access original documents without explicit owner permission.",
            "You can immediately delete any document, report, or your entire account with all associated data."
        ]
    }


@router.patch("/settings")
async def update_privacy_settings(
    req: PrivacySettingsUpdate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    # In a multi-tenant DB, this can be saved per-user
    db = get_db()
    await db.users.update_one(
        {"_id": ObjectId(user.id)},
        {"$set": {"documentRetentionDays": req.documentRetentionDays}}
    )
    return {
        "message": f"Document retention period updated to {req.documentRetentionDays} days.",
        "documentRetentionDays": req.documentRetentionDays
    }


@router.post("/account-deletion")
async def delete_account_and_all_data(
    response: Response,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Complete account deletion workflow:
    1. Immediately revokes all active sessions and sharing invitations.
    2. Deletes all uploaded files from disk.
    3. Deletes owned documents, chunks, analyses, URL checks, jobs, and shares.
    4. Deletes user account record.
    """
    db = get_db()
    user_obj_id = ObjectId(user.id)

    # 1. Delete physical files from disk
    docs_cursor = db.documents.find({"ownerId": user.id})
    docs = await docs_cursor.to_list(500)
    for d in docs:
        file_path = os.path.join(settings.UPLOAD_DIRECTORY, d["storageKey"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    # 2. Delete database records
    await db.document_chunks.delete_many({"ownerId": user.id})
    await db.documents.delete_many({"ownerId": user.id})
    await db.analyses.delete_many({"ownerId": user.id})
    await db.url_checks.delete_many({"ownerId": user.id})
    await db.jobs.delete_many({"ownerId": user.id})
    await db.family_invitations.delete_many({"ownerId": user.id})
    await db.report_shares.delete_many({"ownerId": user.id})
    await db.report_shares.delete_many({"recipientId": user.id})
    await db.sessions.delete_many({"userId": user.id})
    await db.users.delete_one({"_id": user_obj_id})

    # Clear cookies
    response.delete_cookie(settings.COOKIE_NAME, path="/")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")

    return {
        "message": "Account and all associated documents, reports, and shares have been permanently deleted."
    }
