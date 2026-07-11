"""Security response headers for every endpoint + a CSP for the served SPAs.

Pure-ASGI middleware (no BaseHTTPMiddleware — that would buffer StreamingResponse
bodies, and /chat + /kid-chat stream SSE).

Headers:
- X-Content-Type-Options / Referrer-Policy / X-Frame-Options / Permissions-Policy
  always.
- Strict-Transport-Security only when ENABLE_HSTS=1 (prod is HTTPS-terminated at
  Railway; local dev is plain HTTP and must not get pinned).
- Content-Security-Policy only on the SPA document paths (/dashboard, /cms). The
  API itself doesn't render HTML, and the SPAs are Vite bundles: self-hosted
  assets + inline styles (tailwind preflight) + PostHog for analytics.
"""
from __future__ import annotations

import os

_ALWAYS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"x-frame-options", b"DENY"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
]

_HSTS = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")

# posthog-js talks to the PostHog US ingestion + assets hosts (Phase 3).
_CSP = (
    b"content-security-policy",
    b"default-src 'self'; script-src 'self' https://us-assets.i.posthog.com; "
    b"style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
    b"connect-src 'self' https://us.i.posthog.com https://us-assets.i.posthog.com; "
    b"frame-ancestors 'none'",
)

_SPA_PREFIXES = ("/dashboard", "/cms")


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app
        self.hsts = os.getenv("ENABLE_HSTS", "0").lower() in ("1", "true", "yes")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        is_spa = any(path == p or path.startswith(p + "/") for p in _SPA_PREFIXES)

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {k.lower() for k, _ in headers}
                for k, v in _ALWAYS:
                    if k not in existing:
                        headers.append((k, v))
                if self.hsts and _HSTS[0] not in existing:
                    headers.append(_HSTS)
                if is_spa and _CSP[0] not in existing:
                    headers.append(_CSP)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
