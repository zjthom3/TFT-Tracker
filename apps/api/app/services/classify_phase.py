from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Asset,
    IndicatorSnapshot,
    MarketSnapshot,
    PhaseHistory,
    PhaseState,
    SentimentObservation,
)
from app.config import get_settings

PHASE_COOP = "COOP"
PHASE_DEFECT = "DEFECT"
PHASE_FORGIVE = "FORGIVE"


@dataclass
class PhaseResult:
    phase: str
    confidence: float
    rationale: str
    computed_at: datetime


class PhaseClassifier:
    """Rule-based phase classifier for MVP."""

    DEFECT_DROP = -2.0
    COOP_LOWER = -0.5
    COOP_UPPER = 1.5
    RSI_LOW = 35.0
    RSI_FLOOR = 40.0
    RSI_HIGH = 65.0

    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def evaluate(self, asset: Asset, previous_state: Optional[PhaseState]) -> Optional[PhaseResult]:
        market_snapshots = list(
            self.session.scalars(
                select(MarketSnapshot)
                .where(MarketSnapshot.asset_id == asset.id)
                .order_by(MarketSnapshot.as_of.desc())
                .limit(2)
            )
        )
        if not market_snapshots:
            return None

        indicator_snapshots = list(
            self.session.scalars(
                select(IndicatorSnapshot)
                .where(IndicatorSnapshot.asset_id == asset.id)
                .order_by(IndicatorSnapshot.as_of.desc())
                .limit(2)
            )
        )

        current_market = market_snapshots[0]
        previous_market = market_snapshots[1] if len(market_snapshots) > 1 else None
        current_indicator = indicator_snapshots[0] if indicator_snapshots else None
        previous_indicator = indicator_snapshots[1] if len(indicator_snapshots) > 1 else None

        price_change_pct = self._resolve_price_change(current_market, previous_market)
        volatility_delta = self._resolve_volatility_change(current_market, previous_market)
        rsi_current = self._to_float(current_indicator.rsi_14) if current_indicator else None
        rsi_previous = self._to_float(previous_indicator.rsi_14) if previous_indicator else None

        sentiment_current = None
        sentiment_previous = None
        sentiment_stale = False
        if self.settings.enable_sentiment:
            sentiment_current, sentiment_previous, sentiment_stale = self._resolve_sentiment(asset.id)

        phase, confidence, rationale = self._determine_phase(
            price_change_pct=price_change_pct,
            rsi_current=rsi_current,
            rsi_previous=rsi_previous,
            volatility_delta=volatility_delta,
            previous_phase=previous_state.phase if previous_state else None,
            sentiment_current=sentiment_current,
            sentiment_previous=sentiment_previous,
            sentiment_stale=sentiment_stale,
        )

        computed_at = current_market.as_of
        return PhaseResult(phase=phase, confidence=confidence, rationale=rationale, computed_at=computed_at)

    def _determine_phase(
        self,
        *,
        price_change_pct: Optional[float],
        rsi_current: Optional[float],
        rsi_previous: Optional[float],
        volatility_delta: Optional[float],
        previous_phase: Optional[str],
        sentiment_current: Optional[float],
        sentiment_previous: Optional[float],
        sentiment_stale: bool,
    ) -> tuple[str, float, str]:
        reasons: list[str] = []
        confidence = 0.55

        # Rule 1: Defection
        defect_triggers = 0
        if price_change_pct is not None and price_change_pct <= self.DEFECT_DROP:
            defect_triggers += 1
            reasons.append(f"Price drop {price_change_pct:.2f}% <= {self.DEFECT_DROP}%")
        if rsi_current is not None and rsi_current < self.RSI_LOW:
            defect_triggers += 1
            reasons.append(f"RSI {rsi_current:.1f} below {self.RSI_LOW}")
        if sentiment_current is not None and sentiment_current <= -0.2:
            defect_triggers += 1
            reasons.append(f"Negative sentiment {sentiment_current:.2f}")

        if defect_triggers:
            confidence = min(0.6 + defect_triggers * 0.12, 0.95)
            return PHASE_DEFECT, confidence, "; ".join(reasons)

        # Rule 2: Forgiveness (requires previous phase defection)
        if previous_phase == PHASE_DEFECT:
            forgiveness_reasons: list[str] = []
            stable_price = price_change_pct is not None and abs(price_change_pct) < 0.5
            if stable_price:
                forgiveness_reasons.append("Price stabilized within ±0.5%")
            if rsi_current is not None:
                if rsi_previous is not None and rsi_current > rsi_previous:
                    forgiveness_reasons.append("RSI rising")
                elif rsi_current >= self.RSI_FLOOR:
                    forgiveness_reasons.append(f"RSI recovered above {self.RSI_FLOOR}")
            if (
                sentiment_current is not None
                and sentiment_previous is not None
                and sentiment_current - sentiment_previous >= 0.1
            ):
                forgiveness_reasons.append("Sentiment recovering")

            if forgiveness_reasons:
                confidence = min(0.62 + len(forgiveness_reasons) * 0.1, 0.9)
                rationale = "; ".join(forgiveness_reasons)
                return PHASE_FORGIVE, confidence, rationale

        # Rule 3: Cooperation
        coop_reasons: list[str] = []
        if price_change_pct is not None and self.COOP_LOWER <= price_change_pct <= self.COOP_UPPER:
            coop_reasons.append("Price change within stable band")
        if rsi_current is not None and self.RSI_FLOOR <= rsi_current <= self.RSI_HIGH:
            coop_reasons.append("RSI in neutral range")
        if volatility_delta is not None and volatility_delta < 0:
            coop_reasons.append("Volatility trending down")
        if sentiment_current is not None and sentiment_current >= 0.15:
            coop_reasons.append("Positive sentiment backdrop")

        if coop_reasons:
            confidence = min(0.6 + len(coop_reasons) * 0.1, 0.9)
            rationale = "; ".join(coop_reasons)
            return PHASE_COOP, confidence, rationale

        # Fallback to previous phase with reduced confidence or mild cooperation
        fallback_phase = previous_phase or PHASE_COOP
        if fallback_phase == PHASE_COOP:
            fallback_reason = "Defaulting to cooperation due to limited signals"
        else:
            fallback_reason = "Insufficient new evidence; carrying forward previous phase"
        confidence = 0.45 if previous_phase else 0.5
        if sentiment_stale:
            confidence = max(confidence - 0.05, 0.3)
        return fallback_phase, confidence, fallback_reason

    def _resolve_price_change(
        self,
        current: MarketSnapshot,
        previous: Optional[MarketSnapshot],
    ) -> Optional[float]:
        if current.price_change_pct is not None:
            return float(current.price_change_pct)
        if previous and previous.price and current.price:
            if previous.price == 0:
                return None
            return (current.price - previous.price) / previous.price * 100
        return None

    def _resolve_volatility_change(
        self,
        current: MarketSnapshot,
        previous: Optional[MarketSnapshot],
    ) -> Optional[float]:
        if previous is None or current.volatility_1d is None or previous.volatility_1d is None:
            return None
        return float(current.volatility_1d) - float(previous.volatility_1d)

    def _to_float(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return float(value)

    def _resolve_sentiment(self, asset_id: UUID) -> tuple[Optional[float], Optional[float], bool]:
        observations = list(
            self.session.scalars(
                select(SentimentObservation)
                .where(SentimentObservation.asset_id == asset_id)
                .order_by(SentimentObservation.observed_at.desc())
                .limit(2)
            )
        )
        if not observations:
            return None, None, False

        current = observations[0]
        previous = observations[1] if len(observations) > 1 else None
        now = datetime.now(timezone.utc)
        stale = (now - current.observed_at) > timedelta(minutes=self.settings.sentiment_window_minutes * 2)
        return current.score, previous.score if previous else None, stale


class PhaseUpdateService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.classifier = PhaseClassifier(session)

    def update_all(self) -> list[PhaseState]:
        assets = self.session.scalars(select(Asset)).all()
        results: list[PhaseState] = []
        for asset in assets:
            state = self.update_asset(asset)
            if state is not None:
                results.append(state)
        return results

    def update_assets_by_ticker(self, tickers: list[str]) -> list[PhaseState]:
        normalized = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
        if not normalized:
            return []
        assets = self.session.scalars(select(Asset).where(Asset.ticker.in_(normalized))).all()
        results: list[PhaseState] = []
        for asset in assets:
            state = self.update_asset(asset)
            if state is not None:
                results.append(state)
        return results

    def update_asset(self, asset: Asset) -> Optional[PhaseState]:
        previous_state = self.session.get(PhaseState, asset.id)
        result = self.classifier.evaluate(asset, previous_state)
        if result is None:
            return previous_state

        state = previous_state or PhaseState(asset_id=asset.id)
        phase_changed = state.phase != result.phase if previous_state else True
        from_phase = state.phase if previous_state else None

        state.phase = result.phase
        state.confidence = round(result.confidence, 2)
        state.rationale = result.rationale
        state.computed_at = result.computed_at

        if previous_state is None:
            self.session.add(state)

        if phase_changed:
            history_entry = PhaseHistory(
                asset_id=asset.id,
                from_phase=from_phase,
                to_phase=result.phase,
                confidence=state.confidence,
                rationale=result.rationale,
                changed_at=result.computed_at,
            )
            self.session.add(history_entry)

        return state
