"""Dashboard principal — vue d'ensemble ESG Mauritanie."""

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="ESG Platform — Mauritanie",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

from esg_data.fixtures import (
    COMPANIES,
    EMISSIONS,
    FINANCIAL_METRICS,
    RISK_LEVELS,
)
from streamlit_app.utils.styling import (
    PILLAR_COLORS,
    apply_global_styles,
    company_card,
    kpi_card,
)

apply_global_styles()


@st.cache_data(ttl=3600, show_spinner="Calcul des scores ESG en cours…")
def _load_scores():  # type: ignore[no-untyped-def]
    from esg_data.services import compute_all_scores

    return compute_all_scores()


scores_data = _load_scores()
st.session_state["scores"] = scores_data
company_scores = scores_data["company_scores"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding:24px 8px 16px 8px;border-bottom:1px solid rgba(255,255,255,0.06)">
            <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.01em">
                ESG Platform
            </div>
            <div style="font-size:0.72rem;color:#475569;margin-top:3px;letter-spacing:0.04em">
                MAURITANIE · ALPHA
            </div>
        </div>
        <div style="padding:16px 8px 0 8px;font-size:0.7rem;color:#334155;line-height:1.7">
            Méthodologie : Default ESG v1.0.0<br>
            Licence : Apache 2.0 · Open Source
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Tableau de Bord</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Mauritanie — Intelligence ESG en temps réel · 4 sociétés analysées</p>",
    unsafe_allow_html=True,
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
all_scores = {t: company_scores[t].final_score for t in company_scores}
best_ticker = max(all_scores, key=lambda t: all_scores[t])
best_mc_ticker = max(FINANCIAL_METRICS, key=lambda t: FINANCIAL_METRICS[t]["market_cap"])
avg_score = sum(all_scores.values()) / len(all_scores)

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Sociétés Analysées", str(len(COMPANIES)), "Mauritanie")
with col2:
    kpi_card("Meilleur Score ESG", f"{all_scores[best_ticker]:.1f}", COMPANIES[best_ticker].name)
with col3:
    kpi_card("Moyenne Plateforme", f"{avg_score:.1f}", "Score ESG pondéré")

st.markdown("<div style='margin:32px 0'></div>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    name_filter = st.text_input(
        "Rechercher une société",
        "",
        placeholder="Recherche",
        key="dash_name",
        label_visibility="collapsed",
    )
with col_f2:
    sectors = ["Tous les secteurs"] + sorted({c.sector for c in COMPANIES.values()})
    sector_filter = st.selectbox(
        "Secteur", sectors, key="dash_sector", label_visibility="collapsed"
    )

# Apply filters
filtered: dict[str, object] = {}
for ticker, co in COMPANIES.items():
    if sector_filter != "Tous les secteurs" and co.sector != sector_filter:
        continue
    if (
        name_filter
        and name_filter.lower() not in co.name.lower()
        and name_filter.lower() not in ticker.lower()
    ):
        continue
    filtered[ticker] = co

st.caption(f"{len(filtered)} société(s) affichée(s) sur {len(COMPANIES)}")

# ── Company cards ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Sociétés</div>", unsafe_allow_html=True)

if not filtered:
    st.info("Aucune société ne correspond aux filtres sélectionnés.")
else:
    cols = st.columns(2)
    for i, (ticker, co) in enumerate(filtered.items()):  # type: ignore[assignment]
        em = EMISSIONS[ticker]
        total_carbon = em.scope_1 + em.scope_2 + em.total_scope_3
        fm = FINANCIAL_METRICS[ticker]
        with cols[i % 2]:
            company_card(
                ticker=ticker,
                name=co.name,  # type: ignore[union-attr]
                sector=co.sector,  # type: ignore[union-attr]
                score=all_scores[ticker],
                carbon=total_carbon,
                risk=RISK_LEVELS[ticker],
                mc=fm["market_cap"],
            )

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Scores ESG</div>", unsafe_allow_html=True)

tickers_list = list(COMPANIES.keys())
c1, c2 = st.columns(2)

with c1:
    fig_bar = go.Figure()
    for pillar_id, color in PILLAR_COLORS.items():
        label_map = {
            "environment": "Environnement",
            "social": "Social",
            "governance": "Gouvernance",
        }
        values = []
        for t in tickers_list:
            ps = company_scores[t].pillar(pillar_id)
            values.append(ps.score if ps else 0.0)
        fig_bar.add_trace(
            go.Bar(
                name=label_map.get(pillar_id, pillar_id.title()),
                x=tickers_list,
                y=values,
                marker_color=color,
                marker_opacity=0.85,
            )
        )
    fig_bar.update_layout(
        barmode="group",
        title=dict(text="Scores par Pilier", font=dict(size=13, color="#94a3b8")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", range=[0, 105], tickfont=dict(size=11)),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(
        fig_bar,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": [
                "zoom2d",
                "pan2d",
                "select2d",
                "lasso2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d",
                "resetScale2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
            "displaylogo": False,
        },
    )

with c2:
    categories = ["Environnement", "Social", "Gouvernance"]
    fig_radar = go.Figure()
    colors = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444"]
    fills = [
        "rgba(99,102,241,0.15)",
        "rgba(34,197,94,0.15)",
        "rgba(245,158,11,0.15)",
        "rgba(239,68,68,0.15)",
    ]
    for idx, t in enumerate(tickers_list):
        ps_env = company_scores[t].pillar("environment")
        ps_soc = company_scores[t].pillar("social")
        ps_gov = company_scores[t].pillar("governance")
        vals = [
            ps_env.score if ps_env else 0,
            ps_soc.score if ps_soc else 0,
            ps_gov.score if ps_gov else 0,
        ]
        fig_radar.add_trace(
            go.Scatterpolar(
                r=vals + [vals[0]],
                theta=categories + [categories[0]],
                name=t,
                line=dict(color=colors[idx], width=2),
                fill="toself",
                fillcolor=fills[idx],
            )
        )
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="rgba(255,255,255,0.08)",
                tickfont=dict(size=9, color="#475569"),
            ),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        title=dict(text="Radar ESG", font=dict(size=13, color="#94a3b8")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(
        fig_radar,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": [
                "zoom2d",
                "pan2d",
                "select2d",
                "lasso2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d",
                "resetScale2d",
            ],
            "displaylogo": False,
        },
    )
