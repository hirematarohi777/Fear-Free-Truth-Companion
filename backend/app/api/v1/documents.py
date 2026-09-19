import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Response
from fastapi.responses import FileResponse
from bson import ObjectId
from app.core.config import settings
from app.api.deps import get_current_user, AuthenticatedUser
from app.db.mongo import get_db
from app.services.documents.validator import validate_file_content, FileValidationError
from app.schemas.documents import DocumentUploadResponse, DocumentDetailResponse


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_loan_document(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Accept PDF, DOCX, PNG, JPG loan documents up to 20MB.
    Validates magic bytes, checks for passwords, saves to private volume, and enqueues analysis job.
    """
    content = await file.read()
    filename = file.filename or "uploaded_document"

    try:
        mime_type, ext = validate_file_content(content, filename)
    except FileValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # Generate isolated storage key (never store by user filename)
    storage_key = f"{uuid.uuid4().hex}.{ext}"
    storage_path = os.path.join(settings.UPLOAD_DIRECTORY, storage_key)
    with open(storage_path, "wb") as f:
        f.write(content)

    sha256_hash = hashlib.sha256(content).hexdigest()
    now = datetime.now(timezone.utc)
    db = get_db()

    # Create document record
    doc_record = {
        "ownerId": user.id,
        "originalFilename": filename,
        "storageKey": storage_key,
        "detectedMimeType": mime_type,
        "sizeBytes": len(content),
        "sha256": sha256_hash,
        "extractionStatus": "queued",
        "pageCount": None,
        "latestAnalysisId": None,
        "pendingDeletion": False,
        "createdAt": now
    }
    doc_res = await db.documents.insert_one(doc_record)
    document_id = str(doc_res.inserted_id)

    # Create background job
    job_record = {
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
    job_res = await db.jobs.insert_one(job_record)
    job_id = str(job_res.inserted_id)

    return DocumentUploadResponse(
        documentId=document_id,
        originalFilename=filename,
        sizeBytes=len(content),
        pageCount=None,
        detectedMimeType=mime_type,
        jobId=job_id,
        status="queued",
        message="Document uploaded securely. Analysis job enqueued."
    )


@router.get("", response_model=List[DocumentDetailResponse])
async def list_documents(user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    cursor = db.documents.find({"ownerId": user.id, "pendingDeletion": {"$ne": True}}).sort("createdAt", -1)
    docs = await cursor.to_list(length=100)

    results = []
    for d in docs:
        results.append(DocumentDetailResponse(
            id=str(d["_id"]),
            originalFilename=d["originalFilename"],
            sizeBytes=d["sizeBytes"],
            pageCount=d.get("pageCount"),
            detectedMimeType=d["detectedMimeType"],
            sha256=d["sha256"],
            extractionStatus=d.get("extractionStatus", "queued"),
            createdAt=d["createdAt"],
            latestAnalysisId=d.get("latestAnalysisId")
        ))
    return results


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    doc = await db.documents.find_one({"_id": obj_id, "pendingDeletion": {"$ne": True}})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Authorization check
    if doc["ownerId"] != user.id:
        raise HTTPException(status_code=403, detail="Access to this document is unauthorized.")

    return DocumentDetailResponse(
        id=str(doc["_id"]),
        originalFilename=doc["originalFilename"],
        sizeBytes=doc["sizeBytes"],
        pageCount=doc.get("pageCount"),
        detectedMimeType=doc["detectedMimeType"],
        sha256=doc["sha256"],
        extractionStatus=doc.get("extractionStatus", "queued"),
        createdAt=doc["createdAt"],
        latestAnalysisId=doc.get("latestAnalysisId")
    )


@router.get("/{document_id}/download")
async def download_document(document_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    doc = await db.documents.find_one({"_id": obj_id, "pendingDeletion": {"$ne": True}})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Permission check: Owner or Family recipient with shareOriginalDocument
    is_owner = (doc["ownerId"] == user.id)
    has_share_permission = False

    if not is_owner:
        # Check if there is an active share for this document's analysis
        if doc.get("latestAnalysisId"):
            share = await db.report_shares.find_one({
                "recipientId": user.id,
                "reportId": doc["latestAnalysisId"],
                "revokedAt": None
            })
            if share and share.get("permissions", {}).get("shareOriginalDocument") is True:
                has_share_permission = True

    if not is_owner and not has_share_permission:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download the original document."
        )

    file_path = os.path.join(settings.UPLOAD_DIRECTORY, doc["storageKey"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File content missing from private storage.")

    return FileResponse(
        path=file_path,
        media_type=doc["detectedMimeType"],
        filename=doc["originalFilename"]
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(document_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    doc = await db.documents.find_one({"_id": obj_id, "ownerId": user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    # Mark pending deletion first
    await db.documents.update_one({"_id": obj_id}, {"$set": {"pendingDeletion": True}})

    # Cancel jobs
    await db.jobs.update_many({"resourceId": document_id}, {"$set": {"status": "cancelled", "stage": "cancelled"}})

    # Remove file from disk
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, doc["storageKey"])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    # Cascading delete
    await db.document_chunks.delete_many({"documentId": document_id})
    
    # If analysis exists, remove shares and analysis
    analyses = await db.analyses.find({"documentId": document_id}).to_list(100)
    for a in analyses:
        a_id = str(a["_id"])
        await db.report_shares.delete_many({"reportId": a_id})
        await db.family_invitations.delete_many({"reportId": a_id})
    
    await db.analyses.delete_many({"documentId": document_id})
    await db.documents.delete_one({"_id": obj_id})

    return {"message": "Document, chunks, analyses, and shares deleted permanently."}
