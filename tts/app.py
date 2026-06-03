"""Self-hosted neural TTS (Piper) — CPU, free, runs anywhere.

POST /synthesize  {text, lang}  -> audio/wav
GET  /health
"""
import io
import wave

import numpy as np
from fastapi import FastAPI, Response
from pydantic import BaseModel
from piper import PiperVoice

VOICE_FILES = {
    "ru": "/voices/ru_RU-dmitri-medium.onnx",
    "en": "/voices/en_US-ryan-high.onnx",
}

# Load voices once at startup (held in memory for fast synthesis).
_VOICES: dict[str, PiperVoice] = {}
for lang, path in VOICE_FILES.items():
    try:
        _VOICES[lang] = PiperVoice.load(path)
    except Exception as exc:  # noqa: BLE001
        print(f"[tts] failed to load {lang} voice: {exc}")

app = FastAPI(title="Tarot TTS")


class SynthRequest(BaseModel):
    text: str
    lang: str = "ru"


def _mysterious(wav_bytes: bytes) -> bytes:
    """Turn a plain Piper voice into a mystical one: a soft hall reverb for space
    plus a slight deepening/slowing — atmospheric rather than casual."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        rate = wf.getframerate()
        nch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

    # Warmth: a short moving-average low-pass softens harsh highs → gentle, lulling.
    kernel = np.ones(7, dtype=np.float32) / 7.0
    audio = np.convolve(audio, kernel, mode="same")

    out = audio.copy()
    # Dreamy, longer reverb tail → soothing, lullaby-like space.
    for delay_ms, gain in ((50, 0.30), (110, 0.22), (190, 0.15), (290, 0.09), (400, 0.05)):
        d = int(rate * delay_ms / 1000)
        if d < len(audio):
            out[d:] += audio[: len(audio) - d] * gain

    peak = float(np.max(np.abs(out))) or 1.0
    # Quieter (24k vs 32k full-scale) so it sits gently under the ambient drone.
    out = (out / peak * 24000.0).astype(np.int16)

    # Lower the playback rate ~12% → deeper, slower, calmer (a soft lullaby pace).
    out_rate = int(rate * 0.88)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(nch)
        wf.setsampwidth(sampwidth)
        wf.setframerate(out_rate)
        wf.writeframes(out.tobytes())
    return buf.getvalue()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "voices": sorted(_VOICES.keys())}


@app.post("/synthesize")
def synthesize(req: SynthRequest) -> Response:
    text = (req.text or "").strip()
    if not text:
        return Response(status_code=400, content=b"empty text")
    voice = _VOICES.get(req.lang) or _VOICES.get("ru") or next(iter(_VOICES.values()), None)
    if voice is None:
        return Response(status_code=503, content=b"no voice loaded")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        voice.synthesize(text, wf)
    data = _mysterious(buf.getvalue())
    return Response(content=data, media_type="audio/wav", headers={
        "Cache-Control": "public, max-age=86400",
    })
