"""Indicator domain models — value and definition."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class IndicatorValue(BaseModel, frozen=True):
    """A single ESG data point for one indicator at one point in time.

    Carries the raw value, provenance (source), confidence, and
    temporal context. Confidence < 1.0 means the value is estimated
    or from a low-quality source — the scoring engine uses this to
    apply missing-data strategies.

    Reproducibility: frozen=True; confidence range enforced by validator.
    """

    value: float = Field(..., description="The raw measured or estimated value")
    source: str = Field(
        ...,
        min_length=1,
        description="Data provenance, e.g. 'CDP', 'GRI', 'company_report', 'estimated'",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Reliability score in [0.0, 1.0]. 1.0 = verified third-party. 0.0 = pure estimate.",
    )
    as_of_date: date = Field(..., description="The date the data point refers to")

    @field_validator("confidence")
    @classmethod
    def confidence_in_unit_interval(cls, v: float) -> float:
        """Validate confidence is strictly within [0.0, 1.0].

        Reproducibility: out-of-range confidence values are rejected
        rather than silently clipped.
        """
        if not (0.0 <= v <= 1.0):
            msg = f"confidence must be in [0.0, 1.0], got {v}"
            raise ValueError(msg)
        return v


class IndicatorDefinition(BaseModel, frozen=True):
    """Metadata describing what an ESG indicator measures.

    This is the 'schema' for an indicator — it does not carry a value,
    it describes the indicator's identity, unit, and scoring direction.

    Reproducibility: frozen=True; direction is constrained to a Literal.
    """

    id: str = Field(
        ..., min_length=1, description="Machine-readable identifier, e.g. 'scope_1_intensity'"
    )
    name: str = Field(..., min_length=1, description="Human-readable label")
    pillar: str = Field(..., description="ESG pillar: 'environment', 'social', or 'governance'")
    theme: str = Field(
        ..., min_length=1, description="Theme within the pillar, e.g. 'climate_change'"
    )
    unit: str = Field(..., min_length=1, description="Measurement unit, e.g. 'tCO2e/M$'")
    direction: Literal["higher_is_better", "lower_is_better"] = Field(
        ...,
        description="'higher_is_better' means a larger value → better score (e.g. renewable energy %). "
        "'lower_is_better' means a smaller value → better score (e.g. emissions intensity).",
    )
