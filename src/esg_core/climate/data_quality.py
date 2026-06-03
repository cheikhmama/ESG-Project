"""PCAF Data Quality Score (1–5) per the PCAF Global GHG Accounting Standard.

Reference: "The Global GHG Accounting and Reporting Standard for the Financial
Industry", Part A, section 5.10 — Data Quality. Lower score = higher quality.

PCAF Data Quality levels (listed from best to worst):
  1 — Audited/verified emissions data (third-party assurance).
  2 — Unverified emissions data calculated by the reporting entity from
      primary activity data (e.g. own fuel consumption × emission factors).
  3 — Reported sector/region average emissions intensity applied to
      company-specific physical activity data.
  4 — Estimated emissions based on company revenue (sector emission
      intensity × company revenue).
  5 — Estimated emissions based on total assets — highest uncertainty.

Reproducibility: pure functions, deterministic, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from esg_core.climate.attribution import AttributedEmissions
from esg_core.models.emissions import Emissions
from esg_core.models.portfolio import Portfolio

# Source string → PCAF Data Quality Score (1-5).
# Conservative mapping: when in doubt, assign a higher (worse) score so the
# reported quality is not optimistic. Unknown sources default to 5.
_SOURCE_TO_PCAF: dict[str, int] = {
    "audited": 1,
    "verified": 1,
    "third_party_verified": 1,
    "cdp": 2,
    "gri": 2,
    "company_report": 2,
    "self_reported": 2,
    "sector_intensity": 3,
    "estimated_from_activity": 3,
    "estimated": 4,
    "estimated_from_revenue": 4,
    "estimated_from_assets": 5,
}


def pcaf_score_for_source(source: str) -> int:
    """Map an Emissions ``source`` string to its PCAF Data Quality Score.

    Args:
        source: The provenance label on the Emissions record.

    Returns:
        Integer 1–5 (1 = best). Unknown sources default to 5 (most uncertain).
    """
    return _SOURCE_TO_PCAF.get(source.lower().strip(), 5)


@dataclass(frozen=True)
class HoldingDataQuality:
    """Per-holding PCAF Data Quality details."""

    ticker: str
    source: str
    pcaf_score: int  # 1 (best) to 5 (worst)
    holding_weight: float  # portfolio weight, [0, 1]


@dataclass(frozen=True)
class PortfolioDataQualityReport:
    """Portfolio-level PCAF Data Quality summary.

    weighted_pcaf_score is the holding-weight-weighted average across the
    portfolio. PCAF recommends disclosing the weighted score alongside total
    financed emissions so the user can interpret the latter in context.
    """

    weighted_pcaf_score: float  # weighted average, 1.0–5.0
    coverage: float  # share of portfolio weight with emissions data, [0, 1]
    per_holding: list[HoldingDataQuality]


def compute_portfolio_data_quality(
    portfolio: Portfolio,
    emissions_by_ticker: dict[str, Emissions],
    per_holding_attribution: list[AttributedEmissions],
) -> PortfolioDataQualityReport:
    """Compute the portfolio-level PCAF Data Quality score.

    Args:
        portfolio: The portfolio being analysed.
        emissions_by_ticker: Map of ticker → Emissions for all holdings.
        per_holding_attribution: The list from :func:`attribute_emissions`,
            used to identify which holdings were actually included in the
            footprint (matches the attribution coverage).

    Returns:
        A :class:`PortfolioDataQualityReport`. ``weighted_pcaf_score`` is
        ``5.0`` (worst) if no holding has emissions data — that signals
        "we have no quality information at all", not "perfect quality".

    Reproducibility: deterministic; holdings processed in portfolio order.
    """
    attributed_tickers = {ae.ticker for ae in per_holding_attribution}
    per_holding: list[HoldingDataQuality] = []
    weighted_sum = 0.0
    weight_covered = 0.0

    for holding in portfolio.holdings:
        ticker = holding.company.ticker
        if ticker not in emissions_by_ticker or ticker not in attributed_tickers:
            continue
        em = emissions_by_ticker[ticker]
        score = pcaf_score_for_source(em.source)
        per_holding.append(
            HoldingDataQuality(
                ticker=ticker,
                source=em.source,
                pcaf_score=score,
                holding_weight=holding.weight,
            )
        )
        weighted_sum += holding.weight * score
        weight_covered += holding.weight

    weighted = (weighted_sum / weight_covered) if weight_covered > 0 else 5.0

    return PortfolioDataQualityReport(
        weighted_pcaf_score=weighted,
        coverage=weight_covered,
        per_holding=per_holding,
    )
