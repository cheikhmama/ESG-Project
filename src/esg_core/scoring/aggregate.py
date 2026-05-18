"""Aggregation functions — indicators → themes → pillars → company.

All functions are pure: given the same inputs they return the same outputs.
No I/O, no randomness, no hidden state.

Reproducibility: dict keys are always sorted before iteration to guarantee
ordering-independence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

import numpy as np

from esg_core.models.methodology import (
    MissingDataStrategy,
    PillarConfig,
    ThemeConfig,
)
from esg_core.models.score import (
    IndicatorScore,
    PillarScore,
    ThemeScore,
)
from esg_core.scoring.missing_data import apply_missing_data_strategy
from esg_core.scoring.normalize import normalize_percentile


def _inputs_hash(data: dict[str, float | None]) -> str:
    """SHA-256 of a sorted JSON representation of the input data dict."""
    serialised = json.dumps(
        {k: v for k, v in sorted(data.items())},
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def aggregate_theme(
    indicator_values: dict[str, float | None],
    peer_matrix: dict[str, list[float]],
    theme_config: ThemeConfig,
    strategy: MissingDataStrategy,
) -> ThemeScore | None:
    """Aggregate indicator values into a ThemeScore.

    Args:
        indicator_values: Map of indicator_id → raw value (None if missing).
        peer_matrix: Map of indicator_id → list of peer raw values (for normalisation).
        theme_config: Configuration for this theme from the Methodology.
        strategy: Missing-data strategy from the Methodology.

    Returns:
        ThemeScore, or None if strategy==PROPAGATE_NULL and any value is missing.

    Reproducibility: sorts indicator keys before iteration; deterministic.
    """
    indicator_scores: list[IndicatorScore] = []
    active_weight_total = 0.0

    for ind_id in sorted(theme_config.indicators.keys()):
        ind_cfg = theme_config.indicators[ind_id]
        raw = indicator_values.get(ind_id)
        peers = np.array(peer_matrix.get(ind_id, []), dtype=np.float64)

        if raw is None:
            peer_normalised = np.array(
                [normalize_percentile(float(p), peers, ind_cfg.direction) for p in peers],
                dtype=np.float64,
            ) if len(peers) > 0 else np.array([], dtype=np.float64)
            sub = apply_missing_data_strategy(strategy, peer_normalised, ind_cfg.direction)
            if sub is None:
                if strategy == MissingDataStrategy.PROPAGATE_NULL:
                    return None
                # EXCLUDE_INDICATOR — skip weight
                continue
            normalised = sub
        else:
            normalised = normalize_percentile(float(raw), peers, ind_cfg.direction)

        active_weight_total += ind_cfg.weight
        indicator_scores.append(
            IndicatorScore(
                indicator_id=ind_id,
                raw_value=raw if raw is not None else float("nan"),
                normalized_value=normalised,
                weight=ind_cfg.weight,
                weighted_contribution=ind_cfg.weight * normalised,
            )
        )

    if not indicator_scores:
        return None

    # Renormalise weights if any indicator was excluded
    if abs(active_weight_total - 1.0) > 1e-6 and active_weight_total > 1e-10:
        scale = 1.0 / active_weight_total
        indicator_scores = [
            IndicatorScore(
                indicator_id=s.indicator_id,
                raw_value=s.raw_value,
                normalized_value=s.normalized_value,
                weight=s.weight * scale,
                weighted_contribution=s.weight * scale * s.normalized_value,
            )
            for s in indicator_scores
        ]

    theme_score = float(sum(s.weighted_contribution for s in indicator_scores))
    theme_score = float(np.clip(theme_score, 0.0, 100.0))

    return ThemeScore(
        theme_id="",  # set by caller
        score=theme_score,
        weight=theme_config.weight,
        weighted_contribution=theme_config.weight * theme_score,
        indicators=indicator_scores,
    )


def aggregate_pillar(
    pillar_id: str,
    pillar_config: PillarConfig,
    all_indicator_values: dict[str, float | None],
    all_peer_matrix: dict[str, dict[str, list[float]]],
    strategy: MissingDataStrategy,
) -> PillarScore | None:
    """Aggregate all themes within a pillar into a PillarScore.

    Args:
        pillar_id: Identifier for this pillar, e.g. 'environment'.
        pillar_config: Configuration for this pillar.
        all_indicator_values: Flat map of indicator_id → raw value.
        all_peer_matrix: Nested map theme_id → indicator_id → [peer values].
        strategy: Missing-data strategy from the Methodology.

    Returns:
        PillarScore, or None if propagate_null and any theme is None.

    Reproducibility: sorts theme keys before iteration.
    """
    theme_scores: list[ThemeScore] = []
    active_weight_total = 0.0

    for theme_id in sorted(pillar_config.themes.keys()):
        theme_cfg = pillar_config.themes[theme_id]
        peer_matrix = all_peer_matrix.get(theme_id, {})

        ts = aggregate_theme(all_indicator_values, peer_matrix, theme_cfg, strategy)

        if ts is None:
            if strategy == MissingDataStrategy.PROPAGATE_NULL:
                return None
            continue

        active_weight_total += theme_cfg.weight
        # Rebuild with correct theme_id (aggregate_theme leaves it blank)
        ts = ThemeScore(
            theme_id=theme_id,
            score=ts.score,
            weight=ts.weight,
            weighted_contribution=ts.weighted_contribution,
            indicators=ts.indicators,
        )
        theme_scores.append(ts)

    if not theme_scores:
        return None

    # Renormalise if themes were excluded
    if abs(active_weight_total - 1.0) > 1e-6 and active_weight_total > 1e-10:
        scale = 1.0 / active_weight_total
        theme_scores = [
            ThemeScore(
                theme_id=ts.theme_id,
                score=ts.score,
                weight=ts.weight * scale,
                weighted_contribution=ts.weight * scale * ts.score,
                indicators=ts.indicators,
            )
            for ts in theme_scores
        ]

    pillar_score = float(sum(ts.weighted_contribution for ts in theme_scores))
    pillar_score = float(np.clip(pillar_score, 0.0, 100.0))

    return PillarScore(
        pillar_id=pillar_id,
        score=pillar_score,
        weight=pillar_config.weight,
        weighted_contribution=pillar_config.weight * pillar_score,
        themes=theme_scores,
    )
