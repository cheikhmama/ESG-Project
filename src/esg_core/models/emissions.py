"""Emissions domain models — GHG Protocol Scope 1/2/3."""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Scope3Category(str, Enum):
    """All 15 GHG Protocol Scope 3 categories.

    Source: GHG Protocol Corporate Value Chain (Scope 3) Accounting
    and Reporting Standard, Table 5.4.
    """

    PURCHASED_GOODS_AND_SERVICES = "purchased_goods_and_services"
    CAPITAL_GOODS = "capital_goods"
    FUEL_AND_ENERGY = "fuel_and_energy"
    UPSTREAM_TRANSPORT = "upstream_transport"
    WASTE = "waste"
    BUSINESS_TRAVEL = "business_travel"
    EMPLOYEE_COMMUTING = "employee_commuting"
    UPSTREAM_LEASED_ASSETS = "upstream_leased_assets"
    DOWNSTREAM_TRANSPORT = "downstream_transport"
    PROCESSING_OF_SOLD_PRODUCTS = "processing_of_sold_products"
    USE_OF_SOLD_PRODUCTS = "use_of_sold_products"
    END_OF_LIFE_TREATMENT = "end_of_life_treatment"
    DOWNSTREAM_LEASED_ASSETS = "downstream_leased_assets"
    FRANCHISES = "franchises"
    INVESTMENTS = "investments"


class Emissions(BaseModel, frozen=True):
    """Full GHG emissions record for one company at one point in time.

    Scope 1 and Scope 2 are aggregate figures (tCO2e).
    Scope 3 is a partial or full breakdown by GHG Protocol category.
    Not all 15 categories need to be present — the dict may be sparse.

    Reproducibility: frozen=True; confidence range enforced by validator.
    """

    scope_1: float = Field(..., ge=0.0, description="Direct emissions (tCO2e)")
    scope_2: float = Field(
        ..., ge=0.0, description="Indirect emissions from purchased energy (tCO2e)"
    )
    scope_3: dict[Scope3Category, float] = Field(
        default_factory=dict,
        description="Scope 3 breakdown by GHG Protocol category (tCO2e). May be partial.",
    )
    source: str = Field(
        ...,
        min_length=1,
        description="Data provenance: 'CDP', 'GRI', 'company_report', 'estimated'",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall data reliability in [0.0, 1.0]",
    )
    as_of_date: date = Field(..., description="Reporting period end date")

    @field_validator("confidence")
    @classmethod
    def confidence_in_unit_interval(cls, v: float) -> float:
        """Validate confidence is strictly within [0.0, 1.0].

        Reproducibility: out-of-range values are rejected rather than clipped.
        """
        if not (0.0 <= v <= 1.0):
            msg = f"confidence must be in [0.0, 1.0], got {v}"
            raise ValueError(msg)
        return v

    @field_validator("scope_3")
    @classmethod
    def scope_3_values_non_negative(
        cls, v: dict[Scope3Category, float]
    ) -> dict[Scope3Category, float]:
        """All Scope 3 category values must be non-negative."""
        for category, value in v.items():
            if value < 0.0:
                msg = f"Scope 3 category {category} has negative value {value}"
                raise ValueError(msg)
        return v

    @property
    def total_scope_3(self) -> float:
        """Sum of all reported Scope 3 categories (tCO2e)."""
        return sum(self.scope_3.values())

    @property
    def total_emissions(self) -> float:
        """Sum of Scope 1 + Scope 2 + total Scope 3 (tCO2e)."""
        return self.scope_1 + self.scope_2 + self.total_scope_3
