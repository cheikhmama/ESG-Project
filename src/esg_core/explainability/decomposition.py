"""Score decomposition — walks the score tree to compute contributions.

Produces a flat, human-readable breakdown of how each indicator contributed
to the final ESG score.

Reproducibility: pure function, deterministic, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from esg_core.models.score import CompanyScore, IndicatorScore, PillarScore, ThemeScore


@dataclass(frozen=True)
class IndicatorContribution:
    """The contribution of one indicator to the final company score."""

    pillar_id: str
    theme_id: str
    indicator_id: str
    raw_value: float
    normalized_value: float
    indicator_weight_in_theme: float
    theme_weight_in_pillar: float
    pillar_weight_in_methodology: float
    # contribution = normalized × w_indicator × w_theme × w_pillar
    absolute_contribution: float


@dataclass(frozen=True)
class ScoreDecomposition:
    """Full decomposition of a CompanyScore into indicator-level contributions."""

    company_name: str
    final_score: float
    pillar_scores: dict[str, float]
    theme_scores: dict[str, float]  # "pillar/theme" → score
    contributions: list[IndicatorContribution]
    methodology_hash: str

    @property
    def top_contributors(self) -> list[IndicatorContribution]:
        """Top 5 positive contributors (highest absolute_contribution)."""
        return sorted(self.contributions, key=lambda c: c.absolute_contribution, reverse=True)[:5]

    @property
    def bottom_contributors(self) -> list[IndicatorContribution]:
        """Bottom 5 contributors (lowest absolute_contribution)."""
        return sorted(self.contributions, key=lambda c: c.absolute_contribution)[:5]


def decompose_score(company_score: CompanyScore) -> ScoreDecomposition:
    """Walk the score tree and produce a flat ScoreDecomposition.

    Args:
        company_score: The full CompanyScore with nested pillar/theme/indicator breakdown.

    Returns:
        A :class:`ScoreDecomposition` with all contribution data.

    Reproducibility: pure traversal of frozen models — deterministic.
    """
    contributions: list[IndicatorContribution] = []
    pillar_scores: dict[str, float] = {}
    theme_scores: dict[str, float] = {}

    for ps in company_score.pillars:
        pillar_scores[ps.pillar_id] = ps.score

        for ts in ps.themes:
            theme_key = f"{ps.pillar_id}/{ts.theme_id}"
            theme_scores[theme_key] = ts.score

            for ind_s in ts.indicators:
                abs_contribution = ind_s.normalized_value * ind_s.weight * ts.weight * ps.weight
                contributions.append(
                    IndicatorContribution(
                        pillar_id=ps.pillar_id,
                        theme_id=ts.theme_id,
                        indicator_id=ind_s.indicator_id,
                        raw_value=ind_s.raw_value,
                        normalized_value=ind_s.normalized_value,
                        indicator_weight_in_theme=ind_s.weight,
                        theme_weight_in_pillar=ts.weight,
                        pillar_weight_in_methodology=ps.weight,
                        absolute_contribution=abs_contribution,
                    )
                )

    return ScoreDecomposition(
        company_name=company_score.company.name,
        final_score=company_score.final_score,
        pillar_scores=pillar_scores,
        theme_scores=theme_scores,
        contributions=contributions,
        methodology_hash=company_score.methodology_hash,
    )
