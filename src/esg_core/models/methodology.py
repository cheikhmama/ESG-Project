"""Methodology domain models — weight tree and configuration."""

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_WEIGHT_TOLERANCE = 1e-6


class MissingDataStrategy(str, Enum):
    """Strategy applied when an indicator value is absent.

    propagate_null       — score becomes null; propagates up the tree.
    industry_median      — substitute the sector median for the indicator.
    worst_case_penalty   — assign the lowest possible normalised score (0).
    exclude_indicator    — drop the indicator and renormalise remaining weights.
    """

    PROPAGATE_NULL = "propagate_null"
    INDUSTRY_MEDIAN = "industry_median"
    WORST_CASE_PENALTY = "worst_case_penalty"
    EXCLUDE_INDICATOR = "exclude_indicator"


class IndicatorConfig(BaseModel, frozen=True):
    """Configuration for a single indicator within a theme.

    Reproducibility: frozen=True; direction is a constrained Literal.
    """

    weight: float = Field(..., gt=0.0, le=1.0, description="Relative weight within the theme")
    direction: Literal["higher_is_better", "lower_is_better"] = Field(
        ..., description="Scoring direction for this indicator"
    )


class ThemeConfig(BaseModel, frozen=True):
    """Configuration for a theme: groups indicators, validates their weights.

    Reproducibility: frozen=True; weights are validated to sum to 1.0 ± 1e-6.
    """

    weight: float = Field(..., gt=0.0, le=1.0, description="Relative weight within the pillar")
    indicators: dict[str, IndicatorConfig] = Field(
        ..., min_length=1, description="Indicator id → IndicatorConfig map"
    )

    @model_validator(mode="after")
    def indicator_weights_sum_to_one(self) -> "ThemeConfig":
        """Validate that indicator weights within this theme sum to 1.0 ± 1e-6.

        Reproducibility: reject malformed methodology rather than normalise silently.
        """
        total = sum(ind.weight for ind in self.indicators.values())
        if abs(total - 1.0) > _WEIGHT_TOLERANCE:
            msg = (
                f"Indicator weights within a theme must sum to 1.0 ± {_WEIGHT_TOLERANCE}. "
                f"Got {total:.8f} for indicators: {list(self.indicators.keys())}"
            )
            raise ValueError(msg)
        return self


class PillarConfig(BaseModel, frozen=True):
    """Configuration for a pillar (E, S, or G): groups themes.

    Reproducibility: frozen=True; theme weights validated to sum to 1.0 ± 1e-6.
    """

    weight: float = Field(..., gt=0.0, le=1.0, description="Relative weight within the methodology")
    themes: dict[str, ThemeConfig] = Field(
        ..., min_length=1, description="Theme id → ThemeConfig map"
    )

    @model_validator(mode="after")
    def theme_weights_sum_to_one(self) -> "PillarConfig":
        """Validate that theme weights within this pillar sum to 1.0 ± 1e-6.

        Reproducibility: reject malformed methodology rather than normalise silently.
        """
        total = sum(theme.weight for theme in self.themes.values())
        if abs(total - 1.0) > _WEIGHT_TOLERANCE:
            msg = (
                f"Theme weights within a pillar must sum to 1.0 ± {_WEIGHT_TOLERANCE}. "
                f"Got {total:.8f} for themes: {list(self.themes.keys())}"
            )
            raise ValueError(msg)
        return self


class Methodology(BaseModel, frozen=True):
    """Root methodology object — the complete scoring configuration.

    Carries the version (semver), pillar weights, missing-data strategy,
    and all indicator definitions. Every score produced with this methodology
    must reference it by SHA-256 hash (methodology_hash) for auditability.

    Reproducibility: frozen=True; semver enforced; pillar weights validated.
    """

    version: str = Field(..., description="Semver string, e.g. '1.0.0'")
    name: str = Field(..., min_length=1, description="Human-readable methodology name")
    description: str = Field(default="", description="Optional description")
    pillars: dict[str, PillarConfig] = Field(
        ..., min_length=1, description="Pillar id → PillarConfig map"
    )
    missing_data_strategy: MissingDataStrategy = Field(
        ..., description="Default strategy when an indicator value is missing"
    )

    @model_validator(mode="after")
    def version_is_semver(self) -> "Methodology":
        """Validate that version matches X.Y.Z semver pattern.

        Reproducibility: non-semver versions make audit trails ambiguous.
        """
        if not _SEMVER_RE.match(self.version):
            msg = f"Methodology version must be semver (X.Y.Z), got '{self.version}'"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def pillar_weights_sum_to_one(self) -> "Methodology":
        """Validate that pillar weights sum to 1.0 ± 1e-6.

        Reproducibility: reject malformed methodology rather than normalise silently.
        """
        total = sum(pillar.weight for pillar in self.pillars.values())
        if abs(total - 1.0) > _WEIGHT_TOLERANCE:
            msg = (
                f"Pillar weights must sum to 1.0 ± {_WEIGHT_TOLERANCE}. "
                f"Got {total:.8f} for pillars: {list(self.pillars.keys())}"
            )
            raise ValueError(msg)
        return self
