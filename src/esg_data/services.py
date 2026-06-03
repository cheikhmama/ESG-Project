"""Layer-2 scoring service — orchestrates the core engine over fixture data.

This module sits in the data layer because it:
  * performs I/O (reads the methodology YAML from disk),
  * loads fixture data (``esg_data.fixtures``),
  * and orchestrates calls into the pure ``esg_core`` engine.

Both the FastAPI layer and the Streamlit dashboard import from here, which is
exactly the kind of cross-cutting "service" the four-layer architecture in
CLAUDE.md §3 expects to live in Layer 2 (data) rather than Layer 4 (UI).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from esg_core.climate.portfolio_metrics import compute_portfolio_carbon
from esg_core.explainability.decomposition import decompose_score
from esg_core.explainability.narrative import generate_narrative
from esg_core.methodology.loader import load_methodology
from esg_core.models.methodology import Methodology
from esg_core.models.portfolio import Holding, Portfolio
from esg_core.models.score import CompanyScore
from esg_core.scoring.engine import score_company, score_portfolio
from esg_data.fixtures import (
    COMPANIES,
    EMISSIONS,
    INDICATOR_VALUES,
    REFERENCE_PORTFOLIOS,  # noqa: F401  -- re-exported for callers
)

_METHODOLOGY_PATH = Path(__file__).resolve().parents[2] / "methodologies" / "default_v1.yaml"


def get_methodology() -> Methodology:
    """Load the active methodology YAML and return a validated Methodology."""
    return load_methodology(_METHODOLOGY_PATH)


def compute_all_scores() -> dict[str, Any]:
    """Run scoring engine for all 4 companies. Returns a results bundle.

    Under ``propagate_null`` a company can be unscored — those tickers are
    listed in ``unscored_tickers`` and excluded from ``company_scores`` so
    callers don't silently see a partial score where there is none.
    """
    methodology = get_methodology()
    tickers_in_order = list(INDICATOR_VALUES.keys())
    all_indicator_data = [INDICATOR_VALUES[t] for t in tickers_in_order]
    all_sectors = [COMPANIES[t].sector for t in tickers_in_order]
    scored_at = datetime(2025, 12, 31, tzinfo=UTC)

    company_scores: dict[str, CompanyScore] = {}
    unscored: list[str] = []
    for ticker, company in COMPANIES.items():
        cs = score_company(
            company=company,
            indicator_values=INDICATOR_VALUES[ticker],
            methodology=methodology,
            all_company_data=all_indicator_data,
            all_company_sectors=all_sectors,
            scored_at=scored_at,
        )
        if cs is None:
            unscored.append(ticker)
            continue
        company_scores[ticker] = cs

    if not company_scores:
        msg = "No company could be scored under the active methodology"
        raise RuntimeError(msg)

    return {
        "company_scores": company_scores,
        "unscored_tickers": unscored,
        "methodology": methodology,
        "methodology_hash": next(iter(company_scores.values())).methodology_hash,
    }


def build_portfolio(portfolio_def: dict[str, Any]) -> Portfolio:
    """Build a :class:`Portfolio` object from a reference-portfolio dict."""
    holdings = [
        Holding(
            company=COMPANIES[h["ticker"]],
            weight=float(h["weight"]),
            investment_value=float(h["investment_value"]),
        )
        for h in portfolio_def["holdings"]
        if h["ticker"] in COMPANIES
    ]
    return Portfolio(
        id=str(portfolio_def["id"]),
        name=str(portfolio_def["name"]),
        holdings=holdings,
        currency=str(portfolio_def["currency"]),
        as_of_date=date(2025, 12, 31),
    )


def compute_portfolio_score(
    portfolio: Portfolio,
    company_scores: dict[str, CompanyScore],
    methodology: Methodology,
) -> dict[str, Any]:
    """Compute portfolio-level ESG and carbon metrics.

    ``scored_at`` is derived from the underlying ``CompanyScore`` instances so
    the audit chain is self-consistent: the portfolio score carries the same
    timestamp as the per-company scores it aggregates.
    """
    if not company_scores:
        msg = "company_scores must be non-empty to derive a deterministic scored_at"
        raise ValueError(msg)
    scored_at = next(iter(company_scores.values())).scored_at
    ps = score_portfolio(portfolio, company_scores, methodology, scored_at=scored_at)
    carbon = compute_portfolio_carbon(portfolio, EMISSIONS)
    return {"portfolio_score": ps, "carbon_report": carbon}


def get_decomposition(
    ticker: str,
    company_scores: dict[str, CompanyScore],
) -> tuple[Any, str]:
    """Return ``(ScoreDecomposition, narrative_string)`` for one company."""
    cs = company_scores[ticker]
    decomp = decompose_score(cs)
    narrative = generate_narrative(decomp, company_score=cs)
    return decomp, narrative
