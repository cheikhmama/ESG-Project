"""Narrative generation — template-based human-readable score explanations.

Produces a concise plain-text narrative for a ScoreDecomposition.
No ML required — fully deterministic rule-based templates.

Reproducibility: pure function, no randomness.
"""

from __future__ import annotations

from esg_core.explainability.decomposition import ScoreDecomposition


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


def generate_narrative(decomposition: ScoreDecomposition) -> str:
    """Generate a human-readable ESG score explanation.

    Args:
        decomposition: A :class:`ScoreDecomposition` from :func:`decompose_score`.

    Returns:
        A multi-sentence plain-text narrative suitable for a report or dashboard.

    Reproducibility: fully deterministic template logic; same input → same output.
    """
    name = decomposition.company_name
    score = decomposition.final_score
    label = _score_label(score)

    lines: list[str] = [
        f"{name} received an overall ESG score of {score:.1f}/100, "
        f"which is considered {label}.",
    ]

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
