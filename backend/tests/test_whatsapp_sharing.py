import pytest

from app.core.config import settings
from app.services.sharing.whatsapp_service import (
    build_safe_whatsapp_payload,
    normalize_phone,
    send_whatsapp_share,
)


def permissions(**enabled):
    return {
        "shareSummary": enabled.get("summary", False),
        "shareFindings": enabled.get("findings", False),
        "shareFinancialAmounts": enabled.get("amounts", False),
        "shareSourceExcerpts": enabled.get("excerpts", False),
        "shareOriginalDocument": enabled.get("original", False),
    }


def test_whatsapp_payload_summary_only():
    payload = build_safe_whatsapp_payload(
        "+91 98765 43210", "Home Loan Report.pdf", permissions(summary=True), "https://app.test/family/accept?token=secret"
    )
    assert payload["recipient_phone"] == "919876543210"
    assert payload["permissions"] == ["Summary"]


def test_whatsapp_payload_summary_and_findings():
    payload = build_safe_whatsapp_payload(
        "919876543210", "Home Loan Report.pdf", permissions(summary=True, findings=True), "https://app.test/share/secret"
    )
    assert payload["permissions"] == ["Summary", "Findings"]


def test_whatsapp_payload_all_permissions():
    payload = build_safe_whatsapp_payload(
        "919876543210", "Home Loan Report.pdf", permissions(summary=True, findings=True, amounts=True, excerpts=True, original=True), "https://app.test/share/secret"
    )
    assert payload["permissions"] == [
        "Summary", "Findings", "Financial figures", "Source excerpts", "Original document"
    ]


def test_whatsapp_payload_excludes_report_content():
    payload = build_safe_whatsapp_payload(
        "919876543210", "Home Loan Report.pdf", permissions(summary=True), "https://app.test/share/secret"
    )
    serialized = str(payload)
    for private_value in ("4000000", "34713", "8.5", "Processing Fee", "bank account", "source quote"):
        assert private_value not in serialized


def test_whatsapp_requires_permission():
    with pytest.raises(ValueError, match="at least one permission"):
        build_safe_whatsapp_payload("919876543210", "Report.pdf", permissions(), "https://app.test/share/secret")


def test_phone_validation():
    assert normalize_phone("+91 (98765) 43210") == "919876543210"
    with pytest.raises(ValueError):
        normalize_phone("123")


@pytest.mark.asyncio
async def test_n8n_unavailable_is_reported(monkeypatch):
    monkeypatch.setattr(settings, "N8N_WHATSAPP_WEBHOOK_URL", "")
    with pytest.raises(RuntimeError, match="not configured"):
        await send_whatsapp_share({"event": "family_report_share"})