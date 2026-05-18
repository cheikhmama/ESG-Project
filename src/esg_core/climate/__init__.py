"""Climate / carbon module package."""

from esg_core.climate.attribution import attribute_emissions
from esg_core.climate.portfolio_metrics import compute_portfolio_carbon

__all__ = ["attribute_emissions", "compute_portfolio_carbon"]
