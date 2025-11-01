🧩 Product Requirements Document (PRD)
Project: Tit-for-Tat Asset Tracker (TFT Tracker)

Author: Product Manager & Game Theory Systems Designer
Version: MVP v1.0
Date: November 2025

1. Problem Statement

Financial markets behave like iterative games where participants (investors, institutions, traders) repeatedly react to one another’s decisions.
However, most investors lack a structured way to visualize this behavioral interplay. Traditional technical analysis shows what happened but not why market sentiment swings between trust, fear, and recovery.

The Tit-for-Tat Asset Tracker solves this gap by translating game-theory phases into real-time behavioral insights:

Cooperation → the market rewards mutual confidence (price stability, steady volume, optimism)

Defection → one side “betrays” (fear, sell-offs, volatility spikes)

Forgiveness → the market resets, inviting trust to rebuild

This behavioral framing helps users interpret asset sentiment cycles visually, understand when to enter or exit trades, and predict how other participants may respond next.

2. User Personas
Retail Trader (Ava)

Goal: Understand short-term market psychology to time entries/exits.

Pain Point: Overwhelmed by conflicting indicators and noise.

Use Case: Tracks 3–5 favorite assets (NVDA, BTC, TSLA) and relies on TFT phases to sense crowd behavior.

Market Analyst (Liam)

Goal: Incorporate behavioral frameworks into data-driven reports.

Pain Point: Quant data lacks intuitive storylines.

Use Case: Embeds TFT dashboards into research presentations.

Educator / Coach (Dr. Reyes)

Goal: Teach behavioral economics and game theory in real-world contexts.

Pain Point: Students struggle to link abstract models with live market data.

Use Case: Uses the app in classroom discussions to illustrate iterative cooperation and defection patterns.

3. Objectives & Success Metrics
Objective	Metric	Target
Enable users to understand asset behavior intuitively	70% of users interpret phase correctly via dashboard explanations	Within 30 days post-launch
Deliver consistent real-time updates	<30 sec data refresh latency	MVP release
Drive recurring usage	≥ 50% weekly active users (WAU) retention	Month 1
Demonstrate phase accuracy	70% correlation between detected phase and subsequent sentiment shift	Within 3 months
4. Core Features (MVP)
1. Asset Input & Watchlist

Users can search and add assets (stocks, crypto) by ticker or name.

Watchlist persists in local storage (MVP) or database (post-MVP).

2. Phase Detection Logic

Inputs: Price change %, volume, RSI, sentiment score.

Algorithm:

Cooperation: Low volatility, gradual gains, high sentiment.

Defection: Sudden drop in price or negative sentiment delta.

Forgiveness: Stabilization after defection, moderate sentiment recovery.

Display real-time phase classification with timestamp.

3. Dashboard Visualization

Color-coded phase tiles per asset:

🟢 Cooperation

🔴 Defection

🟡 Forgiveness

Hover tooltip explains reasoning (“Price drop 4.2%, negative sentiment trend → Defection”).

Mini chart showing last 7 days of phase shifts.

4. Real-Time Data Feed

APIs: Yahoo Finance (price/volume), AlphaVantage, or Finnhub (news sentiment).

Refresh every 60 seconds.

5. Explanatory Panel

Displays phase definitions and short “next-step insights.”
Example:

“BTC is in Forgiveness — traders are rebuilding trust after a sharp correction.”

5. Data Model & Architecture
Entities
Entity	Description	Key Fields
User	Tracks preferences & watchlist	user_id, email, settings
Asset	Any trackable instrument	asset_id, ticker, name, type
PhaseState	Current phase snapshot	asset_id, phase (Coop/Def/Forg), timestamp, confidence_score
SentimentFeed	Latest data from APIs	asset_id, sentiment_score, volume, rsi, price_change_pct
Relationships

A User can track many Assets.

Each Asset has a current PhaseState.

Each PhaseState is computed using SentimentFeed data.

System Architecture (Simplified)
Frontend (React/Next.js)
   ↓
API Gateway (FastAPI/Flask)
   ↓
Data Layer (SQLite/PostgreSQL)
   ↓
Data Sources: Yahoo Finance, AlphaVantage, Twitter/X Sentiment APIs


Hosting: Vercel (frontend) + Render/AWS Lambda (backend)

MVP Tech Stack: Python (FastAPI), React, TailwindCSS, SQLite

6. User Flow / UI Summary

Step 1: User logs in (or uses guest mode) → sees default dashboard.
Step 2: User adds assets (NVDA, BTC).
Step 3: System fetches data, runs phase detection.
Step 4: Dashboard updates:

Each asset card shows phase color, short description, and “last updated” time.
Step 5: Optional: User clicks “Explain” for contextual insights and sentiment breakdown.

UI Principles:

3-color minimalism (Green, Red, Yellow)

Lightweight transitions for phase changes

One-click asset add/remove

Mobile-responsive

7. Next Iteration Opportunities
Feature	Description	Value
AI Forecasting Agent	Predicts next phase using ML model (e.g., Random Forest / LSTM).	Early signal for traders
Social Sentiment Integration	Incorporate Reddit, X, and StockTwits data.	Captures retail emotion shifts
Multi-Asset Correlation Heatmap	Visualizes synchronized behaviors between assets.	Spot macro “trust” or “panic” trends
Phase Alerts	Notify users when an asset shifts between phases.	Increase engagement
Portfolio Mode	Track aggregate “market cooperation index.”	Useful for analysts/institutions
8. Technical Notes

MVP Algorithm: Rule-based phase detection (thresholds on sentiment delta, volatility, RSI).

Post-MVP: Machine learning classifier trained on labeled phase data.

Security: Minimal user data storage (only watchlist).

Scalability: Upgrade from SQLite → PostgreSQL as data volume grows.

9. Appendix / References

Core Theories:

Axelrod, R. The Evolution of Cooperation (1984).

Iterated Prisoner’s Dilemma models applied to market behavior.

Inspirational Analogies:

Cooperation = bull market stability

Defection = sell-off cascades

Forgiveness = consolidation/recovery
