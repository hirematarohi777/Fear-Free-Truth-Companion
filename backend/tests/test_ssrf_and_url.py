import pytest
import ipaddress
from app.services.url_checks.fetcher import (
    validate_url_syntax,
    is_ip_disallowed,
    SSRFValidationError,
    SafeUrlFetchResult
)
from app.services.url_checks.rules import analyze_url_risk_signals
from app.services.url_checks.official_sources import (
    verify_against_official_sources,
    IdentityVerificationStatus
)
from app.schemas.url_checks import CheckStatus, OverallOutcome


def test_ssrf_url_syntax_validation():
    # Valid
    scheme, host, port = validate_url_syntax("https://sbi.co.in/personal-banking")
    assert scheme == "https"
    assert host == "sbi.co.in"
    assert port == 443

    scheme, host, port = validate_url_syntax("http://bank.example.org:80/loans")
    assert scheme == "http"
    assert port == 80

    # Rejected: scheme
    with pytest.raises(SSRFValidationError, match="Only HTTP and HTTPS"):
        validate_url_syntax("ftp://files.example.com")

    with pytest.raises(SSRFValidationError, match="Only HTTP and HTTPS"):
        validate_url_syntax("file:///etc/passwd")

    # Rejected: embedded credentials
    with pytest.raises(SSRFValidationError, match="embedded usernames"):
        validate_url_syntax("https://admin:secret@malicious.com")

    # Rejected: disallowed port
    with pytest.raises(SSRFValidationError, match="Port 8080 is not permitted"):
        validate_url_syntax("https://example.com:8080/path")

    with pytest.raises(SSRFValidationError, match="Port 27017 is not permitted"):
        validate_url_syntax("http://example.com:27017")


def test_ssrf_disallowed_ips():
    # Loopback
    assert is_ip_disallowed(ipaddress.ip_address("127.0.0.1")) is True
    assert is_ip_disallowed(ipaddress.ip_address("::1")) is True

    # Private
    assert is_ip_disallowed(ipaddress.ip_address("10.0.0.5")) is True
    assert is_ip_disallowed(ipaddress.ip_address("192.168.1.100")) is True
    assert is_ip_disallowed(ipaddress.ip_address("172.16.0.1")) is True

    # Cloud metadata
    assert is_ip_disallowed(ipaddress.ip_address("169.254.169.254")) is True
    assert is_ip_disallowed(ipaddress.ip_address("169.254.169.253")) is True

    # Public routable IPs (Allowed)
    assert is_ip_disallowed(ipaddress.ip_address("8.8.8.8")) is False
    assert is_ip_disallowed(ipaddress.ip_address("1.1.1.1")) is False


def test_url_risk_signals_detection():
    # Mock a suspicious loan offer page
    suspicious_fetch = SafeUrlFetchResult(
        submitted_url="http://quick-instant-loan.xyz/apply",
        final_url="http://quick-instant-loan.xyz/apply",
        status_code=200,
        redirect_chain=["http://quick-instant-loan.xyz/apply"],
        page_title="Instant Loan - 100% Guaranteed Approval",
        extracted_text=(
            "Apply now for 100% guaranteed approval instant loan without CIBIL score check! "
            "Please pay processing fee in advance before disbursement to activate your file. "
            "Enter your netbanking password to verify income."
        ),
        tls_info={"is_https": False, "cert_valid": False},
        headers={},
        links=[]
    )

    checks, outcome = analyze_url_risk_signals(suspicious_fetch)

    assert outcome == OverallOutcome.SIGNIFICANT_RISKS

    # Verify specific signals identified
    check_names = {c.checkName: c for c in checks}
    assert check_names["Transport Layer Security (HTTPS)"].status == CheckStatus.CONCERN
    assert check_names["Unrealistic Financial & Approval Claims"].status == CheckStatus.CONCERN
    assert check_names["Advance Fee Payment Requirement"].status == CheckStatus.CONCERN
    assert check_names["Sensitive Credential Solicitation"].status == CheckStatus.CONCERN


def test_official_sources_corroboration_vs_unverified():
    # 1. Official Bank Domain Match
    status1, claimed1, check1 = verify_against_official_sources(
        url="https://sbi.co.in/web/personal-banking/loans/home-loans",
        page_title="State Bank of India - Home Loans",
        page_text="Welcome to State Bank of India official portal for personal and housing finance."
    )
    assert status1 == IdentityVerificationStatus.ENTITY_MATCHED_OWNERSHIP_CORROBORATED
    assert claimed1 == "state bank of india"
    assert check1.status == CheckStatus.NO_CONCERN_FOUND

    # 2. Impersonation / Unverified Domain: Claims HDFC Bank, but operates on suspicious domain
    status2, claimed2, check2 = verify_against_official_sources(
        url="https://hdfc-instant-loans.online/apply",
        page_title="HDFC Bank Easy Personal & Home Loan",
        page_text="Apply for fast loan sanction from HDFC Bank."
    )
    assert status2 == IdentityVerificationStatus.ENTITY_MATCHED_OWNERSHIP_UNVERIFIED
    assert claimed2 == "hdfc bank"
    assert check2.status == CheckStatus.CONCERN

    # 3. Unrecognized or unlisted entity produces "Entity match uncertain"
    status3, claimed3, check3 = verify_against_official_sources(
        url="https://randomfinanceltd.com",
        page_title="Random Finance Service Provider",
        page_text="We offer peer to peer loan matching services."
    )
    assert status3 == IdentityVerificationStatus.ENTITY_MATCH_UNCERTAIN
    assert check3.status == CheckStatus.INCONCLUSIVE
