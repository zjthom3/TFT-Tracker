from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class AssetCreate(BaseModel):
    ticker: str
    name: str | None = None
    type: str = "stock"
    exchange: str | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticker: str
    name: str | None = None
    type: str
    exchange: str | None = None
    created_at: datetime
    updated_at: datetime


class IngestResult(BaseModel):
    ticker: str = Field(..., description="Ticker symbol requested")
    ingested_at: datetime = Field(..., description="Timestamp of the newest snapshot stored")
    market_records: int = Field(..., description="Number of market snapshots inserted")
    indicator_records: int = Field(..., description="Number of indicator snapshots inserted")
    phase: str | None = Field(default=None, description="Latest detected phase after ingest")
    phase_confidence: float | None = Field(default=None, description="Confidence for the detected phase")
    sentiment_score: float | None = Field(default=None, description="Average sentiment score for the ingest window")


class MarketSnapshotRead(BaseModel):
    asset_id: UUID
    ticker: str
    asset_name: str | None = None
    asset_type: str
    as_of: datetime
    price: float | None = None
    price_change_pct: float | None = None
    volume: float | None = None
    vwap: float | None = None
    volatility_1d: float | None = None


class IndicatorSnapshotRead(BaseModel):
    asset_id: UUID
    ticker: str
    asset_name: str | None = None
    asset_type: str
    as_of: datetime
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    atr_14: float | None = None


class PhaseStateRead(BaseModel):
    asset_id: UUID
    ticker: str
    asset_name: str | None = None
    asset_type: str
    phase: str
    confidence: float | None = None
    rationale: str | None = None
    computed_at: datetime


class PhaseHistoryRead(BaseModel):
    id: UUID
    asset_id: UUID
    ticker: str
    from_phase: str | None = None
    to_phase: str
    confidence: float | None = None
    rationale: str | None = None
    changed_at: datetime
