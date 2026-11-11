"""API de transcricao compativel com OpenAI (POST /v1/audio/transcriptions)."""
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse

TOKEN = os.environ.get("AUDIO_API_TOKEN", "")
WHISPER_URL = os.environ.get("WHISPER_URL", "http://127.0.0.1:8765/transcribe")
DEFAULT_LANG = os.environ.get("DEFAULT_LANGUAGE", "pt")

app = FastAPI(title="ClickGerais Audio API")


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization.split()[-1] != TOKEN:
        raise HTTPException(401, "invalid api key")


def _transcribe(path: str, language: str) -> dict:
    payload = json.dumps({"audio": path, "language": language}).encode()
    req = urllib.request.Request(
        WHISPER_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": "whisper-1", "object": "model", "owned_by": "clickgerais"}]}


@app.post("/v1/audio/transcriptions")
async def transcriptions(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form(DEFAULT_LANG),
    response_format: str = Form("json"),
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty audio")
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
        tmp.close()
        try:
            result = _transcribe(tmp.name, language)
        except urllib.error.URLError as exc:
            raise HTTPException(502, f"stt backend unreachable: {exc}") from exc
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    text = (result.get("text") or "").strip()
    if response_format == "text":
        return JSONResponse(content=text)
    return {"text": text, "language": result.get("language", language), "duration": result.get("duration")}
