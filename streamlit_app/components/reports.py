"""Report-specific layout components for the Streamlit dashboard."""

from __future__ import annotations

from streamlit_app.components.render import render_into


def company_header(sector: str, sector_color: str, website: str, website_label: str, link_color: str) -> None:
    """Render the company header row with sector chip and official site link."""
    render_into(
        "company_header.html",
        sector=sector,
        sector_color=sector_color,
        website=website,
        website_label=website_label,
        link_color=link_color,
    )


def reliability_block(confidence: int, source: str, color: str) -> None:
    """Render a small reliability block showing confidence and data provenance."""
    render_into("reliability_block.html", confidence=confidence, source=source, color=color)


def report_card(
    title: str,
    body: str,
    *,
    variant: str = "default",
    href: str | None = None,
    action_text: str = "",
) -> None:
    """Render a report card for official or estimated documents."""
    render_into(
        "report_card.html",
        title=title,
        body=body,
        variant=variant,
        href=href,
        action_text=action_text,
    )
