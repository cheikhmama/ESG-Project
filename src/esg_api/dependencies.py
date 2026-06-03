"""Shared FastAPI dependencies — data + scoring access.

Imports come from ``esg_data.fixtures`` (Layer 2). The Layer-3 API depends on
the Layer-2 data layer per the four-layer architecture in CLAUDE.md §3.
TODO Phase 3: swap ``esg_data.fixtures`` for ``esg_data.repositories`` once
the real ingestion pipeline is implemented.
"""

from __future__ import annotations

from functools import lru_cache

from esg_data.fixtures import (
    COMPANIES,
    EMISSIONS,
    FINANCIAL_METRICS,
    REFERENCE_PORTFOLIOS,
    RISK_LEVELS,
)
from esg_data.services import (
    build_portfolio,
    compute_all_scores,
    compute_portfolio_score,
    get_decomposition,
    get_methodology,
)


@lru_cache(maxsize=1)
def _scores() -> dict:  # type: ignore[type-arg]
    """Cached scoring results — expensive to compute, stable for the process lifetime."""
    return compute_all_scores()


def get_scores() -> dict:  # type: ignore[type-arg]
    return _scores()


def get_companies() -> dict:  # type: ignore[type-arg]
    return COMPANIES


def get_emissions() -> dict:  # type: ignore[type-arg]
    return EMISSIONS


def get_risk_levels() -> dict[str, str]:
    return RISK_LEVELS


def get_financial_metrics() -> dict:  # type: ignore[type-arg]
    return FINANCIAL_METRICS


def get_reference_portfolios() -> list:  # type: ignore[type-arg]
    return REFERENCE_PORTFOLIOS


__all__ = [
    "build_portfolio",
    "compute_portfolio_score",
    "get_companies",
    "get_decomposition",
    "get_emissions",
    "get_financial_metrics",
    "get_methodology",
    "get_reference_portfolios",
    "get_risk_levels",
    "get_scores",
]
