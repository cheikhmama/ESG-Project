"""Score routes — GET /scores, GET /companies/{ticker}/score."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from esg_api.dependencies import get_scores
from esg_api.schemas import CompanyScoreOut, PillarScoreOut

router = APIRouter(tags=["Scores"])


def _build_score_out(ticker: str, cs: object) -> CompanyScoreOut:  # type: ignore[type-arg]
    from esg_core.models.score import CompanyScore

    assert isinstance(cs, CompanyScore)
    return CompanyScoreOut(
        ticker=ticker,
        company_name=cs.company.name,
        final_score=round(cs.final_score, 4),
        pillars=[
            PillarScoreOut(
                pillar_id=p.pillar_id,
                score=round(p.score, 4),
                weight=p.weight,
                weighted_contribution=round(p.weighted_contribution, 4),
            )
            for p in cs.pillars
        ],
        methodology_hash=cs.methodology_hash,
        inputs_hash=cs.inputs_hash,
        scored_at=cs.scored_at.isoformat(),
    )


@router.get("/scores", response_model=list[CompanyScoreOut], summary="All company ESG scores")
def list_scores() -> list[CompanyScoreOut]:
    """Return ESG scores for every company on the platform."""
    data = get_scores()
    return [
        _build_score_out(ticker, cs)
        for ticker, cs in data["company_scores"].items()
    ]


@router.get(
    "/companies/{ticker}/score",
    response_model=CompanyScoreOut,
    summary="ESG score for one company",
)
def get_company_score(ticker: str) -> CompanyScoreOut:
    """Return the full ESG score breakdown for a single company."""
    ticker = ticker.upper()
    data = get_scores()
    if ticker not in data["company_scores"]:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    return _build_score_out(ticker, data["company_scores"][ticker])
