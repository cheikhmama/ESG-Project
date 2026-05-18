"""Explainability module package."""

from esg_core.explainability.decomposition import decompose_score
from esg_core.explainability.narrative import generate_narrative

__all__ = ["decompose_score", "generate_narrative"]
