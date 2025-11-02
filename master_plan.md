# Master Plan — Tit-for-Tat Asset Tracker (MVP v1.0)

## Vision and Problem Statement
- Treat financial markets as an iterated game where sentiment cycles through cooperation, defection, and forgiveness.
- Traditional technical analysis struggles to explain why swings occur; the tracker maps behavioral phases onto real-time asset data to provide interpretable signals.
- MVP targets actionable insight for retail traders, analysts, and educators by pairing market data with clear narrative explanations.

## Personas and Core Use Cases
- **Retail Trader (Ava):** Track 3–5 tickers, rely on TFT phases to time entries and exits, needs noise reduction.
- **Market Analyst (Liam):** Embed behavioral framing into reports, wants data-backed storylines.
- **Educator/Coach (Dr. Reyes):** Demonstrate applied game theory in class, needs intuitive visuals connected to live markets.

## Objectives and Success Metrics
| Objective | Metric | Target | Timeline |
|-----------|--------|--------|----------|
| Help users interpret TFT phases correctly | ≥70% correct interpretation from in-app explanations | Day 30 post-launch | |
| Deliver timely updates | <30s data refresh latency | MVP release | |
| Drive retention | ≥50% weekly active retention | End of Month 1 | |
| Validate phase accuracy | ≥70% correlation between detected phase and subsequent sentiment shift | Within 3 months | |

## MVP Scope Overview
1. **Asset Watchlist:** Search/add/remove assets with duplicate prevention and persistent storage (guest via localStorage, user via DB).
2. **Phase Detection Logic:** Rule-based classifier using price deltas, RSI, volume/volatility, and sentiment, writing to `phase_state` and `phase_history`.
3. **Dashboard Visualization:** Color-coded phase cards, mini timeline, explain modal, responsive layout, accessibility support.
4. **Data Ingestion and Refresh:** Ingest market data (Yahoo Finance/AlphaVantage), compute indicators, pull sentiment feeds, refresh at 60s cadence.
5. **Explanatory Panel and Alerts:** Contextual reasoning, confidence scoring, in-app alerts on phase changes.

## Data Architecture Summary
- **Core entities:** `users`, `assets`, `phase_state`, `phase_history`, `market_snapshot`, `indicator_snapshot`, `sentiment_source`, `sentiment_observation`.
- **Relationships:** Users track many assets (`user_asset` join). Each asset has one current phase and many historical phases. Market, indicator, and sentiment snapshots feed the classifier. Sentiment observations link to specific sources with reliability tiers.
- **Storage guidelines:** PostgreSQL with enumerated types for phase, asset type, sentiment channel, and reliability. Index heavily on `(asset_id, timestamp)` for fast queries.
- **Processing flow:** Ingest jobs pull market and indicator data, sentiment adapters add signals, classifier produces phase outputs with confidence and rationale strings.

## Execution Roadmap (4-Week MVP)
- **Sprint 1 — Foundations:** Bootstrap mono-repo, scaffold Next.js frontend and FastAPI backend, provision Postgres with Alembic migrations, implement market ingest and indicator calculations, publish API contracts, configure CI/CD.
- **Sprint 2 — Phase Intelligence:** Finalize phase enums/tables, implement rule-based classifier and scheduled worker, expose phase endpoints, build asset cards and explain modal, cover with unit/API/FE tests.
- **Sprint 3 — Watchlist and UX Polish:** Deliver ticker search and autocomplete, persistence, reorder/remove interactions, responsive layout, loading/error states, telemetry, accessibility adjustments.
- **Sprint 4 — Sentiment and Release Prep:** Integrate sentiment adapter, wire alerting, enable feature flags, harden security/rate limits, complete QA pass and documentation, instrument monitoring and release playbook.

## Product Backlog Snapshot
- **Epic 1 — User Management & Watchlist:** Registration (optional), add/remove assets, persistent watchlist, reorder UX.
- **Epic 2 — Data Integration & Phase Detection:** Market data ingest, technical indicator computation, sentiment ingestion, classifier, scheduled updates.
- **Epic 3 — Dashboard & Visualization:** Phase indicator cards, history timeline, explain modal, responsive design.
- **Epic 4 — System Architecture & API:** Database setup, REST endpoints, validation and error handling.
- **Epic 5 — Post-MVP Enhancements:** AI forecasting, sentiment source expansion, alerts/notifications (beyond in-app), correlation heatmap, portfolio cooperation index.

## Risks and Mitigations
- **API rate limits or data gaps:** Cache latest good snapshot, backoff retries, degrade confidence scores when feeds stale.
- **Limited sentiment coverage:** Allow classifier to fall back to market/indicator data and flag low-confidence outputs.
- **Volatility noise causing false signals:** Apply minimum time windows and smoothing before classifying.
- **Time-zone inconsistencies:** Store all timestamps in UTC, convert only for display.

## Future Opportunities
- Machine-learning phase prediction (Random Forest/LSTM) with `phase_prediction` table.
- Broader sentiment ingestion (Reddit, X, StockTwits) with source reliability weighting.
- Multi-asset correlation heatmaps to show macro cooperation vs defection clusters.
- Phase-change alerts via email/push and portfolio-level cooperation index for analysts.

## Release Definition of Done (MVP)
- All Epics 1–4 user stories implemented, tested, and documented.
- Data refresh every 60 seconds with ingestion, indicators, sentiment feeds, and classifier operating end-to-end.
- Dashboard shows distinct phases for seeded assets (e.g., NVDA, BTC) with rationale and confidence.
- Production deployment live with monitoring, logging, and rollback plan in place.
