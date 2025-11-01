📆 Sprint Plan (4 weeks) — Tit-for-Tat Asset Tracker (MVP v1.0)

Team (RACI):

PM (Jerel): R/A for scope & acceptance

FE: R for UI (Next.js, Tailwind)

BE: R for APIs, data, jobs (FastAPI)

DS/Algo: R for phase logic & indicators

QA: R for test plans & regression

Environments: Dev → Preview → Prod (Vercel FE, Render/AWS BE)
Cadence: Daily standup, bi-weekly retro; code review on all PRs

🚀 Sprint 1 — Project Setup, Schema, Ingest (Week 1)
Goals

Repo + CI ready, DB schema live, baseline market data ingest, indicator calc, skeleton API.

Issues & Estimates

Monorepo Bootstrap (2h)

PNPM workspace or separate repos; base READMEs; repo lint/format hooks.

Frontend Scaffold (Next.js + Tailwind) (4h)

Pages: / Dashboard placeholder; shared layout; dark mode toggle.

Backend Scaffold (FastAPI) (6h)

Routers: /health, /assets, /ingest/run; CORS; Pydantic models.

DB Provisioning & Schema Migration (6h)

Postgres + SQL migrations (Alembic); tables per ERD; local Docker compose.

Market Data Ingest Job (8h)

Yahoo/AlphaVantage adaptor; 60s polling; write market_snapshot.

Indicators Module (RSI, MACD)** (6h)

Compute from market_snapshot; write indicator_snapshot.

Seed Data: NVDA, BTC (2h)

Asset records + initial snapshots for smoke tests.

API Contracts v0 (OpenAPI)** (4h)

/assets, /snapshots/latest, /indicators/latest; JSON examples & Postman collection.

CI/CD (6h)

GitHub Actions: lint, test, type-check; preview deploys (Vercel FE, Render BE).

Definition of Done

docker compose up boots FE/BE/DB locally.

Alembic migrates schema without errors.

/health returns 200; /assets lists seed assets.

Nightly job (or manual trigger) populates snapshots for NVDA & BTC.

OpenAPI JSON served at /docs.json.

Demo Script

Show /health & /assets.

Run ingest job → verify market_snapshot and indicator_snapshot rows.

Open Postman collection → call latest snapshots for NVDA.

🧭 Sprint 2 — Phase Logic & Core Dashboard (Week 2)
Goals

Implement TFT phase detection (rule-based), persist current/historical phases, and render cards.

Issues & Estimates

Phase Enum & Tables (2h)

phase_state (current), phase_history (append-only); indexes.

Rule-Based Phase Classifier v1 (12h)

Inputs: price Δ% (5–60m), RSI(14), sentiment score (placeholder 0), volatility_1d.

Heuristics (example defaults, env-tuned):

Defection: price Δ% ≤ −2% (5–30m) OR RSI < 35 OR sentiment Δ ≤ −0.1

Cooperation: −0.5% ≤ price Δ% ≤ +1.5% AND 35 ≤ RSI ≤ 65 AND volatility_1d ↓

Forgiveness: prior phase Defection AND price stabilization (|Δ%| < 0.5%) AND RSI rising slope

Output: phase + confidence (0–1) + rationale string.

Phase Update Worker (6h)

Runs each minute; writes phase_state if change; appends phase_history.

FE: Asset Card UI (8h)

Color badges (🟢/🔴/🟡), price, RSI, updatedAt, confidence bar.

FE: Tooltip/Explain Modal (6h)

Show rationale, thresholds triggered, last 3 snapshots.

API: Phase Endpoints (6h)

/phase/{ticker} current; /phase/{ticker}/history?days=7.

Tests (6h)

Unit tests for classifier; API tests for contracts; snapshot tests for FE cards.

Definition of Done

Phase state computes for NVDA & BTC with non-trivial transitions across a trading day.

Dashboard shows phase badges, confidence, and “Explain” modal.

/phase/* endpoints documented and covered by tests.

Demo Script

Trigger worker → watch dashboard update.

Show rationale text and confidence effect with mock deltas.

Phase history timeline renders last 7 days (if data exists; otherwise seeded).

📊 Sprint 3 — Watchlist, Persistence, UX Polish (Week 3)
Goals

Let users add/remove assets, persist watchlist, and harden UX with loading/empty/error states.

Issues & Estimates

Search & Add Ticker (8h)

Autocomplete with exchange/type; debounce; duplicate prevention.

Watchlist Persistence (6h)

Guest: localStorage; Auth (optional): user_asset table.

Remove/Reorder (6h)

Drag to reorder (mobile friendly), delete icon, optimistic updates.

Skeleton/Empty/Error States (6h)

Loading shimmers; “No data yet” copy; retry on API errors.

Responsive Layout & Dark Mode (6h)

Grid tuning; color contrast; prefers-color-scheme integration.

Performance (4h)

SWR cache keys per-ticker; 30–60s polling; avoid overfetching.

Analytics & Telemetry (MVP) (4h)

Page views, add/remove events, phase-card interactions (Tinybird/PostHog).

Accessibility Pass (4h)

Focus states, semantic roles, ARIA on badges and modals.

Definition of Done

Users can add NVDA/BTC/other tickers and see phases immediately.

Watchlist persists across reloads (guest + optional auth path).

Dashboard smooth on mobile; keyboard accessible.

Demo Script

Add/remove/reorder three assets.

Hard refresh → watchlist persists.

Toggle dark mode; verify contrast & readability.

🔧 Sprint 4 — Hardening, Sentiment Stub, Release (Week 4)
Goals

Add basic sentiment signal, alerts on phase change (in-app), QA hardening, and release process.

Issues & Estimates

Sentiment Adapter (MVP) (10h)

Finnhub/NewsAPI score ingestion every 5–10m; write sentiment_observation.

Integrate into classifier weighting (small alpha initially).

In-App Phase-Change Alerts (6h)

Toast/banner when phase flips; badge pulse animation; dismissible.

Feature Flags (4h)

Toggle sentiment weighting and polling intervals via env/flag.

Security & Rate Limits (4h)

API keys via secrets manager; simple per-IP throttling.

QA Pass & Bug Bash (8h)

Cross-browser; network throttling; time-zone sanity.

Docs & Runbooks (6h)

README quickstart; Postman export; dashboard tour; on-call runbook.

Release & Monitoring (6h)

Sentry + uptime checks; prod deploy; rollback plan.

Definition of Done

Sentiment score present and visible in Explain modal; classifier uses it when available.

Alerts fire on phase transitions without duplicates.

Stable prod release with SLO: ≥99.5% uptime (target), median API <300ms.

Demo Script

Flip sentiment toggle → show effect on confidence/rationale.

Force a phase change (mock delta) → verify alert & history append.

Show Sentry dashboard with healthy status & sample error trace.

📁 Repo Structure (suggested)
tft-tracker/
  apps/
    web/                # Next.js
      src/
        components/
          AssetCard.tsx
          PhaseBadge.tsx
          ExplainModal.tsx
        pages/
          index.tsx
        lib/swr.ts
        styles/
      public/
      package.json
    api/                # FastAPI
      app/
        main.py
        routers/
          health.py
          assets.py
          phase.py
          history.py
        services/
          ingest_market.py
          indicators.py
          classify_phase.py
          sentiment.py
        db/
          models.py
          session.py
        jobs/
          scheduler.py
      pyproject.toml
  infra/
    docker-compose.yml
    Dockerfile.api
  db/
    alembic/
    migrations/
    seeds/seed_assets.sql
  .github/workflows/
    ci.yml
  README.md

🧪 Acceptance Test Checklist (MVP)

 Add NVDA; phase computed within 60s; card shows 🟢/🔴/🟡 with confidence.

 Remove asset → disappears instantly; no fetches continue.

 Phase change writes to phase_history exactly once.

 Tooltip shows rationale with the exact thresholds triggered.

 Refresh → watchlist persists.

 Mobile view: cards stack; interactions are reachable via keyboard.

🧮 Phase Classifier v1 (concrete thresholds)

Tune via env: DEFECT_DROP=-2.0, COOP_UPPER=1.5, COOP_LOWER=-0.5, RSI_LOW=35, RSI_HIGH=65, SENTI_DEFECT=-0.10

Inputs (rolling):
- Δp%_30m, Δp%_5m, RSI_14, volatility_1d (std), sentiment_score (−1..+1), sentiment_delta_1h

Rules (ordered):
1) DEFECT if (Δp%_30m <= DEFECT_DROP) OR (RSI_14 < RSI_LOW) OR (sentiment_delta_1h <= SENTI_DEFECT)
2) COOP if (COOP_LOWER <= Δp%_30m <= COOP_UPPER) AND (RSI_LOW <= RSI_14 <= RSI_HIGH) AND (volatility_1d decreasing vs 24h)
3) FORGIVE if (prev_phase == DEFECT) AND (|Δp%_5m| < 0.5) AND (RSI_14 slope > 0) AND (sentiment_delta_1h ≥ 0)
Else fallback to previous phase with lower confidence.

Confidence:
- Base 0.6 + 0.1 for each satisfied condition (cap 0.95), −0.2 if any upstream data stale.

⚙️ VS Code Developer Quality-of-Life

apps/api/app/main.py (dev server) launcher:

// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/apps/api/.venv/bin/uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/apps/api",
      "env": { "PYTHONPATH": "${workspaceFolder}/apps/api" }
    }
  ]
}


Frontend dev task:

// apps/web/.vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    { "label": "dev:web", "type": "shell", "command": "next dev" }
  ]
}

🧰 Setup & Run Commands
# Infra
docker compose up -d db
# Backend
cd apps/api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
# Frontend
cd ../../web && pnpm i && pnpm dev

🧱 Risks & Mitigations

API rate limits / data gaps: cache last good snapshot; exponential backoff; degrade confidence.

No sentiment for some tickers: compute phase without sentiment; flag “limited data.”

False positives on micro-volatility: enforce min window length; median filters.

Time-zone drift: store in UTC; convert in FE only for display.

📦 Release Notes (MVP v1.0)

Real-time phase detection for user-selected assets (NVDA, BTC, etc.).

Visual dashboard with phase badges, confidence, tooltips, and short history.

Basic sentiment weighting (toggleable).

Watchlist add/remove/reorder with persistence.

Health checks, logging, and monitoring enabled.
