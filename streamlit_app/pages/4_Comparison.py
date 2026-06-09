"""Page 4 — Comparaison côte à côte de deux portefeuilles."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Comparaison — ESG Platform", page_icon="◆", layout="wide", initial_sidebar_state="expanded")

from esg_data.fixtures import COMPANIES, REFERENCE_PORTFOLIOS
from streamlit_app.components import layout, tables
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import (
    PILLAR_LABELS,
    apply_global_styles,
    page_header,
    plotly_layout,
)

apply_global_styles()
render_sidebar_nav()


@st.cache_data(ttl=3600)
def _get_scored_portfolios():  # type: ignore[no-untyped-def]
    from esg_data.services import (
        build_portfolio,
        compute_all_scores,
        compute_portfolio_score,
    )

    sd = compute_all_scores()
    out: dict[str, dict] = {}
    for pdef in REFERENCE_PORTFOLIOS:
        port = build_portfolio(pdef)  # type: ignore[arg-type]
        res = compute_portfolio_score(port, sd["company_scores"], sd["methodology"])
        out[str(pdef["name"])] = {
            "port": port,
            "result": res,
            "company_scores": sd["company_scores"],
        }
    return out, sd


ref_portfolios, scores_data = _get_scored_portfolios()
company_scores_all = scores_data["company_scores"]

# Build full option list (reference + user)
options: dict[str, dict] = dict(ref_portfolios)
for up in st.session_state.get("user_portfolios", []):
    uid = up.get("id", "")
    holdings_raw = [h for h in up.get("holdings", []) if h["ticker"] in COMPANIES]
    if not holdings_raw:
        continue
    from datetime import date

    from esg_core.models.portfolio import Holding, Portfolio
    from esg_data.services import compute_portfolio_score

    port_obj = Portfolio(
        id=uid,
        name=up["name"],
        holdings=[
            Holding(
                company=COMPANIES[h["ticker"]],
                weight=float(h["weight"]),
                investment_value=float(h["investment_value"]),
            )
            for h in holdings_raw
        ],
        currency=up.get("currency", "USD"),
        as_of_date=date(2025, 12, 31),
    )
    res = compute_portfolio_score(port_obj, company_scores_all, scores_data["methodology"])
    options[up["name"]] = {
        "port": port_obj,
        "result": res,
        "company_scores": company_scores_all,
    }

# ── Header ─────────────────────────────────────────────────────────────────────
page_header("Comparaison", "Analysez les écarts ESG entre deux portefeuilles côte à côte.")

if len(options) < 2:
    st.info(
        "Créez au moins deux portefeuilles pour les comparer. Utilisez les portefeuilles de référence ou créez les vôtres dans Mes Portefeuilles."
    )
    st.stop()

# ── Selectors ──────────────────────────────────────────────────────────────────
PLACEHOLDER = "— Sélectionner —"
names = list(options.keys())

col_a, col_vs, col_b = st.columns([5, 1, 5])
with col_a:
    choice_a = st.selectbox("Portefeuille A", [PLACEHOLDER] + names, key="cmp_a")
with col_vs:
    layout.vs_divider()
with col_b:
    remaining = [n for n in names if n != choice_a]
    choice_b = st.selectbox("Portefeuille B", [PLACEHOLDER] + remaining, key="cmp_b")

if choice_a == PLACEHOLDER or choice_b == PLACEHOLDER or choice_a == choice_b:
    layout.comparison_placeholder()
    st.stop()

sel_a = options[choice_a]
sel_b = options[choice_b]
port_a = sel_a["port"]
port_b = sel_b["port"]
ps_a = sel_a["result"]["portfolio_score"]
ps_b = sel_b["result"]["portfolio_score"]
carbon_a = sel_a["result"]["carbon_report"]
carbon_b = sel_b["result"]["carbon_report"]
wps_a = ps_a.weighted_portfolio_score
wps_b = ps_b.weighted_portfolio_score

# ═══════════════════════════════════════════════════════════════════════════════
# Section 1 — KPI Comparison
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Résumé comparatif")


def _delta_data(
    val_a: float, val_b: float, higher_is_better: bool = True
) -> dict[str, str] | None:
    delta = val_a - val_b
    if abs(delta) < 0.05:
        return {"kind": "neutral", "text": "—"}
    arrow = "▲" if delta > 0 else "▼"
    kind = "pos" if (delta > 0) == higher_is_better else "neg"
    sign = "+" if delta > 0 else ""
    return {"kind": kind, "text": f"{arrow} {sign}{delta:.1f}"}


kpi_rows = [
    {
        "indicator": "Score ESG Pondéré",
        "a": f"{wps_a:.1f} / 100",
        "b": f"{wps_b:.1f} / 100",
        "delta": _delta_data(wps_a, wps_b, higher_is_better=True),
    },
    {
        "indicator": "Positions",
        "a": str(len(port_a.holdings)),
        "b": str(len(port_b.holdings)),
        "delta": None,
    },
    {
        "indicator": "Capital Total",
        "a": f"${port_a.total_investment_value / 1000:.0f}K",
        "b": f"${port_b.total_investment_value / 1000:.0f}K",
        "delta": None,
    },
    {
        "indicator": "Émissions Financées",
        "a": f"{carbon_a.total_financed_emissions / 1000:.1f}K tCO₂e",
        "b": f"{carbon_b.total_financed_emissions / 1000:.1f}K tCO₂e",
        "delta": _delta_data(
            carbon_a.total_financed_emissions,
            carbon_b.total_financed_emissions,
            higher_is_better=False,
        ),
    },
    {
        "indicator": "Intensité Carbone",
        "a": f"{carbon_a.carbon_intensity:.1f} tCO₂e/$M",
        "b": f"{carbon_b.carbon_intensity:.1f} tCO₂e/$M",
        "delta": _delta_data(
            carbon_a.carbon_intensity, carbon_b.carbon_intensity, higher_is_better=False
        ),
    },
    {
        "indicator": "WACI (tCO₂e/$M CA)",
        "a": f"{carbon_a.waci:.1f}",
        "b": f"{carbon_b.waci:.1f}",
        "delta": _delta_data(carbon_a.waci, carbon_b.waci, higher_is_better=False),
    },
    {
        "indicator": "Carbon-to-Value (tCO₂e/$M EVIC)",
        "a": f"{carbon_a.carbon_to_value:.1f}",
        "b": f"{carbon_b.carbon_to_value:.1f}",
        "delta": _delta_data(
            carbon_a.carbon_to_value, carbon_b.carbon_to_value, higher_is_better=False
        ),
    },
]

tables.comparison_table(choice_a, choice_b, kpi_rows)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 2 — Pillar score comparison
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Scores par Pilier")

pillar_ids = list(PILLAR_LABELS.keys())


def _portfolio_pillar_avg(port, cs_dict: dict, pillar_id: str) -> float:  # type: ignore[no-untyped-def]
    total_weight = 0.0
    weighted_score = 0.0
    for h in port.holdings:
        t = h.company.ticker
        cs = cs_dict.get(t)
        if not cs:
            continue
        ps = cs.pillar(pillar_id)
        if ps:
            weighted_score += h.weight * ps.score
            total_weight += h.weight
    return weighted_score / total_weight if total_weight > 1e-9 else 0.0


vals_a = [_portfolio_pillar_avg(port_a, company_scores_all, pid) for pid in pillar_ids]
vals_b = [_portfolio_pillar_avg(port_b, company_scores_all, pid) for pid in pillar_ids]
labels = [PILLAR_LABELS[pid] for pid in pillar_ids]

fig_cmp = go.Figure()
fig_cmp.add_trace(
    go.Bar(
        name=choice_a,
        x=labels,
        y=vals_a,
        marker=dict(color="#6366f1", opacity=0.85),
        text=[f"{v:.1f}" for v in vals_a],
        textposition="outside",
        textfont=dict(size=10, color="#94a3b8"),
    )
)
fig_cmp.add_trace(
    go.Bar(
        name=choice_b,
        x=labels,
        y=vals_b,
        marker=dict(color="#22c55e", opacity=0.85),
        text=[f"{v:.1f}" for v in vals_b],
        textposition="outside",
        textfont=dict(size=10, color="#94a3b8"),
    )
)
fig_cmp.update_layout(
    **plotly_layout(
        barmode="group",
        height=300,
        yaxis=dict(range=[0, 110]),
        margin=dict(l=0, r=0, t=10, b=0),
    )
)
st.plotly_chart(
    fig_cmp,
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

# ═══════════════════════════════════════════════════════════════════════════════
# Section 3 — Theme-level differences
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Analyse par Thème")


def _theme_scores(port, cs_dict: dict) -> dict[str, float]:  # type: ignore[no-untyped-def]
    totals: dict[str, list[float]] = {}
    for h in port.holdings:
        cs = cs_dict.get(h.company.ticker)
        if not cs:
            continue
        for ps in cs.pillars:
            for ts in ps.themes:
                key = f"{PILLAR_LABELS.get(ps.pillar_id, ps.pillar_id)} / {ts.theme_id.replace('_', ' ').title()}"
                totals.setdefault(key, []).append(ts.score)
    return {k: sum(v) / len(v) for k, v in totals.items()}


themes_a = _theme_scores(port_a, company_scores_all)
themes_b = _theme_scores(port_b, company_scores_all)
all_themes = sorted(set(themes_a) | set(themes_b))

theme_rows = []
for theme in all_themes:
    sa = themes_a.get(theme, 0.0)
    sb = themes_b.get(theme, 0.0)
    delta = sa - sb
    direction = "A supérieur" if delta > 0.5 else ("B supérieur" if delta < -0.5 else "Équivalent")
    theme_rows.append(
        {
            "Thème": theme,
            choice_a: f"{sa:.1f}",
            choice_b: f"{sb:.1f}",
            "Écart (A − B)": f"{delta:+.1f}",
            "Avantage": direction,
        }
    )

theme_df = pd.DataFrame(theme_rows)
st.dataframe(theme_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 4 — Top contributors to differences
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Principaux Écarts")

sorted_themes = sorted(
    [(t, themes_a.get(t, 0.0) - themes_b.get(t, 0.0)) for t in all_themes],
    key=lambda x: abs(x[1]),
    reverse=True,
)

top = sorted_themes[:6]
col_l, col_r = st.columns(2)

a_better = [(t, d) for t, d in top if d > 0.5][:3]
b_better = [(t, d) for t, d in top if d < -0.5][:3]

with col_l:
    layout.advantage_block(
        choice_a,
        [{"theme": t, "delta": f"+{d:.1f}"} for t, d in a_better],
        "a",
    )

with col_r:
    layout.advantage_block(
        choice_b,
        [{"theme": t, "delta": f"{d:.1f}"} for t, d in b_better],
        "b",
    )
