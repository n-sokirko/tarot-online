"""Signed short-lived tokens for Telegram payment deep-links.

Format: base64url(json_payload).hmac_prefix
The token is embedded in t.me/tarott_online_bot?start=buy_TOKEN
"""
import base64
import hashlib
import hmac
import json
import time

from django.conf import settings


def _secret() -> bytes:
    return settings.TELEGRAM_PAYMENT_SECRET.encode()


def generate_payment_token(user_id: int, plan_slug: str) -> str:
    payload = json.dumps({'u': user_id, 'p': plan_slug, 't': int(time.time())}, separators=(',', ':'))
    b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
    sig = hmac.new(_secret(), b64.encode(), hashlib.sha256).hexdigest()[:24]
    return f'{b64}.{sig}'


def validate_payment_token(token: str, max_age: int = 3600) -> dict | None:
    """Return {'user_id': int, 'plan_slug': str} or None if invalid/expired."""
    try:
        b64, sig = token.rsplit('.', 1)
        expected = hmac.new(_secret(), b64.encode(), hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected):
            return None
        pad = (4 - len(b64) % 4) % 4
        data = json.loads(base64.urlsafe_b64decode(b64 + '=' * pad).decode())
        if time.time() - data['t'] > max_age:
            return None
        return {'user_id': data['u'], 'plan_slug': data['p']}
    except Exception:
        return None
