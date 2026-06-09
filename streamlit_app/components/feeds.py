"""Feed components — recent-activity feed and risk-alert list.

Presentation-only: receives already-computed colours and formatted strings
(prepared by the caller) and renders the matching template. No scoring or
palette logic here.
"""

from __future__ import annotations

from typing import Any

from streamlit_app.components.render import render_into


def activity_feed(items: list[dict[str, Any]]) -> None:
    """Render the recent-activity feed.

    Each ``item`` carries ``color`` (status colour), ``name`` and
    ``score_str`` (the score formatted as ``"NN.N"``).
    """
    render_into("activity_feed.html", items=items)


def risk_alerts(items: list[dict[str, Any]]) -> None:
    """Render the risk-alerts list.

    Each ``item`` carries ``risk_color``, ``name``, ``risk`` (the level label)
    and ``desc`` (the pre-formatted description line).
    """
    render_into("alerts.html", items=items)
