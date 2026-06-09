"""Dashboard principal — vue d'ensemble ESG Mauritanie."""

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="ESG Platform — Mauritanie",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

from typing import Any

from esg_data.fixtures import (
    COMPANIES,
    EMISSIONS,
    RISK_LEVELS,
)
from streamlit_app.components import feeds, tables
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import (
    PILLAR_COLORS,
    PILLAR_LABELS,
    RISK_COLORS,
    SECTOR_COLORS,
    apply_global_styles,
    dash_section,
    kpi_v2,
    page_header,
    plotly_layout,
    score_color5,
)

apply_global_styles()
render_sidebar_nav()


@st.cache_data(ttl=3600, show_spinner="Calcul des scores…")
def _load_scores():  # type: ignore[no-untyped-def]
    from esg_data.services import compute_all_scores

    return compute_all_scores()


scores_data = _load_scores()
st.session_state["scores"] = scores_data
company_scores = scores_data["company_scores"]

# ── Derived KPI data ──────────────────────────────────────────────────────────
all_scores = {t: company_scores[t].final_score for t in company_scores}
best_ticker = max(all_scores, key=lambda t: all_scores[t])
avg_score = sum(all_scores.values()) / len(all_scores)
total_emissions_t = sum(
    EMISSIONS[t].scope_1 + EMISSIONS[t].scope_2 + EMISSIONS[t].total_scope_3
    for t in EMISSIONS
    if t in COMPANIES
)
tickers_list = list(COMPANIES.keys())

# ── Page header ───────────────────────────────────────────────────────────────
page_header("Tableau de Bord", "Mauritanie · 4 sociétés · Alpha")

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_v2(
        "Score ESG Moyen",
        f"{avg_score:.1f}",
        sub="/ 100",
        color="var(--esg-accent)",
        pct=avg_score,
    )
with k2:
    kpi_v2(
        "Meilleur Score",
        f"{all_scores[best_ticker]:.1f}",
        sub=COMPANIES[best_ticker].name,
        color="#0ea672",
        pct=all_scores[best_ticker],
    )
with k3:
    kpi_v2(
        "Émissions Totales",
        f"{total_emissions_t / 1_000:.0f}K",
        sub="tCO₂e · Scope 1+2+3",
        color="#e89e0c",
        pct=58,
    )
with k4:
    kpi_v2(
        "Couverture",
        f"{len(COMPANIES)} / {len(COMPANIES)}",
        sub="Sociétés analysées",
        color="var(--esg-accent-alt)",
        pct=100,
    )

# ── Charts ────────────────────────────────────────────────────────────────────
dash_section("Analyse ESG", "scores par pilier · classement global")

ch1, ch2 = st.columns([3, 2])

with ch1:
    fig_bar = go.Figure()
    for pillar_id, color in PILLAR_COLORS.items():
        vals = []
        for t in tickers_list:
            ps = company_scores[t].pillar(pillar_id)
            vals.append(ps.score if ps else 0.0)
        fig_bar.add_trace(
            go.Bar(
                name=PILLAR_LABELS[pillar_id],
                x=tickers_list,
                y=vals,
                marker_color=color,
                marker_opacity=0.88,
            )
        )
    fig_bar.update_layout(
        **plotly_layout(
            barmode="group",
            title={"text": "Scores par Pilier E / S / G", "font": {"size": 12}},
            yaxis={"range": [0, 108]},
            height=270,
            legend={"orientation": "h", "y": -0.18, "x": 0},
        )
    )
    st.plotly_chart(
        fig_bar,
        use_container_width=True,
        config={"displaylogo": False, "displayModeBar": False},
    )

with ch2:
    sorted_t = sorted(tickers_list, key=lambda t: all_scores[t])
    sorted_s = [all_scores[t] for t in sorted_t]
    bar_colors = [score_color5(s) for s in sorted_s]
    fig_rank = go.Figure(
        go.Bar(
            x=sorted_s,
            y=sorted_t,
            orientation="h",
            marker_color=bar_colors,
            marker_opacity=0.90,
            text=[f"{s:.1f}" for s in sorted_s],
            textposition="outside",
            textfont={"size": 11},
        )
    )
    fig_rank.update_layout(
        **plotly_layout(
            title={"text": "Classement ESG Global", "font": {"size": 12}},
            xaxis={"range": [0, 118]},
            height=270,
        )
    )
    st.plotly_chart(
        fig_rank,
        use_container_width=True,
        config={"displaylogo": False, "displayModeBar": False},
    )

# ── Filters ───────────────────────────────────────────────────────────────────
cf1, cf2 = st.columns([3, 1])
with cf1:
    name_filter = st.text_input(
        "Rechercher",
        "",
        placeholder="Rechercher une société ou un symbole…",
        key="dash_name",
        label_visibility="collapsed",
    )
with cf2:
    sectors = ["Tous les secteurs", *sorted({c.sector for c in COMPANIES.values()})]
    sector_filter = st.selectbox(
        "Secteur", sectors, key="dash_sector", label_visibility="collapsed"
    )

filtered: dict[str, object] = {}
for ticker, co in COMPANIES.items():
    if sector_filter != "Tous les secteurs" and co.sector != sector_filter:
        continue
    if name_filter and (
        name_filter.lower() not in co.name.lower()
        and name_filter.lower() not in ticker.lower()
    ):
        continue
    filtered[ticker] = co

# ── Company ranking table ─────────────────────────────────────────────────────
dash_section("Classement des Sociétés", f"{len(filtered)} résultat(s)")

if filtered:
    sorted_filtered = sorted(filtered.keys(), key=lambda t: all_scores[t], reverse=True)

    def _pillar(score: float | None, pid: str) -> dict[str, Any]:
        """Prepare a pillar cell: formatted value (or None) + pillar colour."""
        return {
            "val": None if score is None else f"{score:.0f}",
            "color": PILLAR_COLORS.get(pid, "#6366f1"),
        }

    rank_rows: list[dict[str, Any]] = []
    for rank, t in enumerate(sorted_filtered, 1):
        co = COMPANIES[t]
        score = all_scores[t]
        em = EMISSIONS[t]
        carbon_kt = (em.scope_1 + em.scope_2 + em.total_scope_3) / 1000
        risk = RISK_LEVELS.get(t, "—")
        ps_env = company_scores[t].pillar("environment")
        ps_soc = company_scores[t].pillar("social")
        ps_gov = company_scores[t].pillar("governance")
        rank_rows.append(
            {
                "rank": rank,
                "name": co.name,
                "ticker": t,
                "score_str": f"{score:.1f}",
                "score_pct": f"{score:.0f}",
                "score_color": score_color5(score),
                "pillars": [
                    _pillar(ps_env.score if ps_env else None, "environment"),
                    _pillar(ps_soc.score if ps_soc else None, "social"),
                    _pillar(ps_gov.score if ps_gov else None, "governance"),
                ],
                "carbon_str": f"{carbon_kt:.1f}K tCO₂e",
                "sector": co.sector,
                "sector_color": SECTOR_COLORS.get(co.sector, "#6366f1"),
                "risk": risk,
                "risk_color": RISK_COLORS.get(risk, "#94a3b8"),
            }
        )

    tables.ranking_table(rank_rows, header_colors=PILLAR_COLORS)
else:
    st.info("Aucune société ne correspond aux filtres sélectionnés.")

# ── Activity feed + Risk alerts ───────────────────────────────────────────────
ba1, ba2 = st.columns(2)

with ba1:
    dash_section("Activité Récente", "scoring automatique")

    activity_items: list[dict[str, Any]] = []
    for t in sorted(tickers_list, key=lambda x: all_scores[x], reverse=True):
        co = COMPANIES[t]
        score = all_scores[t]
        activity_items.append(
            {
                "color": score_color5(score),
                "name": co.name,
                "score_str": f"{score:.1f}",
            }
        )
    feeds.activity_feed(activity_items)

with ba2:
    dash_section("Alertes & Risques", "basé sur les données ESG")

    _risk_order = {"High": 0, "Medium": 1, "Low": 2}
    alert_items: list[dict[str, Any]] = []
    for t in sorted(RISK_LEVELS, key=lambda x: _risk_order.get(RISK_LEVELS.get(x, "Low"), 2)):
        if t not in COMPANIES:
            continue
        co = COMPANIES[t]
        risk = RISK_LEVELS[t]
        em_alert = EMISSIONS.get(t)
        if not em_alert:
            continue
        if risk == "High":
            desc = (
                f"Scope 1 : {em_alert.scope_1 / 1_000:.0f}K tCO₂e. "
                f"Revue climatique prioritaire recommandée."
            )
        elif risk == "Medium":
            desc = (
                f"Intensité carbone modérée. "
                f"Confiance données : {em_alert.confidence * 100:.0f}%."
            )
        else:
            desc = "Performance ESG satisfaisante. Surveillance standard."

        alert_items.append(
            {
                "risk_color": RISK_COLORS.get(risk, "#94a3b8"),
                "name": co.name,
                "risk": risk,
                "desc": desc,
            }
        )
    feeds.risk_alerts(alert_items)
