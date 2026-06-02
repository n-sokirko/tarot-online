"""Self-hosted neural TTS (Piper) — CPU, free, runs anywhere.

POST /synthesize  {text, lang}  -> audio/wav
GET  /health
"""
import io
import wave

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
    data = buf.getvalue()
    return Response(content=data, media_type="audio/wav", headers={
        "Cache-Control": "public, max-age=86400",
    })
