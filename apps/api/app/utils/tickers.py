from __future__ import annotations

from typing import Tuple

from app.config import get_settings


def resolve_ticker(raw_ticker: str) -> Tuple[str, str]:
    settings = get_settings()
    normalized = raw_ticker.upper()
    aliases = {alias.upper(): target.upper() for alias, target in settings.ticker_aliases.items()}
    canonical = aliases.get(normalized, normalized)
    display = normalized if canonical != normalized else canonical
    return canonical, display
