"""Explainability routes — GET /companies/{ticker}/explain."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from esg_api.dependencies import get_decomposition, get_scores
from esg_api.schemas import ExplainOut, IndicatorContributionOut

router = APIRouter(tags=["Explainability"])


@router.get(
    "/companies/{ticker}/explain",
    response_model=ExplainOut,
    summary="Score decomposition and narrative for one company",
)
def explain_company(ticker: str) -> ExplainOut:
    """Return a full score decomposition with indicator-level contributions
    and a human-readable narrative explaining the ESG score drivers."""
    ticker = ticker.upper()
    scores = get_scores()
    if ticker not in scores["company_scores"]:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    decomp, narrative = get_decomposition(ticker, scores["company_scores"])

    def _contrib_out(c: object) -> IndicatorContributionOut:
        from esg_core.explainability.decomposition import IndicatorContribution

        assert isinstance(c, IndicatorContribution)
        return IndicatorContributionOut(
            pillar_id=c.pillar_id,
            theme_id=c.theme_id,
            indicator_id=c.indicator_id,
            raw_value=round(c.raw_value, 4),
            normalized_value=round(c.normalized_value, 4),
            absolute_contribution=round(c.absolute_contribution, 4),
        )

    return ExplainOut(
        ticker=ticker,
        company_name=decomp.company_name,
        final_score=round(decomp.final_score, 4),
        narrative=narrative,
        pillar_scores={k: round(v, 4) for k, v in decomp.pillar_scores.items()},
        theme_scores={k: round(v, 4) for k, v in decomp.theme_scores.items()},
        top_contributors=[_contrib_out(c) for c in decomp.top_contributors],
        bottom_contributors=[_contrib_out(c) for c in decomp.bottom_contributors],
        methodology_hash=decomp.methodology_hash,
    )
