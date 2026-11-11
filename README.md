# ClickGerais Audio API

API de transcricao compativel com OpenAI (`POST /v1/audio/transcriptions`), usada pelo
formulario de anuncio por voz do clickgerais.com.br.

## Variaveis de ambiente

- `AUDIO_API_TOKEN` — bearer token exigido no header `Authorization`
- `WHISPER_URL` — endpoint do backend Whisper (default `http://127.0.0.1:8765/transcribe`)
- `DEFAULT_LANGUAGE` — default `pt`

## Uso

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -F file=@audio.webm -F model=whisper-1 -F language=pt \
  https://api.clickgerais.com.br/v1/audio/transcriptions
```
