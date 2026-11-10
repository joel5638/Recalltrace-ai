# RecallTrace AI — Conversational investigation platform

Supplier quality investigation with conversational search, evidence grounding, bounded tools, persistent sessions, approval interrupts, observability and optional realtime voice.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Set `OPENAI_API_KEY` for model-backed chat and realtime voice. Without it, the chat uses deterministic local responses. The supplied dataset is synthetic.

## Optional production-oriented components

```bash
pip install -r requirements-enterprise.txt
export RECALLTRACE_VECTOR_BACKEND=qdrant
export QDRANT_URL=http://localhost:6333
```

Start Qdrant separately or with Docker Compose. Then call `POST /api/admin/reindex` to index evidence. For production, set `RECALLTRACE_ENV=production`, `OIDC_ISSUER`, `OIDC_AUDIENCE`, and configure TLS, network isolation, secrets, backups, and deployment-specific authorization. **Do not expose this demo directly to the internet.**

## Architecture

Browser → FastAPI → LangGraph planner → allowlisted investigation tools → hybrid retrieval → evidence-grounded answer. Session context and tool traces persist in SQLite. A separate LangGraph review graph uses SQLite checkpoints and `interrupt()`/`Command(resume=...)` for durable approval. Realtime voice is a bidirectional WebSocket audio relay to a model provider; it does not yet invoke the investigation tools, so voice responses are not evidence-grounded. Qdrant provides a persistent vector index when enabled. Optional cross-encoder reranking is enabled by `RECALLTRACE_RERANKER`.

## API

- `POST /api/chat`, `POST /api/chat/stream` for text conversation
- `GET /api/session/{uuid}`, `GET /api/lot/{lot}` for session and investigation context
- `POST /api/workflows/review`, `POST /api/workflows/{uuid}/resume` for checkpointed approvals
- `WS /api/voice/realtime` for realtime audio event relay (PCM16 base64)
- `POST /api/admin/reindex` for vector indexing
- `GET /internal/metrics` for Prometheus; optional OTLP spans
- `GET /api/admin/audit` for trace audit view
- `python -m app.evaluation` for regression evaluation

## Honest limitations

This is an engineering reference implementation, not a security-certified production deployment. The realtime audio protocol depends on provider version and needs integration testing with live credentials. The browser UI uses browser speech recognition for convenient voice input; realtime PCM capture/playback is exposed at the WebSocket API but not wired into the browser UI. OIDC roles depend on the identity provider's token claim conventions. SQLite works for local demos; scale-out should migrate session and checkpoint storage to managed PostgreSQL and apply per-tenant authorization. Realtime voice and text workflows are not unified yet. Prometheus metrics and OTLP traces are available but dashboards and alert policies require an external stack. No outbound supplier actions execute.
