import io
import pytest
from pypdf import PdfWriter
from app.services.documents.validator import validate_file_content, FileValidationError
from app.services.documents.extractor import ExtractedUnit
from app.services.documents.quote_verifier import verify_quote_in_units
from app.services.documents.rules import run_deterministic_rules
from app.schemas.analyses import FieldStatus, ChargeCategory


def test_magic_byte_validation():
    # Valid minimal PDF bytes
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    mime, ext = validate_file_content(pdf_bytes, "loan_agreement.pdf")
    assert mime == "application/pdf"
    assert ext == "pdf"

    # Fake PDF: text or executable with .pdf extension
    malicious_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
    with pytest.raises(FileValidationError, match="Unsupported or malformed file format"):
        validate_file_content(malicious_bytes, "malware.pdf")

    # Empty file
    with pytest.raises(FileValidationError, match="Uploaded file is empty"):
        validate_file_content(b"", "empty.pdf")


def test_quote_verification_in_units():
    units = [
        ExtractedUnit(source_ref="Page 1", text="The Sanctioned Loan Amount is Rs. 40,00,000 at an interest rate of 8.5% p.a."),
        ExtractedUnit(source_ref="Page 2", text="Processing fee of 0.5% plus applicable GST is payable prior to disbursement.")
    ]

    # Exact quote present
    found, ref = verify_quote_in_units("Processing fee of 0.5% plus applicable GST", units)
    assert found is True
    assert ref == "Page 2"

    # Normalized whitespace quote
    found2, ref2 = verify_quote_in_units("Sanctioned Loan Amount is   Rs. 40,00,000", units)
    assert found2 is True
    assert ref2 == "Page 1"

    # Hallucinated quote NOT present in text
    found_fake, _ = verify_quote_in_units("Mandatory non-refundable penalty fee of 5%", units)
    assert found_fake is False


def test_deterministic_rules_and_conflicting_terms():
    # Document with conflicting interest rates: Page 1 says 8.5%, Page 4 says 9.25%
    units = [
        ExtractedUnit(source_ref="Page 1", text="Sanctioned Loan Amount: Rs. 35,00,000. Rate of Interest: 8.5% p.a. Tenure: 180 months."),
        ExtractedUnit(source_ref="Page 4", text="Subject to the terms herein, Rate of Interest: 9.25% p.a. upon commencement of amortization.")
    ]

    terms, findings = run_deterministic_rules(units)

    # Loan amount found
    assert terms.loanAmount.status == FieldStatus.FOUND
    assert terms.loanAmount.numericValue == 3500000.0

    # Interest rate marked conflicting
    assert terms.interestRate.status == FieldStatus.CONFLICTING

    # Conflicting terms finding generated
    conflicting_findings = [f for f in findings if f.category == ChargeCategory.CONFLICTING_TERMS]
    assert len(conflicting_findings) >= 1
    assert "conflicting" in conflicting_findings[0].title.lower()

    # Missing field (e.g. administrative fee) remains NOT_FOUND, never zero
    assert terms.administrativeFee.status == FieldStatus.NOT_FOUND
    assert terms.administrativeFee.numericValue is None
