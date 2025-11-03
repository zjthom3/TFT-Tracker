from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Iterable, Optional

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.db.models import Asset, SentimentObservation, SentimentSource


@dataclass
class SentimentSummary:
    ticker: str
    observations: int
    average_score: float | None
    observed_at: datetime | None


class SentimentIngestor:
    """Pulls lightweight sentiment using Yahoo Finance news + VADER."""

    def __init__(self, session: Session, window_minutes: int = 60) -> None:
        self.session = session
        self.window = timedelta(minutes=window_minutes)
        self.analyzer = SentimentIntensityAnalyzer()
        self.source = self._ensure_source("Yahoo Finance", channel="news", reliability="B")

    def ingest_many(self, tickers: Iterable[str]) -> list[SentimentSummary]:
        summaries: list[SentimentSummary] = []
        for ticker in tickers:
            summary = self.ingest_single(ticker)
            if summary:
                summaries.append(summary)
        return summaries

    def ingest_single(self, ticker: str) -> Optional[SentimentSummary]:
        asset = self._ensure_asset(ticker)
        news_items = self._fetch_recent_news(ticker)
        if not news_items:
            return None

        entries = []
        for item in news_items:
            title = item.get("title") or ""
            summary = item.get("summary") or item.get("publisher") or ""
            text = f"{title}. {summary}".strip()
            if not text:
                continue
            score_data = self.analyzer.polarity_scores(text)
            observed_at = datetime.fromtimestamp(item["providerPublishTime"], tz=timezone.utc)
            entries.append((observed_at, score_data["compound"], score_data["pos"] - score_data["neg"]))

        if not entries:
            return None

        latest_time = max(entry[0] for entry in entries)
        average_score = sum(entry[1] for entry in entries) / len(entries)
        average_magnitude = sum(abs(entry[2]) for entry in entries) / len(entries)

        existing = self.session.scalars(
            select(SentimentObservation).where(
                SentimentObservation.asset_id == asset.id,
                SentimentObservation.source_id == self.source.id,
                SentimentObservation.observed_at == latest_time,
            )
        ).first()

        if existing:
            existing.score = round(average_score, 4)
            existing.magnitude = round(average_magnitude, 4)
            existing.features = {"sample_size": len(entries)}
            observation = existing
        else:
            observation = SentimentObservation(
                asset_id=asset.id,
                source_id=self.source.id,
                score=round(average_score, 4),
                magnitude=round(average_magnitude, 4),
                features={"sample_size": len(entries)},
                observed_at=latest_time,
            )
            self.session.add(observation)
        return SentimentSummary(
            ticker=ticker,
            observations=len(entries),
            average_score=average_score,
            observed_at=latest_time,
        )

    def _fetch_recent_news(self, ticker: str) -> list[dict[str, object]]:
        try:
            news = yf.Ticker(ticker).news or []
        except Exception:
            return []
        if not news:
            return []
        cutoff = datetime.now(timezone.utc) - self.window
        filtered: list[dict[str, object]] = []
        for item in news:
            timestamp = item.get("providerPublishTime")
            if not isinstance(timestamp, (int, float)):
                continue
            observed_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            if observed_at < cutoff:
                continue
            filtered.append(item)
        return filtered

    def _ensure_source(self, name: str, channel: str, reliability: str) -> SentimentSource:
        stmt = select(SentimentSource).where(SentimentSource.name == name)
        source = self.session.scalars(stmt).first()
        if source:
            return source

        source = SentimentSource(name=name, channel=channel, reliability_tier=reliability)
        self.session.add(source)
        self.session.flush()
        self.session.refresh(source)
        return source

    def _ensure_asset(self, ticker: str) -> Asset:
        normalized = ticker.upper()
        stmt = select(Asset).where(Asset.ticker == normalized)
        asset = self.session.scalars(stmt).first()
        if asset:
            return asset
        asset = Asset(ticker=normalized, type="crypto" if normalized.endswith("-USD") else "stock")
        self.session.add(asset)
        self.session.flush()
        self.session.refresh(asset)
        return asset
