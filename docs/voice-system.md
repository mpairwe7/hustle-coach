# Voice & Speech System — HustleCoach

Streaming voice pipeline for multilingual business coaching in Luganda, Runyankole, Swahili, and English.

## Architecture

```
Youth entrepreneur speaks → PCM16 → WebSocket → VAD → ASR → [MT] → LLM (Groq)
                                                                       ↓
                                                   Business advice + market prices
                                                   + funding sources + budgets
                                                                       ↓
                                                        [MT] → Sentence-chunked TTS
                                                                       ↓
                                                           Youth hears coaching
```

## Endpoints

| Endpoint | Type | Description |
|----------|------|-------------|
| `POST /v1/voice/stt` | HTTP | Batch speech-to-text |
| `POST /v1/voice/tts` | HTTP | Batch text-to-speech |
| `WS /v1/voice/chat/stream` | WebSocket | Full streaming voice coaching |

## WebSocket Protocol

Same protocol as Musawo/Magezi (see voice-system.md in those repos).

### Key Events
- `session_start` → `session_ready`
- Binary audio → `vad_state` → `transcript_final`
- `reply_text` (streamed sentences) → `audio_start` → binary TTS → `audio_end`
- `latency_report` with per-stage timing
- `barge_in` to interrupt

## Features

- **Energy-based VAD** — CPU-only, no neural deps
- **Sentence-chunked TTS** — sub-second time-to-first-audio
- **Barge-in** — interrupt AI mid-response
- **8 agentic tools** — market prices, budgets, break-even, funding match, business doctor
- **162 knowledge base docs** — business models, market prices, funding sources (pre-indexed BM25)
- **Multilingual** — English, Luganda, Runyankole, Swahili

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/voice_stream.py` | 301 | VAD + streaming pipeline |
| `backend/app/voice_ws.py` | 136 | WebSocket handler |
| `frontend/src/services/voiceWebSocket.ts` | 186 | WebSocket client + AudioRecorder |
| `frontend/src/services/voiceService.ts` | ~200 | Browser SpeechRecognition + SpeechSynthesis |
| `frontend/src/hooks/useSpeech.ts` | ~100 | React hook for voice input/output |
| `frontend/src/components/VoiceModal.tsx` | ~150 | Voice chat UI modal |

## Deployment

Production URL: https://hustle-coach-6774ea00.renu-01.cranecloud.io
Docker Hub: `landwind/hustle-coach:latest`
GitHub: https://github.com/mpairwe7/hustle-coach
