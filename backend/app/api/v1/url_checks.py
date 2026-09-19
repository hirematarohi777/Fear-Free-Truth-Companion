from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser
from app.schemas.url_checks import UrlSubmitRequest, UrlCheckResponse
from app.services.url_checks.fetcher import validate_url_syntax, SSRFValidationError


router = APIRouter(prefix="/url-checks", tags=["Loan URL Verification"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_loan_url(
    req: UrlSubmitRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Submit a loan offer website URL for SSRF-safe retrieval, risk heuristic analysis,
    and official registry checks.
    """
    raw_url = req.url.strip()
    try:
        scheme, hostname, port = validate_url_syntax(raw_url)
    except SSRFValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    db = get_db()
    now = datetime.now(timezone.utc)

    url_doc = {
        "ownerId": user.id,
        "submittedUrl": raw_url,
        "finalUrl": raw_url,
        "redirectChain": [raw_url],
        "claimedEntity": None,
        "overallOutcome": "Insufficient evidence to assess",
        "identityVerificationStatus": "Not checked",
        "checks": [],
        "evidence": {},
        "limitations": [],
        "modelSummary": None,
        "pendingDeletion": False,
        "createdAt": now,
        "completedAt": None
    }
    url_res = await db.url_checks.insert_one(url_doc)
    check_id = str(url_res.inserted_id)

    # Enqueue background job
    job_doc = {
        "ownerId": user.id,
        "type": "url_verification",
        "resourceId": check_id,
        "status": "queued",
        "stage": "fetching_website",
        "attemptCount": 0,
        "leaseOwner": None,
        "leaseExpiresAt": None,
        "errorCode": None,
        "createdAt": now,
        "updatedAt": now
    }
    job_res = await db.jobs.insert_one(job_doc)

    return {
        "checkId": check_id,
        "jobId": str(job_res.inserted_id),
        "status": "queued",
        "message": "Loan link verification enqueued."
    }


@router.get("")
async def list_url_checks(user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    cursor = db.url_checks.find({"ownerId": user.id, "pendingDeletion": {"$ne": True}}).sort("createdAt", -1)
    checks = await cursor.to_list(length=100)

    results = []
    for c in checks:
        results.append({
            "id": str(c["_id"]),
            "submittedUrl": c["submittedUrl"],
            "finalUrl": c.get("finalUrl", c["submittedUrl"]),
            "claimedEntity": c.get("claimedEntity"),
            "overallOutcome": c.get("overallOutcome"),
            "identityVerificationStatus": c.get("identityVerificationStatus"),
            "createdAt": c["createdAt"],
            "completedAt": c.get("completedAt")
        })
    return results


@router.get("/{check_id}")
async def get_url_check(check_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(check_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid check ID format.")

    c = await db.url_checks.find_one({"_id": obj_id, "pendingDeletion": {"$ne": True}})
    if not c:
        raise HTTPException(status_code=404, detail="URL check record not found.")

    # Authorization
    is_owner = (c["ownerId"] == user.id)
    if not is_owner:
        # Check active family share
        now = datetime.now(timezone.utc)
        share = await db.report_shares.find_one({
            "recipientId": user.id,
            "reportId": check_id,
            "revokedAt": None,
            "expiresAt": {"$gt": now}
        })
        if not share:
            raise HTTPException(status_code=403, detail="Unauthorized access to this URL report.")

    res = dict(c)
    res["id"] = str(res["_id"])
    del res["_id"]
    return res


@router.delete("/{check_id}")
async def delete_url_check(check_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(check_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid check ID format.")

    c = await db.url_checks.find_one({"_id": obj_id, "ownerId": user.id})
    if not c:
        raise HTTPException(status_code=404, detail="URL check record not found or unauthorized.")

    await db.url_checks.delete_one({"_id": obj_id})
    await db.jobs.delete_many({"resourceId": check_id})
    await db.report_shares.delete_many({"reportId": check_id})
    await db.family_invitations.delete_many({"reportId": check_id})

    return {"message": "URL check record deleted."}
