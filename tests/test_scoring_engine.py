"""Engine tests — deterministic scoring + all four missing-data strategies.

This is the test suite the project's own ``CLAUDE.md`` §5 (Phase 4 exit
criterion) declared "non-negotiable" but did not exist until now. It locks in:

  * Byte-identical reproducibility across runs (the foundation of the audit
    trail and Phase 9 verification CLI).
  * Correct semantics for each of the four missing-data strategies.
  * Hash sensitivity to every input that legitimately affects the score.
  * Input validation (typo guard).
  * Methodology-hash invariance under key reordering.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import yaml

from esg_core.methodology.hashing import methodology_hash
from esg_core.methodology.loader import load_methodology
from esg_core.models.methodology import MissingDataStrategy
from esg_core.models.score import IndicatorQualityFlag
from esg_core.scoring.engine import score_company
from esg_data.fixtures import COMPANIES, INDICATOR_VALUES
from esg_data.services import _METHODOLOGY_PATH, get_methodology

_SCORED_AT = datetime(2025, 12, 31, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def methodology():
    """The on-disk default methodology."""
    return get_methodology()


@pytest.fixture
def all_data():
    """Indicator dicts for every fixture company, in insertion order."""
    return [INDICATOR_VALUES[t] for t in INDICATOR_VALUES]


@pytest.fixture
def all_sectors():
    """Sectors parallel to ``all_data``."""
    return [COMPANIES[t].sector for t in INDICATOR_VALUES]


def _serialise(score) -> str:
    """Canonical JSON of a CompanyScore — used for byte-identity checks."""
    return score.model_dump_json()


# ---------------------------------------------------------------------------
# Determinism — Phase 4 exit criterion
# ---------------------------------------------------------------------------


def test_score_company_byte_identical_across_runs(
    methodology,
    all_data,
    all_sectors,
) -> None:
    """Same inputs, repeated calls → byte-identical JSON output."""
    snim = COMPANIES["SNIM"]
    runs = [
        score_company(
            company=snim,
            indicator_values=INDICATOR_VALUES["SNIM"],
            methodology=methodology,
            all_company_data=all_data,
            all_company_sectors=all_sectors,
            scored_at=_SCORED_AT,
        )
        for _ in range(20)
    ]
    payloads = {_serialise(r) for r in runs}
    assert len(payloads) == 1, "20 runs produced more than one distinct payload"


def test_methodology_hash_invariant_under_yaml_key_reorder(tmp_path) -> None:
    """Reordering YAML keys must not change the methodology hash."""
    original = yaml.safe_load(_METHODOLOGY_PATH.read_text(encoding="utf-8"))

    def _reverse(obj):
        if isinstance(obj, dict):
            return {k: _reverse(obj[k]) for k in reversed(list(obj))}
        if isinstance(obj, list):
            return [_reverse(x) for x in obj]
        return obj

    scrambled = _reverse(original)
    scrambled_path = tmp_path / "scrambled.yaml"
    scrambled_path.write_text(yaml.safe_dump(scrambled), encoding="utf-8")

    m1 = load_methodology(_METHODOLOGY_PATH)
    m2 = load_methodology(scrambled_path)
    assert methodology_hash(m1) == methodology_hash(m2)


# ---------------------------------------------------------------------------
# Missing-data strategies — all four covered
# ---------------------------------------------------------------------------


def _missing(ticker: str, indicator_id: str) -> dict[str, float | None]:
    """Clone ticker's indicator dict with one entry set to None."""
    return {k: (None if k == indicator_id else v) for k, v in INDICATOR_VALUES[ticker].items()}


def test_strategy_propagate_null_returns_none(methodology, all_data, all_sectors) -> None:
    m = methodology.model_copy(
        update={"missing_data_strategy": MissingDataStrategy.PROPAGATE_NULL},
    )
    cs = score_company(
        company=COMPANIES["SNIM"],
        indicator_values=_missing("SNIM", "scope_1_intensity"),
        methodology=m,
        all_company_data=all_data,
        all_company_sectors=all_sectors,
        scored_at=_SCORED_AT,
    )
    assert cs is None


def test_strategy_industry_median_imputes_and_flags(
    methodology,
    all_data,
    all_sectors,
) -> None:
    m = methodology.model_copy(
        update={"missing_data_strategy": MissingDataStrategy.INDUSTRY_MEDIAN},
    )
    cs = score_company(
        company=COMPANIES["SNIM"],
        indicator_values=_missing("SNIM", "scope_1_intensity"),
        methodology=m,
        all_company_data=all_data,
        all_company_sectors=all_sectors,
        scored_at=_SCORED_AT,
    )
    assert cs is not None
    flag = next(
        ind.quality_flag
        for p in cs.pillars
        for t in p.themes
        for ind in t.indicators
        if ind.indicator_id == "scope_1_intensity"
    )
    # 4-companies-4-sectors → sector bucket size 1 < threshold 2 → global fallback
    assert flag == IndicatorQualityFlag.IMPUTED_GLOBAL_MEDIAN


def test_strategy_exclude_indicator_renormalises(methodology, all_data, all_sectors) -> None:
    m = methodology.model_copy(
        update={"missing_data_strategy": MissingDataStrategy.EXCLUDE_INDICATOR},
    )
    cs = score_company(
        company=COMPANIES["SNIM"],
        indicator_values=_missing("SNIM", "scope_1_intensity"),
        methodology=m,
        all_company_data=all_data,
        all_company_sectors=all_sectors,
        scored_at=_SCORED_AT,
    )
    assert cs is not None
    # The excluded indicator must not appear in the breakdown
    indicator_ids = {ind.indicator_id for p in cs.pillars for t in p.themes for ind in t.indicators}
    assert "scope_1_intensity" not in indicator_ids
    # Sibling indicator weights in the same theme must renormalise to sum 1
    theme = next(t for p in cs.pillars for t in p.themes if t.theme_id == "climate_change")
    assert abs(sum(ind.weight for ind in theme.indicators) - 1.0) < 1e-6


def test_strategy_worst_case_penalty_imputes_zero(methodology, all_data, all_sectors) -> None:
    m = methodology.model_copy(
        update={"missing_data_strategy": MissingDataStrategy.WORST_CASE_PENALTY},
    )
    cs = score_company(
        company=COMPANIES["SNIM"],
        indicator_values=_missing("SNIM", "scope_1_intensity"),
        methodology=m,
        all_company_data=all_data,
        all_company_sectors=all_sectors,
        scored_at=_SCORED_AT,
    )
    assert cs is not None
    ind = next(
        i
        for p in cs.pillars
        for t in p.themes
        for i in t.indicators
        if i.indicator_id == "scope_1_intensity"
    )
    assert ind.normalized_value == 0.0
    assert ind.quality_flag == IndicatorQualityFlag.IMPUTED_WORST_CASE


# ---------------------------------------------------------------------------
# Sector bucketing — must actually fire when enough sector peers exist
# ---------------------------------------------------------------------------


def test_industry_median_uses_sector_when_enough_peers(
    methodology,
    all_data,
    all_sectors,
) -> None:
    """With ≥2 same-sector peers, the sector median (not global) is used."""

    def neutral_mining(scope_1: float) -> dict[str, float | None]:
        return {
            k: (scope_1 if k == "scope_1_intensity" else None) for k in INDICATOR_VALUES["SNIM"]
        }

    boosted_data = list(all_data) + [neutral_mining(3000.0), neutral_mining(3000.0)]
    boosted_sectors = list(all_sectors) + ["Mining & Metals", "Mining & Metals"]

    cs = score_company(
        company=COMPANIES["SNIM"],
        indicator_values=_missing("SNIM", "scope_1_intensity"),
        methodology=methodology,
        all_company_data=boosted_data,
        all_company_sectors=boosted_sectors,
        scored_at=_SCORED_AT,
    )
    assert cs is not None
    ind = next(
        i
        for p in cs.pillars
        for t in p.themes
        for i in t.indicators
        if i.indicator_id == "scope_1_intensity"
    )
    assert ind.quality_flag == IndicatorQualityFlag.IMPUTED_SECTOR_MEDIAN


# ---------------------------------------------------------------------------
# Hash sensitivity to legitimate inputs
# ---------------------------------------------------------------------------


def test_inputs_hash_changes_when_peer_added(
    methodology,
    all_data,
    all_sectors,
) -> None:
    snim = COMPANIES["SNIM"]
    full = score_company(
        snim,
        INDICATOR_VALUES["SNIM"],
        methodology,
        all_data,
        all_sectors,
        _SCORED_AT,
    )
    smaller_data = all_data[:3]
    smaller_sectors = all_sectors[:3]
    # SNIM is the first row, so it's still in the smaller peer set
    smaller = score_company(
        snim,
        INDICATOR_VALUES["SNIM"],
        methodology,
        smaller_data,
        smaller_sectors,
        _SCORED_AT,
    )
    assert full.inputs_hash != smaller.inputs_hash


def test_inputs_hash_changes_when_sector_swapped(
    methodology,
    all_data,
    all_sectors,
) -> None:
    snim = COMPANIES["SNIM"]
    base = score_company(
        snim, INDICATOR_VALUES["SNIM"], methodology, all_data, all_sectors, _SCORED_AT
    )
    swapped = list(all_sectors)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    other = score_company(
        snim, INDICATOR_VALUES["SNIM"], methodology, all_data, swapped, _SCORED_AT
    )
    assert base.inputs_hash != other.inputs_hash


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_rejects_unknown_indicator_in_target(methodology, all_data, all_sectors) -> None:
    typo = {
        ("scope1_intensity" if k == "scope_1_intensity" else k): v
        for k, v in INDICATOR_VALUES["SNIM"].items()
    }
    with pytest.raises(ValueError, match="indicator_values contains indicator IDs"):
        score_company(
            COMPANIES["SNIM"],
            typo,
            methodology,
            all_data,
            all_sectors,
            _SCORED_AT,
        )


def test_rejects_unknown_indicator_in_peer(methodology, all_data, all_sectors) -> None:
    poisoned = [dict(d) for d in all_data]
    poisoned[2]["bogus_indicator"] = 1.0
    with pytest.raises(ValueError, match="all_company_data"):
        score_company(
            COMPANIES["SNIM"],
            INDICATOR_VALUES["SNIM"],
            methodology,
            poisoned,
            all_sectors,
            _SCORED_AT,
        )


def test_rejects_misaligned_sectors_array(methodology, all_data, all_sectors) -> None:
    with pytest.raises(ValueError, match="all_company_sectors length"):
        score_company(
            COMPANIES["SNIM"],
            INDICATOR_VALUES["SNIM"],
            methodology,
            all_data,
            all_sectors[:-1],  # one short
            _SCORED_AT,
        )


# ---------------------------------------------------------------------------
# Golden — locks in the exact final_score for the 4 fixture companies
# ---------------------------------------------------------------------------


def test_golden_company_scores_on_default_methodology(
    methodology,
    all_data,
    all_sectors,
) -> None:
    """Regression guard: the canonical 4 companies score to known values.

    If this test fails after a methodology or fixture change, that's OK —
    update the expected dict deliberately. But silent drift here would mean
    a reproducibility break.
    """
    expected = {
        "SNIM": 46.92,
        "SOMELEC": 38.64,
        "MAURITEL": 73.13,
        "NEXT": 98.75,
    }
    for ticker, expected_score in expected.items():
        cs = score_company(
            company=COMPANIES[ticker],
            indicator_values=INDICATOR_VALUES[ticker],
            methodology=methodology,
            all_company_data=all_data,
            all_company_sectors=all_sectors,
            scored_at=_SCORED_AT,
        )
        assert cs is not None
        assert abs(cs.final_score - expected_score) < 0.01, (
            f"{ticker}: score drift {cs.final_score:.4f} vs golden {expected_score}"
        )
