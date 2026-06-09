"""Shared styling utilities — dual light/dark theme via CSS custom properties."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit_shadcn_ui as ui

from streamlit_app.components import cards, kpi, layout
from streamlit_app.utils import tokens

# Single source of truth for structural / component CSS. Lives on disk so the
# stylesheet can be edited without touching Python (see docs/refactor/01-plan).
_CSS_PATH = Path(__file__).resolve().parents[1] / "assets" / "styles.css"


@lru_cache(maxsize=1)
def _static_css() -> str:
    """Return the structural stylesheet, read once from ``assets/styles.css``."""
    return _CSS_PATH.read_text(encoding="utf-8")

# ── Semantic colour maps (unchanged by theme) ─────────────────────────────────

SECTOR_COLORS: dict[str, str] = {
    "Mining & Metals": "#ef4444",
    "Utilities": "#f97316",
    "Telecommunications": "#3b82f6",
    "Technology": "#22c55e",
}

RISK_COLORS: dict[str, str] = {
    "High": "#ef4444",
    "Medium": "#f59e0b",
    "Low": "#22c55e",
}

PILLAR_COLORS: dict[str, str] = {
    "environment": "#22c55e",
    "social": "#3b82f6",
    "governance": "#8b5cf6",
}

# French display labels for the three ESG pillars (shared by the dashboard,
# comparison and explainability pages).
PILLAR_LABELS: dict[str, str] = {
    "environment": "Environnement",
    "social": "Social",
    "governance": "Gouvernance",
}

_COUNTRY_NAMES: dict[str, str] = {
    "MR": "Mauritanie",
    "MA": "Maroc",
    "SN": "Sénégal",
    "CI": "Côte d'Ivoire",
    "FR": "France",
    "US": "États-Unis",
    "GB": "Royaume-Uni",
    "DE": "Allemagne",
}

# ── Palette tokens ─────────────────────────────────────────────────────────────
# Palettes now live in ``tokens.py`` (single source of truth). Re-exported here
# under their historical names for backward compatibility.

_DARK = tokens.DARK
_LIGHT = tokens.LIGHT

# ── Theme helpers ─────────────────────────────────────────────────────────────


def current_theme() -> str:
    """Return the active theme name: 'dark' or 'light'."""
    return str(st.session_state.get("ui_theme", "dark"))


def palette() -> dict[str, str]:
    """Return the active colour palette."""
    return _DARK if current_theme() == "dark" else _LIGHT


def plotly_layout(**overrides: Any) -> dict[str, Any]:
    """Return a Plotly layout dict pre-configured for the active theme.

    Usage: ``fig.update_layout(**plotly_layout(title=..., barmode="group"))``
    """
    p = palette()
    base: dict[str, Any] = {
        "paper_bgcolor": p["chart_bg"],
        "plot_bgcolor": p["chart_bg"],
        "font": {"color": p["chart_text"], "family": "Inter"},
        "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"size": 11, "color": p["chart_text"]}},
        "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
        "xaxis": {"gridcolor": p["chart_grid"], "tickfont": {"size": 11}},
        "yaxis": {"gridcolor": p["chart_grid"], "tickfont": {"size": 11}},
    }
    base.update(overrides)
    return base


# ── CSS injection ─────────────────────────────────────────────────────────────


def _root_vars(p: dict[str, str]) -> str:
    """Return the ``:root`` block of theme palette variables (delegated to tokens)."""
    return tokens.palette_css(p)


def apply_global_styles() -> None:
    """Inject the active theme's CSS custom properties + structural styles."""
    # Initialise from query param so theme survives page reloads.
    if "ui_theme" not in st.session_state:
        st.session_state["ui_theme"] = st.query_params.get("theme", "dark")
    p = palette()
    st.markdown(
        f"<style>{_root_vars(p)}\n{tokens.static_tokens_css()}\n{_static_css()}</style>",
        unsafe_allow_html=True,
    )


# ── Page helpers ──────────────────────────────────────────────────────────────


def page_header(title: str, subtitle: str = "") -> None:
    """Render a compact page header with optional breadcrumb subtitle."""
    layout.page_header(title, subtitle)


# ── Score helpers ─────────────────────────────────────────────────────────────


def country_name(code: str) -> str:
    """Return the French country name for an ISO 3166-1 alpha-2 code."""
    return _COUNTRY_NAMES.get(code.upper(), code)


_T_HIGH = 70  # score threshold: green
_T_MID  = 50  # score threshold: amber
_T5_A   = 80  # 5-band: top green
_T5_B   = 65  # 5-band: lime
_T5_C   = 50  # 5-band: amber
_T5_D   = 35  # 5-band: orange


def score_color(score: float) -> str:
    if score >= _T_HIGH:
        return "#22c55e"
    if score >= _T_MID:
        return "#f59e0b"
    return "#ef4444"


def score_label(score: float) -> str:
    if score >= _T_HIGH:
        return "Élevé"
    if score >= _T_MID:
        return "Moyen"
    return "Faible"


def score_color5(score: float) -> str:
    """5-level ESG score colour — green → red."""
    if score >= _T5_A:
        return "#0ea672"
    if score >= _T5_B:
        return "#84cc16"
    if score >= _T5_C:
        return "#e89e0c"
    if score >= _T5_D:
        return "#f97316"
    return "#e53e3e"


# ── Card components ───────────────────────────────────────────────────────────


def dash_section(title: str, meta: str = "") -> None:
    """Compact section heading with optional inline meta text."""
    layout.dash_section(title, meta)


def kpi_v2(
    label: str,
    value: str,
    sub: str = "",
    trend: str = "",
    trend_dir: str = "up",
    color: str = "#2d7aed",
    pct: float = 0.0,
) -> None:
    """Compact enterprise KPI card with optional trend badge and progress bar."""
    kpi.kpi_v2(label, value, sub, trend, trend_dir, color, pct)


def kpi_card(label: str, value: str, sublabel: str = "") -> None:
    """KPI metric card — uses shadcn metric_card in light mode, custom HTML in dark."""
    if current_theme() == "light":
        ui.metric_card(title=label, content=value, description=sublabel)
    else:
        kpi.kpi_card_dark(label, value, sublabel)


def company_card(
    ticker: str,
    name: str,
    sector: str,
    score: float,
    carbon: float,
    risk: str,
    mc: float,
) -> None:
    """Company summary card — themed via CSS custom properties."""
    p = palette()
    cards.company_card(
        name=name,
        sector=sector,
        risk=risk,
        ticker=ticker,
        score_str=f"{score:.1f}",
        score_label=score_label(score),
        score_color=score_color(score),
        sector_color=SECTOR_COLORS.get(sector, "#6366f1"),
        risk_color=RISK_COLORS.get(risk, "#94a3b8"),
        carbon_k=f"{carbon / 1000:.1f}",
        mc_m=f"{mc / 1e6:.0f}",
        text_heading=p["text_heading"],
        text=p["text"],
        text_sub=p["text_sub"],
        divider=p["divider"],
        accent=p["accent"],
    )
