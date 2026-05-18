"""Score domain models — the output tree from the scoring engine."""

from datetime import datetime

from pydantic import BaseModel, Field

from esg_core.models.company import Company


class IndicatorScore(BaseModel, frozen=True):
    """Score for a single indicator.

    Carries both the raw and normalised value (0–100 scale), plus the
    weight and weighted contribution used in aggregation.

    Reproducibility: frozen=True; all values explicit for full audit trail.
    """

    indicator_id: str = Field(..., description="Matches IndicatorDefinition.id")
    raw_value: float = Field(..., description="Original data value before normalisation")
    normalized_value: float = Field(..., ge=0.0, le=100.0, description="Value on 0–100 scale")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight within its theme")
    weighted_contribution: float = Field(..., description="weight × normalized_value")


class ThemeScore(BaseModel, frozen=True):
    """Aggregated score for a theme — remembers all its IndicatorScores.

    The full indicator-level breakdown is preserved so that explainability
    can walk the tree without re-running the engine.

    Reproducibility: frozen=True; children always present.
    """

    theme_id: str = Field(..., description="Theme identifier, e.g. 'climate_change'")
    score: float = Field(..., ge=0.0, le=100.0, description="Weighted average of indicator scores")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight within its pillar")
    weighted_contribution: float = Field(..., description="weight × score")
    indicators: list[IndicatorScore] = Field(..., description="All indicator scores for this theme")


class PillarScore(BaseModel, frozen=True):
    """Aggregated score for a pillar (E, S, or G) — remembers all ThemeScores.

    Reproducibility: frozen=True; children always present.
    """

    pillar_id: str = Field(..., description="Pillar identifier: 'environment', 'social', 'governance'")
    score: float = Field(..., ge=0.0, le=100.0, description="Weighted average of theme scores")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight within the methodology")
    weighted_contribution: float = Field(..., description="weight × score")
    themes: list[ThemeScore] = Field(..., description="All theme scores for this pillar")


class CompanyScore(BaseModel, frozen=True):
    """Final ESG score for one company under one methodology.

    Carries the full pillar/theme/indicator breakdown, plus SHA-256 hashes
    of the methodology and input data used — enabling independent verification.

    Reproducibility: frozen=True; methodology_hash + inputs_hash tie this
    score to the exact inputs and configuration that produced it.
    """

    company: Company = Field(..., description="The company that was scored")
    final_score: float = Field(..., ge=0.0, le=100.0, description="Weighted ESG score (0–100)")
    pillars: list[PillarScore] = Field(..., description="Full E/S/G breakdown")
    methodology_hash: str = Field(..., description="SHA-256 hash of the Methodology used")
    inputs_hash: str = Field(..., description="SHA-256 hash of the serialised input data")
    scored_at: datetime = Field(..., description="UTC timestamp when this score was computed")

    def pillar(self, pillar_id: str) -> PillarScore | None:
        """Return the PillarScore for the given pillar_id, or None."""
        return next((p for p in self.pillars if p.pillar_id == pillar_id), None)


class PortfolioScore(BaseModel, frozen=True):
    """Aggregated ESG score across an entire portfolio.

    weighted_portfolio_score is the holding-weight-weighted average of
    all CompanyScore.final_score values.

    Reproducibility: frozen=True; methodology_hash present.
    """

    portfolio_id: str = Field(..., description="Matches Portfolio.id")
    scores: list[CompanyScore] = Field(..., description="Per-company scores")
    weighted_portfolio_score: float = Field(
        ..., ge=0.0, le=100.0, description="Holding-weight-averaged ESG score"
    )
    methodology_hash: str = Field(..., description="SHA-256 hash of the Methodology used")
    scored_at: datetime = Field(..., description="UTC timestamp when this score was computed")
