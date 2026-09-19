import re
from typing import Any, Dict, List
import httpx
from app.core.config import settings

PERMISSION_LABELS = {
    "shareSummary": "Summary",
    "shareFindings": "Findings",
    "shareFinancialAmounts": "Financial figures",
    "shareSourceExcerpts": "Source excerpts",
    "shareOriginalDocument": "Original document",
}

def normalize_phone(phone: str) -> str:
    """Return an international WhatsApp number containing digits only."""
    digits = re.sub(r"\D", "", phone)
    if not 8 <= len(digits) <= 15:
        raise ValueError("Enter a valid international phone number, including country code.")
    return digits

def permission_names(permissions: Dict[str, bool]) -> List[str]:
    return [key for key, label in PERMISSION_LABELS.items() if permissions.get(key) is True]

def build_safe_whatsapp_payload(
    recipient_phone: str,
    document_name: str,
    permissions: Dict[str, bool],
    share_url: str,
) -> Dict[str, Any]:
    granted = permission_names(permissions)
    if not granted:
        raise ValueError("Select at least one permission before sharing via WhatsApp.")
    return {
        "event": "family_report_share",
        "recipient_phone": normalize_phone(recipient_phone),
        "document_name": document_name,
        "permissions": granted,
        "share_url": share_url,
    }

async def send_whatsapp_share(payload: Dict[str, Any]) -> None:
    if not settings.N8N_WHATSAPP_WEBHOOK_URL:
        raise RuntimeError("WhatsApp sharing is not configured on the server.")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(settings.N8N_WHATSAPP_WEBHOOK_URL, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise RuntimeError("The WhatsApp workflow is currently unavailable.") from error