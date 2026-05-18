"""Top-level scoring engine — score_company and score_portfolio.

These are the primary entry points for the scoring pipeline.
Both are pure functions: deterministic, no I/O, no side effects.

Reproducibility: methodology_hash and inputs_hash are attached to every
CompanyScore so that any third party can verify the score independently.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import numpy as np

from esg_core.methodology.hashing import methodology_hash as compute_methodology_hash
from esg_core.models.company import Company
from esg_core.models.methodology import Methodology
from esg_core.models.portfolio import Portfolio
from esg_core.models.score import CompanyScore, PillarScore, PortfolioScore
from esg_core.scoring.aggregate import aggregate_pillar


def _build_peer_matrix(
    all_company_data: list[dict[str, float | None]],
) -> dict[str, list[float]]:
    """Build indicator_id → [peer raw values] from all company data dicts.

    Only non-None values are included in the peer list for normalisation.

    Reproducibility: output is a plain dict of lists; no sorting needed
    because normalisation is symmetric.
    """
    peer: dict[str, list[float]] = {}
    for company_data in all_company_data:
        for ind_id, val in company_data.items():
            if val is not None:
                peer.setdefault(ind_id, []).append(float(val))
    return peer


def _flat_peer_to_nested(
    flat_peer: dict[str, list[float]],
    methodology: Methodology,
) -> dict[str, dict[str, dict[str, list[float]]]]:
    """Reshape flat peer matrix into pillar → theme → indicator → [values]."""
    nested: dict[str, dict[str, dict[str, list[float]]]] = {}
    for pillar_id, pillar_cfg in methodology.pillars.items():
        nested[pillar_id] = {}
        for theme_id, theme_cfg in pillar_cfg.themes.items():
            nested[pillar_id][theme_id] = {}
            for ind_id in theme_cfg.indicators:
                nested[pillar_id][theme_id][ind_id] = flat_peer.get(ind_id, [])
    return nested


def _inputs_hash(data: dict[str, float | None]) -> str:
    """SHA-256 of a sorted canonical JSON of the input indicator values."""
    serialised = json.dumps(
        {k: v for k, v in sorted(data.items())},
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def score_company(
    company: Company,
    indicator_values: dict[str, float | None],
    methodology: Methodology,
    all_company_data: list[dict[str, float | None]],
    scored_at: datetime | None = None,
) -> CompanyScore:
    """Score a single company under a given Methodology.

    Args:
        company: The company being scored.
        indicator_values: Map of indicator_id → raw value (None if missing).
            Keys must align with indicator IDs in the methodology.
        methodology: The validated Methodology to apply.
        all_company_data: List of indicator_value dicts for ALL companies in
            the peer group (including the target company). Required for
            peer-relative normalisation.
        scored_at: UTC datetime of scoring. If None, uses current UTC time.
            Always pass explicitly in production for reproducibility.

    Returns:
        A fully populated, immutable :class:`CompanyScore`.

    Reproducibility: given identical inputs and methodology, produces
    byte-identical output. Uses methodology_hash and inputs_hash for
    third-party verification.
    """
    if scored_at is None:
        scored_at = datetime.now(tz=timezone.utc)

    mhash = compute_methodology_hash(methodology)
    ihash = _inputs_hash(indicator_values)

    flat_peer = _build_peer_matrix(all_company_data)
    nested_peer = _flat_peer_to_nested(flat_peer, methodology)

    pillar_scores: list[PillarScore] = []
    active_pillar_weight_total = 0.0

    for pillar_id in sorted(methodology.pillars.keys()):
        pillar_cfg = methodology.pillars[pillar_id]
        ps = aggregate_pillar(
            pillar_id=pillar_id,
            pillar_config=pillar_cfg,
            all_indicator_values=indicator_values,
            all_peer_matrix=nested_peer.get(pillar_id, {}),
            strategy=methodology.missing_data_strategy,
        )
        if ps is None:
            continue
        active_pillar_weight_total += pillar_cfg.weight
        pillar_scores.append(ps)

    # Renormalise if any pillar dropped
    if abs(active_pillar_weight_total - 1.0) > 1e-6 and active_pillar_weight_total > 1e-10:
        scale = 1.0 / active_pillar_weight_total
        pillar_scores = [
            PillarScore(
                pillar_id=ps.pillar_id,
                score=ps.score,
                weight=ps.weight * scale,
                weighted_contribution=ps.weight * scale * ps.score,
                themes=ps.themes,
            )
            for ps in pillar_scores
        ]

    final_score = float(np.clip(sum(ps.weighted_contribution for ps in pillar_scores), 0.0, 100.0))

    return CompanyScore(
        company=company,
        final_score=final_score,
        pillars=pillar_scores,
        methodology_hash=mhash,
        inputs_hash=ihash,
        scored_at=scored_at,
    )


def score_portfolio(
    portfolio: Portfolio,
    company_scores: dict[str, CompanyScore],
    methodology: Methodology,
    scored_at: datetime | None = None,
) -> PortfolioScore:
    """Aggregate individual CompanyScores into a weighted PortfolioScore.

    Args:
        portfolio: The portfolio being scored.
        company_scores: Map of company ticker → CompanyScore.
        methodology: The Methodology used (for hash reference).
        scored_at: UTC datetime of scoring. Defaults to current UTC time.

    Returns:
        A fully populated, immutable :class:`PortfolioScore`.

    Reproducibility: weighted average is computed over numpy.float64.
    """
    if scored_at is None:
        scored_at = datetime.now(tz=timezone.utc)

    mhash = compute_methodology_hash(methodology)
    scores = list(company_scores.values())

    weighted_score = 0.0
    for holding in portfolio.holdings:
        cs = company_scores.get(holding.company.ticker)
        if cs is not None:
            weighted_score += holding.weight * cs.final_score

    weighted_score = float(np.clip(weighted_score, 0.0, 100.0))

    return PortfolioScore(
        portfolio_id=portfolio.id,
        scores=scores,
        weighted_portfolio_score=weighted_score,
        methodology_hash=mhash,
        scored_at=scored_at,
    )
