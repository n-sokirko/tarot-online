FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Piper bundles espeak-ng phoneme data via piper-phonemize — no system apt needed.
RUN pip install --no-cache-dir piper-tts==1.2.0 fastapi==0.111.0 uvicorn==0.30.1

# Download a deep male RU voice (dmitri) and a male EN voice (ryan) via Python.
RUN mkdir -p /voices && python -c "import urllib.request as u; b='https://huggingface.co/rhasspy/piper-voices/resolve/main'; [u.urlretrieve(b+s,d) or print('got',d) for d,s in {'/voices/ru_RU-dmitri-medium.onnx':'/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx','/voices/ru_RU-dmitri-medium.onnx.json':'/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx.json','/voices/en_US-ryan-high.onnx':'/en/en_US/ryan/high/en_US-ryan-high.onnx','/voices/en_US-ryan-high.onnx.json':'/en/en_US/ryan/high/en_US-ryan-high.onnx.json'}.items()]"

COPY app.py /app/app.py
WORKDIR /app
EXPOSE 5000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
