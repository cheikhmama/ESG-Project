"""Missing-data strategies for ESG scoring.

When an indicator value is absent for a company, one of four strategies
is applied — determined by the Methodology's missing_data_strategy field.

All functions are pure (no I/O, no side effects).

Reproducibility: strategies are deterministic; no randomness introduced.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from esg_core.models.methodology import MissingDataStrategy


def apply_missing_data_strategy(
    strategy: MissingDataStrategy,
    peer_values: npt.NDArray[np.float64],
    direction: str,
) -> float | None:
    """Return a substitute normalised score (0–100) for a missing indicator.

    Args:
        strategy: The methodology-configured strategy.
        peer_values: Array of normalised scores for the peer group.
            Used only for INDUSTRY_MEDIAN.
        direction: 'higher_is_better' or 'lower_is_better'.
            Used only for WORST_CASE_PENALTY.

    Returns:
        A float in [0.0, 100.0] if a substitute is computed,
        or None if the strategy is PROPAGATE_NULL or EXCLUDE_INDICATOR.

    Reproducibility: deterministic; no randomness.
    """
    match strategy:
        case MissingDataStrategy.PROPAGATE_NULL:
            return None
        case MissingDataStrategy.INDUSTRY_MEDIAN:
            if len(peer_values) == 0:
                return 50.0
            return float(np.median(peer_values))
        case MissingDataStrategy.WORST_CASE_PENALTY:
            # Worst case = 0 regardless of direction (0 = worst on 0–100 scale)
            return 0.0
        case MissingDataStrategy.EXCLUDE_INDICATOR:
            # Caller must handle weight renormalisation
            return None
        case _:
            msg = f"Unknown missing data strategy: {strategy}"
            raise ValueError(msg)
