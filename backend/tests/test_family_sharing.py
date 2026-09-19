import pytest
from datetime import datetime, timezone, timedelta
from app.services.sharing.family_service import (
    generate_invitation_token,
    redact_analysis_for_recipient
)
from app.schemas.family import SharingPermissions


def test_token_generation_and_hashing():
    raw, hashed = generate_invitation_token()
    assert len(raw) >= 32
    assert len(hashed) == 64  # SHA-256 hex string


def test_strict_backend_redaction():
    sample_analysis = {
        "summaryStatement": "Detailed borrower loan analysis with identified charges.",
        "extractedTerms": {
            "loanAmount": {
                "fieldName": "Sanctioned Loan Amount",
                "value": "₹40,00,000",
                "numericValue": 4000000.0,
                "supportingQuote": "Sanction amount: Rs. 40,00,000"
            },
            "processingFee": {
                "fieldName": "Processing Fee",
                "value": "₹20,000",
                "numericValue": 20000.0,
                "supportingQuote": "Processing charges: Rs. 20,000"
            }
        },
        "findings": [
            {
                "id": "f1",
                "title": "Processing Fee",
                "amountOrCalculationBasis": "₹20,000",
                "supportingQuote": "Processing charges: Rs. 20,000"
            }
        ],
        "calculations": {"monthlyEmi": 34713.0}
    }

    # Case 1: Default permissions (Everything False)
    default_perms = {
        "shareSummary": False,
        "shareFindings": False,
        "shareFinancialAmounts": False,
        "shareSourceExcerpts": False,
        "shareOriginalDocument": False
    }
    redacted1 = redact_analysis_for_recipient(sample_analysis, default_perms)

    assert "private" in redacted1["summaryStatement"].lower()
    assert len(redacted1["findings"]) == 0
    assert redacted1["calculations"] is None
    assert redacted1["extractedTerms"]["loanAmount"]["value"] == "[Private Amount]"
    assert redacted1["extractedTerms"]["loanAmount"]["numericValue"] is None
    assert redacted1["extractedTerms"]["loanAmount"]["supportingQuote"] is None

    # Case 2: Only shareFindings = True and shareFinancialAmounts = True
    perms2 = {
        "shareSummary": True,
        "shareFindings": True,
        "shareFinancialAmounts": True,
        "shareSourceExcerpts": False,
        "shareOriginalDocument": False
    }
    redacted2 = redact_analysis_for_recipient(sample_analysis, perms2)

    assert redacted2["summaryStatement"] == sample_analysis["summaryStatement"]
    assert len(redacted2["findings"]) == 1
    assert redacted2["extractedTerms"]["loanAmount"]["value"] == "₹40,00,000"
    # Supporting quotes must be stripped because shareSourceExcerpts is False
    assert redacted2["extractedTerms"]["loanAmount"]["supportingQuote"] is None
    assert redacted2["findings"][0]["supportingQuote"] is None


def test_qa_context_cannot_include_unshared_excerpts():
    """Q&A must only receive already-redacted report payloads."""
    sample = {
        "summaryStatement": "Summary of terms.",
        "extractedTerms": {
            "loanAmount": {
                "fieldName": "Sanctioned Loan Amount",
                "value": "₹40,00,000",
                "numericValue": 4000000.0,
                "supportingQuote": "Sanction amount: Rs. 40,00,000",
            }
        },
        "findings": [
            {
                "id": "f1",
                "title": "Processing Fee",
                "amountOrCalculationBasis": "₹20,000",
                "supportingQuote": "Processing charges: Rs. 20,000",
            }
        ],
        "calculations": {"monthlyEmi": 34713.0},
    }
    perms = {
        "shareSummary": True,
        "shareFindings": True,
        "shareFinancialAmounts": False,
        "shareSourceExcerpts": False,
        "shareOriginalDocument": False,
    }
    accessible = redact_analysis_for_recipient(sample, perms)
    assert accessible["extractedTerms"]["loanAmount"]["supportingQuote"] is None
    assert accessible["findings"][0]["supportingQuote"] is None
    assert accessible["extractedTerms"]["loanAmount"]["value"] == "[Private Amount]"
    assert accessible["calculations"] is None
