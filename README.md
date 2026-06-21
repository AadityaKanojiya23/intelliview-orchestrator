# IntelliView Orchestrator

> **Distributed AI-powered interview orchestration platform with real-time risk scoring, multi-node execution, and fault-tolerant task scheduling.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Celery](https://img.shields.io/badge/Queue-Celery-37814A.svg)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Broker-Redis-DC382D.svg)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/Store-PostgreSQL-336791.svg)](https://www.postgresql.org)
[![Next.js](https://img.shields.io/badge/UI-Next.js_14-000.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/Lang-TypeScript-3178C6.svg)](https://www.typescriptlang.org)
[![Tailwind](https://img.shields.io/badge/Style-Tailwind-38BDF8.svg)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Deploy-Docker_Compose-2496ED.svg)](https://docs.docker.com/compose)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen.svg)](./.github/workflows/ci.yml)

---

## Table of contents

- [Why IntelliView](#why-intelliview)
- [Highlights](#highlights)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Frontend](#frontend)
- [Pluggable AI pipelines](#pluggable-ai-pipelines)
- [Operations](#operations)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License & author](#license--author)

---

## Why IntelliView

Conducting interviews at scale means more than recording a video. You
need to:

- Run **video, audio, and NLP analysis** in parallel without
  one slow pipeline blocking the others.
- **Balance load** across workers as they come and go.
- **Retry intelligently** when a worker dies mid-task, and stop retrying
  once the limit is hit (no infinite loops).
- Give operators a **single live view** of risk, throughput, and
  failures — and a way to take action (cancel, retry, switch strategy)
  without a redeploy.

IntelliView Orchestrator ships all of the above as a self-contained,
containerised stack you can run on a single host or scale across a
cluster.

## Highlights

### Scalability
- **Horizontal worker scaling** via Celery + Redis.
- **Three load-balancing strategies** with runtime switching:
  `ROUND_ROBIN`, `LEAST_LOADED`, `QUEUE_BASED`.
- **Pluggable AI pipelines** — swap in MediaPipe, Whisper, Llama, or
  your own model without touching the orchestrator.

### Reliability
- **Exponential backoff** with configurable max retries
  (`MAX_RETRIES`, `RETRY_BASE_DELAY`, `RETRY_MAX_DELAY`).
- **Dead-letter queue** for permanently failed sessions.
- **Heartbeat-based worker health monitoring** with stale-worker
  detection.
- **Scheduler rollback**: if Celery dispatch fails, the worker
  active-task counter is decremented so the registry never over-reports
  load.

### Observability
- **Structured JSON logging** (`JSON_LOGGING=1`) with a `log_event`
  helper and `X-Request-ID` correlation on every request.
- **Live metrics dashboard** with auto-refresh.
- **WebSocket push** for live system updates
  (`/monitoring/ws/metrics?token=…`).
- **Failure analytics**, risk-score distributions, retry telemetry.

### Security
- **API-token authentication** for every privileged endpoint
  (`/start-interview`, `/register-worker`, `/switch-strategy`,
  `/retry-session/{id}`, `/detect-failures`, `/clear-cache`,
  `/deregister-worker/{id}`).
- **Configurable CORS** with the production-safe default of an explicit
  origin list (never `*` with credentials).
- **Non-root Docker image** with a `/health` `HEALTHCHECK`.
- See [`SECURITY.md`](./SECURITY.md) for the hardening checklist and
  disclosure policy.

### Developer experience
- **Type-safe** on both ends: Pydantic v2 request/response models on the
  backend, a hand-written TS mirror in `frontend/src/lib/types.ts`.
- **91 automated tests** (unit + contract + e2e smoke) running in CI on
  every push.
- **Lint + format + typecheck + production build** all enforced in CI.

## Architecture

```
                  ┌──────────────────────────┐
                  │     Next.js Dashboard    │  ← operator UI
                  └────────────┬─────────────┘
                               │ HTTPS / WSS
                  ┌────────────▼─────────────┐
                  │   FastAPI Orchestrator   │
                  │  (Scheduler + LB + Auth) │
                  └──┬───────┬───────────────┘
                     │       │
                ┌────▼─┐ ┌───▼──────────┐
                │Redis │ │  PostgreSQL  │
                │Cache │ │ (truth + log)│
                └─┬────┘ └──────────────┘
                  │
          ┌───────┴──────── Celery broker
          │
   ┌──────▼───────┐   ┌──────────────┐   ┌──────────────┐
   │ Worker Node 1│   │ Worker Node 2│ … │ Worker Node N│
   │  ┌──────────┐│   │  ┌──────────┐│   │  ┌──────────┐│
   │  │ video    ││   │  │ video    ││   │  │ video    ││
   │  │ audio    ││   │  │ audio    ││   │  │ audio    ││
   │  │ eval/NLP ││   │  │ eval/NLP ││   │  │ eval/NLP ││
   │  └────┬─────┘│   │  └────┬─────┘│   │  └────┬─────┘│
   └───────┼──────┘   └───────┼──────┘   └───────┼──────┘
           └──────────────┬──┴──┬───────────────┘
                          │     │
                  ┌───────▼─┐ ┌─▼──────────┐
                  │ Postgres│ │   Redis    │
                  │  state  │ │  + queue   │
                  └─────────┘ └────────────┘
```

Each worker node runs:
- The **Celery worker** that consumes `process_interview_session` tasks.
- The **worker agent** that registers, heartbeats, and deregisters
  itself with the orchestrator.
- One **pluggable AI pipeline** per stage (video / audio / evaluation).

## Quick start

### Prerequisites
- Docker 24+ with Compose v2
- 4 GB RAM free for the full stack

### One-command bootstrap
```bash
git clone https://github.com/rajat-wyrm/intelliview-orchestrator
cd intelliview-orchestrator
cp .env.example .env          # then edit API_TOKEN, POSTGRES_PASSWORD
docker compose up -d --build
```

After about 30 seconds:

| Service  | URL                          | Notes                              |
| -------- | ---------------------------- | ---------------------------------- |
| API      | http://localhost:8000        | OpenAPI docs at `/docs`            |
| Frontend | http://localhost:3000        | Paste your `API_TOKEN` in top bar  |
| Flower   | http://localhost:5555/flower | Celery task UI                     |
| Postgres | localhost:5432               | `postgres / postgres` (dev only)   |
| Redis    | localhost:6379               | No password (dev only)             |

### Smoke test
```bash
curl -s http://localhost:8000/health | jq
# {"status":"system running","timestamp":"…"}

curl -s -X POST http://localhost:8000/start-interview \
  -H "X-API-Token: dev-token-change-me" \
  -H "Content-Type: application/json" \
  -d '{"candidate_id":"cand-001","priority":"medium"}' | jq
```

## Configuration

All settings are loaded from environment variables (or `.env` in dev).
The full reference lives in `.env.example`. Key variables:

| Variable             | Default                     | Purpose                                      |
| -------------------- | --------------------------- | -------------------------------------------- |
| `REDIS_URL`          | `redis://localhost:6379/0`  | Celery broker + state cache                  |
| `POSTGRES_*`         | dev defaults                | DSN parts                                    |
| `API_TOKEN`          | `dev-token-change-me`       | Required for privileged endpoints            |
| `CORS_ALLOW_ORIGINS` | `*`                         | Comma-separated origin list; never `*` in prod with credentials |
| `WORKER_CONCURRENCY` | `4`                         | Per-worker Celery concurrency                |
| `MAX_RETRIES`        | `3`                         | Per-session Celery task retry cap            |
| `JSON_LOGGING`       | `1`                         | Emit structured JSON logs (set `0` for dev)  |

`API_TOKEN` defaults to a clearly-marked dev value; the orchestrator
logs a `WARNING` at startup whenever it sees the default so it can't
silently ship to production.

## API reference

The full OpenAPI schema is generated automatically and served at
`/docs` when the API is running.

### Session lifecycle

| Method | Path                              | Auth | Purpose                                     |
| ------ | --------------------------------- | ---- | ------------------------------------------- |
| POST   | `/start-interview`                | ✅   | Enqueue a new session                       |
| GET    | `/session-status/{id}`            |      | Current status, risk, assigned node          |
| GET    | `/task-status/{task_id}`          |      | Celery task status                          |

### Session tracking

| Method | Path                       | Purpose                                     |
| ------ | -------------------------- | ------------------------------------------- |
| GET    | `/active-sessions`         | Sessions in non-terminal states            |
| GET    | `/completed-sessions`      | Last N completed (sorted by `end_time`)    |
| GET    | `/failed-sessions`         | Sessions that ended in `FAILED`/`TIMEOUT`   |
| GET    | `/stuck-sessions`          | Sessions over the timeout threshold         |
| GET    | `/session-statistics`      | Aggregate counters + risk stats            |
| GET    | `/high-risk-sessions`      | Sessions with risk ≥ threshold (default 0.8) |
| GET    | `/worker-distribution`     | Per-worker session counts                  |

### Workers (auth required for mutations)

| Method | Path                              | Auth | Purpose                          |
| ------ | --------------------------------- | ---- | -------------------------------- |
| POST   | `/register-worker`                | ✅   | Register a new worker node       |
| POST   | `/worker/heartbeat`               | ✅   | Worker liveness + load signal    |
| DELETE | `/deregister-worker/{id}`         | ✅   | Remove a worker                  |
| GET    | `/workers`                        |      | List all workers + health        |
| GET    | `/worker-statistics`              |      | Aggregate utilisation            |

### Scheduling & load balancing

| Method | Path                  | Auth | Purpose                              |
| ------ | --------------------- | ---- | ------------------------------------ |
| GET    | `/scheduling-status`  |      | Current strategy + recommendation   |
| GET    | `/load-status`        |      | Utilisation, queue depth, capacity  |
| POST   | `/switch-strategy`    | ✅   | Change strategy at runtime          |

### Cache management

| Method | Path                          | Auth | Purpose                                |
| ------ | ----------------------------- | ---- | -------------------------------------- |
| GET    | `/cache-stats`                |      | Redis cache hit / miss counters       |
| POST   | `/sync-to-database`           | ✅   | Force flush of cache to Postgres       |
| DELETE | `/clear-cache`                | ✅   | Wipe Redis session cache (destructive) |

### Fault tolerance & recovery

| Method | Path                          | Auth | Purpose                                |
| ------ | ----------------------------- | ---- | -------------------------------------- |
| GET    | `/failure-log`                |      | Recent failure log entries             |
| GET    | `/recovery-queue`             |      | Tasks awaiting retry                   |
| GET    | `/dead-letter-queue`          |      | Permanently failed sessions            |
| GET    | `/fault-statistics`           |      | Failure counts + retry telemetry       |
| POST   | `/retry-session/{id}`         | ✅   | Manually requeue a failed session      |
| POST   | `/detect-failures`            | ✅   | Trigger one failure-detection sweep    |

### Health & monitoring

| Method | Path                              | Purpose                                   |
| ------ | --------------------------------- | ----------------------------------------- |
| GET    | `/health`                         | Liveness probe                            |
| GET    | `/system-health`                  | Component-level health snapshot           |
| GET    | `/worker-health`                  | Per-worker health                         |
| GET    | `/monitoring/metrics/system`      | System metrics (SWR-polled by dashboard)  |
| WS     | `/monitoring/ws/metrics?token=…`  | Live metric stream                        |

Every JSON response includes `X-Request-ID` and `X-Response-Time-ms`
headers. Pass `X-Request-ID` on the request to thread your own
correlation ID.

## Frontend

```
frontend/
├── src/
│   ├── app/                # Next.js App Router
│   │   ├── page.tsx        # Overview
│   │   ├── sessions/       # Sessions + start form
│   │   ├── workers/        # Worker pool
│   │   ├── analytics/      # Risk distribution + failures
│   │   ├── settings/       # Token, theme, strategy, manual scan
│   │   ├── loading.tsx     # Global skeleton
│   │   ├── error.tsx       # Global error boundary
│   │   └── not-found.tsx   # 404
│   ├── components/         # Card, Stat, Badge, Dialog, Pipeline, …
│   ├── hooks/              # useWebSocket, useKeyboardNav, useHydrateToken
│   └── lib/                # api.ts, types.ts, theme/store/toast stores
└── package.json
```

### Highlights
- **Command palette** (`⌘K` / `Ctrl-K`): jump to pages, start an
  interview, switch strategy, trigger failure scan.
- **Live WebSocket indicator** in the top bar (auto-reconnect with
  exponential backoff, max 15 s).
- **Theme toggle** with `dark` / `light` / `system`, persisted to
  `localStorage` and applied as a class on `<html>`.
- **Keyboard shortcuts**: `g s` (sessions), `g w` (workers),
  `g a` (analytics), `g o` (overview), `g ,` (settings), `?` (help).
- **Accessibility**: skip-to-content link, focus trap + `aria-modal`
  on `Dialog`, `prefers-reduced-motion` respected via
  `useReducedMotion`.

## Pluggable AI pipelines

The orchestrator relies on three pipeline contracts. Replace the body
of any function — the rest of the system consumes the returned dict
shape unchanged.

| Pipeline                  | Module                                | Replace with                    |
| ------------------------- | ------------------------------------- | ------------------------------- |
| Video detection           | `workers/video_pipeline.py`           | MediaPipe, YOLO, OpenCV         |
| Audio transcription + NLP | `workers/audio_pipeline.py`           | Whisper, Wav2Vec2, pyannote     |
| Answer evaluation         | `workers/evaluation_pipeline.py`      | OpenAI, Anthropic, local Llama  |

Risk is then computed in `workers/risk_engine.py`:

```
final_risk = 0.4·video_risk + 0.3·audio_risk + 0.3·evaluation_risk
```

…classified as `LOW` (< 0.3), `MEDIUM` (< 0.6), `HIGH` (< 0.8), or
`CRITICAL` (≥ 0.8).

The provided defaults are deterministic per-session seeded stubs so
end-to-end risk thresholds exercise without GPU dependencies — drop in
your real model and the rest of the stack keeps working.

## Operations

### Graceful shutdown
The FastAPI lifespan closes Redis-backed resources (state cache,
metrics, websocket manager) when the process receives `SIGTERM`.
Celery workers use `task_acks_late` so in-flight tasks are
re-delivered on hard kill.

### Stuck-session recovery
A background job (operator-triggered via `POST /detect-failures`,
or wired to Celery Beat in production) runs `health_monitor` over the
session pool, reassigns stuck sessions to healthy workers, and moves
permanently-failed sessions to the DLQ.

### Log shipping
Set `JSON_LOGGING=1` to emit one JSON object per line on stdout — drop
straight into your aggregator (Loki, ELK, Datadog). Every entry carries
`request_id` (when available), `timestamp`, `level`, and `message`.

### Migrations
The dev default uses `Base.metadata.create_all` for first-boot
convenience. Before you ship, introduce Alembic migrations under
`database/migrations/` — `migrations/env.py` is a drop-in once added.

## Project structure

```
intelliview-orchestrator/
├── orchestrator/        # FastAPI app + scheduling, load balancing, fault tolerance
│   ├── main.py          # All HTTP routes, middleware, lifespan
│   ├── session_manager.py
│   ├── session_tracker.py
│   ├── state_sync.py
│   ├── scheduler.py
│   ├── load_balancer.py
│   ├── worker_registry.py
│   ├── fault_manager.py
│   ├── retry_manager.py
│   ├── health_monitor.py
│   └── logging_config.py
├── workers/             # Celery tasks + AI pipelines + worker agent
│   ├── celery_app.py
│   ├── tasks.py
│   ├── video_pipeline.py
│   ├── audio_pipeline.py
│   ├── evaluation_pipeline.py
│   ├── risk_engine.py
│   ├── worker_agent.py
│   └── worker_entrypoint.py
├── monitoring/          # Metrics collection, WebSocket manager, dashboard API
│   ├── metrics_collector.py
│   ├── websocket_manager.py
│   ├── dashboard_api.py
│   └── dashboard.html
├── database/            # SQLAlchemy models + connection management
│   ├── db.py
│   └── models.py
├── frontend/            # Next.js 14 dashboard
│   └── src/{app,components,hooks,lib}/
├── tests/               # 91 pytest cases (unit + contract + e2e smoke)
├── config.py            # Centralized configuration
├── docker-compose.yml   # Full stack orchestration
├── Dockerfile           # Python service image (non-root, HEALTHCHECK)
├── .dockerignore
├── .env.example
├── pyproject.toml
└── README.md
```

## Testing

```bash
# Unit + contract (no external services)
pytest tests/ --ignore=tests/test_e2e_smoke.py

# End-to-end smoke (requires the stack running)
pytest tests/test_e2e_smoke.py

# Lint + format
ruff check .
ruff format --check .

# Type check (best effort)
mypy --ignore-missing-imports orchestrator workers monitoring database

# Frontend
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

CI runs all of the above on every push and PR.

## Security

Read [`SECURITY.md`](./SECURITY.md) for:
- The vulnerability disclosure process.
- A production hardening checklist (TLS, secrets, CORS, token rotation).
- The current threat model.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for development setup, code
conventions, and the PR process. Be kind — we're all here to ship good
software.

## License & author

MIT — see [`LICENSE`](./LICENSE).

**Author: [Rajat Kumar](https://github.com/rajat-wyrm)** · `rajatkumar7861813@gmail.com`
