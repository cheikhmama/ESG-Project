"""API-specific Pydantic response schemas.

These are distinct from domain models in esg_core — they control the JSON
shape exposed to API consumers and can evolve independently of the engine.
"""

from __future__ import annotations

from pydantic import BaseModel


class PillarScoreOut(BaseModel):
    pillar_id: str
    score: float
    weight: float
    weighted_contribution: float


class CompanyOut(BaseModel):
    ticker: str
    name: str
    sector: str
    country: str
    isin: str
    enterprise_value: float
    risk_level: str
    market_cap: float | None = None
    revenue: float | None = None
    employees: int | None = None


class CompanyScoreOut(BaseModel):
    ticker: str
    company_name: str
    final_score: float
    pillars: list[PillarScoreOut]
    methodology_hash: str
    inputs_hash: str
    scored_at: str


class HoldingOut(BaseModel):
    ticker: str
    company_name: str
    weight: float
    investment_value: float
    esg_score: float | None = None


class PortfolioScoreOut(BaseModel):
    portfolio_id: str
    name: str
    weighted_portfolio_score: float
    total_financed_emissions: float  # tCO2e
    carbon_intensity: float  # tCO2e / $M invested (portfolio footprint)
    waci: float  # PCAF WACI — tCO2e / $M revenue, weighted by holding share
    waci_coverage: float  # share of holdings with usable revenue, [0, 1]
    carbon_to_value: float  # tCO2e / $M EVIC — distinct from WACI
    pcaf_data_quality: float  # PCAF Data Quality 1.0-5.0 (lower is better)
    pcaf_coverage: float  # share of holdings with data-quality info, [0, 1]
    total_investment: float
    holdings: list[HoldingOut]


class MethodologyOut(BaseModel):
    version: str
    name: str
    description: str
    methodology_hash: str
    pillar_weights: dict[str, float]
    missing_data_strategy: str


class IndicatorContributionOut(BaseModel):
    pillar_id: str
    theme_id: str
    indicator_id: str
    raw_value: float
    normalized_value: float
    absolute_contribution: float


class ExplainOut(BaseModel):
    ticker: str
    company_name: str
    final_score: float
    narrative: str
    pillar_scores: dict[str, float]
    theme_scores: dict[str, float]
    top_contributors: list[IndicatorContributionOut]
    bottom_contributors: list[IndicatorContributionOut]
    methodology_hash: str
