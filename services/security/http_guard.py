"""HTTP response hardening helpers for the offline UI."""
from __future__ import annotations

from typing import Mapping

CSP_HEADER = (
    "default-src 'none';"
    " script-src 'self';"
    " style-src 'self';"
    " img-src 'self';"
    " connect-src 'self';"
    " font-src 'self';"
    " object-src 'none';"
    " base-uri 'none';"
    " form-action 'self';"
    " frame-ancestors 'none'"
)
SECURE_HEADERS = {
    "Content-Security-Policy": CSP_HEADER,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "*=(\"\")",
}
AUDIT_CSP_APPLIED = "CSP applied (offline assets only)."


def apply_secure_headers(response: Mapping[str, str] | dict) -> tuple[Mapping[str, str], str]:
    """Return headers with secure defaults applied and an audit string."""
    headers = dict(response)
    headers.update(SECURE_HEADERS)
    return headers, AUDIT_CSP_APPLIED
