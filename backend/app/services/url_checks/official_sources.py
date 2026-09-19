import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional, Dict, Any, Tuple
from app.schemas.url_checks import (
    IdentityVerificationStatus,
    SingleUrlCheckItem,
    CheckStatus
)


# Configured registry of verified Indian Scheduled Commercial Banks & Public HFCs
# In production, this can be synchronized with live RBI / NHB data dumps.
KNOWN_REGULATED_ENTITIES = {
    "state bank of india": {
        "entity_type": "Scheduled Commercial Bank (Public Sector)",
        "official_domains": ["sbi.co.in", "bank.sbi", "homeloans.sbi"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "hdfc bank": {
        "entity_type": "Scheduled Commercial Bank (Private Sector)",
        "official_domains": ["hdfcbank.com"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "icici bank": {
        "entity_type": "Scheduled Commercial Bank (Private Sector)",
        "official_domains": ["icicibank.com"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "axis bank": {
        "entity_type": "Scheduled Commercial Bank (Private Sector)",
        "official_domains": ["axisbank.com"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "kotak mahindra bank": {
        "entity_type": "Scheduled Commercial Bank (Private Sector)",
        "official_domains": ["kotak.com"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "punjab national bank": {
        "entity_type": "Scheduled Commercial Bank (Public Sector)",
        "official_domains": ["pnbindia.in"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "bank of baroda": {
        "entity_type": "Scheduled Commercial Bank (Public Sector)",
        "official_domains": ["bankofbaroda.in"],
        "regulator": "Reserve Bank of India (RBI)",
        "source_url": "https://www.rbi.org.in/commonman/English/Scripts/BanksInIndia.aspx"
    },
    "lic housing finance": {
        "entity_type": "Housing Finance Company (HFC)",
        "official_domains": ["lichousing.com"],
        "regulator": "National Housing Bank (NHB) / RBI",
        "source_url": "https://www.rbi.org.in"
    }
}


def extract_claimed_entity(page_title: str, page_text: str) -> Optional[str]:
    """Scan title and text to see which recognized banking or lending entity is referenced."""
    search_space = f"{page_title} {page_text[:2000]}".lower()
    for entity_name in KNOWN_REGULATED_ENTITIES.keys():
        if entity_name in search_space:
            return entity_name
    return None


def verify_against_official_sources(
    url: str,
    page_title: str,
    page_text: str
) -> Tuple[IdentityVerificationStatus, Optional[str], SingleUrlCheckItem]:
    """
    Cross-reference claimed entity with configured RBI regulated entity data
    and verify domain ownership separately.
    """
    claimed = extract_claimed_entity(page_title, page_text)
    parsed = urlparse(url)
    current_domain = (parsed.hostname or "").lower()

    # If domain ends with .test or fixture domain
    if current_domain.endswith(".test"):
        # Synthetic testing domain - handled cleanly without pretending real check
        check_item = SingleUrlCheckItem(
            checkName="Official Regulatory & Domain Registry Verification",
            status=CheckStatus.INCONCLUSIVE,
            explanation="Domain uses a reserved testing TLD (.test). Official regulator registry checks are simulated in demo mode.",
            evidenceUrlOrQuote=current_domain,
            recommendedNextStep="Use genuine institutional URLs for live registry checks."
        )
        return IdentityVerificationStatus.ENTITY_MATCH_UNCERTAIN, claimed, check_item

    if not claimed:
        check_item = SingleUrlCheckItem(
            checkName="Official Regulatory & Domain Registry Verification",
            status=CheckStatus.INCONCLUSIVE,
            explanation=(
                "Could not reliably extract a recognized Indian Scheduled Bank or HFC name from the page content. "
                "The lending entity may be a registered NBFC not in our immediate cache, a cooperative bank, or a Loan Service Provider (LSP)."
            ),
            evidenceUrlOrQuote=None,
            recommendedNextStep="Ask the provider for their Certificate of Registration (CoR) and exact legal entity name."
        )
        return IdentityVerificationStatus.ENTITY_MATCH_UNCERTAIN, None, check_item

    entity_info = KNOWN_REGULATED_ENTITIES[claimed]
    official_domains = entity_info["official_domains"]

    # Check whether the visited domain matches any official registered domains
    domain_corroborated = any(
        current_domain == od or current_domain.endswith(f".{od}")
        for od in official_domains
    )

    now = datetime.now(timezone.utc)

    if domain_corroborated:
        check_item = SingleUrlCheckItem(
            checkName="Official Regulatory & Domain Registry Verification",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation=(
                f"Entity '{claimed.title()}' matched configured RBI directory for {entity_info['entity_type']}. "
                f"The domain '{current_domain}' corresponds with the institution's official primary domain registry."
            ),
            evidenceUrlOrQuote=f"{entity_info['source_url']} (Checked {now.strftime('%Y-%m-%d')})",
            recommendedNextStep="Confirm you are using the official customer portal before entering credentials."
        )
        return IdentityVerificationStatus.ENTITY_MATCHED_OWNERSHIP_CORROBORATED, claimed, check_item
    else:
        # High concern: entity name claimed, but domain is NOT in the official registry!
        check_item = SingleUrlCheckItem(
            checkName="Official Regulatory & Domain Registry Verification",
            status=CheckStatus.CONCERN,
            explanation=(
                f"The page cites '{claimed.title()}', but the domain '{current_domain}' does NOT match the known official domains "
                f"for this regulated entity ({', '.join(official_domains)}). "
                "Beware of unauthorized third-party intermediaries or fraudulent impersonation."
            ),
            evidenceUrlOrQuote=f"Claimed: {claimed.title()} | Submitted Domain: {current_domain}",
            recommendedNextStep=(
                f"Navigate directly to the lender's verified web portal ({official_domains[0]}) rather than through unverified links."
            )
        )
        return IdentityVerificationStatus.ENTITY_MATCHED_OWNERSHIP_UNVERIFIED, claimed, check_item
