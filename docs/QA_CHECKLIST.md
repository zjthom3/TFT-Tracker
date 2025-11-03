# QA Checklist — TFT Tracker MVP

## Pre-flight
- [ ] `docker compose -f infra/docker-compose.yml up -d db`
- [ ] `alembic upgrade head` applied
- [ ] `uvicorn app.main:app --reload` running with `TFT_ENABLE_SENTIMENT`/other env vars set as needed
- [ ] `pnpm dev` running in `apps/web`

## Functional
- [ ] Add tickers (e.g., `NVDA`, `BTC-USD`) via watchlist panel; duplicates are rejected gracefully
- [ ] Watchlist reorder (Move up/down) immediately updates card ordering
- [ ] Removing a ticker updates cards and persists after refresh
- [ ] New guest sessions receive a `X-Session-Token`; watchlist persists after refresh using the same token
- [ ] Manual ingest (`curl -X POST http://localhost:8000/ingest/run`) updates price/indicator data and phase rationale
- [ ] Phase alerts banner appears on phase transition, then auto-dismisses
- [ ] Sentiment score logged in ingest response and influences phase rationale (negative sentiment increases DEFECT odds)
- [ ] Rate limit returns HTTP 429 after exceeding threshold; normal usage remains unaffected
- [ ] Analytics endpoint (if configured) receives watchlist/phase events (verify via network inspector or logs)

## Visual / UX
- [ ] Dashboard renders correctly on mobile (<768px) with stacked cards
- [ ] Watchlist input accessible via keyboard; focus rings visible for actionable controls
- [ ] Dark mode gradients readable; color contrast AA-compliant (check with browser audit)
- [ ] Empty-state message appears when watchlist cleared

## Backend
- [ ] `pytest` passes (`source apps/api/.venv/bin/activate && pytest`)
- [ ] Logs show sentiment ingestor success and no tracebacks under normal usage
- [ ] Sentry receives a test exception when `TFT_SENTRY_DSN` is set (`raise ValueError("sentry smoke test")`)

## Observability
- [ ] Sentry traces display FastAPI request spans
- [ ] Optional: configure uptime monitor hitting `/health`; verify 200 response

## Deploy Readiness
- [ ] `pnpm lint` (frontend) passes
- [ ] `.env.production` includes rate-limit, sentiment, and alert toggles
- [ ] Update release notes with any new migrations (`202411020001`) or config changes
