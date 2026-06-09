"""Page 2 — Catalogue de portefeuilles de référence."""

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Portefeuilles — ESG Platform", page_icon="◆", layout="wide", initial_sidebar_state="expanded")

from esg_data.fixtures import EMISSIONS, REFERENCE_PORTFOLIOS, RISK_LEVELS
from streamlit_app.components import layout
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import apply_global_styles, page_header, plotly_layout

apply_global_styles()
render_sidebar_nav()

import pandas as pd


@st.cache_data(ttl=3600)
def _get_data():  # type: ignore[no-untyped-def]
    from esg_data.services import (
        build_portfolio,
        compute_all_scores,
        compute_portfolio_score,
    )

    scores = compute_all_scores()
    results = []
    for pdef in REFERENCE_PORTFOLIOS:
        port = build_portfolio(pdef)
        result = compute_portfolio_score(port, scores["company_scores"], scores["methodology"])
        results.append({"def": pdef, "portfolio": port, "result": result})
    return scores, results


scores_data, portfolio_results = _get_data()
company_scores = scores_data["company_scores"]

page_header(
    "Portefeuilles de Référence",
    "Catalogues communautaires — explorez, clonez ou envoyez vers l'audit.",
)

CARD_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444"]

for item in portfolio_results:
    pdef = item["def"]
    port = item["portfolio"]
    ps_score = item["result"]["portfolio_score"]
    carbon = item["result"]["carbon_report"]
    wps = ps_score.weighted_portfolio_score

    with st.expander(
        f"{pdef['name']}  ·  Score ESG : {wps:.1f} / 100  ·  {len(port.holdings)} positions",
        expanded=False,
    ):
        layout.portfolio_description(pdef["description"])

        # KPIs
        k1, k2, k3 = st.columns(3)
        k1.metric("Score ESG Pondéré", f"{wps:.1f} / 100")
        k2.metric("Émissions Financées", f"{carbon.total_financed_emissions / 1000:.1f}K tCO₂e")
        k3.metric("Capital Total", f"${port.total_investment_value / 1000:.0f}K")

        layout.divider()

        # Holdings table
        rows = []
        for h in port.holdings:
            t = h.company.ticker
            cs = company_scores.get(t)
            em = EMISSIONS.get(t)
            total_c = (em.scope_1 + em.scope_2 + em.total_scope_3) if em else 0.0
            rows.append(
                {
                    "Société": h.company.name,
                    "Secteur": h.company.sector,
                    "Poids": f"{h.weight * 100:.1f}%",
                    "Investissement": f"${h.investment_value:,.0f}",
                    "Score ESG": f"{cs.final_score:.1f}" if cs else "—",
                    "Carbone (tCO₂e)": f"{total_c:,.0f}",
                    "Risque": RISK_LEVELS.get(t, "—"),
                }
            )

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Charts
        c1, c2 = st.columns(2)
        tickers = [h.company.ticker for h in port.holdings]
        colors = CARD_COLORS[: len(tickers)]

        with c1:
            fig_donut = go.Figure(
                go.Pie(
                    labels=[h.company.name for h in port.holdings],
                    values=[h.weight * 100 for h in port.holdings],
                    hole=0.62,
                    marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=0)),
                    textfont=dict(size=11, color="white"),
                )
            )
            fig_donut.update_layout(
                **plotly_layout(
                    title=dict(text="Répartition des poids", font=dict(size=12)),
                    height=260,
                    margin=dict(t=40, b=0, l=0, r=0),
                )
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with c2:
            esg_vals = [
                company_scores[t].final_score if t in company_scores else 0 for t in tickers
            ]
            fig_bar = go.Figure(
                go.Bar(
                    x=[h.company.name for h in port.holdings],
                    y=esg_vals,
                    marker=dict(color=colors, opacity=0.85),
                    text=[f"{s:.1f}" for s in esg_vals],
                    textposition="outside",
                    textfont=dict(size=10, color="#94a3b8"),
                )
            )
            fig_bar.update_layout(
                **plotly_layout(
                    title=dict(text="Score ESG par société", font=dict(size=12)),
                    height=260,
                    margin=dict(t=40, b=0, l=0, r=0),
                    xaxis=dict(tickfont=dict(size=10)),
                    yaxis=dict(range=[0, 115]),
                )
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

        # Actions
        btn1, btn2, _ = st.columns([2, 2, 8])
        with btn1:
            if st.button("Cloner", key=f"clone_{pdef['id']}", use_container_width=True):
                st.session_state[f"show_clone_{pdef['id']}"] = True
        with btn2:
            if st.button(
                "Analyser", key=f"audit_{pdef['id']}", type="primary", use_container_width=True
            ):
                st.session_state["audit_portfolio"] = str(pdef["id"])
                st.switch_page("pages/5_Explainability.py")

        if st.session_state.get(f"show_clone_{pdef['id']}"):
            with st.container(key=f"clonebox_{pdef['id']}"):
                clone_name = st.text_input(
                    "Nom du portefeuille cloné",
                    value=f"Copie — {pdef['name']}",
                    key=f"clone_name_{pdef['id']}",
                )
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button(
                        "Confirmer le clonage", key=f"clone_confirm_{pdef['id']}", type="primary"
                    ):
                        import uuid
                        from datetime import date

                        new_port = {
                            "id": str(uuid.uuid4())[:8],
                            "name": clone_name.strip() or pdef["name"],
                            "holdings": [
                                {
                                    "ticker": h.company.ticker,
                                    "company_name": h.company.name,
                                    "weight": h.weight,
                                    "investment_value": h.investment_value,
                                    "currency": port.currency,
                                }
                                for h in port.holdings
                            ],
                            "currency": port.currency,
                            "created_at": date.today().isoformat(),
                            "total_investment": port.total_investment_value,
                        }
                        if "user_portfolios" not in st.session_state:
                            st.session_state["user_portfolios"] = []
                        st.session_state["user_portfolios"].append(new_port)
                        st.session_state[f"show_clone_{pdef['id']}"] = False
                        st.success(
                            f"Portefeuille « {new_port['name']} » ajouté à Mes Portefeuilles."
                        )
                with cc2:
                    if st.button("Annuler", key=f"clone_cancel_{pdef['id']}"):
                        st.session_state[f"show_clone_{pdef['id']}"] = False
                        st.rerun()
