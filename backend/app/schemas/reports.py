from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReportQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class CitedSource(BaseModel):
    sourceReference: str
    quote: Optional[str] = None


class ReportQuestionResponse(BaseModel):
    question: str
    answer: str
    citedSources: List[CitedSource]
    cannotAnswerReason: Optional[str] = None
    isFinancialAdviceDisclaimer: str = (
        "This response is derived strictly from accessible document evidence for informational clarity. "
        "It does not constitute financial, legal, or regulatory advice."
    )


class ReportListItem(BaseModel):
    id: str
    reportType: str
    title: str
    createdAt: datetime
    status: str
    isSharedWithMe: bool = False
    permissions: Optional[Dict[str, bool]] = None
    ownerDisplayName: Optional[str] = None
