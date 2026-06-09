"""Page 1 — Répertoire des sociétés avec filtres avancés."""

import streamlit as st

st.set_page_config(page_title="Sociétés — ESG Platform", page_icon="◆", layout="wide", initial_sidebar_state="expanded")

from esg_data.fixtures import (
    COMPANIES,
    EMISSIONS,
    FINANCIAL_METRICS,
)
from streamlit_app.components import cards, layout
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import (
    PILLAR_COLORS,
    PILLAR_LABELS,
    SECTOR_COLORS,
    apply_global_styles,
    country_name,
    page_header,
)

apply_global_styles()
render_sidebar_nav()


@st.cache_data(ttl=3600)
def _get_scores():  # type: ignore[no-untyped-def]
    from esg_data.services import compute_all_scores

    return compute_all_scores()


scores_data = _get_scores()
company_scores = scores_data["company_scores"]

page_header("Sociétés", "Explorez et comparez les sociétés répertoriées sur la plateforme.")

# ── Filters ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    search = st.text_input(
        "",
        placeholder="Recherche",
        key="ent_search",
        label_visibility="collapsed",
    )
with col2:
    sectors = ["Tous les secteurs"] + sorted({c.sector for c in COMPANIES.values()})
    sector_f = st.selectbox(" ", sectors, key="ent_sector", label_visibility="collapsed")

# Apply filters
filtered = {}
for ticker, co in COMPANIES.items():
    if search and search.lower() not in co.name.lower() and search.lower() not in ticker.lower():
        continue
    if sector_f != "Tous les secteurs" and co.sector != sector_f:
        continue
    filtered[ticker] = co

st.caption(f"**{len(filtered)}** société(s) trouvée(s)")

# ── Company detail cards ────────────────────────────────────────────────────────
for ticker, co in filtered.items():
    cs = company_scores[ticker]
    em = EMISSIONS[ticker]
    fm = FINANCIAL_METRICS[ticker]
    total_carbon = em.scope_1 + em.scope_2 + em.total_scope_3

    with st.expander(
        f"{co.name} ({ticker})  ·  Score ESG : {cs.final_score:.1f} / 100",
        expanded=False,
    ):
        c1, c2 = st.columns([2, 3])

        with c1:
            cards.company_detail(
                sector=co.sector,
                sector_color=SECTOR_COLORS.get(co.sector, "#6366f1"),
                country=country_name(co.country),
                employees=f"{int(fm['employees']):,}",
            )

        with c2:
            layout.section_label("Empreinte Carbone", flush=True)
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Scope 1", f"{em.scope_1 / 1000:.0f}K t")
            mc2.metric("Scope 2", f"{em.scope_2 / 1000:.0f}K t")
            mc3.metric("Scope 3", f"{em.total_scope_3 / 1000:.0f}K t")
            cards.carbon_total(f"{total_carbon / 1000:.1f}")

        layout.section_label("Scores par Pilier")
        pc1, pc2, pc3 = st.columns(3)
        for col, pillar_id in [(pc1, "environment"), (pc2, "social"), (pc3, "governance")]:
            ps = cs.pillar(pillar_id)
            pscore = ps.score if ps else 0.0
            with col:
                cards.pillar_tile(
                    color=PILLAR_COLORS[pillar_id],
                    score_str=f"{pscore:.1f}",
                    label=PILLAR_LABELS[pillar_id],
                )
