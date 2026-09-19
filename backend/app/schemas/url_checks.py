from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class CheckStatus(str, Enum):
    CONCERN = "concern"
    NO_CONCERN_FOUND = "no_concern_found"
    INCONCLUSIVE = "inconclusive"
    NOT_CHECKED = "not_checked"


class OverallOutcome(str, Enum):
    SIGNIFICANT_RISKS = "Significant risk indicators found"
    SOME_CONCERNS = "Some concerns require verification"
    NO_MAJOR_INDICATORS = "No major indicators found in completed checks"
    INSUFFICIENT_EVIDENCE = "Insufficient evidence to assess"


class IdentityVerificationStatus(str, Enum):
    ENTITY_MATCHED_OWNERSHIP_CORROBORATED = "Entity matched; website ownership corroborated"
    ENTITY_MATCHED_OWNERSHIP_UNVERIFIED = "Entity matched; website ownership unverified"
    ENTITY_MATCH_UNCERTAIN = "Entity match uncertain"
    NOT_CHECKED = "Not checked"


class SingleUrlCheckItem(BaseModel):
    checkName: str
    status: CheckStatus
    explanation: str
    evidenceUrlOrQuote: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recommendedNextStep: str


class UrlSubmitRequest(BaseModel):
    url: str


class UrlCheckResponse(BaseModel):
    id: str
    ownerId: str
    submittedUrl: str
    finalUrl: str
    redirectChain: List[str]
    claimedEntity: Optional[str] = None
    overallOutcome: OverallOutcome
    identityVerificationStatus: IdentityVerificationStatus
    checks: List[SingleUrlCheckItem]
    evidence: Dict[str, Any]
    limitations: List[str]
    modelSummary: Optional[str] = None
    createdAt: datetime
    completedAt: Optional[datetime] = None
