"""Hand-curated fixture data for Mauritanian companies.

These are *placeholder* values until Phase 3 (real ingestion from annual
reports via the per-company parsers) lands. They live in the data layer so
the API and Streamlit pages share a single source and the four-layer
architecture is preserved (API/UI must not depend on each other).
"""

from esg_data.fixtures.companies_data import (
    COMPANIES,
    EMISSIONS,
    FINANCIAL_METRICS,
    INDICATOR_VALUES,
    REFERENCE_PORTFOLIOS,
    RISK_LEVELS,
)

__all__ = [
    "COMPANIES",
    "EMISSIONS",
    "FINANCIAL_METRICS",
    "INDICATOR_VALUES",
    "REFERENCE_PORTFOLIOS",
    "RISK_LEVELS",
]
