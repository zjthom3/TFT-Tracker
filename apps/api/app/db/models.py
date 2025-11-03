from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    Numeric,
    String,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class GUID(TypeDecorator):
    """Platform-independent GUID type."""

    impl = PGUUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return UUID(str(value))


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("ticker", "type", name="uq_assets_ticker_type"),)

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(16), default="stock")
    exchange: Mapped[Optional[str]] = mapped_column(String(64))
    display_ticker: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    market_snapshots: Mapped[list["MarketSnapshot"]] = relationship(back_populates="asset")
    indicator_snapshots: Mapped[list["IndicatorSnapshot"]] = relationship(back_populates="asset")
    phase_state: Mapped[Optional["PhaseState"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    phase_history: Mapped[list["PhaseHistory"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", order_by="PhaseHistory.changed_at"
    )
    sentiment_observations: Mapped[list["SentimentObservation"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshot"
    __table_args__ = (UniqueConstraint("asset_id", "as_of", name="uq_market_snapshot_asset_time"),)

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("assets.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float)
    price_change_pct: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[float]] = mapped_column(Float)
    vwap: Mapped[Optional[float]] = mapped_column(Float)
    volatility_1d: Mapped[Optional[float]] = mapped_column(Float)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="market_snapshots")
    indicator_snapshot: Mapped["IndicatorSnapshot"] = relationship(
        back_populates="market_snapshot", uselist=False
    )


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshot"
    __table_args__ = (
        UniqueConstraint("asset_id", "as_of", name="uq_indicator_snapshot_asset_time"),
    )

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("assets.id"), nullable=False)
    market_snapshot_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("market_snapshot.id"),
        nullable=False,
        unique=True,
    )
    rsi_14: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    macd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    macd_signal: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    atr_14: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="indicator_snapshots")
    market_snapshot: Mapped[MarketSnapshot] = relationship(back_populates="indicator_snapshot")


class PhaseState(Base):
    __tablename__ = "phase_state"

    asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True
    )
    phase: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    rationale: Mapped[Optional[str]] = mapped_column(String(512))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    asset: Mapped[Asset] = relationship(back_populates="phase_state")


class PhaseHistory(Base):
    __tablename__ = "phase_history"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    from_phase: Mapped[Optional[str]] = mapped_column(String(16))
    to_phase: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    rationale: Mapped[Optional[str]] = mapped_column(String(512))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    asset: Mapped[Asset] = relationship(back_populates="phase_history")


class SentimentSource(Base):
    __tablename__ = "sentiment_source"

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    reliability_tier: Mapped[Optional[str]] = mapped_column(String(8))
    meta: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    observations: Mapped[list["SentimentObservation"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SentimentObservation(Base):
    __tablename__ = "sentiment_observation"
    __table_args__ = (
        UniqueConstraint("asset_id", "source_id", "observed_at", name="uq_sentiment_unique"),
    )

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sentiment_source.id", ondelete="RESTRICT"), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float)
    magnitude: Mapped[Optional[float]] = mapped_column(Float)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="sentiment_observations")
    source: Mapped[SentimentSource] = relationship(back_populates="observations")
