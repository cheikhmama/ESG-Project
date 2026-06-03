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
from esg_core.models.score import IndicatorQualityFlag
from esg_core.scoring.normalize import normalize_percentile

# Minimum same-sector peers required for sector-bucketed median. Below this,
# we fall back to the global peer median. With the current 4-company /
# 4-sector dataset every sector has 1 company, so the fallback always
# triggers — but the architecture is in place for larger datasets.
DEFAULT_MIN_SECTOR_PEERS = 2


def apply_missing_data_strategy(
    strategy: MissingDataStrategy,
    raw_peers: npt.NDArray[np.float64],
    sector_peers: npt.NDArray[np.float64],
    direction: str,
    min_sector_peers: int = DEFAULT_MIN_SECTOR_PEERS,
) -> tuple[float, IndicatorQualityFlag] | None:
    """Return a substitute normalised score (0–100) for a missing indicator.

    Args:
        strategy: The methodology-configured strategy.
        raw_peers: Raw values for the full peer group (any sector).
            Used for global median fallback and final normalisation.
        sector_peers: Raw values for same-sector peers only. May be empty
            or smaller than ``min_sector_peers`` — in which case the
            INDUSTRY_MEDIAN strategy falls back to ``raw_peers``.
        direction: 'higher_is_better' or 'lower_is_better'.
        min_sector_peers: Threshold for using sector-bucketed median.
            Below this, INDUSTRY_MEDIAN falls back to the global median.

    Returns:
        ``(score, quality_flag)`` if a substitute is computed, or ``None``
        for PROPAGATE_NULL / EXCLUDE_INDICATOR (the caller decides whether
        to propagate the null or drop the indicator and renormalise).

    Reproducibility: deterministic; no randomness.
    """
    match strategy:
        case MissingDataStrategy.PROPAGATE_NULL:
            return None

        case MissingDataStrategy.INDUSTRY_MEDIAN:
            if len(sector_peers) >= min_sector_peers:
                median_raw = float(np.median(sector_peers))
                used_sector = True
            elif len(raw_peers) > 0:
                median_raw = float(np.median(raw_peers))
                used_sector = False
            else:
                # No peers at all — neutral score, marked as such.
                return 50.0, IndicatorQualityFlag.NORMALIZED_NEUTRAL_NO_PEERS

            # Normalise the median raw value through the SAME percentile-rank
            # pipeline used for present values, so the imputed score reflects
            # the median's position in the broader peer distribution.
            normalised, _ = normalize_percentile(median_raw, raw_peers, direction)
            flag = (
                IndicatorQualityFlag.IMPUTED_SECTOR_MEDIAN
                if used_sector
                else IndicatorQualityFlag.IMPUTED_GLOBAL_MEDIAN
            )
            return normalised, flag

        case MissingDataStrategy.WORST_CASE_PENALTY:
            # 0 = worst on the 0–100 normalised scale, regardless of raw
            # value direction (the normalised scale is direction-corrected).
            return 0.0, IndicatorQualityFlag.IMPUTED_WORST_CASE

        case MissingDataStrategy.EXCLUDE_INDICATOR:
            # Caller must handle weight renormalisation.
            return None

        case _:
            msg = f"Unknown missing data strategy: {strategy}"
            raise ValueError(msg)
