from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser
from app.schemas.jobs import JobResponse


router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    job = await db.jobs.find_one({"_id": obj_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["ownerId"] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to job status.")

    return JobResponse(
        id=str(job["_id"]),
        ownerId=job["ownerId"],
        type=job["type"],
        resourceId=job["resourceId"],
        status=job["status"],
        stage=job.get("stage", "queued"),
        attemptCount=job.get("attemptCount", 0),
        errorCode=job.get("errorCode"),
        resultSummary=job.get("resultSummary"),
        createdAt=job["createdAt"],
        updatedAt=job.get("updatedAt", job["createdAt"])
    )


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    db = get_db()
    try:
        obj_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    job = await db.jobs.find_one({"_id": obj_id, "ownerId": user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized.")

    if job["status"] in ("completed", "failed", "cancelled"):
        return {"message": f"Job is already in terminal status: {job['status']}."}

    now = datetime.now(timezone.utc)
    await db.jobs.update_one(
        {"_id": obj_id},
        {"$set": {"status": "cancelled", "stage": "cancelled", "updatedAt": now}}
    )

    return {"message": "Job cancelled successfully."}
