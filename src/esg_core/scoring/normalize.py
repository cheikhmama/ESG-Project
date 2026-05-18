"""Indicator normalisation — raw values → 0–100 scale.

Two strategies are supported:
  - percentile_rank: position within the peer group (default, robust)
  - z_score: standard-score then linearly mapped to [0, 100]

All functions are pure (no I/O, no randomness) and operate on numpy arrays
for determinism with numpy.float64 precision.

Reproducibility: no randomness, no hidden state. Same inputs → same output.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def _direction_factor(direction: str) -> float:
    """Return +1 for higher_is_better, -1 for lower_is_better."""
    if direction == "lower_is_better":
        return -1.0
    return 1.0


def normalize_percentile(
    value: float,
    peer_values: npt.NDArray[np.float64],
    direction: str,
) -> float:
    """Normalise a single value relative to its peer group using percentile rank.

    Args:
        value: Raw indicator value for the target company.
        peer_values: Array of raw values for the entire peer group (including target).
        direction: 'higher_is_better' or 'lower_is_better'.

    Returns:
        Score in [0.0, 100.0].

    Reproducibility: deterministic — same inputs → same output. No randomness.
    """
    factor = _direction_factor(direction)
    signed = peer_values * factor
    target = value * factor

    n = len(signed)
    if n <= 1:
        return 50.0  # single company → neutral score

    rank = float(np.sum(signed <= target))
    percentile = (rank / n) * 100.0
    return float(np.clip(percentile, 0.0, 100.0))


def normalize_zscore(
    value: float,
    peer_values: npt.NDArray[np.float64],
    direction: str,
) -> float:
    """Normalise a single value using z-score then map to [0, 100].

    Z-scores outside [−3, +3] are clipped before mapping.
    Mapping: z_clipped ∈ [−3, 3] → [0, 100].

    Args:
        value: Raw indicator value for the target company.
        peer_values: Array of raw values for the entire peer group.
        direction: 'higher_is_better' or 'lower_is_better'.

    Returns:
        Score in [0.0, 100.0].

    Reproducibility: deterministic. Uses numpy.float64 arithmetic.
    """
    factor = _direction_factor(direction)
    signed = peer_values * factor
    target = value * factor

    std = float(np.std(signed, ddof=0))
    if std < 1e-10:
        return 50.0  # all values identical → neutral score

    mean = float(np.mean(signed))
    z = (target - mean) / std
    z_clipped = float(np.clip(z, -3.0, 3.0))
    return float((z_clipped + 3.0) / 6.0 * 100.0)
