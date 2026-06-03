"""Portfolio-level carbon metrics per PCAF and GHG Protocol.

Computes:
  - Total Financed Emissions (tCO2e)
  - Carbon Footprint (tCO2e / $M invested) — portfolio-level carbon intensity
  - Weighted Average Carbon Intensity (WACI) — Σ(wᵢ × (emissionsᵢ / revenueᵢ))
        (PCAF: revenue is the denominator, NOT EVIC)
  - Carbon-to-Value Ratio (CTV) — Σ(wᵢ × (emissionsᵢ / EVICᵢ))
        (uses EVIC; conceptually distinct from WACI)

Reproducibility: pure functions, deterministic, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from esg_core.climate.attribution import AttributedEmissions, attribute_emissions
from esg_core.climate.data_quality import (
    PortfolioDataQualityReport,
    compute_portfolio_data_quality,
)
from esg_core.models.emissions import Emissions
from esg_core.models.portfolio import Portfolio


@dataclass(frozen=True)
class PortfolioCarbonReport:
    """Aggregated carbon metrics for an entire portfolio."""

    portfolio_id: str
    total_financed_emissions: float  # tCO2e
    carbon_intensity: float  # tCO2e / $M invested (portfolio carbon footprint)
    waci: float  # Σ(wᵢ × emissionsᵢ / revenueᵢ), tCO2e / $M revenue
    carbon_to_value: float  # Σ(wᵢ × emissionsᵢ / EVICᵢ), tCO2e / $M EVIC
    per_holding: list[AttributedEmissions]
    total_investment_value: float  # USD
    waci_coverage: float  # share of portfolio weight with usable revenue, [0, 1]
    data_quality: PortfolioDataQualityReport  # PCAF Data Quality score 1-5


def compute_portfolio_carbon(
    portfolio: Portfolio,
    emissions_by_ticker: dict[str, Emissions],
) -> PortfolioCarbonReport:
    """Compute portfolio-level carbon footprint using PCAF methodology.

    Args:
        portfolio: The portfolio to analyse.
        emissions_by_ticker: Map of company ticker → Emissions data.
            Companies without emissions data are skipped.

    Returns:
        A :class:`PortfolioCarbonReport` with per-holding and aggregate metrics.

    Reproducibility: deterministic; holdings processed in portfolio order.
    """
    per_holding: list[AttributedEmissions] = []
    waci = 0.0
    waci_weight_covered = 0.0
    ctv = 0.0
    ctv_weight_covered = 0.0

    for holding in portfolio.holdings:
        ticker = holding.company.ticker
        if ticker not in emissions_by_ticker:
            continue
        emissions = emissions_by_ticker[ticker]
        ae = attribute_emissions(holding, emissions)
        per_holding.append(ae)

        total_em = emissions.scope_1 + emissions.scope_2 + emissions.total_scope_3

        # WACI (PCAF): emissions per $M of revenue, holding-weight-weighted.
        revenue = holding.company.revenue
        if revenue > 0:
            intensity_rev = total_em / (revenue / 1_000_000)
            waci += holding.weight * intensity_rev
            waci_weight_covered += holding.weight

        # Carbon-to-Value: emissions per $M of EVIC, holding-weight-weighted.
        # Distinct from WACI — uses enterprise value, not revenue.
        evic = holding.company.enterprise_value
        if evic > 0:
            intensity_evic = total_em / (evic / 1_000_000)
            ctv += holding.weight * intensity_evic
            ctv_weight_covered += holding.weight

    total_financed = sum(ae.attributed_total for ae in per_holding)
    total_invested = portfolio.total_investment_value
    carbon_intensity = (
        (total_financed / (total_invested / 1_000_000)) if total_invested > 0 else 0.0
    )

    data_quality = compute_portfolio_data_quality(
        portfolio,
        emissions_by_ticker,
        per_holding,
    )

    return PortfolioCarbonReport(
        portfolio_id=portfolio.id,
        total_financed_emissions=total_financed,
        carbon_intensity=carbon_intensity,
        waci=waci,
        carbon_to_value=ctv,
        per_holding=per_holding,
        total_investment_value=total_invested,
        waci_coverage=waci_weight_covered,
        data_quality=data_quality,
    )
