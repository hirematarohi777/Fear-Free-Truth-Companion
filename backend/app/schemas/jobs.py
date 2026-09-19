from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    ownerId: str
    type: str  # document_analysis or url_verification
    resourceId: str
    status: str  # queued, processing, completed, completed_with_limitations, failed, cancelled
    stage: str
    attemptCount: int
    errorCode: Optional[str] = None
    resultSummary: Optional[Dict[str, Any]] = None
    createdAt: datetime
    updatedAt: datetime
