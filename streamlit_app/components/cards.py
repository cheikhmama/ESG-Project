"""Card components — company summary card.

The component is presentation-only: it receives already-computed colours and
formatted values (prepared by the caller, e.g. ``styling.company_card``) and
renders the ``card_company.html`` template. No scoring or palette logic here.
"""

from __future__ import annotations

from typing import Any

from streamlit_app.components.render import render_into


def company_card(**ctx: Any) -> None:
    """Render a company summary card from a prepared context dict."""
    render_into("card_company.html", **ctx)


def company_detail(**ctx: Any) -> None:
    """Render the company-detail info block (sector chip, country, headcount).

    Context: ``sector``, ``sector_color`` (semantic, dynamic), ``country``
    and ``employees`` (pre-formatted string). Palette colours come from CSS
    custom properties, not context.
    """
    render_into("company_detail.html", **ctx)


def carbon_total(total_str: str) -> None:
    """Render the "Total CO₂e" summary box. ``total_str`` is the value in K t."""
    render_into("carbon_total.html", total_str=total_str)


def pillar_tile(color: str, score_str: str, label: str) -> None:
    """Render a single pillar score tile (border/score coloured by ``color``)."""
    render_into("pillar_tile.html", color=color, score_str=score_str, label=label)
