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
```
This triggers the market ingest workflow for seeded tickers (NVDA, BTC), storing market and indicator snapshots and recalculating their current Tit-for-Tat phase state.

### Watchlist Tips
- The dashboard defaults to tracking `NVDA` and `BTC-USD`. Edit the watchlist from the UI; entries persist in `localStorage`.
- Each addition calls the `/assets` endpoint (creating the asset if it does not exist) and future ingests will populate snapshots automatically.

## CI
GitHub Actions run linting and tests for both services on pull requests.

## Environment
Default environment variables are defined in `apps/api/app/config.py`. Override via `.env` files or shell environment.

Frontend reads the API host from `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`).
