from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    DateTime,
    Float,
    ForeignKey,
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
