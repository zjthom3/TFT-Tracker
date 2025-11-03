from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset, IndicatorSnapshot, MarketSnapshot
from app.services.indicators import compute_atr, compute_macd, compute_rsi
from app.utils.tickers import resolve_ticker


@dataclass
class IngestSummary:
    ticker: str
    ingested_at: datetime
    market_records: int
    indicator_records: int


class MarketIngestor:
    def __init__(self, session: Session, window_days: int = 7) -> None:
        self.session = session
        self.window_days = window_days

    def ingest_many(self, tickers: Iterable[str]) -> list[IngestSummary]:
        summaries: list[IngestSummary] = []
        for ticker in tickers:
            canonical, _ = resolve_ticker(ticker)
            summary = self.ingest_single(canonical)
            if summary:
                summaries.append(summary)
        return summaries

    def ingest_single(self, ticker: str) -> IngestSummary | None:
        canonical, display = resolve_ticker(ticker)
        asset = self._ensure_asset(canonical, display)
        frame = self._fetch_price_history(canonical)
        if frame.empty:
            return None

        frame = self._prepare_indicators(frame)

        market_inserted = 0
        indicator_inserted = 0
        last_timestamp = None

        for row in frame.itertuples():
            as_of = pd.Timestamp(row.Index).to_pydatetime()
            last_timestamp = as_of

            # Skip if snapshot already stored
            exists_stmt = select(MarketSnapshot).where(
                MarketSnapshot.asset_id == asset.id,
                MarketSnapshot.as_of == as_of,
            )
            if self.session.scalars(exists_stmt).first():
                continue

            market_snapshot = MarketSnapshot(
                asset_id=asset.id,
                price=float(row.Close),
                price_change_pct=self._safe_float(row.price_change_pct),
                volume=self._safe_float(row.Volume),
                vwap=self._safe_float(row.vwap),
                volatility_1d=self._safe_float(row.volatility_1d),
                as_of=as_of,
            )
            self.session.add(market_snapshot)
            self.session.flush()
            market_inserted += 1

            indicator_snapshot = IndicatorSnapshot(
                asset_id=asset.id,
                market_snapshot_id=market_snapshot.id,
                rsi_14=self._safe_float(row.rsi_14),
                macd=self._safe_float(row.macd),
                macd_signal=self._safe_float(row.macd_signal),
                atr_14=self._safe_float(row.atr_14),
                as_of=as_of,
            )
            self.session.add(indicator_snapshot)
            indicator_inserted += 1

        if last_timestamp is None:
            return None

        return IngestSummary(
            ticker=canonical,
            ingested_at=last_timestamp,
            market_records=market_inserted,
            indicator_records=indicator_inserted,
        )

    def _safe_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            if pd.isna(value):  # type: ignore[arg-type]
                return None
        except TypeError:
            return None
        return float(value)

    def _ensure_asset(self, ticker: str, display: str | None) -> Asset:
        normalized = ticker.upper()
        stmt = select(Asset).where(Asset.ticker == normalized)
        asset = self.session.scalars(stmt).first()
        if asset:
            if display and asset.display_ticker != display:
                asset.display_ticker = display
                self.session.add(asset)
            return asset

        asset = Asset(
            ticker=normalized,
            display_ticker=display,
            type="crypto" if normalized.endswith("-USD") else "stock",
        )
        self.session.add(asset)
        self.session.flush()
        self.session.refresh(asset)
        return asset

    def _fetch_price_history(self, ticker: str) -> pd.DataFrame:
        data = yf.download(
            tickers=ticker,
            period=f"{self.window_days}d",
            interval="1h",
            progress=False,
            auto_adjust=True,
        )
        if data.empty:
            return data
        if isinstance(data.columns, pd.MultiIndex):
            data = data.droplevel(-1, axis=1)

        lower_map = {str(col).lower(): col for col in data.columns}
        canonical_order = ["open", "high", "low", "close", "volume"]
        missing_keys = [key for key in canonical_order if key not in lower_map]
        if missing_keys:
            raise KeyError(f"Missing columns from price frame: {missing_keys}")

        ordered_columns = [lower_map[key] for key in canonical_order]
        data = data[ordered_columns]
        data.columns = ["Open", "High", "Low", "Close", "Volume"]
        if data.index.tzinfo is None:
            data.index = data.index.tz_localize("UTC")
        else:
            data.index = data.index.tz_convert("UTC")
        return data

    def _prepare_indicators(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        if "Close" not in frame.columns:
            raise KeyError(
                f"Close column missing; columns available: {[str(col) for col in frame.columns]}"
            )
        frame["price_change_pct"] = frame["Close"].pct_change() * 100
        price_returns = frame["Close"].pct_change()
        frame["volatility_1d"] = price_returns.rolling(window=24).std().mul((24) ** 0.5)
        volume = frame["Volume"].replace(0, pd.NA)
        cumulative_vp = (frame["Close"] * volume).cumsum()
        cumulative_volume = volume.cumsum()
        frame["vwap"] = cumulative_vp / cumulative_volume

        frame["rsi_14"] = compute_rsi(frame["Close"])
        macd, macd_signal = compute_macd(frame["Close"])
        frame["macd"] = macd
        frame["macd_signal"] = macd_signal
        frame["atr_14"] = compute_atr(frame["High"], frame["Low"], frame["Close"])
        return frame.loc[frame["Close"].notna()]
