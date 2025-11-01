🧩 Product Backlog — Tit-for-Tat Asset Tracker (TFT Tracker)

Version: MVP v1.0
Author: Product Manager / Game Theory Systems Designer
Date: November 2025

Epic 1 — User Management & Watchlist
🎯 Goal

Allow users to easily add, remove, and manage assets they want to track.

User Story 1.1 — User Registration (MVP optional)

As a user, I want to create an account or use guest mode so that I can start tracking assets immediately.

Acceptance Criteria

 Users can log in or continue as guests.

 Session persists via cookies or local storage.

 No personal data beyond email (optional) stored.

User Story 1.2 — Add Asset to Watchlist

As a user, I want to add a stock or crypto ticker to my watchlist so I can track its phase.

Acceptance Criteria

 Input field with search/autocomplete for tickers (e.g., NVDA, BTC).

 Asset appears instantly on dashboard after selection.

 Duplicate prevention (cannot add same ticker twice).

 Data fetch begins automatically on add.

User Story 1.3 — Remove Asset from Watchlist

As a user, I want to remove assets I no longer care about so I can declutter my dashboard.

Acceptance Criteria

 Delete (🗑) icon removes asset instantly.

 Removal confirmation prompt (optional).

 Local state updates immediately without reload.

User Story 1.4 — Persistent Watchlist

As a user, I want my tracked assets to persist across sessions so I don’t lose them after refresh.

Acceptance Criteria

 Saved to local storage or user table if logged in.

 Automatically reloaded on next visit.

Epic 2 — Data Integration & Phase Detection
🎯 Goal

Implement core logic to determine which game theory phase (Cooperation, Defection, Forgiveness) each asset is currently in.

User Story 2.1 — Fetch Market Data

As the system, I need to fetch real-time price, volume, and volatility data so I can compute phase changes.

Acceptance Criteria

 Integrate Yahoo Finance, AlphaVantage, or Finnhub API.

 Refresh every 60 seconds.

 Store snapshots in market_snapshot.

User Story 2.2 — Compute Technical Indicators

As the system, I need RSI and MACD values to support phase detection.

Acceptance Criteria

 RSI(14) and MACD indicators calculated on data pull.

 Saved in indicator_snapshot.

 Computation occurs server-side via Python (pandas/ta).

User Story 2.3 — Fetch Sentiment Data

As the system, I need to retrieve social/news sentiment data to detect Defection or Forgiveness phases.

Acceptance Criteria

 Use Finnhub or alternative sentiment API.

 Map score range (-1 to +1).

 Store in sentiment_observation.

User Story 2.4 — Phase Detection Algorithm

As the system, I need to classify each asset’s current phase (Cooperation, Defection, Forgiveness) using quantitative thresholds.

Acceptance Criteria

 Rule-based logic (price delta %, RSI thresholds, sentiment trend).

 Output stored in phase_state with confidence score.

 Historical changes appended to phase_history.

User Story 2.5 — Scheduled Phase Updates

As the system, I want to run phase updates periodically so the dashboard remains accurate.

Acceptance Criteria

 CRON job or background worker triggers every 1–5 minutes.

 Phase recomputation occurs asynchronously.

 No duplicate writes unless phase changes.

Epic 3 — Dashboard & Visualization
🎯 Goal

Provide users with a clear, intuitive dashboard that visually displays each asset’s phase, reasoning, and sentiment.

User Story 3.1 — Phase Indicator Cards

As a user, I want to see each asset’s current phase represented visually on a card.

Acceptance Criteria

 Color-coded system: 🟢 Cooperation, 🔴 Defection, 🟡 Forgiveness.

 Display price, sentiment, and rationale summary.

 Auto-refresh without page reload.

User Story 3.2 — Phase History Timeline

As a user, I want to view recent phase transitions for each asset.

Acceptance Criteria

 Mini timeline or sparkline showing last 7 days of phase changes.

 Hover tooltip displays rationale per phase shift.

User Story 3.3 — Tooltip Explanation

As a user, I want to understand why an asset is in its current phase.

Acceptance Criteria

 Tooltip or “Explain” modal.

 Pulls rationale and confidence from phase_state.

 Example text: “BTC is in Forgiveness — sentiment recovering +3.2%.”

User Story 3.4 — Responsive Dashboard

As a user, I want the dashboard to look clean on mobile, tablet, and desktop.

Acceptance Criteria

 Built using TailwindCSS grid/flexbox.

 Collapsible panels for smaller screens.

 Phase colors and fonts adjust for dark mode.

Epic 4 — System Architecture & Database
🎯 Goal

Ensure data is structured and accessible for scalable API interactions.

User Story 4.1 — Database Setup

As a developer, I need to initialize all core tables so that assets, sentiment, and phases can be stored properly.

Acceptance Criteria

 Tables: users, assets, phase_state, phase_history, sentiment_source, sentiment_observation, market_snapshot, indicator_snapshot.

 Schema aligns with PRD and ERD.

 Indexed queries for fast lookups.

User Story 4.2 — API Endpoints

As a frontend developer, I need clean endpoints to retrieve and update asset phase data.

Acceptance Criteria

 /assets → list tracked assets

 /phase/{asset} → current phase + confidence + rationale

 /history/{asset} → phase history data

 /sentiment/{asset} → latest sentiment summary

User Story 4.3 — Data Validation & Error Handling

As a system, I must gracefully handle missing or delayed API data.

Acceptance Criteria

 Fallback logic for unavailable sentiment feeds.

 Phase confidence decreases if data incomplete.

 Errors logged with context.

Epic 5 — Next Iteration Enhancements (Post-MVP)
🎯 Goal

Prepare for scalability, intelligence, and deeper insights once MVP adoption is validated.

User Story 5.1 — AI Forecasting Agent

Predict likely next phase transitions using LSTM or Random Forest models.

Acceptance Criteria

 Trained on historical phase data.

 Returns “Next probable phase” and confidence.

 Stored in new phase_prediction table.

User Story 5.2 — Sentiment Source Expansion

Include Reddit and X/Twitter for real-time retail sentiment.

Acceptance Criteria

 Add new sentiment_source entries.

 Parse and score posts using sentiment analysis API.

 Update phase confidence weighting.

User Story 5.3 — Alerts & Notifications

Send alerts when assets change phases.

Acceptance Criteria

 Email or in-app notification triggers on phase change.

 Includes previous and new phase in message.

User Story 5.4 — Multi-Asset Correlation View

Visualize how assets behave relative to one another.

Acceptance Criteria

 Correlation heatmap (asset vs asset).

 Filters for time range and sector.

 Color scale: green = aligned, red = diverging.

User Story 5.5 — Portfolio Mode

Aggregate phase data across user’s watchlist into one “Market Cooperation Index.”

Acceptance Criteria

 Weighted average of all tracked assets’ confidence scores.

 Single color-coded summary tile at dashboard top.

✅ MVP Completion Definition

All stories from Epics 1–4 implemented and tested.

Data auto-refreshes every 60 seconds.

Dashboard visually updates without manual reload.

At least two assets (e.g., NVDA, BTC) correctly display distinct phases.

Deployed to production environment (e.g., Vercel + Render).
