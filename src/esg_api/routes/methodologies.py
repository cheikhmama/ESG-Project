"""Methodology routes — GET /methodologies/current."""

from __future__ import annotations

from fastapi import APIRouter

from esg_api.dependencies import get_methodology, get_scores
from esg_api.schemas import MethodologyOut

router = APIRouter(prefix="/methodologies", tags=["Methodologies"])


@router.get("/current", response_model=MethodologyOut, summary="Active ESG methodology")
def get_current_methodology() -> MethodologyOut:
    """Return the active scoring methodology — version, weights, and hash."""
    meth = get_methodology()
    scores = get_scores()
    pillar_weights = {
        pillar_id: config.weight
        for pillar_id, config in meth.pillars.items()
    }
    return MethodologyOut(
        version=meth.version,
        name=meth.name,
        description=meth.description,
        methodology_hash=scores["methodology_hash"],
        pillar_weights=pillar_weights,
        missing_data_strategy=meth.missing_data_strategy,
    )
