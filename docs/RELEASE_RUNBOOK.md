# Release Runbook — TFT Tracker MVP

## 1. Pre-release Checklist
- [ ] Merge latest `main` with all Sprint deliverables
- [ ] Confirm database migrations (`alembic history`) include `202411020001_add_phase_tables`
- [ ] Verify `.env` has:
  - `TFT_DATABASE_URL`
  - `TFT_ENABLE_SENTIMENT` (default `true`)
  - `TFT_SENTIMENT_WINDOW_MINUTES`
  - `TFT_ENABLE_PHASE_ALERTS`
  - `TFT_REQUESTS_PER_MINUTE`
  - `TFT_SENTRY_DSN` (optional but recommended)
  - `TFT_REDIS_URL` (optional shared rate limiter)
- [ ] Frontend: set `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_PHASE_ALERTS`
  - Optional: `NEXT_PUBLIC_ANALYTICS_URL`
- [ ] Apply latest migrations including `202511031142_add_display_ticker` and `202511031548_create_user_tables`
- [ ] Run test & lint suites:
  - `source apps/api/.venv/bin/activate && pytest`
  - `cd apps/web && pnpm lint`

## 2. Deployment Steps (Preview)
1. `docker compose -f infra/docker-compose.yml up -d db`
2. Apply migrations: `alembic upgrade head`
3. Seed or trigger ingest: `curl -X POST http://localhost:8000/ingest/run`
4. Verify API endpoints (`/health`, `/phase`, `/snapshots/latest`)
5. Start frontend (`pnpm dev` or production build) and confirm dashboard shows data

## 3. Production Release
1. Build backend container / deploy to hosting provider (Render/AWS Lambda)
2. Configure secrets in environment (same keys as above)
3. Run DB migration against production Postgres
4. Deploy frontend (e.g., Vercel) with updated `NEXT_PUBLIC_*` env vars
5. Warm ingest job or set cron/scheduler to invoke `poll_market_data`

## 4. Post-release Validation
- [ ] Ingest logs show successful market + sentiment pulls
- [ ] Phase alerts fire on forced transition (use mock data or manual asset updates)
- [ ] Rate limiting returns 429 under load-test scenario
- [ ] Sentry dashboard displays new release version and heartbeat check

## 5. Rollback Plan
- Alembic downgrade: `alembic downgrade 202401010000`
- Redeploy previous backend container image
- Clear frontend cache / redeploy prior static build
- Monitor Sentry for residual errors
