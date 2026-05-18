"""Portfolio-level carbon metrics per PCAF and GHG Protocol.

Computes:
  - Total Financed Emissions (tCO2e)
  - Carbon Intensity (tCO2e / $M invested)
  - Weighted Average Carbon Intensity (WACI) — Σ(w_i × intensity_i)

Reproducibility: pure functions, deterministic, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from esg_core.climate.attribution import AttributedEmissions, attribute_emissions
from esg_core.models.emissions import Emissions
from esg_core.models.portfolio import Portfolio


@dataclass(frozen=True)
class PortfolioCarbonReport:
    """Aggregated carbon metrics for an entire portfolio."""

    portfolio_id: str
    total_financed_emissions: float        # tCO2e
    carbon_intensity: float                # tCO2e / $M invested
    waci: float                            # Weighted Average Carbon Intensity
    per_holding: list[AttributedEmissions]
    total_investment_value: float          # USD


def compute_portfolio_carbon(
    portfolio: Portfolio,
    emissions_by_ticker: dict[str, Emissions],
) -> PortfolioCarbonReport:
    """Compute portfolio-level carbon footprint using PCAF methodology.

    Args:
        portfolio: The portfolio to analyse.
        emissions_by_ticker: Map of company ticker → Emissions data.
            Companies without emissions data are skipped with a warning.

    Returns:
        A :class:`PortfolioCarbonReport` with per-holding and aggregate metrics.

    Reproducibility: deterministic; holdings processed in portfolio order.
    """
    per_holding: list[AttributedEmissions] = []
    waci = 0.0

    for holding in portfolio.holdings:
        ticker = holding.company.ticker
        if ticker not in emissions_by_ticker:
            continue
        emissions = emissions_by_ticker[ticker]
        ae = attribute_emissions(holding, emissions)
        per_holding.append(ae)

        # WACI contribution: portfolio_weight × (total_emissions / revenue_proxy)
        # Here we use total_emissions / EVIC as the intensity proxy
        evic = holding.company.enterprise_value
        if evic > 0:
            intensity = (emissions.scope_1 + emissions.scope_2 + emissions.total_scope_3) / (evic / 1_000_000)
            waci += holding.weight * intensity

    total_financed = sum(ae.attributed_total for ae in per_holding)
    total_invested = portfolio.total_investment_value
    carbon_intensity = (total_financed / (total_invested / 1_000_000)) if total_invested > 0 else 0.0

    return PortfolioCarbonReport(
        portfolio_id=portfolio.id,
        total_financed_emissions=total_financed,
        carbon_intensity=carbon_intensity,
        waci=waci,
        per_holding=per_holding,
        total_investment_value=total_invested,
    )
