"""Layout components — page headers and section dividers."""

from __future__ import annotations

from streamlit_app.components.render import render_into


def page_header(title: str, subtitle: str = "") -> None:
    """Render a compact page header with optional breadcrumb subtitle."""
    render_into("page_header.html", title=title, subtitle=subtitle)


def dash_section(title: str, meta: str = "") -> None:
    """Compact section heading with optional inline meta text."""
    render_into("section_header.html", title=title, meta=meta)


def section_label(title: str, *, flush: bool = False) -> None:
    """Underlined uppercase section label (the ``.section-header`` rule).

    ``flush=True`` removes the default top margin (for a label that opens a
    column with no preceding content).
    """
    render_into("section_label.html", title=title, flush=flush)


def divider() -> None:
    """Thin horizontal rule (the global ``hr`` rule styles it).

    Routes the plain ``<hr>`` through the render seam so pages keep no raw
    ``unsafe_allow_html`` call; the DOM and styling are identical to the old
    inline ``st.markdown("<hr>")`` (and unlike ``st.divider()``, which carries
    its own heavier margins).
    """
    render_into("divider.html")


def portfolio_description(text: str) -> None:
    """Muted lead paragraph (e.g. a reference-portfolio description).

    Colour comes from the ``--esg-text-muted`` palette token so the text is
    legible in both themes (replaces the old dark-only ``#64748b`` literal).
    """
    render_into("portfolio_desc.html", text=text)


# ── Portfolio-builder pieces (page 3 — Mes Portefeuilles) ─────────────────────


def field_label(text: str, *, variant: str = "") -> None:
    """Uppercase muted field label (``.cp-label``).

    ``variant`` selects an optional spacing modifier class: ``"rep"`` (the
    Répartition heading) or ``"imp"`` (the import name field). Colour is the
    ``--esg-text-muted`` token so the label is legible in both themes.
    """
    render_into("field_label.html", text=text, variant=variant)


def column_label(text: str) -> None:
    """Small uppercase column header (``.cp-col-label``)."""
    render_into("col_label.html", text=text)


def positions_header(count: int) -> None:
    """"Positions" title with a count pill (``.cp-positions-title``)."""
    render_into("positions_header.html", count=count)


def position_number(n: int) -> None:
    """Gradient circular position-index badge (``.cp-pos-num``)."""
    render_into("position_number.html", n=n)


def allocation_tile(pct: str, name: str) -> None:
    """Per-holding weight tile used in the live allocation preview."""
    render_into("alloc_tile.html", pct=pct, name=name)


def info_card(title: str, fields: list[str]) -> None:
    """Indigo-tinted card listing required import fields as ``<code>`` chips."""
    render_into("info_card.html", title=title, fields=fields)


def preview_header(tag: str, count: int, capital: str) -> None:
    """Import-preview header: a coloured tag plus a position/capital summary."""
    render_into("preview_header.html", tag=tag, count=count, capital=capital)


def success_banner(
    title: str,
    *,
    subtitle: str = "",
    count: int | None = None,
    capital: str = "",
    holdings: list[dict[str, str]] | None = None,
) -> None:
    """Green "portfolio created" banner.

    Two shapes share one template: pass ``holdings`` (each ``{"name", "pct"}``)
    with ``count``/``capital`` for the manual-create breakdown, or ``subtitle``
    for the simpler import confirmation.
    """
    render_into(
        "banner.html",
        title=title,
        subtitle=subtitle,
        count=count,
        capital=capital,
        holdings=holdings or [],
    )


def empty_state() -> None:
    """Centred "no portfolios yet" placeholder (``.cp-empty``)."""
    render_into("empty_state.html")


def vspace(size: str = "md") -> None:
    """Vertical spacer. ``size`` is ``"sm"`` (6px), ``"md"`` (18px), or ``"lg"`` (28px)."""
    render_into("vspace.html", size=size)


# ── Comparison pieces (page 4 — Comparaison) ──────────────────────────────────


def vs_divider() -> None:
    """Centred "VS" separator between the two portfolio selectors."""
    render_into("vs_divider.html")


def comparison_placeholder() -> None:
    """Centred prompt shown until two distinct portfolios are selected."""
    render_into("cmp_placeholder.html")


def advantage_block(title: str, items: list[dict[str, str]], kind: str) -> None:
    """One "advantage" column for the comparison page.

    ``title`` is the portfolio name (rendered as "{title} en avance"). ``items``
    is a list of ``{"theme", "delta"}`` dicts (already formatted). ``kind`` is
    ``"a"`` (indigo) or ``"b"`` (green); an empty ``items`` shows a fallback.
    """
    render_into("advantage_block.html", title=title, items=items, kind=kind)


# ── Explainability pieces (page 5 — Analyse extra-financière) ─────────────────


def analysis_placeholder() -> None:
    """Centred prompt shown until a portfolio is selected for analysis."""
    render_into("exp_placeholder.html")


def callout_howto() -> None:
    """Indigo "Comment lire ce tableau ?" explanatory callout (theme decomposition)."""
    render_into("callout_howto.html")


def callout_unsigned() -> None:
    """Amber "document non signé" disclaimer callout (Phase 9 not yet shipped)."""
    render_into("callout_unsigned.html")
