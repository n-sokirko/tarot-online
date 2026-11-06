"""Personal tarologist: persona, style mirroring, reading memory and dossier.

``build()`` turns a person's TarotProfile into an extra system block (and maybe a
stronger model); ``parse_tail()`` strips the hidden <memo>/<dossier> tail the
model writes; ``TailFilter`` keeps that tail out of a live SSE stream.

Who gets what:
- signed-in, memory on → memos of recent readings (cheap, all tiers);
- Premium → also the dossier, a persona and style mirroring, on the persona model;
- Val 18+ → Premium plus a confirmed age, otherwise it quietly falls back to Val.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.readings.models import Interpretation, Reading, TarotProfile
from services.ai import personas

MEMORY_ITEMS = 5
MEMORY_DAYS = 60

_MEMO_RE = re.compile(r'<memo>(.*?)</memo>', re.S | re.I)
_DOSSIER_RE = re.compile(r'<dossier>(.*?)</dossier>', re.S | re.I)
_TAIL_START = re.compile(r'<(memo|dossier)\b', re.I)
_TAGS = ('<memo', '<dossier')


@dataclass
class Personalization:
    system: str = ''
    model: str | None = None        # override for the tier's model, if any
    wants_memo: bool = False
    wants_dossier: bool = False


def get_profile(user) -> TarotProfile | None:
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    profile, _ = TarotProfile.objects.get_or_create(user=user)
    return profile


def effective_persona(profile: TarotProfile, premium: bool) -> str:
    """The persona that will actually speak, after the Premium and age gates."""
    p = profile.persona
    if not premium:
        return TarotProfile.PERSONA_CLASSIC
    if p == TarotProfile.PERSONA_VAL18 and not profile.adult_confirmed_at:
        return TarotProfile.PERSONA_VAL
    return p


def _memory_lines(reading: Reading) -> list[str]:
    since = timezone.now() - timedelta(days=MEMORY_DAYS)
    past = (Interpretation.objects
            .filter(reading__user_id=reading.user_id, reading__deleted_at__isnull=True,
                    reading__created_at__gte=since)
            .exclude(reading_id=reading.pk).exclude(memo='')
            .select_related('reading').order_by('-generated_at')[:MEMORY_ITEMS])
    out = []
    for i in past:
        q = (i.reading.question or '').strip().replace('\n', ' ')[:120]
        day = timezone.localtime(i.reading.created_at).strftime('%d.%m')
        out.append(f'- {day} · «{q}» · {i.memo}' if q else f'- {day} · {i.memo}')
    return out


def build(user, reading: Reading, tier: str) -> Personalization:
    profile = get_profile(user)
    if profile is None:
        return Personalization()
    ru = reading.locale == 'ru'
    premium = tier in ('premium', 'deep')
    persona = effective_persona(profile, premium)
    mirror = premium and profile.mirror_style
    blocks: list[str] = []

    if persona != TarotProfile.PERSONA_CLASSIC or mirror:
        blocks.append(personas.voice_override(reading.locale))
        if persona != TarotProfile.PERSONA_CLASSIC:
            blocks.append(personas.persona_prompt(persona, reading.locale))
        if mirror:
            adult = bool(profile.adult_confirmed_at)
            blocks.append(personas.mirror_prompt(reading.locale, allow_swearing=adult))

    wants_memo = profile.remember and reading.user_id is not None
    wants_dossier = wants_memo and premium
    if wants_memo:
        lines = _memory_lines(reading)
        if lines:
            blocks.append((personas.MEMORY_HEADER_RU if ru else personas.MEMORY_HEADER_EN)
                          + '\n' + '\n'.join(lines))
    if wants_dossier and profile.dossier:
        blocks.append((personas.DOSSIER_HEADER_RU if ru else personas.DOSSIER_HEADER_EN)
                      + '\n' + '\n'.join(f'- {x}' for x in profile.dossier))
    if wants_memo:
        blocks.append(personas.MEMO_TAIL_RU if ru else personas.MEMO_TAIL_EN)
    if wants_dossier:
        blocks.append(personas.DOSSIER_TAIL_RU if ru else personas.DOSSIER_TAIL_EN)

    model = None
    if premium and (persona != TarotProfile.PERSONA_CLASSIC or mirror):
        # Haiku ignores the voice blocks too often (see services/ai/personas.py).
        model = getattr(settings, 'ANTHROPIC_MODEL_PERSONA', '') or None
    return Personalization(system='\n\n'.join(blocks), model=model,
                           wants_memo=wants_memo, wants_dossier=wants_dossier)


def clean_dossier(items) -> list[str]:
    out: list[str] = []
    for x in items or []:
        if not isinstance(x, str):
            continue
        x = x.strip().lstrip('-•').strip()
        if x and x not in out:
            out.append(x[:TarotProfile.DOSSIER_MAX_LEN])
    return out[:TarotProfile.DOSSIER_MAX_ITEMS]


def parse_tail(body: str) -> tuple[str, str, list[str] | None]:
    """Split the model output into (visible body, memo, dossier or None)."""
    memo_m = _MEMO_RE.search(body)
    dossier_m = _DOSSIER_RE.search(body)
    memo = re.sub(r'\s+', ' ', memo_m.group(1)).strip()[:300] if memo_m else ''
    dossier = clean_dossier(dossier_m.group(1).splitlines()) if dossier_m else None
    cut = _TAIL_START.search(body)
    visible = body[:cut.start()] if cut else body
    return visible.rstrip(), memo, dossier


def save_tail(user, interpretation: Interpretation, memo: str, dossier: list[str] | None,
              p: Personalization) -> None:
    if p.wants_memo and memo:
        interpretation.memo = memo
        interpretation.save(update_fields=['memo'])
    if p.wants_dossier and dossier:
        TarotProfile.objects.filter(user=user).update(dossier=dossier, updated_at=timezone.now())


class TailFilter:
    """Feed streamed chunks; emits only the visible part, holding back anything
    that might be the start of the hidden <memo>/<dossier> tail."""

    def __init__(self) -> None:
        self.buf = ''
        self.done = False

    def feed(self, chunk: str) -> str:
        if self.done:
            return ''
        self.buf += chunk
        m = _TAIL_START.search(self.buf)
        if m:
            out, self.buf, self.done = self.buf[:m.start()], '', True
            return out
        lt = self.buf.rfind('<')
        if lt != -1 and any(t.startswith(self.buf[lt:].lower()) for t in _TAGS):
            out, self.buf = self.buf[:lt], self.buf[lt:]
            return out
        out, self.buf = self.buf, ''
        return out

    def flush(self) -> str:
        out, self.buf = ('' if self.done else self.buf), ''
        return out
