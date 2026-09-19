import os
from typing import Tuple
import pypdf
from app.core.config import settings


# Supported MIME types and signatures
MAGIC_SIGNATURES = {
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg"
}


class FileValidationError(Exception):
    pass


def validate_file_content(content: bytes, filename: str) -> Tuple[str, str]:
    """
    Validate file content by magic bytes, size limit, and encryption status.
    Returns (detected_mime_type, file_extension).
    """
    # 1. Size check
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise FileValidationError(
            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB. Current size: {len(content) / (1024*1024):.2f} MB."
        )

    if len(content) == 0:
        raise FileValidationError("Uploaded file is empty.")

    # 2. Magic byte check
    detected_mime = None
    for signature, mime in MAGIC_SIGNATURES.items():
        if content.startswith(signature):
            detected_mime = mime
            break

    if not detected_mime:
        raise FileValidationError(
            "Unsupported or malformed file format. Only PDF, DOCX, PNG, and JPG documents are accepted. "
            "File header does not match valid document signatures."
        )

    # 3. PDF specific checks (e.g. password protection & page count)
    if detected_mime == "application/pdf":
        import io
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise FileValidationError(
                    "This PDF is password-protected or encrypted. To analyze this document, please unlock it using your PDF viewer "
                    "(e.g., 'Print to PDF' without a password) and re-upload the unprotected copy."
                )
            page_count = len(reader.pages)
            if page_count > settings.MAX_PDF_PAGES:
                raise FileValidationError(
                    f"PDF exceeds the maximum page limit of {settings.MAX_PDF_PAGES} pages (found {page_count} pages). "
                    "Please upload only the sanction letter or relevant loan agreement schedule pages."
                )
        except pypdf.errors.PdfReadError as e:
            if "encrypted" in str(e).lower() or "password" in str(e).lower():
                raise FileValidationError(
                    "This PDF is password-protected or encrypted. Please remove the password and re-upload."
                )
            raise FileValidationError(f"Malformed or corrupted PDF file: {str(e)}")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return detected_mime, ext
