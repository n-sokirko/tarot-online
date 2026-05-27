"""IP-based rate limiting for anonymous AI interpretation requests.

Uses Django's cache backend (Redis in production) — no migration needed.
"""
from __future__ import annotations

from django.core.cache import cache
from django.utils import timezone

# Anonymous users get this many free AI interpretations per day (per IP).
ANON_DAILY_LIMIT = 3


def get_client_ip(request) -> str:
    """Return the real client IP, respecting Cloudflare and nginx proxy headers."""
    # Cloudflare sets CF-Connecting-IP to the original visitor IP.
    cf = request.META.get("HTTP_CF_CONNECTING_IP", "").strip()
    if cf:
        return cf
    # Generic reverse-proxy header (nginx / other CDN).
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def check_anon_daily_limit(request, kind: str = "ai") -> tuple[bool, int]:
    """Check whether this anonymous request is within the daily free limit.

    Returns:
        (allowed, remaining) — if allowed is False the caller should return 429.
    """
    ip = get_client_ip(request)
    today = timezone.now().date().isoformat()
    key = f"anon_limit:{kind}:{ip}:{today}"

    count = cache.get(key, 0)
    if count >= ANON_DAILY_LIMIT:
        return False, 0

    # Increment; TTL = 25 h so the key definitely expires before the next day
    # even with small clock skew.
    cache.set(key, count + 1, timeout=90_000)
    return True, ANON_DAILY_LIMIT - count - 1
