"""Fixture data for the 4 Mauritanian test companies."""

from __future__ import annotations

from datetime import date

from esg_core.models.company import Company
from esg_core.models.emissions import Emissions, Scope3Category

COMPANIES: dict[str, Company] = {
    "SNIM": Company(
        ticker="SNIM", name="Société Nationale Industrielle et Minière",
        sector="Mining & Metals", country="MR", isin="MR0000000001",
        enterprise_value=1_200_000_000.0,
    ),
    "SOMELEC": Company(
        ticker="SOMELEC", name="Société Mauritanienne d'Électricité",
        sector="Utilities", country="MR", isin="MR0000000002",
        enterprise_value=450_000_000.0,
    ),
    "MAURITEL": Company(
        ticker="MAURITEL", name="Mauritanienne de Télécommunications",
        sector="Telecommunications", country="MR", isin="MR0000000003",
        enterprise_value=280_000_000.0,
    ),
    "NEXT": Company(
        ticker="NEXT", name="Next Informatique",
        sector="Technology", country="MR", isin="MR0000000004",
        enterprise_value=35_000_000.0,
    ),
}

EMISSIONS: dict[str, Emissions] = {
    "SNIM": Emissions(
        scope_1=850_000.0, scope_2=120_000.0,
        scope_3={
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: 180_000.0,
            Scope3Category.UPSTREAM_TRANSPORT: 95_000.0,
            Scope3Category.FUEL_AND_ENERGY: 40_000.0,
            Scope3Category.WASTE: 25_000.0,
            Scope3Category.EMPLOYEE_COMMUTING: 8_000.0,
            Scope3Category.BUSINESS_TRAVEL: 3_500.0,
        },
        source="company_report", confidence=0.75,
        as_of_date=date(2024, 12, 31),
    ),
    "SOMELEC": Emissions(
        scope_1=1_250_000.0, scope_2=48_000.0,
        scope_3={
            Scope3Category.FUEL_AND_ENERGY: 95_000.0,
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: 55_000.0,
            Scope3Category.UPSTREAM_TRANSPORT: 22_000.0,
            Scope3Category.WASTE: 12_000.0,
            Scope3Category.EMPLOYEE_COMMUTING: 6_500.0,
        },
        source="company_report", confidence=0.70,
        as_of_date=date(2024, 12, 31),
    ),
    "MAURITEL": Emissions(
        scope_1=24_500.0, scope_2=43_000.0,
        scope_3={
            Scope3Category.USE_OF_SOLD_PRODUCTS: 38_000.0,
            Scope3Category.EMPLOYEE_COMMUTING: 4_200.0,
            Scope3Category.BUSINESS_TRAVEL: 2_100.0,
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: 18_000.0,
            Scope3Category.WASTE: 1_800.0,
        },
        source="estimated", confidence=0.55,
        as_of_date=date(2024, 12, 31),
    ),
    "NEXT": Emissions(
        scope_1=780.0, scope_2=3_400.0,
        scope_3={
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: 4_200.0,
            Scope3Category.EMPLOYEE_COMMUTING: 650.0,
            Scope3Category.BUSINESS_TRAVEL: 420.0,
            Scope3Category.USE_OF_SOLD_PRODUCTS: 1_200.0,
        },
        source="estimated", confidence=0.60,
        as_of_date=date(2024, 12, 31),
    ),
}

INDICATOR_VALUES: dict[str, dict[str, float | None]] = {
    "SNIM": {
        "scope_1_intensity": 708.3, "scope_2_intensity": 100.0,
        "scope_3_intensity": 292.5, "climate_policy": 40.0, "renewable_energy_pct": 8.0,
        "water_intensity": 95.0, "water_recycling_pct": 22.0, "water_policy": 50.0,
        "land_use_impact": 85.0, "biodiversity_policy": 30.0,
        "waste_intensity": 180.0, "recycling_rate": 18.0,
        "employee_turnover": 12.5, "gender_pay_gap": 22.0, "training_hours": 28.0, "injury_rate": 8.5,
        "supply_chain_audit": 35.0, "human_rights_policy": 45.0, "child_labor_incidents": 0.0,
        "community_investment": 55.0, "local_procurement_pct": 62.0, "social_impact_programs": 50.0,
        "board_independence_pct": 40.0, "women_on_board_pct": 15.0,
        "ceo_chair_separation": 100.0, "board_esg_expertise": 30.0,
        "esg_reporting_quality": 45.0, "audit_independence": 60.0, "disclosure_score": 40.0,
        "anti_bribery_policy": 50.0, "whistleblower_policy": 40.0, "corruption_incidents": 1.0,
    },
    "SOMELEC": {
        "scope_1_intensity": 1388.9, "scope_2_intensity": 53.3,
        "scope_3_intensity": 211.1, "climate_policy": 30.0, "renewable_energy_pct": 12.0,
        "water_intensity": 120.0, "water_recycling_pct": 15.0, "water_policy": 35.0,
        "land_use_impact": 70.0, "biodiversity_policy": 25.0,
        "waste_intensity": 145.0, "recycling_rate": 12.0,
        "employee_turnover": 9.0, "gender_pay_gap": 28.0, "training_hours": 20.0, "injury_rate": 5.5,
        "supply_chain_audit": 25.0, "human_rights_policy": 40.0, "child_labor_incidents": 0.0,
        "community_investment": 60.0, "local_procurement_pct": 55.0, "social_impact_programs": 45.0,
        "board_independence_pct": 35.0, "women_on_board_pct": 10.0,
        "ceo_chair_separation": 100.0, "board_esg_expertise": 20.0,
        "esg_reporting_quality": 35.0, "audit_independence": 55.0, "disclosure_score": 30.0,
        "anti_bribery_policy": 40.0, "whistleblower_policy": 30.0, "corruption_incidents": 2.0,
    },
    "MAURITEL": {
        "scope_1_intensity": 87.5, "scope_2_intensity": 153.6,
        "scope_3_intensity": 228.6, "climate_policy": 60.0, "renewable_energy_pct": 18.0,
        "water_intensity": 12.0, "water_recycling_pct": 45.0, "water_policy": 65.0,
        "land_use_impact": 20.0, "biodiversity_policy": 55.0,
        "waste_intensity": 22.0, "recycling_rate": 42.0,
        "employee_turnover": 7.5, "gender_pay_gap": 15.0, "training_hours": 45.0, "injury_rate": 1.8,
        "supply_chain_audit": 55.0, "human_rights_policy": 65.0, "child_labor_incidents": 0.0,
        "community_investment": 70.0, "local_procurement_pct": 72.0, "social_impact_programs": 68.0,
        "board_independence_pct": 58.0, "women_on_board_pct": 25.0,
        "ceo_chair_separation": 100.0, "board_esg_expertise": 55.0,
        "esg_reporting_quality": 62.0, "audit_independence": 70.0, "disclosure_score": 58.0,
        "anti_bribery_policy": 70.0, "whistleblower_policy": 65.0, "corruption_incidents": 0.0,
    },
    "NEXT": {
        "scope_1_intensity": 22.3, "scope_2_intensity": 97.1,
        "scope_3_intensity": 178.6, "climate_policy": 75.0, "renewable_energy_pct": 35.0,
        "water_intensity": 4.5, "water_recycling_pct": 60.0, "water_policy": 70.0,
        "land_use_impact": 5.0, "biodiversity_policy": 70.0,
        "waste_intensity": 8.0, "recycling_rate": 68.0,
        "employee_turnover": 5.0, "gender_pay_gap": 8.0, "training_hours": 65.0, "injury_rate": 0.5,
        "supply_chain_audit": 70.0, "human_rights_policy": 80.0, "child_labor_incidents": 0.0,
        "community_investment": 75.0, "local_procurement_pct": 80.0, "social_impact_programs": 78.0,
        "board_independence_pct": 65.0, "women_on_board_pct": 33.0,
        "ceo_chair_separation": 100.0, "board_esg_expertise": 70.0,
        "esg_reporting_quality": 72.0, "audit_independence": 75.0, "disclosure_score": 68.0,
        "anti_bribery_policy": 80.0, "whistleblower_policy": 75.0, "corruption_incidents": 0.0,
    },
}

REFERENCE_PORTFOLIOS: list[dict[str, object]] = [
    {
        "id": "mauritania-diversified", "name": "Mauritania Diversified",
        "description": "Equal-weight portfolio across all 4 Mauritanian companies",
        "holdings": [
            {"ticker": "SNIM", "weight": 0.25, "investment_value": 250_000.0},
            {"ticker": "SOMELEC", "weight": 0.25, "investment_value": 250_000.0},
            {"ticker": "MAURITEL", "weight": 0.25, "investment_value": 250_000.0},
            {"ticker": "NEXT", "weight": 0.25, "investment_value": 250_000.0},
        ],
        "currency": "USD",
    },
    {
        "id": "mauritania-esg-leaders", "name": "Mauritania ESG Leaders",
        "description": "Overweighted toward highest ESG scorers (tech + telecom)",
        "holdings": [
            {"ticker": "NEXT", "weight": 0.40, "investment_value": 400_000.0},
            {"ticker": "MAURITEL", "weight": 0.35, "investment_value": 350_000.0},
            {"ticker": "SNIM", "weight": 0.15, "investment_value": 150_000.0},
            {"ticker": "SOMELEC", "weight": 0.10, "investment_value": 100_000.0},
        ],
        "currency": "USD",
    },
    {
        "id": "mauritania-infrastructure", "name": "Mauritania Infrastructure",
        "description": "Heavy industries: SNIM + SOMELEC",
        "holdings": [
            {"ticker": "SNIM", "weight": 0.60, "investment_value": 600_000.0},
            {"ticker": "SOMELEC", "weight": 0.40, "investment_value": 400_000.0},
        ],
        "currency": "USD",
    },
]

RISK_LEVELS: dict[str, str] = {
    "SNIM": "High", "SOMELEC": "High", "MAURITEL": "Medium", "NEXT": "Low",
}

FINANCIAL_METRICS: dict[str, dict[str, float]] = {
    "SNIM":     {"market_cap": 980_000_000.0,  "revenue": 1_200_000_000.0, "employees": 6500},
    "SOMELEC":  {"market_cap": 380_000_000.0,  "revenue": 900_000_000.0,   "employees": 4200},
    "MAURITEL": {"market_cap": 250_000_000.0,  "revenue": 280_000_000.0,   "employees": 1800},
    "NEXT":     {"market_cap": 28_000_000.0,   "revenue": 35_000_000.0,    "employees": 320},
}
