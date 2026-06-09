"""Table components — the dashboard company ranking table.

Presentation-only: receives already-computed colours and formatted values
(prepared by the caller, e.g. the dashboard page) and renders ``table.html``.
No scoring, filtering or palette logic here.
"""

from __future__ import annotations

from typing import Any

from streamlit_app.components.render import render_into


def ranking_table(rows: list[dict[str, Any]], header_colors: dict[str, str]) -> None:
    """Render the company ranking table from prepared row dicts.

    Each ``row`` carries ``rank``, ``name``, ``ticker``, ``score_str``,
    ``score_pct``, ``score_color``, ``pillars`` (list of ``{val, color}``,
    ``val`` may be ``None``), ``carbon_str``, ``sector``, ``sector_color``,
    ``risk`` and ``risk_color``. ``header_colors`` maps the pillar ids
    (``environment`` / ``social`` / ``governance``) to their header colour.
    """
    render_into("table.html", rows=rows, header_colors=header_colors)


def comparison_table(a_label: str, b_label: str, rows: list[dict[str, Any]]) -> None:
    """Render the A/B KPI comparison table (page 4 — Comparaison).

    ``a_label`` / ``b_label`` head the two value columns. Each ``row`` carries
    ``indicator`` (label), ``a`` / ``b`` (formatted values) and ``delta``:
    either ``None`` (renders a plain ``—``) or a dict ``{"kind", "text"}`` where
    ``kind`` is ``"pos"`` / ``"neg"`` / ``"neutral"``.
    """
    render_into("comparison_table.html", a_label=a_label, b_label=b_label, rows=rows)
