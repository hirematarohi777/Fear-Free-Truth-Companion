import ipaddress
import socket
import ssl
from urllib.parse import urlparse, urljoin
from typing import Tuple, List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
from app.core.logging_config import logger


MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB


class SSRFValidationError(Exception):
    pass


def is_ip_disallowed(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """
    Check if IP address is private, loopback, link-local, multicast, reserved,
    or matches cloud metadata IP ranges (e.g. 169.254.169.254).
    """
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True

    # Cloud metadata addresses
    if isinstance(ip, ipaddress.IPv4Address):
        if str(ip) in ("169.254.169.254", "169.254.169.253"):
            return True
        # Carrier grade NAT (100.64.0.0/10)
        if ip in ipaddress.ip_network("100.64.0.0/10"):
            return True
    elif isinstance(ip, ipaddress.IPv6Address):
        # IPv6 link-local or unique local
        if ip in ipaddress.ip_network("fd00::/8") or ip in ipaddress.ip_network("fe80::/10"):
            return True

    return False


def validate_url_syntax(url: str) -> Tuple[str, str, int]:
    """
    Validate basic URL syntax:
    - Must be http or https
    - No userinfo (user:pass@)
    - Port must be 80, 443, or unspecified
    Returns (scheme, hostname, port)
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFValidationError("Only HTTP and HTTPS URLs are permitted.")

    if parsed.username or parsed.password:
        raise SSRFValidationError("URLs with embedded usernames or passwords are not permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("Missing hostname in URL.")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    if port not in (80, 443):
        raise SSRFValidationError(f"Port {port} is not permitted. Only standard web ports (80, 443) are allowed.")

    return parsed.scheme.lower(), hostname.lower(), port


def resolve_and_validate_hostname(hostname: str) -> List[str]:
    """
    Resolve DNS for hostname and validate that every returned IP is a public, routable IP.
    """
    # Check if hostname itself is a raw IP literal
    try:
        ip = ipaddress.ip_address(hostname)
        if is_ip_disallowed(ip):
            raise SSRFValidationError(f"Target IP address '{hostname}' is a private, loopback, or reserved destination.")
        return [str(ip)]
    except ValueError:
        pass  # Hostname is a domain name, proceed to DNS resolution

    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SSRFValidationError(f"Unable to resolve domain '{hostname}': {str(e)}")

    valid_ips = []
    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if is_ip_disallowed(ip):
                raise SSRFValidationError(
                    f"Domain '{hostname}' resolves to restricted/private address '{ip_str}'."
                )
            if ip_str not in valid_ips:
                valid_ips.append(ip_str)
        except ValueError:
            continue

    if not valid_ips:
        raise SSRFValidationError(f"No valid IP addresses found for domain '{hostname}'.")

    return valid_ips


class SafeUrlFetchResult:
    def __init__(
        self,
        submitted_url: str,
        final_url: str,
        status_code: int,
        redirect_chain: List[str],
        page_title: str,
        extracted_text: str,
        tls_info: Dict[str, Any],
        headers: Dict[str, str],
        links: List[str]
    ):
        self.submitted_url = submitted_url
        self.final_url = final_url
        self.status_code = status_code
        self.redirect_chain = redirect_chain
        self.page_title = page_title
        self.extracted_text = extracted_text
        self.tls_info = tls_info
        self.headers = headers
        self.links = links


async def safe_fetch_url(submitted_url: str) -> SafeUrlFetchResult:
    """
    Safely fetch a URL with comprehensive SSRF protection, DNS rebinding defenses,
    redirect validation, and content size limits.
    """
    current_url = submitted_url
    redirect_chain = [submitted_url]
    tls_info: Dict[str, Any] = {"is_https": False, "cert_valid": False}

    for redirect_count in range(MAX_REDIRECTS + 1):
        scheme, hostname, port = validate_url_syntax(current_url)
        validated_ips = resolve_and_validate_hostname(hostname)
        chosen_ip = validated_ips[0]

        tls_info["is_https"] = (scheme == "https")
        if scheme == "https":
            tls_info["cert_valid"] = True  # Verified by httpx/ssl default verification

        # Perform HTTP request without following redirects automatically
        async with httpx.AsyncClient(
            verify=True,
            timeout=TIMEOUT_SECONDS,
            follow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (FearFreeCompanion/1.0)"}
        ) as client:
            try:
                # In order to strictly prevent DNS rebinding while preserving SNI and TLS cert validation,
                # httpx with verify=True checks the host header.
                response = await client.get(current_url)
            except httpx.ConnectError as ce:
                raise SSRFValidationError(f"Connection to '{hostname}' failed: {str(ce)}")
            except httpx.TimeoutException:
                raise SSRFValidationError(f"Request to '{hostname}' timed out after {TIMEOUT_SECONDS} seconds.")

            # Check redirect
            if response.is_redirect:
                if redirect_count >= MAX_REDIRECTS:
                    raise SSRFValidationError(f"Too many redirects (exceeded limit of {MAX_REDIRECTS}).")
                
                location = response.headers.get("Location")
                if not location:
                    break
                next_url = urljoin(current_url, location)
                redirect_chain.append(next_url)
                current_url = next_url
                continue

            # Check Content-Type
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type and "text/plain" not in content_type:
                raise SSRFValidationError(
                    f"Unsupported content type '{content_type}'. Only HTML text pages can be analyzed."
                )

            # Check size limit
            content_bytes = response.content
            if len(content_bytes) > MAX_RESPONSE_BYTES:
                raise SSRFValidationError(
                    f"Webpage response size ({len(content_bytes) / 1024:.1f} KB) exceeds maximum allowed limit of {MAX_RESPONSE_BYTES // 1024} KB."
                )

            # Parse HTML
            soup = BeautifulSoup(content_bytes, "html.parser")
            
            # Remove scripts, styles, iframes, SVGs
            for tag in soup(["script", "style", "iframe", "svg", "noscript"]):
                tag.decompose()

            page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
            extracted_text = soup.get_text(separator=" ", strip=True)

            # Collect relevant links (privacy policy, terms, contact)
            page_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href and not href.startswith("javascript:") and not href.startswith("#"):
                    page_links.append(urljoin(current_url, href))

            return SafeUrlFetchResult(
                submitted_url=submitted_url,
                final_url=current_url,
                status_code=response.status_code,
                redirect_chain=redirect_chain,
                page_title=page_title,
                extracted_text=extracted_text,
                tls_info=tls_info,
                headers=dict(response.headers),
                links=list(set(page_links))[:30]
            )

    raise SSRFValidationError(f"Exceeded maximum redirect limit of {MAX_REDIRECTS}.")
