"""Scoring utility — runs the full ESG engine for all fixture companies."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from src/ and repo root
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from datetime import date, datetime, timezone

from esg_core.methodology.loader import load_methodology
from esg_core.models.portfolio import Holding, Portfolio
from esg_core.scoring.engine import score_company, score_portfolio
from esg_core.climate.portfolio_metrics import compute_portfolio_carbon
from esg_core.explainability.decomposition import decompose_score
from esg_core.explainability.narrative import generate_narrative
from streamlit_app.data.companies_data import (
    COMPANIES, EMISSIONS, INDICATOR_VALUES, REFERENCE_PORTFOLIOS,
)

_METHODOLOGY_PATH = Path(__file__).parent.parent.parent / "methodologies" / "default_v1.yaml"


def get_methodology():  # type: ignore[no-untyped-def]
    return load_methodology(_METHODOLOGY_PATH)


def compute_all_scores() -> dict:  # type: ignore[type-arg]
    """Run scoring engine for all 4 companies. Returns full results dict."""
    methodology = get_methodology()
    all_indicator_data = list(INDICATOR_VALUES.values())
    scored_at = datetime(2025, 12, 31, tzinfo=timezone.utc)

    company_scores = {}
    for ticker, company in COMPANIES.items():
        cs = score_company(
            company=company,
            indicator_values=INDICATOR_VALUES[ticker],
            methodology=methodology,
            all_company_data=all_indicator_data,
            scored_at=scored_at,
        )
        company_scores[ticker] = cs

    return {
        "company_scores": company_scores,
        "methodology": methodology,
        "methodology_hash": company_scores["SNIM"].methodology_hash,
    }


def build_portfolio(portfolio_def: dict) -> Portfolio:  # type: ignore[type-arg]
    """Build a Portfolio object from a reference portfolio dict."""
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


def compute_portfolio_score(portfolio: Portfolio, company_scores: dict, methodology) -> dict:  # type: ignore[type-arg]
    """Compute portfolio-level ESG and carbon metrics."""
    ps = score_portfolio(portfolio, company_scores, methodology)
    carbon = compute_portfolio_carbon(portfolio, EMISSIONS)
    return {"portfolio_score": ps, "carbon_report": carbon}


def get_decomposition(ticker: str, company_scores: dict):  # type: ignore[type-arg]
    """Get full decomposition and narrative for one company."""
    cs = company_scores[ticker]
    decomp = decompose_score(cs)
    narrative = generate_narrative(decomp)
    return decomp, narrative
