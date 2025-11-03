# Tit-for-Tat Asset Tracker (TFT Tracker)

MVP implementation for translating iterated game theory behavior into real-time market insights.

## Project Structure

```
tft-tracker/
├── apps/
│   ├── api/        # FastAPI service, Alembic migrations, background jobs
│   └── web/        # Next.js frontend (TailwindCSS)
├── db/             # Database migrations, seeds
├── infra/          # Docker & environment configuration
├── .github/        # CI workflows
└── *.md            # Product documentation
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm 8+
- Docker & Docker Compose

### Spin Up Services

```bash
# Start Postgres
docker compose -f infra/docker-compose.yml up -d db

# Backend setup
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload

# background ingest worker starts automatically on launch; adjust TFT_ variables to configure cadence

# Frontend setup
cd ../web
pnpm install
# optional: override API base URL for the dashboard
export NEXT_PUBLIC_API_BASE="http://localhost:8000"
pnpm dev
```

### Manual Ingest Seed
```bash
curl -X POST http://localhost:8000/ingest/run
# or target specific tickers
curl -X POST http://localhost:8000/ingest/run \
  -H 'Content-Type: application/json' \
  -d '{"tickers":["SMCI","TSLA"]}'
```
This triggers the market ingest workflow for seeded tickers (NVDA, BTC), storing market and indicator snapshots and recalculating their current Tit-for-Tat phase state.

### Authentication & Sessions
- Request a guest session token:
  ```bash
  curl -X POST http://localhost:8000/auth/guest
  ```
  Persist the returned `session_token` in the client and send it with the `X-Session-Token` header on watchlist-related requests.
- Watchlist mutations (`/watchlist`, `/watchlist/order`) require the session token and keep your list synced between devices.

### Watchlist Tips
- The first time you open the app a guest session token (`X-Session-Token`) is issued automatically; watchlist changes are stored against that session server-side and mirrored locally.
- Add tickers directly from the UI; the backend resolves aliases and ensures the canonical Yahoo Finance symbol exists before triggering an ingest.
- Common crypto aliases automatically resolve to the canonical Yahoo symbol (e.g. `TRUMP-USD` → `TRUMP35336-USD`) while retaining the user-friendly label.

## CI
GitHub Actions run linting and tests for both services on pull requests.

## Environment
Default environment variables are defined in `apps/api/app/config.py`. Override via `.env` files or shell environment.

| Variable | Description | Default |
|----------|-------------|---------|
| `TFT_ENABLE_SENTIMENT` | Toggle Yahoo News/VADER sentiment weighting | `true` |
| `TFT_SENTIMENT_WINDOW_MINUTES` | Lookback window (minutes) for sentiment fetch | `60` |
| `TFT_ENABLE_PHASE_ALERTS` | Enable server-side alert processing | `true` |
| `TFT_REQUESTS_PER_MINUTE` | In-memory rate limit (per IP) | `120` |
| `TFT_SENTRY_DSN` | Optional DSN for Sentry error/trace monitoring | _unset_ |
| `TFT_REDIS_URL` | Optional Redis connection for shared rate limiting | _unset_ |

Frontend reads the API host from `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`), phase alerts via `NEXT_PUBLIC_PHASE_ALERTS`, and optional telemetry endpoint via `NEXT_PUBLIC_ANALYTICS_URL`.

Operational checklists live under `docs/QA_CHECKLIST.md` and `docs/RELEASE_RUNBOOK.md`.
