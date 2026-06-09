"""Page 5 — Audit extra-financier par portefeuille."""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Analyse — ESG Platform", page_icon="◆", layout="wide", initial_sidebar_state="expanded")

from datetime import UTC, datetime

from esg_data.fixtures import COMPANIES, EMISSIONS, REFERENCE_PORTFOLIOS
from esg_data.reporting import build_text_report
from streamlit_app.components import layout
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import PILLAR_LABELS, apply_global_styles, page_header

apply_global_styles()
render_sidebar_nav()


@st.cache_data(ttl=3600)
def _scores():  # type: ignore[no-untyped-def]
    from esg_data.services import compute_all_scores

    return compute_all_scores()


@st.cache_data(ttl=3600)
def _ref_portfolios():  # type: ignore[no-untyped-def]
    from esg_data.services import build_portfolio, compute_portfolio_score

    sd = _scores()
    out: dict[str, dict] = {}
    for pdef in REFERENCE_PORTFOLIOS:
        port = build_portfolio(pdef)  # type: ignore[arg-type]
        res = compute_portfolio_score(port, sd["company_scores"], sd["methodology"])
        out[str(pdef["id"])] = {
            "name": str(pdef["name"]),
            "port": port,
            "result": res,
        }
    return out


sd = _scores()
company_scores = sd["company_scores"]
ref_ports = _ref_portfolios()

options: dict[str, dict] = dict(ref_ports)
for up in st.session_state.get("user_portfolios", []):
    uid = up.get("id", "")
    if uid in options:
        continue
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
    res = compute_portfolio_score(port_obj, company_scores, sd["methodology"])
    options[uid] = {"name": up["name"], "port": port_obj, "result": res}

# ── Header ─────────────────────────────────────────────────────────────────────
page_header(
    "Analyse extra-financière",
    "Sélectionnez un portefeuille pour afficher son audit ESG complet.",
)

# ── Selector ───────────────────────────────────────────────────────────────────
PLACEHOLDER = "— Choisir un portefeuille —"
choice = st.selectbox(
    "Portefeuille",
    [PLACEHOLDER] + [v["name"] for v in options.values()],
    label_visibility="collapsed",
    key="exp_sel",
)

if choice == PLACEHOLDER:
    layout.analysis_placeholder()
    st.stop()

pid = next(k for k, v in options.items() if v["name"] == choice)
sel = options[pid]
port = sel["port"]
ps = sel["result"]["portfolio_score"]
carbon = sel["result"]["carbon_report"]
wps = ps.weighted_portfolio_score


def _show(df: pd.DataFrame, key: str) -> None:
    st.dataframe(df, use_container_width=True, hide_index=True, key=key)


# ═══════════════════════════════════════════════════════════════════════════════
# Section 1 — Résumé
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label(f"Résumé — {sel['name']}")

_show(
    pd.DataFrame(
        [
            {"Indicateur": "Score ESG Pondéré", "Valeur": f"{wps:.1f} / 100"},
            {"Indicateur": "Nombre de positions", "Valeur": str(len(port.holdings))},
            {
                "Indicateur": "Émissions Financées",
                "Valeur": f"{carbon.total_financed_emissions:,.0f} tCO₂e",
            },
            {
                "Indicateur": "Intensité Carbone",
                "Valeur": f"{carbon.carbon_intensity:.1f} tCO₂e / $M investi",
            },
            {
                "Indicateur": "WACI (PCAF, base CA)",
                "Valeur": f"{carbon.waci:.1f} tCO₂e / $M de CA  (couverture {carbon.waci_coverage * 100:.0f}%)",
            },
            {
                "Indicateur": "Carbon-to-Value (EVIC)",
                "Valeur": f"{carbon.carbon_to_value:.1f} tCO₂e / $M d'EVIC",
            },
            {
                "Indicateur": "Qualité PCAF (1=meilleur, 5=pire)",
                "Valeur": f"{carbon.data_quality.weighted_pcaf_score:.2f} / 5  (couverture {carbon.data_quality.coverage * 100:.0f}%)",
            },
            {
                "Indicateur": "Capital Total Investi",
                "Valeur": f"${carbon.total_investment_value:,.0f}",
            },
        ]
    ),
    "kpi_tbl",
)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 2 — Scores ESG par Société
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Scores ESG par Société")

esg_rows = []
for h in port.holdings:
    t = h.company.ticker
    cs = company_scores.get(t)
    if not cs:
        continue
    p_env = cs.pillar("environment")
    p_soc = cs.pillar("social")
    p_gov = cs.pillar("governance")
    esg_rows.append(
        {
            "Société": h.company.name,
            "Secteur": h.company.sector,
            "Poids": f"{h.weight * 100:.1f}%",
            "Environnement": f"{p_env.score:.1f}" if p_env else "—",
            "Social": f"{p_soc.score:.1f}" if p_soc else "—",
            "Gouvernance": f"{p_gov.score:.1f}" if p_gov else "—",
            "Score ESG": f"{cs.final_score:.1f}",
        }
    )
_show(pd.DataFrame(esg_rows), "esg_tbl")

# ═══════════════════════════════════════════════════════════════════════════════
# Section 3 — Décomposition par Thème
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Décomposition par Thème")

layout.callout_howto()

theme_rows = []
for h in port.holdings:
    t = h.company.ticker
    cs = company_scores.get(t)
    if not cs:
        continue
    for pillar in cs.pillars:
        for theme in pillar.themes:
            theme_rows.append(
                {
                    "Société": h.company.name,
                    "Pilier": PILLAR_LABELS.get(pillar.pillar_id, pillar.pillar_id.title()),
                    "Thème": theme.theme_id.replace("_", " ").title(),
                    "Poids Pilier": f"{pillar.weight * 100:.0f}%",
                    "Poids Thème": f"{theme.weight * 100:.0f}%",
                    "Score": f"{theme.score:.1f}",
                    "Contribution": f"{theme.weighted_contribution:.2f}",
                }
            )
_show(pd.DataFrame(theme_rows), "theme_tbl")

# ═══════════════════════════════════════════════════════════════════════════════
# Section 4 — Empreinte Carbone
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Empreinte Carbone — Scope 1 / 2 / 3")

carbon_rows = []
for h in port.holdings:
    t = h.company.ticker
    em = EMISSIONS.get(t)
    if not em:
        continue
    ae = next((a for a in carbon.per_holding if a.ticker == t), None)
    carbon_rows.append(
        {
            "Société": h.company.name,
            "Scope 1 (tCO₂e)": f"{em.scope_1:,.0f}",
            "Scope 2 (tCO₂e)": f"{em.scope_2:,.0f}",
            "Scope 3 (tCO₂e)": f"{em.total_scope_3:,.0f}",
            "Total (tCO₂e)": f"{em.total_emissions:,.0f}",
            "Attribué (tCO₂e)": f"{ae.attributed_total:,.0f}" if ae else "—",
            "Fiabilité": f"{em.confidence * 100:.0f}%",
            "Source": em.source.replace("_", " ").title(),
        }
    )
_show(pd.DataFrame(carbon_rows), "carbon_tbl")

# ═══════════════════════════════════════════════════════════════════════════════
# Section 5 — Rapport officiel
# ═══════════════════════════════════════════════════════════════════════════════
layout.section_label("Rapport d'Audit — Brouillon Non Signé")

layout.callout_unsigned()

generated_at = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
# All companies in this portfolio were scored at the same instant
# (see compute_all_scores) so any score's metadata is representative.
sample_score = next(
    (
        company_scores[h.company.ticker]
        for h in port.holdings
        if h.company.ticker in company_scores
    ),
    None,
)
scored_at_str = sample_score.scored_at.strftime("%Y-%m-%d %H:%M UTC") if sample_score else "—"
mhash = sample_score.methodology_hash if sample_score else "—"

st.download_button(
    label="Télécharger le rapport d'audit",
    data=build_text_report(
        portfolio_name=sel["name"],
        portfolio_id=pid,
        weighted_score=wps,
        carbon=carbon,
        esg_rows=esg_rows,
        carbon_rows=carbon_rows,
        methodology_hash=mhash,
        scored_at=scored_at_str,
        generated_at=generated_at,
    ),
    file_name=f"audit_esg_{pid}.txt",
    mime="text/plain",
)

# ═══════════════════════════════════════════════════════════════════════════════
# Section 6 — Détails techniques (collapsed by default)
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("Détails techniques — provenance et hachage", expanded=False):
    prov_rows = []
    for h in port.holdings:
        t = h.company.ticker
        cs = company_scores.get(t)
        if not cs:
            continue
        em = EMISSIONS.get(t)
        prov_rows.append(
            {
                "Société": h.company.name,
                "Version Méthodologie": "Default ESG v1.0.0",
                "Algorithme": "SHA-256",
                "Date du Score": cs.scored_at.strftime("%Y-%m-%d %H:%M UTC"),
                "Date des Données": em.as_of_date.strftime("%Y-%m-%d") if em else "—",
                "Hash Méthodologie": cs.methodology_hash[:32] + "…",
            }
        )
    _show(pd.DataFrame(prov_rows), "prov_tbl")
