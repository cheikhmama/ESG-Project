"""PCAF-compliant emissions attribution for a single holding.

Attribution formula (PCAF Standard, 2020):
    Attributed Emissions = (Investment_Value / EVIC) × Total_Emissions

Where EVIC = Enterprise Value Including Cash.

Reproducibility: pure function, no I/O, no randomness.
"""

from __future__ import annotations

from dataclasses import dataclass

from esg_core.models.emissions import Emissions
from esg_core.models.portfolio import Holding


@dataclass(frozen=True)
class AttributedEmissions:
    """PCAF-attributed emissions for one holding.

    All values in tCO2e. Attribution splits are proportional to
    (investment_value / EVIC) × scope_emissions.
    """

    ticker: str
    company_name: str
    attribution_factor: float  # investment_value / EVIC
    attributed_scope_1: float  # tCO2e
    attributed_scope_2: float  # tCO2e
    attributed_scope_3: float  # tCO2e
    attributed_total: float  # tCO2e
    data_source: str
    confidence: float


def attribute_emissions(
    holding: Holding,
    emissions: Emissions,
) -> AttributedEmissions:
    """Compute PCAF-attributed emissions for one portfolio holding.

    Args:
        holding: The portfolio position (weight, investment_value).
        emissions: The company's Scope 1/2/3 emissions data.

    Returns:
        :class:`AttributedEmissions` with per-scope breakdowns.

    Raises:
        ValueError: If the company's enterprise_value is zero or negative,
            making PCAF attribution undefined.

    Reproducibility: deterministic; uses only the inputs provided.
        No datetime.now(), no randomness.
    """
    evic = holding.company.enterprise_value
    if evic <= 0.0:
        msg = (
            f"Company '{holding.company.ticker}' has enterprise_value={evic}. "
            "PCAF attribution requires a positive EVIC."
        )
        raise ValueError(msg)

    factor = holding.investment_value / evic

    a_scope_1 = factor * emissions.scope_1
    a_scope_2 = factor * emissions.scope_2
    a_scope_3 = factor * emissions.total_scope_3

    return AttributedEmissions(
        ticker=holding.company.ticker,
        company_name=holding.company.name,
        attribution_factor=factor,
        attributed_scope_1=a_scope_1,
        attributed_scope_2=a_scope_2,
        attributed_scope_3=a_scope_3,
        attributed_total=a_scope_1 + a_scope_2 + a_scope_3,
        data_source=emissions.source,
        confidence=emissions.confidence,
    )
