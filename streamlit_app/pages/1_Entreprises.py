"""Page 1 — Répertoire des sociétés avec filtres avancés."""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

import streamlit as st

st.set_page_config(page_title="Sociétés — ESG Platform", page_icon="◆", layout="wide")

from streamlit_app.utils.styling import (
    apply_global_styles,
    country_name,
    SECTOR_COLORS,
    PILLAR_COLORS,
)
from streamlit_app.data.companies_data import (
    COMPANIES,
    EMISSIONS,
    FINANCIAL_METRICS,
)

apply_global_styles()


@st.cache_data(ttl=3600)
def _get_scores():  # type: ignore[no-untyped-def]
    from streamlit_app.utils.scoring_engine import compute_all_scores
    return compute_all_scores()


scores_data = _get_scores()
company_scores = scores_data["company_scores"]

st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Sociétés</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Explorez et comparez les sociétés répertoriées sur la plateforme.</p>",
    unsafe_allow_html=True,
)

# ── Filters ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    search = st.text_input(
        "",
        placeholder="Rechercher une société par nom ou symbole…",
        key="ent_search",
        label_visibility="collapsed",
    )
with col2:
    sectors = ["Tous les secteurs"] + sorted({c.sector for c in COMPANIES.values()})
    sector_f = st.selectbox("", sectors, key="ent_sector", label_visibility="collapsed")

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
    sk = SECTOR_COLORS.get(co.sector, "#6366f1")

    with st.expander(
        f"{co.name} ({ticker})  ·  Score ESG : {cs.final_score:.1f} / 100",
        expanded=False,
    ):
        c1, c2 = st.columns([2, 3])

        with c1:
            st.markdown(
                f"""
                <div style="padding:4px 0">
                    <div style="margin-bottom:12px;display:flex;gap:6px;flex-wrap:wrap">
                        <span style="background:{sk}18;color:{sk};padding:3px 10px;
                                     border-radius:5px;font-size:0.72rem;font-weight:600">{co.sector}</span>
                    </div>
                    <div style="color:#94a3b8;font-size:0.83rem;line-height:2">
                        <span style="color:#475569;font-size:0.65rem;text-transform:uppercase;
                                     letter-spacing:0.08em;font-weight:600">Pays</span><br>
                        <span style="color:#e2e8f0;font-weight:500">{country_name(co.country)}</span>
                    </div>
                    <div style="color:#94a3b8;font-size:0.83rem;line-height:2;margin-top:6px">
                        <span style="color:#475569;font-size:0.65rem;text-transform:uppercase;
                                     letter-spacing:0.08em;font-weight:600">Effectif</span><br>
                        <span style="color:#e2e8f0;font-weight:500">{int(fm['employees']):,} collaborateurs</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                "<div class='section-header' style='margin-top:0'>Empreinte Carbone</div>",
                unsafe_allow_html=True,
            )
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Scope 1", f"{em.scope_1/1000:.0f}K t")
            mc2.metric("Scope 2", f"{em.scope_2/1000:.0f}K t")
            mc3.metric("Scope 3", f"{em.total_scope_3/1000:.0f}K t")
            st.markdown(
                f"<div style='margin-top:10px;background:rgba(255,255,255,0.03);"
                f"border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;"
                f"display:flex;justify-content:space-between;align-items:center'>"
                f"<span style='font-size:0.72rem;color:#64748b;text-transform:uppercase;"
                f"letter-spacing:0.08em'>Total CO₂e</span>"
                f"<span style='font-weight:700;color:#f1f5f9;font-size:1rem'>{total_carbon/1000:.1f}K t</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-header'>Scores par Pilier</div>", unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns(3)
        for col, pillar_id, label, color in [
            (pc1, "environment", "Environnement", PILLAR_COLORS["environment"]),
            (pc2, "social",      "Social",         PILLAR_COLORS["social"]),
            (pc3, "governance",  "Gouvernance",     PILLAR_COLORS["governance"]),
        ]:
            ps = cs.pillar(pillar_id)
            pscore = ps.score if ps else 0.0
            with col:
                st.markdown(
                    f"<div style='text-align:center;padding:14px;background:rgba(255,255,255,0.03);"
                    f"border-radius:10px;border:1px solid {color}30'>"
                    f"<div style='font-size:1.6rem;font-weight:800;color:{color}'>{pscore:.1f}</div>"
                    f"<div style='font-size:0.65rem;color:#64748b;text-transform:uppercase;"
                    f"letter-spacing:0.08em;margin-top:4px'>{label}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
