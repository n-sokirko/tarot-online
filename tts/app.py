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
    out = audio.copy()
    # Sum a few decaying delayed copies → an ethereal cathedral-like reverb tail.
    for delay_ms, gain in ((45, 0.34), (95, 0.22), (160, 0.14), (240, 0.08)):
        d = int(rate * delay_ms / 1000)
        if d < len(audio):
            out[d:] += audio[: len(audio) - d] * gain

    peak = float(np.max(np.abs(out))) or 1.0
    out = (out / peak * 31000.0).astype(np.int16)

    # Lower the playback rate ~8% → deeper timbre + slower, more deliberate pace.
    out_rate = int(rate * 0.92)
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
