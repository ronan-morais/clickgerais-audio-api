FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    MODEL_DIR=/models \
    WHISPER_MODEL=base \
    COMPUTE_TYPE=int8 \
    PORT=8770

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# baixa o modelo no build (runtime fica offline e rapido)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8', download_root='/models')"

COPY app.py .
EXPOSE 8770
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
