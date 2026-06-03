"""Portfolio routes — GET /portfolios, GET /portfolios/{id}/score."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from esg_api.dependencies import (
    build_portfolio,
    compute_portfolio_score,
    get_reference_portfolios,
    get_scores,
)
from esg_api.schemas import HoldingOut, PortfolioScoreOut

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


def _build_portfolio_out(pdef: dict, scores: dict) -> PortfolioScoreOut:  # type: ignore[type-arg]
    portfolio = build_portfolio(pdef)
    result = compute_portfolio_score(portfolio, scores["company_scores"], scores["methodology"])
    ps = result["portfolio_score"]
    carbon = result["carbon_report"]

    holdings_out = [
        HoldingOut(
            ticker=h.company.ticker,
            company_name=h.company.name,
            weight=h.weight,
            investment_value=h.investment_value,
            esg_score=round(scores["company_scores"][h.company.ticker].final_score, 4)
            if h.company.ticker in scores["company_scores"]
            else None,
        )
        for h in portfolio.holdings
    ]

    return PortfolioScoreOut(
        portfolio_id=str(pdef["id"]),
        name=str(pdef["name"]),
        weighted_portfolio_score=round(ps.weighted_portfolio_score, 4),
        total_financed_emissions=round(carbon.total_financed_emissions, 2),
        carbon_intensity=round(carbon.carbon_intensity, 4),
        waci=round(carbon.waci, 4),
        waci_coverage=round(carbon.waci_coverage, 4),
        carbon_to_value=round(carbon.carbon_to_value, 4),
        pcaf_data_quality=round(carbon.data_quality.weighted_pcaf_score, 2),
        pcaf_coverage=round(carbon.data_quality.coverage, 4),
        total_investment=portfolio.total_investment_value,
        holdings=holdings_out,
    )


@router.get(
    "", response_model=list[PortfolioScoreOut], summary="All reference portfolios with scores"
)
def list_portfolios() -> list[PortfolioScoreOut]:
    """Return all reference portfolios with their ESG and carbon metrics."""
    scores = get_scores()
    return [_build_portfolio_out(pdef, scores) for pdef in get_reference_portfolios()]


@router.get(
    "/{portfolio_id}/score", response_model=PortfolioScoreOut, summary="Score for one portfolio"
)
def get_portfolio_score(portfolio_id: str) -> PortfolioScoreOut:
    """Return the ESG score and carbon footprint for a specific reference portfolio."""
    portfolios = {str(p["id"]): p for p in get_reference_portfolios()}
    if portfolio_id not in portfolios:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found.")
    scores = get_scores()
    return _build_portfolio_out(portfolios[portfolio_id], scores)
