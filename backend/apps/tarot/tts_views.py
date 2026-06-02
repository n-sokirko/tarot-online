"""Proxy to the self-hosted Piper TTS service.

POST /api/v1/tts/  {text, lang}  -> audio/wav

Keeps the TTS service internal (not exposed publicly) and lets the frontend
fetch synthesized audio from our own origin.
"""
from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def tts_synthesize(request) -> HttpResponse:
    import requests as http

    text = (request.data.get('text') or '').strip()[:5000]
    lang = request.data.get('lang') or 'ru'
    if lang not in ('ru', 'en'):
        lang = 'ru'
    if not text:
        return HttpResponse(b'empty text', status=400)

    tts_url = getattr(settings, 'TTS_URL', '') or 'http://tts:5000'
    try:
        r = http.post(f'{tts_url}/synthesize', json={'text': text, 'lang': lang}, timeout=120)
        r.raise_for_status()
    except Exception:  # noqa: BLE001 — TTS is best-effort; frontend falls back
        return HttpResponse(b'tts_unavailable', status=503)

    resp = HttpResponse(r.content, content_type='audio/wav')
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp
