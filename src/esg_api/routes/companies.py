"""Company routes — GET /companies, GET /companies/{ticker}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from esg_api.dependencies import get_companies, get_financial_metrics, get_risk_levels
from esg_api.schemas import CompanyOut

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=list[CompanyOut], summary="List all companies")
def list_companies() -> list[CompanyOut]:
    """Return all companies registered on the platform."""
    companies = get_companies()
    risk = get_risk_levels()
    fm = get_financial_metrics()
    return [
        CompanyOut(
            ticker=ticker,
            name=co.name,
            sector=co.sector,
            country=co.country,
            isin=co.isin,
            enterprise_value=co.enterprise_value,
            risk_level=risk.get(ticker, "—"),
            market_cap=fm.get(ticker, {}).get("market_cap"),
            revenue=fm.get(ticker, {}).get("revenue"),
            employees=int(fm.get(ticker, {}).get("employees", 0)) or None,
        )
        for ticker, co in companies.items()
    ]


@router.get("/{ticker}", response_model=CompanyOut, summary="Get company by ticker")
def get_company(ticker: str) -> CompanyOut:
    """Return a single company by its ticker symbol (e.g. SNIM, SOMELEC)."""
    companies = get_companies()
    ticker = ticker.upper()
    if ticker not in companies:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    co = companies[ticker]
    risk = get_risk_levels()
    fm = get_financial_metrics()
    return CompanyOut(
        ticker=ticker,
        name=co.name,
        sector=co.sector,
        country=co.country,
        isin=co.isin,
        enterprise_value=co.enterprise_value,
        risk_level=risk.get(ticker, "—"),
        market_cap=fm.get(ticker, {}).get("market_cap"),
        revenue=fm.get(ticker, {}).get("revenue"),
        employees=int(fm.get(ticker, {}).get("employees", 0)) or None,
    )
