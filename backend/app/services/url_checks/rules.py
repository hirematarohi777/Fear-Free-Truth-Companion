import re
from urllib.parse import urlparse
from typing import List, Dict, Any, Tuple
from app.schemas.url_checks import (
    SingleUrlCheckItem,
    CheckStatus,
    OverallOutcome,
    IdentityVerificationStatus
)
from app.services.url_checks.fetcher import SafeUrlFetchResult


def analyze_url_risk_signals(fetch_result: SafeUrlFetchResult) -> Tuple[List[SingleUrlCheckItem], OverallOutcome]:
    """Execute deterministic website risk rules and generate structured check items."""
    checks: List[SingleUrlCheckItem] = []
    has_significant_concern = False
    has_moderate_concern = False

    parsed_orig = urlparse(fetch_result.submitted_url)
    parsed_final = urlparse(fetch_result.final_url)
    orig_domain = parsed_orig.hostname or ""
    final_domain = parsed_final.hostname or ""

    # Check 1: HTTPS Encryption
    is_https = parsed_final.scheme.lower() == "https"
    if is_https:
        checks.append(SingleUrlCheckItem(
            checkName="Transport Layer Security (HTTPS)",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation=(
                "Webpage connection is encrypted using HTTPS. "
                "Note: An encrypted connection protects data in transit, but does not verify that the business itself is licensed or safe."
            ),
            evidenceUrlOrQuote=fetch_result.final_url,
            recommendedNextStep="Inspect lender registration separately from transport encryption."
        ))
    else:
        has_moderate_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Transport Layer Security (HTTPS)",
            status=CheckStatus.CONCERN,
            explanation="The website uses unencrypted HTTP. Any credentials or financial information submitted could be intercepted.",
            evidenceUrlOrQuote=fetch_result.final_url,
            recommendedNextStep="Do not submit personal documents or financial information on unencrypted websites."
        ))

    # Check 2: IP-Address URL
    is_raw_ip = bool(re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', orig_domain))
    if is_raw_ip:
        has_significant_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Raw IP Address Usage",
            status=CheckStatus.CONCERN,
            explanation="The loan website uses a bare numerical IP address rather than a registered domain name, which is atypical for legitimate lenders.",
            evidenceUrlOrQuote=orig_domain,
            recommendedNextStep="Avoid transacting with financial sites operating directly from raw IP addresses."
        ))
    else:
        checks.append(SingleUrlCheckItem(
            checkName="Raw IP Address Usage",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="The website utilizes a registered domain name rather than a raw IP address.",
            evidenceUrlOrQuote=orig_domain,
            recommendedNextStep="Proceed with domain and legal entity checks."
        ))

    # Check 3: Lookalike & Internationalized Domains (Punycode)
    if "xn--" in orig_domain or "xn--" in final_domain:
        has_significant_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Domain Character Integrity (Lookalike / Punycode)",
            status=CheckStatus.CONCERN,
            explanation="The domain uses Punycode / Internationalized characters, a common technique in phishing to imitate reputable banking institutions.",
            evidenceUrlOrQuote=orig_domain,
            recommendedNextStep="Do not log in. Verify the bank's true domain via verified official banking directories."
        ))
    else:
        checks.append(SingleUrlCheckItem(
            checkName="Domain Character Integrity (Lookalike / Punycode)",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="No suspicious Punycode or homoglyph domain patterns were detected in the hostname.",
            evidenceUrlOrQuote=orig_domain,
            recommendedNextStep="Continue verification of claimed corporate identity."
        ))

    # Check 4: Domain Redirection
    if orig_domain != final_domain and len(fetch_result.redirectChain) > 1:
        has_moderate_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Cross-Domain Redirection",
            status=CheckStatus.CONCERN,
            explanation=f"The submitted URL ({orig_domain}) redirected across domains to '{final_domain}'.",
            evidenceUrlOrQuote=" -> ".join(fetch_result.redirectChain),
            recommendedNextStep="Verify if the destination domain is the genuine operating portal of the intended lender."
        ))
    else:
        checks.append(SingleUrlCheckItem(
            checkName="Cross-Domain Redirection",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="No unexpected cross-domain redirects occurred.",
            evidenceUrlOrQuote=fetch_result.final_url,
            recommendedNextStep="Confirm domain matches official records."
        ))

    page_text = fetch_result.extracted_text.lower()

    # Check 5: Guaranteed Approval / Unrealistic Claims
    unrealistic_patterns = [
        (r'\b(100%|guaranteed)\s+(approval|sanction|loan)\b', "Guaranteed 100% loan approval claim"),
        (r'\b(no\s+cibil|without\s+cibil|zero\s+cibil|no\s+credit\s+check)\b', "No credit or CIBIL score check required"),
        (r'\b(instant\s+sanction\s+in\s+[1-5]\s+mins?)\b', "Unrealistic instant sanction guarantee")
    ]
    unrealistic_found = []
    for pat, label in unrealistic_patterns:
        m = re.search(pat, page_text)
        if m:
            unrealistic_found.append((label, m.group(0)))

    if unrealistic_found:
        has_significant_concern = True
        labels_str = "; ".join([f"{l} ('{q}')" for l, q in unrealistic_found])
        checks.append(SingleUrlCheckItem(
            checkName="Unrealistic Financial & Approval Claims",
            status=CheckStatus.CONCERN,
            explanation=f"The website makes high-risk or prohibited promotional claims: {labels_str}. Under RBI rules, prudent credit underwriting is mandatory.",
            evidenceUrlOrQuote=unrealistic_found[0][1],
            recommendedNextStep="Treat guaranteed approval claims as an indicator of predatory lending or advance-fee scams."
        ))
    else:
        checks.append(SingleUrlCheckItem(
            checkName="Unrealistic Financial & Approval Claims",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="No overt 'guaranteed approval' or 'no credit check' claims were detected in visible page text.",
            evidenceUrlOrQuote=None,
            recommendedNextStep="Request a Key Facts Statement (KFS) detailing approval criteria."
        ))

    # Check 6: Advance Fee / Upfront Payment Demand
    advance_fee_patterns = [
        r'\b(pay\s+(?:processing|registration|file|clearance|security)\s+fee\s+(?:in\s+advance|before\s+disbursement|upfront))\b',
        r'\b(security\s+deposit\s+required\s+before\s+transfer)\b',
        r'\b(refundable\s+insurance\s+deposit\s+to\s+release\s+funds)\b'
    ]
    advance_fee_found = None
    for pat in advance_fee_patterns:
        m = re.search(pat, page_text)
        if m:
            advance_fee_found = m.group(0)
            break

    if advance_fee_found:
        has_significant_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Advance Fee Payment Requirement",
            status=CheckStatus.CONCERN,
            explanation=(
                f"Page text requests fee payment before loan funds are released ('{advance_fee_found}'). "
                "Legitimate Indian banks and NBFCs deduct fees from the sanctioned loan disbursement or take crossed cheques in the name of the institution, "
                "never requesting upfront money transfers to personal bank accounts or UPI IDs."
            ),
            evidenceUrlOrQuote=advance_fee_found,
            recommendedNextStep="NEVER transfer money in advance to secure a loan. Cease interaction immediately."
        ))
    else:
        checks.append(SingleUrlCheckItem(
            checkName="Advance Fee Payment Requirement",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="No upfront advance-fee demands were identified in the readable content.",
            evidenceUrlOrQuote=None,
            recommendedNextStep="Confirm whether fees are deducted from disbursement or paid via official bank receipt."
        ))

    # Check 7: Credential Solicitation (OTPs / Passwords / PINs)
    cred_patterns = [
        r'\b(?:enter\s+your\s+(?:bank\s+|netbanking\s+)?(?:password|pin)|netbanking\s+password)\b',
        r'\b(?:share\s+(?:the\s+)?otp\s+received)\b',
        r'\b(?:atm\s+card\s+pin)\b'
    ]
    cred_found = None
    for pat in cred_patterns:
        m = re.search(pat, page_text)
        if m:
            cred_found = m.group(0)
            break

    if cred_found:
        has_significant_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Sensitive Credential Solicitation",
            status=CheckStatus.CONCERN,
            explanation=f"Page appears to request private banking secrets ('{cred_found}'). Genuine lenders never ask for ATM PINs or net banking passwords.",
            evidenceUrlOrQuote=cred_found,
            recommendedNextStep="Do not share OTPs, PINs, or net banking passwords under any circumstances."
        ))
    else:
        checks.append(SingleUrlCheckItem(
            checkName="Sensitive Credential Solicitation",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="No solicitations for banking passwords or OTPs detected on the page.",
            evidenceUrlOrQuote=None,
            recommendedNextStep="Remember to never share OTPs with loan agents."
        ))

    # Check 8: Regulatory Disclosure & Grievance Contact
    has_grievance = bool(re.search(r'\b(grievance\s+officer|nodal\s+officer|ombudsman)\b', page_text))
    has_privacy_link = any("privacy" in link.lower() for link in fetch_result.links) or ("privacy policy" in page_text)
    
    if has_grievance and has_privacy_link:
        checks.append(SingleUrlCheckItem(
            checkName="Grievance Redressal & Privacy Disclosure",
            status=CheckStatus.NO_CONCERN_FOUND,
            explanation="Website mentions a Grievance Redressal / Nodal Officer and maintains a privacy policy disclosure.",
            evidenceUrlOrQuote=None,
            recommendedNextStep="Review the stated grievance redressal timeline and escalations."
        ))
    else:
        has_moderate_concern = True
        checks.append(SingleUrlCheckItem(
            checkName="Grievance Redressal & Privacy Disclosure",
            status=CheckStatus.CONCERN,
            explanation=(
                "Missing clear grievance redressal officer details or privacy policy link. "
                "Under RBI Digital Lending guidelines, regulated entities and their lending service providers must prominently disclose grievance officer contact information."
            ),
            evidenceUrlOrQuote=None,
            recommendedNextStep="Request the full name and official contact of the designated Nodal Grievance Officer."
        ))

    # Overall outcome classification
    if has_significant_concern:
        outcome = OverallOutcome.SIGNIFICANT_RISKS
    elif has_moderate_concern:
        outcome = OverallOutcome.SOME_CONCERNS
    elif len(checks) > 4:
        outcome = OverallOutcome.NO_MAJOR_INDICATORS
    else:
        outcome = OverallOutcome.INSUFFICIENT_EVIDENCE

    return checks, outcome
