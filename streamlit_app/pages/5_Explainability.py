"""Page 5 — Audit extra-financier par portefeuille."""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Analyse — ESG Platform", page_icon="◆", layout="wide")

from datetime import UTC

from esg_data.fixtures import COMPANIES, EMISSIONS, REFERENCE_PORTFOLIOS
from streamlit_app.utils.styling import apply_global_styles

apply_global_styles()


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
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Analyse extra-financière</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Sélectionnez un portefeuille pour afficher son audit ESG complet.</p>",
    unsafe_allow_html=True,
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
    st.markdown(
        "<div style='text-align:center;padding:72px 0;color:#334155'>"
        "<div style='font-size:2rem;font-weight:200;color:#1e293b'>—</div>"
        "<div style='margin-top:12px;font-size:0.9rem'>Sélectionnez un portefeuille pour lancer l'analyse.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
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
st.markdown(
    f"<div class='section-header'>Résumé — {sel['name']}</div>",
    unsafe_allow_html=True,
)

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
st.markdown("<div class='section-header'>Scores ESG par Société</div>", unsafe_allow_html=True)

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
st.markdown("<div class='section-header'>Décomposition par Thème</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="background:rgba(99,102,241,0.06);border-left:3px solid #6366f1;
                border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:16px;font-size:0.83rem;color:#94a3b8">
        <span style="color:#e2e8f0;font-weight:600">Comment lire ce tableau ?</span><br>
        Chaque thème (ex. <em>Changement Climatique</em>) regroupe plusieurs indicateurs.
        Le <strong>Score</strong> est la moyenne pondérée de ces indicateurs (0–100).
        La <strong>Contribution</strong> mesure l'impact réel sur le score ESG final :
        <code>Contribution = Score × Poids Thème × Poids Pilier</code>.
        Une contribution élevée signifie que ce thème tire le score vers le haut ; négative (si score &lt; médiane),
        vers le bas.
    </div>
    """,
    unsafe_allow_html=True,
)

theme_rows = []
pillar_labels = {"environment": "Environnement", "social": "Social", "governance": "Gouvernance"}
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
                    "Pilier": pillar_labels.get(pillar.pillar_id, pillar.pillar_id.title()),
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
st.markdown(
    "<div class='section-header'>Empreinte Carbone — Scope 1 / 2 / 3</div>", unsafe_allow_html=True
)

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
st.markdown(
    "<div class='section-header'>Rapport d'Audit — Brouillon Non Signé</div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div style='background:rgba(245,158,11,0.07);border-left:3px solid #f59e0b;"
    "border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;font-size:0.8rem;color:#94a3b8'>"
    "<b style='color:#f59e0b'>Document non signé.</b> "
    "La signature cryptographique des bundles de score (Ed25519) est prévue en Phase 9 et n'est pas "
    "encore implémentée. Ce rapport est un brouillon de travail, sans valeur réglementaire CSRD ou autre."
    "</div>",
    unsafe_allow_html=True,
)


def _build_report() -> bytes:
    from datetime import datetime

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

    lines = [
        "RAPPORT ESG — BROUILLON NON SIGNÉ",
        "=" * 64,
        f"Portefeuille          : {sel['name']}",
        f"Identifiant           : {pid}",
        f"Score ESG Pondéré     : {wps:.1f} / 100",
        f"Émissions Financées   : {carbon.total_financed_emissions:,.0f} tCO₂e",
        f"Intensité Carbone     : {carbon.carbon_intensity:.1f} tCO₂e / $M investi",
        f"WACI (PCAF, /CA)     : {carbon.waci:.1f} tCO₂e / $M de CA (couverture {carbon.waci_coverage * 100:.0f}%)",
        f"Carbon-to-Value/EVIC : {carbon.carbon_to_value:.1f} tCO₂e / $M d'EVIC",
        f"Qualité données PCAF : {carbon.data_quality.weighted_pcaf_score:.2f}/5 (1=meilleur, 5=pire ; couverture {carbon.data_quality.coverage * 100:.0f}%)",
        "",
        "SCORES ESG PAR SOCIÉTÉ",
        "-" * 64,
    ]
    for row in esg_rows:
        lines.append(
            f"{row['Société']:<40} Poids:{row['Poids']:>6}  "
            f"E:{row['Environnement']:>5}  S:{row['Social']:>5}  G:{row['Gouvernance']:>5}  "
            f"ESG:{row['Score ESG']:>5}"
        )
    lines += ["", "EMPREINTE CARBONE", "-" * 64]
    for row in carbon_rows:
        lines.append(
            f"{row['Société']:<40} "
            f"S1:{row['Scope 1 (tCO₂e)']:>12}  S2:{row['Scope 2 (tCO₂e)']:>12}  "
            f"S3:{row['Scope 3 (tCO₂e)']:>12}  Total:{row['Total (tCO₂e)']:>14}"
        )
    lines += [
        "",
        "PROVENANCE",
        "-" * 64,
        "Méthodologie         : Default ESG v1.0.0",
        f"Hash méthodologie    : {mhash}",
        "Algorithme           : SHA-256 · JSON canonique (clés triées)",
        f"Date du scoring      : {scored_at_str}",
        f"Date de génération   : {generated_at}",
        "Signature            : aucune (Phase 9 non livrée)",
        "Licence plateforme   : Apache 2.0",
        "=" * 64,
    ]
    return "\n".join(lines).encode("utf-8")


st.download_button(
    label="Télécharger le rapport d'audit",
    data=_build_report(),
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
