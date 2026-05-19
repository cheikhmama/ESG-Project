"""Shared FastAPI dependencies — data + scoring access.

TODO Phase 3: replace COMPANIES/EMISSIONS imports with esg_data.repositories
once the ingestion pipeline is implemented.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from streamlit_app.data.companies_data import (  # noqa: E402
    COMPANIES,
    EMISSIONS,
    FINANCIAL_METRICS,
    REFERENCE_PORTFOLIOS,
    RISK_LEVELS,
)
from streamlit_app.utils.scoring_engine import (  # noqa: E402
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
    "get_scores",
    "get_companies",
    "get_emissions",
    "get_risk_levels",
    "get_financial_metrics",
    "get_reference_portfolios",
    "build_portfolio",
    "compute_portfolio_score",
    "get_decomposition",
    "get_methodology",
]
