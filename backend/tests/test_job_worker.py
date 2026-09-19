from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.workers.job_worker import JobWorker


@pytest.fixture
def worker():
    return JobWorker(worker_id="test-worker-1")


class FakeJobsCollection:
    def __init__(self, jobs):
        self.jobs = jobs
        self.updated = []

    async def find_one_and_update(self, filt, update, sort=None, return_document=None):
        now = datetime.now(timezone.utc)
        for job in self.jobs:
            if job.get("status") != filt.get("status"):
                continue
            attempt_filter = filt.get("attemptCount", {})
            max_attempts = attempt_filter.get("$lt", 999)
            if job.get("attemptCount", 0) >= max_attempts:
                continue
            job.update(update.get("$set", {}))
            return job
        return None

    async def update_one(self, filt, update):
        self.updated.append((filt, update))
        result = MagicMock()
        result.modified_count = 1
        result.matched_count = 1
        return result

    async def update_many(self, filt, update):
        now = datetime.now(timezone.utc)
        count = 0
        for job in self.jobs:
            if job.get("status") != filt.get("status"):
                continue
            lease = job.get("leaseExpiresAt")
            if lease and lease < now:
                job.update(update.get("$set", {}))
                job["attemptCount"] = job.get("attemptCount", 0) + update.get("$inc", {}).get("attemptCount", 0)
                count += 1
        result = MagicMock()
        result.modified_count = count
        return result


@pytest.mark.asyncio
async def test_atomic_job_claim_skips_over_retry_budget(worker):
    queued = {
        "_id": ObjectId(),
        "status": "queued",
        "attemptCount": 0,
        "createdAt": datetime.now(timezone.utc),
    }
    exhausted = {
        "_id": ObjectId(),
        "status": "queued",
        "attemptCount": 99,
        "createdAt": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    fake_db = MagicMock()
    fake_db.jobs = FakeJobsCollection([exhausted, queued])

    with patch("app.workers.job_worker.get_db", return_value=fake_db), patch(
        "app.workers.job_worker.settings.WORKER_MAX_RETRIES", 3
    ):
        claimed = await worker.claim_next_job()

    assert claimed is not None
    assert claimed["_id"] == queued["_id"]
    assert claimed["status"] == "processing"
    assert claimed["leaseOwner"] == worker.worker_id
    assert claimed["leaseExpiresAt"] is not None


@pytest.mark.asyncio
async def test_lease_expiry_recovery_requeues_abandoned_jobs(worker):
    expired = {
        "_id": ObjectId(),
        "status": "processing",
        "attemptCount": 1,
        "leaseExpiresAt": datetime.now(timezone.utc) - timedelta(minutes=10),
        "leaseOwner": "crashed-worker",
    }
    still_leased = {
        "_id": ObjectId(),
        "status": "processing",
        "attemptCount": 1,
        "leaseExpiresAt": datetime.now(timezone.utc) + timedelta(minutes=2),
        "leaseOwner": "healthy-worker",
    }
    fake_db = MagicMock()
    fake_db.jobs = FakeJobsCollection([expired, still_leased])

    with patch("app.workers.job_worker.get_db", return_value=fake_db):
        await worker.recover_abandoned_jobs()

    assert expired["status"] == "queued"
    assert expired["leaseOwner"] is None
    assert expired["attemptCount"] == 2
    assert still_leased["status"] == "processing"
    assert still_leased["leaseOwner"] == "healthy-worker"
