🧩 Data Model — Tit-for-Tat Asset Tracker (TFT Tracker)
Entity Relationship Diagram (ERD)
erDiagram
    USER ||--o{ USER_ASSET : tracks
    ASSET ||--o{ USER_ASSET : appears_in
    ASSET ||--|| PHASE_STATE : has_current
    ASSET ||--o{ PHASE_HISTORY : has_past
    ASSET ||--o{ MARKET_SNAPSHOT : has
    ASSET ||--o{ INDICATOR_SNAPSHOT : has
    ASSET ||--o{ SENTIMENT_OBSERVATION : has
    SENTIMENT_SOURCE ||--o{ SENTIMENT_OBSERVATION : provides

    USER {
      uuid id PK
      text email
      jsonb settings
      timestamptz created_at
      timestamptz updated_at
    }

    ASSET {
      uuid id PK
      text ticker  "e.g., NVDA, BTC"
      text name
      text type    "stock|crypto|etf"
      text exchange
      timestamptz created_at
      timestamptz updated_at
      unique(ticker, type)
    }

    USER_ASSET {
      uuid id PK
      uuid user_id FK
      uuid asset_id FK
      int display_order
      timestamptz created_at
      unique(user_id, asset_id)
    }

    PHASE_STATE {
      uuid asset_id PK FK
      text phase   "COOP|DEFECT|FORGIVE"
      numeric confidence   "0..1"
      text rationale       "short explanation"
      timestamptz computed_at
    }

    PHASE_HISTORY {
      uuid id PK
      uuid asset_id FK
      text from_phase
      text to_phase
      numeric confidence
      text rationale
      timestamptz changed_at
      index(asset_id, changed_at)
    }

    MARKET_SNAPSHOT {
      uuid id PK
      uuid asset_id FK
      numeric price
      numeric price_change_pct
      numeric volume
      numeric vwap
      numeric volatility_1d
      timestamptz asof
      index(asset_id, asof)
    }

    INDICATOR_SNAPSHOT {
      uuid id PK
      uuid asset_id FK
      numeric rsi_14
      numeric macd
      numeric macd_signal
      numeric atr_14
      numeric sma_20
      numeric sma_50
      timestamptz asof
      index(asset_id, asof)
    }

    SENTIMENT_SOURCE {
      uuid id PK
      text name       "e.g., Finnhub, Reddit, X"
      text channel    "news|social|forum"
      text reliability_tier  "A|B|C"
      jsonb meta
      timestamptz created_at
    }

    SENTIMENT_OBSERVATION {
      uuid id PK
      uuid asset_id FK
      uuid source_id FK
      numeric score           "-1..1"
      numeric magnitude       "abs intensity"
      jsonb features          "keywords, embeddings, etc."
      timestamptz observed_at
      index(asset_id, observed_at)
    }

Implementation Notes

Single source of truth: PHASE_STATE holds the current phase for each asset (1 row per asset).

Phase transitions: Logged in PHASE_HISTORY for historical analysis and visualization.

Core data sources: Market data → MARKET_SNAPSHOT, Technical Indicators → INDICATOR_SNAPSHOT, Sentiment data → SENTIMENT_OBSERVATION.

User Watchlists: Managed through USER_ASSET linking users to tracked assets.

Future expandability: Add AI forecast outputs as a new table (e.g., PHASE_PREDICTION).

Recommended PostgreSQL Schema (MVP)
-- ENUM TYPES
create type phase_enum as enum ('COOP','DEFECT','FORGIVE');
create type asset_type_enum as enum ('stock','crypto','etf');
create type sentiment_channel_enum as enum ('news','social','forum');
create type reliability_tier_enum as enum ('A','B','C');

-- USERS
create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  settings jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ASSETS
create table assets (
  id uuid primary key default gen_random_uuid(),
  ticker text not null,
  name text,
  type asset_type_enum not null,
  exchange text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (ticker, type)
);

-- USER WATCHLIST
create table user_asset (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  asset_id uuid not null references assets(id) on delete cascade,
  display_order int,
  created_at timestamptz default now(),
  unique (user_id, asset_id)
);

-- CURRENT PHASE
create table phase_state (
  asset_id uuid primary key references assets(id) on delete cascade,
  phase phase_enum not null,
  confidence numeric,
  rationale text,
  computed_at timestamptz not null default now()
);

-- PHASE HISTORY
create table phase_history (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references assets(id) on delete cascade,
  from_phase phase_enum,
  to_phase phase_enum not null,
  confidence numeric,
  rationale text,
  changed_at timestamptz not null default now()
);
create index idx_phase_history_asset_time on phase_history(asset_id, changed_at desc);

-- MARKET SNAPSHOTS
create table market_snapshot (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references assets(id) on delete cascade,
  price numeric,
  price_change_pct numeric,
  volume numeric,
  vwap numeric,
  volatility_1d numeric,
  asof timestamptz not null,
  unique (asset_id, asof)
);
create index idx_market_snapshot_asset_time on market_snapshot(asset_id, asof desc);

-- TECHNICAL INDICATORS
create table indicator_snapshot (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references assets(id) on delete cascade,
  rsi_14 numeric,
  macd numeric,
  macd_signal numeric,
  atr_14 numeric,
  sma_20 numeric,
  sma_50 numeric,
  asof timestamptz not null,
  unique (asset_id, asof)
);
create index idx_indicator_snapshot_asset_time on indicator_snapshot(asset_id, asof desc);

-- SENTIMENT SOURCES
create table sentiment_source (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  channel sentiment_channel_enum not null,
  reliability_tier reliability_tier_enum default 'B',
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- SENTIMENT OBSERVATIONS
create table sentiment_observation (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references assets(id) on delete cascade,
  source_id uuid not null references sentiment_source(id) on delete restrict,
  score numeric,          -- -1..1
  magnitude numeric,      -- intensity
  features jsonb default '{}'::jsonb,
  observed_at timestamptz not null,
  unique (asset_id, source_id, observed_at)
);
create index idx_sentiment_obs_asset_time on sentiment_observation(asset_id, observed_at desc);

Usage Mapping
App Feature	Data Source
Dashboard Cards	PHASE_STATE + latest MARKET_SNAPSHOT
Tooltip / Reasoning	PHASE_STATE.rationale
Phase Timeline	PHASE_HISTORY
Sentiment Meter	Aggregated from SENTIMENT_OBSERVATION
User Watchlist	USER_ASSET
Alerts / Webhooks	Triggered on PHASE_HISTORY inserts
