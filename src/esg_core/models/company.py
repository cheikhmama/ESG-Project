"""Company domain model."""

from pydantic import BaseModel, Field


class Company(BaseModel, frozen=True):
    """Represents a company being assessed for ESG scoring.

    All fields are required. This model is immutable (frozen=True) to
    guarantee that a Company instance is identical across the entire
    scoring pipeline — required for reproducibility.

    Reproducibility: frozen=True ensures identity across pipeline stages.
    """

    ticker: str = Field(..., min_length=1, description="Stock ticker symbol, e.g. 'AAPL'")
    name: str = Field(..., min_length=1, description="Full legal name of the company")
    sector: str = Field(..., min_length=1, description="Industry sector, e.g. 'Technology'")
    country: str = Field(
        ..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"
    )
    isin: str = Field(..., min_length=12, max_length=12, description="ISO 6166 ISIN identifier")
    enterprise_value: float = Field(
        default=0.0,
        ge=0.0,
        description="Enterprise Value Including Cash (EVIC) in USD — used for PCAF carbon attribution",
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.ticker})"
