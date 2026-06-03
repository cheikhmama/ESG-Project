"""Narrative generation — template-based human-readable score explanations.

Produces a concise plain-text narrative for a ScoreDecomposition.
No ML required — fully deterministic rule-based templates.

Reproducibility: pure function, no randomness.
"""

from __future__ import annotations

from esg_core.explainability.decomposition import ScoreDecomposition
from esg_core.models.score import CompanyScore, IndicatorQualityFlag


def _score_label(score: float) -> str:
    """Map a 0–100 score to a qualitative label."""
    if score >= 75:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 45:
        return "moderate"
    if score >= 30:
        return "poor"
    return "very poor"


def _pillar_name(pillar_id: str) -> str:
    return {"environment": "Environmental", "social": "Social", "governance": "Governance"}.get(
        pillar_id, pillar_id.title()
    )


def generate_narrative(
    decomposition: ScoreDecomposition,
    company_score: CompanyScore | None = None,
) -> str:
    """Generate a human-readable ESG score explanation.

    Args:
        decomposition: A :class:`ScoreDecomposition` from :func:`decompose_score`.
        company_score: Optional source :class:`CompanyScore`. When provided,
            the narrative discloses how many indicators were imputed or fell
            back to a neutral score — a key transparency signal.

    Returns:
        A multi-sentence plain-text narrative suitable for a report or dashboard.

    Reproducibility: fully deterministic template logic; same input → same output.
    """
    name = decomposition.company_name
    score = decomposition.final_score
    label = _score_label(score)

    lines: list[str] = [
        f"{name} received an overall ESG score of {score:.1f}/100, which is considered {label}.",
    ]

    # Disclose data-quality issues if a CompanyScore was provided.
    if company_score is not None:
        imputed_flags = {
            IndicatorQualityFlag.IMPUTED_SECTOR_MEDIAN,
            IndicatorQualityFlag.IMPUTED_GLOBAL_MEDIAN,
            IndicatorQualityFlag.IMPUTED_WORST_CASE,
        }
        neutral_flags = {
            IndicatorQualityFlag.NORMALIZED_NEUTRAL_NO_PEERS,
            IndicatorQualityFlag.NORMALIZED_NEUTRAL_ZERO_VARIANCE,
        }
        n_imputed = 0
        n_neutral = 0
        n_total = 0
        for pillar in company_score.pillars:
            for theme in pillar.themes:
                for ind in theme.indicators:
                    n_total += 1
                    if ind.quality_flag in imputed_flags:
                        n_imputed += 1
                    elif ind.quality_flag in neutral_flags:
                        n_neutral += 1
        if n_imputed or n_neutral:
            parts: list[str] = []
            if n_imputed:
                parts.append(f"{n_imputed} indicator(s) were imputed from peer medians")
            if n_neutral:
                parts.append(f"{n_neutral} fell back to a neutral 50 (insufficient peer variance)")
            lines.append(
                "Data quality note: "
                + " and ".join(parts)
                + f", out of {n_total} indicators evaluated."
            )

    # Pillar breakdown
    pillar_parts: list[str] = []
    for pillar_id, pscore in sorted(decomposition.pillar_scores.items()):
        pillar_parts.append(f"{_pillar_name(pillar_id)}: {pscore:.1f}")
    if pillar_parts:
        lines.append("Pillar breakdown — " + ", ".join(pillar_parts) + ".")

    # Strongest contributor
    top = decomposition.top_contributors
    if top:
        best = top[0]
        lines.append(
            f"The strongest contributor was {best.indicator_id.replace('_', ' ')} "
            f"(normalised score: {best.normalized_value:.1f}), "
            f"within the {best.theme_id.replace('_', ' ')} theme of the "
            f"{_pillar_name(best.pillar_id)} pillar."
        )

    # Weakest contributor
    bottom = decomposition.bottom_contributors
    if bottom:
        worst = bottom[0]
        lines.append(
            f"The area with most room for improvement was "
            f"{worst.indicator_id.replace('_', ' ')} "
            f"(normalised score: {worst.normalized_value:.1f}), "
            f"within the {worst.theme_id.replace('_', ' ')} theme."
        )

    lines.append(
        f"This score was computed using methodology version tracked by hash "
        f"{decomposition.methodology_hash[:12]}..."
    )

    return " ".join(lines)
