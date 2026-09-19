from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class SharingPermissions(BaseModel):
    shareSummary: bool = Field(default=False, description="Allow recipient to see the high-level summary")
    shareFindings: bool = Field(default=False, description="Allow recipient to see categorized charge findings")
    shareFinancialAmounts: bool = Field(default=False, description="Allow recipient to see exact monetary figures and rates")
    shareSourceExcerpts: bool = Field(default=False, description="Allow recipient to see verbatim quoted clauses from document")
    shareOriginalDocument: bool = Field(default=False, description="Allow recipient to download original uploaded document")


class CreateInvitationRequest(BaseModel):
    recipientEmail: EmailStr
    reportId: str
    reportType: str = Field(default="document_analysis", description="document_analysis or url_check")
    permissions: SharingPermissions
    expiresInHours: int = Field(default=72, ge=1, le=720)


class InvitationCreatedResponse(BaseModel):
    invitationId: str
    recipientEmail: str
    reportId: str
    reportType: str
    permissions: SharingPermissions
    expiresAt: datetime
    invitationLink: str  # Given to the owner to share with family or sent via mailer

class WhatsAppShareRequest(BaseModel):
    invitationId: str
    invitationLink: str
    recipientPhone: str = Field(min_length=8, max_length=20)

class WhatsAppShareResponse(BaseModel):
    status: str
    message: str


class AcceptInvitationRequest(BaseModel):
    token: str


class ReportShareItem(BaseModel):
    id: str
    ownerId: str
    ownerEmail: Optional[str] = None
    recipientId: str
    reportId: str
    reportType: str
    permissions: SharingPermissions
    expiresAt: Optional[datetime] = None
    revokedAt: Optional[datetime] = None
    createdAt: datetime
    reportTitle: Optional[str] = None


class UpdateSharePermissionsRequest(BaseModel):
    permissions: SharingPermissions
