"""Portfolio domain models — Holding and Portfolio."""

from datetime import date

from pydantic import BaseModel, Field, model_validator

from esg_core.models.company import Company

_WEIGHT_TOLERANCE = 1e-6


class Holding(BaseModel, frozen=True):
    """A single position in a portfolio.

    weight is the portfolio weight (fraction, must sum to 1.0 across all
    holdings in a Portfolio). investment_value is the monetary amount invested
    in the portfolio's currency — used for PCAF carbon attribution.

    Reproducibility: frozen=True.
    """

    company: Company = Field(..., description="The company held")
    weight: float = Field(
        ..., gt=0.0, le=1.0, description="Portfolio weight as a fraction (0, 1]"
    )
    investment_value: float = Field(
        ..., ge=0.0, description="Monetary value invested in portfolio currency"
    )


class Portfolio(BaseModel, frozen=True):
    """A named collection of Holdings.

    Enforces that holding weights sum to 1.0 ± 1e-6. This is a mathematical
    requirement — a portfolio where weights don't sum to 1.0 is invalid.

    Reproducibility: frozen=True; weight sum enforced at construction time.
    """

    id: str = Field(..., min_length=1, description="Unique identifier")
    name: str = Field(..., min_length=1, description="Human-readable portfolio name")
    holdings: list[Holding] = Field(..., min_length=1, description="Ordered list of holdings")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code, e.g. 'USD'"
    )
    as_of_date: date = Field(..., description="Valuation date")

    @model_validator(mode="after")
    def holding_weights_sum_to_one(self) -> "Portfolio":
        """Validate that holding weights sum to 1.0 ± 1e-6.

        Reproducibility: a portfolio with invalid weights cannot be scored
        correctly — reject early with a clear error.
        """
        total = sum(h.weight for h in self.holdings)
        if abs(total - 1.0) > _WEIGHT_TOLERANCE:
            msg = (
                f"Portfolio holding weights must sum to 1.0 ± {_WEIGHT_TOLERANCE}. "
                f"Got {total:.8f}"
            )
            raise ValueError(msg)
        return self

    @property
    def total_investment_value(self) -> float:
        """Total monetary value across all holdings."""
        return sum(h.investment_value for h in self.holdings)
