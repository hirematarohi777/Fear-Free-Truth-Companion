from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    documentId: str
    originalFilename: str
    sizeBytes: int
    pageCount: Optional[int] = None
    detectedMimeType: str
    jobId: str
    status: str
    message: str


class DocumentChunkResponse(BaseModel):
    chunkIndex: int
    text: str
    sourceReferences: str
    extractionMethod: str


class DocumentDetailResponse(BaseModel):
    id: str
    originalFilename: str
    sizeBytes: int
    pageCount: Optional[int] = None
    detectedMimeType: str
    sha256: str
    extractionStatus: str
    createdAt: datetime
    latestAnalysisId: Optional[str] = None
