"""Page 4 — Comparaison côte à côte de deux portefeuilles."""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Comparaison — ESG Platform", page_icon="◆", layout="wide")

from streamlit_app.utils.styling import apply_global_styles, score_color, PILLAR_COLORS
from streamlit_app.data.companies_data import COMPANIES, EMISSIONS, REFERENCE_PORTFOLIOS

apply_global_styles()


@st.cache_data(ttl=3600)
def _get_scored_portfolios():  # type: ignore[no-untyped-def]
    from streamlit_app.utils.scoring_engine import (
        compute_all_scores,
        build_portfolio,
        compute_portfolio_score,
    )
    sd = compute_all_scores()
    out: dict[str, dict] = {}
    for pdef in REFERENCE_PORTFOLIOS:
        port = build_portfolio(pdef)  # type: ignore[arg-type]
        res = compute_portfolio_score(port, sd["company_scores"], sd["methodology"])
        out[str(pdef["name"])] = {
            "port": port, "result": res, "company_scores": sd["company_scores"],
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
    from streamlit_app.utils.scoring_engine import compute_portfolio_score
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
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Comparaison</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Analysez les écarts ESG entre deux portefeuilles côte à côte.</p>",
    unsafe_allow_html=True,
)

if len(options) < 2:
    st.info("Créez au moins deux portefeuilles pour les comparer. Utilisez les portefeuilles de référence ou créez les vôtres dans Mes Portefeuilles.")
    st.stop()

# ── Selectors ──────────────────────────────────────────────────────────────────
PLACEHOLDER = "— Sélectionner —"
names = list(options.keys())

col_a, col_vs, col_b = st.columns([5, 1, 5])
with col_a:
    choice_a = st.selectbox("Portefeuille A", [PLACEHOLDER] + names, key="cmp_a")
with col_vs:
    st.markdown(
        "<div style='text-align:center;padding-top:30px;font-size:1rem;font-weight:700;"
        "color:#475569;letter-spacing:0.05em'>VS</div>",
        unsafe_allow_html=True,
    )
with col_b:
    remaining = [n for n in names if n != choice_a]
    choice_b = st.selectbox("Portefeuille B", [PLACEHOLDER] + remaining, key="cmp_b")

if choice_a == PLACEHOLDER or choice_b == PLACEHOLDER or choice_a == choice_b:
    st.markdown(
        "<div style='text-align:center;padding:64px 0;color:#334155'>"
        "<div style='font-size:0.9rem'>Sélectionnez deux portefeuilles différents pour lancer la comparaison.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
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
st.markdown("<div class='section-header'>Résumé comparatif</div>", unsafe_allow_html=True)

def _delta_str(val_a: float, val_b: float, higher_is_better: bool = True) -> str:
    delta = val_a - val_b
    if abs(delta) < 0.05:
        return "<span style='color:#64748b'>—</span>"
    arrow = "▲" if delta > 0 else "▼"
    color = "#22c55e" if (delta > 0) == higher_is_better else "#ef4444"
    sign = "+" if delta > 0 else ""
    return f"<span style='color:{color};font-weight:700'>{arrow} {sign}{delta:.1f}</span>"


kpi_rows = [
    {
        "Indicateur": "Score ESG Pondéré",
        "Portefeuille A": f"{wps_a:.1f} / 100",
        "Portefeuille B": f"{wps_b:.1f} / 100",
        "_delta": _delta_str(wps_a, wps_b, higher_is_better=True),
    },
    {
        "Indicateur": "Positions",
        "Portefeuille A": str(len(port_a.holdings)),
        "Portefeuille B": str(len(port_b.holdings)),
        "_delta": "—",
    },
    {
        "Indicateur": "Capital Total",
        "Portefeuille A": f"${port_a.total_investment_value/1000:.0f}K",
        "Portefeuille B": f"${port_b.total_investment_value/1000:.0f}K",
        "_delta": "—",
    },
    {
        "Indicateur": "Émissions Financées",
        "Portefeuille A": f"{carbon_a.total_financed_emissions/1000:.1f}K tCO₂e",
        "Portefeuille B": f"{carbon_b.total_financed_emissions/1000:.1f}K tCO₂e",
        "_delta": _delta_str(
            carbon_a.total_financed_emissions,
            carbon_b.total_financed_emissions,
            higher_is_better=False,
        ),
    },
    {
        "Indicateur": "Intensité Carbone",
        "Portefeuille A": f"{carbon_a.carbon_intensity:.1f} tCO₂e/$M",
        "Portefeuille B": f"{carbon_b.carbon_intensity:.1f} tCO₂e/$M",
        "_delta": _delta_str(carbon_a.carbon_intensity, carbon_b.carbon_intensity, higher_is_better=False),
    },
    {
        "Indicateur": "WACI",
        "Portefeuille A": f"{carbon_a.waci:.1f}",
        "Portefeuille B": f"{carbon_b.waci:.1f}",
        "_delta": _delta_str(carbon_a.waci, carbon_b.waci, higher_is_better=False),
    },
]

# Render as HTML table for styled delta column
header_a = f"<th style='text-align:right;color:#6366f1;padding:10px 16px'>{choice_a}</th>"
header_b = f"<th style='text-align:right;color:#22c55e;padding:10px 16px'>{choice_b}</th>"
rows_html = ""
for r in kpi_rows:
    rows_html += (
        f"<tr style='border-bottom:1px solid rgba(255,255,255,0.04)'>"
        f"<td style='padding:10px 16px;color:#94a3b8;font-size:0.83rem'>{r['Indicateur']}</td>"
        f"<td style='text-align:right;padding:10px 16px;color:#f1f5f9;font-weight:600'>{r['Portefeuille A']}</td>"
        f"<td style='text-align:right;padding:10px 16px;color:#f1f5f9;font-weight:600'>{r['Portefeuille B']}</td>"
        f"<td style='text-align:center;padding:10px 16px;font-size:0.83rem'>{r['_delta']}</td>"
        f"</tr>"
    )

st.markdown(
    f"<div style='background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);"
    f"border-radius:12px;overflow:hidden'>"
    f"<table style='width:100%;border-collapse:collapse'>"
    f"<thead><tr style='border-bottom:1px solid rgba(255,255,255,0.08)'>"
    f"<th style='text-align:left;padding:10px 16px;color:#475569;font-size:0.63rem;"
    f"text-transform:uppercase;letter-spacing:0.12em'>Indicateur</th>"
    f"{header_a}{header_b}"
    f"<th style='text-align:center;padding:10px 16px;color:#475569;font-size:0.63rem;"
    f"text-transform:uppercase;letter-spacing:0.12em'>Écart</th>"
    f"</tr></thead>"
    f"<tbody>{rows_html}</tbody>"
    f"</table></div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 2 — Pillar score comparison
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='section-header'>Scores par Pilier</div>", unsafe_allow_html=True)

pillar_labels = {"environment": "Environnement", "social": "Social", "governance": "Gouvernance"}
pillar_ids = list(pillar_labels.keys())

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
labels = [pillar_labels[pid] for pid in pillar_ids]

fig_cmp = go.Figure()
fig_cmp.add_trace(go.Bar(
    name=choice_a, x=labels, y=vals_a,
    marker=dict(color="#6366f1", opacity=0.85),
    text=[f"{v:.1f}" for v in vals_a],
    textposition="outside",
    textfont=dict(size=10, color="#94a3b8"),
))
fig_cmp.add_trace(go.Bar(
    name=choice_b, x=labels, y=vals_b,
    marker=dict(color="#22c55e", opacity=0.85),
    text=[f"{v:.1f}" for v in vals_b],
    textposition="outside",
    textfont=dict(size=10, color="#94a3b8"),
))
fig_cmp.update_layout(
    barmode="group",
    height=300,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter", size=11),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    yaxis=dict(range=[0, 110], gridcolor="rgba(255,255,255,0.04)"),
    margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(fig_cmp, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 3 — Theme-level differences
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='section-header'>Analyse par Thème</div>", unsafe_allow_html=True)


def _theme_scores(port, cs_dict: dict) -> dict[str, float]:  # type: ignore[no-untyped-def]
    totals: dict[str, list[float]] = {}
    for h in port.holdings:
        cs = cs_dict.get(h.company.ticker)
        if not cs:
            continue
        for ps in cs.pillars:
            for ts in ps.themes:
                key = f"{pillar_labels.get(ps.pillar_id, ps.pillar_id)} / {ts.theme_id.replace('_', ' ').title()}"
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
    theme_rows.append({
        "Thème":          theme,
        choice_a:         f"{sa:.1f}",
        choice_b:         f"{sb:.1f}",
        "Écart (A − B)":  f"{delta:+.1f}",
        "Avantage":        direction,
    })

theme_df = pd.DataFrame(theme_rows)
st.dataframe(theme_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 4 — Top contributors to differences
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='section-header'>Principaux Écarts</div>", unsafe_allow_html=True)

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
    st.markdown(
        f"<div style='font-size:0.65rem;color:#6366f1;text-transform:uppercase;"
        f"letter-spacing:0.12em;font-weight:700;margin-bottom:12px'>{choice_a} en avance</div>",
        unsafe_allow_html=True,
    )
    if a_better:
        for theme, delta in a_better:
            st.markdown(
                f"<div style='background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);"
                f"border-radius:8px;padding:10px 14px;margin-bottom:8px;display:flex;"
                f"justify-content:space-between;align-items:center'>"
                f"<span style='font-size:0.83rem;color:#cbd5e1'>{theme}</span>"
                f"<span style='font-weight:700;color:#6366f1;font-size:0.9rem'>+{delta:.1f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='color:#334155;font-size:0.83rem;padding:8px 0'>Aucun avantage significatif.</div>",
            unsafe_allow_html=True,
        )

with col_r:
    st.markdown(
        f"<div style='font-size:0.65rem;color:#22c55e;text-transform:uppercase;"
        f"letter-spacing:0.12em;font-weight:700;margin-bottom:12px'>{choice_b} en avance</div>",
        unsafe_allow_html=True,
    )
    if b_better:
        for theme, delta in b_better:
            st.markdown(
                f"<div style='background:rgba(34,197,94,0.05);border:1px solid rgba(34,197,94,0.15);"
                f"border-radius:8px;padding:10px 14px;margin-bottom:8px;display:flex;"
                f"justify-content:space-between;align-items:center'>"
                f"<span style='font-size:0.83rem;color:#cbd5e1'>{theme}</span>"
                f"<span style='font-weight:700;color:#22c55e;font-size:0.9rem'>{delta:.1f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='color:#334155;font-size:0.83rem;padding:8px 0'>Aucun avantage significatif.</div>",
            unsafe_allow_html=True,
        )
