"""Page 6 — Sources de données par entreprise (traçabilité)."""

# ruff: noqa: N999

from typing import Any, cast

import streamlit as st

from esg_data.fixtures import COMPANY_META, OFFICIAL_REPORTS
from esg_data.reporting import build_pdf
from streamlit_app.components import reports
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import SECTOR_COLORS, apply_global_styles, page_header

CONF_THRESHOLD_HIGH = 70
CONF_THRESHOLD_MID = 55

st.set_page_config(
    page_title="Sources — ESG Platform",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
render_sidebar_nav()

# ── Page header ────────────────────────────────────────────────────────────────
page_header(
    "Sources",
    "Traçabilité des données — rapport officiel ou rapport estimé toujours disponible.",
)

search: str = st.text_input(" ", placeholder="Recherche", key="src_search", label_visibility="collapsed") or ""

filtered: dict[str, dict[str, object]] = {
    k: v
    for k, v in COMPANY_META.items()
    if not search
    or search.lower() in cast(str, v["name"]).lower()
    or search.lower() in k.lower()
    or search.lower() in cast(str, v["sector"]).lower()
}

st.caption(f"**{len(filtered)}** entreprise(s)")

# ── Company list ───────────────────────────────────────────────────────────────
for ticker, meta in filtered.items():
    sector = cast(str, meta["sector"])
    website = cast(str, meta["website"])
    data_source = cast(str, meta["data_source"])
    conf = cast(int, meta["confidence"])
    report_years = cast(list[int], meta["report_years"])
    sk = SECTOR_COLORS.get(sector, "#6366f1")
    conf_color = (
        "#22c55e"
        if conf >= CONF_THRESHOLD_HIGH
        else "#f59e0b"
        if conf >= CONF_THRESHOLD_MID
        else "#ef4444"
    )

    with st.expander(f"{cast(str, meta['name'])}  ({ticker})  ·  {sector}", expanded=False):
        top_l, top_r = st.columns([4, 1])
        with top_l:
            reports.company_header(
                sector=sector,
                sector_color=sk,
                website=website,
                website_label="Site officiel",
                link_color="#6366f1",
            )
        with top_r:
            reports.reliability_block(
                confidence=conf,
                source=data_source,
                color=conf_color,
            )

        _raw_year = st.selectbox(
            "Année du rapport",
            report_years,
            index=0,
            key=f"src_{ticker}_year",
        )
        sel_year: int = _raw_year if _raw_year is not None else report_years[0]

        has_official = ticker in OFFICIAL_REPORTS and sel_year in OFFICIAL_REPORTS[ticker]
        col_off, col_est = st.columns(2)

        # ── Rapport officiel ──────────────────────────────────────────────
        with col_off:
            if has_official:
                reports.report_card(
                    title="Rapport officiel",
                    body=f"Rapport annuel {sel_year} publié par l'entreprise.",
                    variant="official",
                    href=OFFICIAL_REPORTS[ticker][sel_year],
                    action_text=f"Voir le rapport {sel_year}",
                )
            else:
                reports.report_card(
                    title="Rapport officiel indisponible",
                    body=(
                        f"Aucun rapport officiel publié pour {sel_year}. "
                        "Les données officielles n'ont pas été rendues publiques pour cet exercice."
                    ),
                    variant="muted",
                )

        # ── Rapport estimé — PDF ──────────────────────────────────────────
        with col_est:
            reports.report_card(
                title="Rapport estimé — Plateforme",
                body=(
                    f"Rapport {sel_year} généré par la plateforme à partir des données publiques "
                    "de l'entreprise et des indicateurs analysés par notre moteur ESG."
                ),
                variant="estimated",
            )
            pdf_bytes = build_pdf(ticker, sel_year)
            st.download_button(
                label=f"Télécharger le rapport estimé {sel_year} (PDF)",
                data=pdf_bytes,
                file_name=f"rapport_estime_{ticker}_{sel_year}.pdf",
                mime="application/pdf",
                key=f"dl_{ticker}_{sel_year}",
                use_container_width=True,
            )
