"""Paddle webhook signature verification.

Paddle Billing v2 signs every webhook with HMAC-SHA256 over `{timestamp}:{raw_body}`.
The header is `Paddle-Signature: ts=...;h1=...` (a single h1 in current docs, but
the format supports multiple signatures during key rotation).
"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Iterable


def _parse_signature_header(header: str) -> dict[str, list[str]]:
    parts: dict[str, list[str]] = {}
    if not header:
        return parts
    for chunk in header.split(';'):
        if '=' not in chunk:
            continue
        key, value = chunk.split('=', 1)
        parts.setdefault(key.strip(), []).append(value.strip())
    return parts


def verify_signature(
    *,
    raw_body: bytes,
    signature_header: str,
    secret: str,
    max_age_seconds: int = 300,
) -> bool:
    """Return True iff the signature header is valid and recent."""
    if not signature_header or not secret:
        return False
    parsed = _parse_signature_header(signature_header)
    ts_values = parsed.get('ts')
    h1_values = parsed.get('h1')
    if not ts_values or not h1_values:
        return False
    ts = ts_values[0]
    try:
        ts_int = int(ts)
    except ValueError:
        return False

    if max_age_seconds > 0 and abs(time.time() - ts_int) > max_age_seconds:
        return False

    payload = ts.encode('ascii') + b':' + raw_body
    expected = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in h1_values)
