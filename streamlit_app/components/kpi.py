"""KPI components — enterprise KPI card (with trend/progress) and metric box."""

from __future__ import annotations

from streamlit_app.components.render import render_into


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
    arrow = "↑" if trend_dir == "up" else "↓"
    pct_fill = f"{min(pct, 100):.0f}" if pct > 0 else ""
    render_into(
        "kpi.html",
        label=label,
        value=value,
        sub=sub,
        trend=trend,
        trend_dir=trend_dir,
        color=color,
        arrow=arrow,
        pct_fill=pct_fill,
    )


def kpi_card_dark(label: str, value: str, sublabel: str = "") -> None:
    """Dark-theme KPI metric box (custom HTML)."""
    render_into("kpi_card.html", label=label, value=value, sublabel=sublabel)
