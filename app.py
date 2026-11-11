"""API de transcricao compativel com OpenAI (POST /v1/audio/transcriptions)."""
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from faster_whisper import WhisperModel

TOKEN = os.environ.get("AUDIO_API_TOKEN", "")
MODEL_DIR = os.environ.get("MODEL_DIR", "/models")
MODEL_NAME = os.environ.get("WHISPER_MODEL", "base")
DEFAULT_LANG = os.environ.get("DEFAULT_LANGUAGE", "pt")
COMPUTE = os.environ.get("COMPUTE_TYPE", "int8")

app = FastAPI(title="ClickGerais Audio API")
_model = None


def _model():
    global _model
    if _model is None:
        path = Path(MODEL_DIR)
        src = str(path) if (path / "model.bin").exists() else MODEL_NAME
        _model = WhisperModel(src, device="cpu", compute_type=COMPUTE)
    return _model


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization.split()[-1] != TOKEN:
        raise HTTPException(401, "invalid api key")


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL_NAME}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": "whisper-1", "object": "model", "owned_by": "clickgerais"}]}


@app.post("/v1/audio/transcriptions")
async def transcriptions(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form(None),
    response_format: str = Form("json"),
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        path = tmp.name
    try:
        segments, info = _model().transcribe(
            path,
            language=language or DEFAULT_LANG,
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text = " ".join(s.text.strip() for s in segments).strip()
    finally:
        Path(path).unlink(missing_ok=True)
    if response_format == "text":
        return text
    return {"text": text, "language": getattr(info, "language", language), "duration": getattr(info, "duration", None)}
