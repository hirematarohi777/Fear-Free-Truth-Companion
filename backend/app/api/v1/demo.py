import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from app.api.deps import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/demo", tags=["Synthetic Demo Fixtures"])

PROJECT_ROOT = Path(__file__).resolve().parents[4]
FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "documents"

FIXTURE_FILES = {
    "standard": "1_standard_home_loan.pdf",
    "additional": "2_additional_charges_loan.docx",
    "conflicting": "3_conflicting_terms_loan.pdf",
    "scanned": "4_scanned_degraded_document.pdf",
}


@router.get("/documents/{fixture_key}")
async def download_synthetic_fixture(
    fixture_key: str,
    _user: AuthenticatedUser = Depends(get_current_user),
):
    """Serve pre-packaged synthetic loan documents for evaluation (not real lender data)."""
    filename = FIXTURE_FILES.get(fixture_key)
    if not filename:
        raise HTTPException(status_code=404, detail="Unknown synthetic fixture.")

    path = FIXTURES_DIR / filename
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Fixture file is not generated yet. Run fixtures/generate_fixtures.py.",
        )

    media = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if filename.endswith(".docx")
        else "application/pdf"
    )
    return FileResponse(path, media_type=media, filename=filename)
