"""Page 3 — Gestion des portefeuilles personnels."""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

import csv
import io
import json
import uuid
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Mes Portefeuilles — ESG Platform", page_icon="◆", layout="wide")

from streamlit_app.utils.styling import apply_global_styles, score_color
from streamlit_app.data.companies_data import COMPANIES, RISK_LEVELS

apply_global_styles()


@st.cache_data(ttl=3600)
def _get_scores():  # type: ignore[no-untyped-def]
    from streamlit_app.utils.scoring_engine import compute_all_scores
    return compute_all_scores()


scores_data = _get_scores()
company_scores = scores_data["company_scores"]

if "user_portfolios" not in st.session_state:
    st.session_state["user_portfolios"] = []

CURRENCIES = ["USD", "EUR", "MRU", "GBP", "MAD", "XOF"]

_NAME_TO_TICKER: dict[str, str] = {co.name: t for t, co in COMPANIES.items()}
_NAME_TO_TICKER.update({t: t for t in COMPANIES})

st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Mes Portefeuilles</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Créez et gérez vos portefeuilles personnels.</p>",
    unsafe_allow_html=True,
)

tab_create, tab_import, tab_list = st.tabs(["Créer", "Importer", "Mes portefeuilles"])

# ── TAB 1 — Création manuelle ──────────────────────────────────────────────────
with tab_create:
    st.markdown("<div class='section-header'>Nouveau portefeuille</div>", unsafe_allow_html=True)

    with st.form("create_portfolio_form", clear_on_submit=False):
        portfolio_name = st.text_input(
            "Nom du portefeuille",
            placeholder="Ex : Portefeuille ESG Mauritanie 2026",
            key="cp_name",
        )

        st.markdown(
            "<div style='font-size:0.8rem;color:#94a3b8;margin:16px 0 8px 0;font-weight:500'>"
            "Positions</div>",
            unsafe_allow_html=True,
        )
        st.caption("Le secteur se remplit automatiquement selon la société sélectionnée.")

        num_holdings = st.number_input(
            "Nombre de positions", min_value=1, max_value=4, value=2, step=1,
        )
        company_options = [co.name for co in COMPANIES.values()]
        holdings_data = []

        for i in range(int(num_holdings)):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1:
                company_name = st.selectbox(
                    f"Société {i + 1}", options=company_options, key=f"cp_company_{i}",
                )
            ticker = _NAME_TO_TICKER.get(company_name, "")
            sector = COMPANIES[ticker].sector if ticker in COMPANIES else ""
            with c2:
                st.text_input(f"Secteur {i + 1}", value=sector, disabled=True, key=f"cp_sector_{i}")
            with c3:
                inv_value = st.number_input(
                    f"Montant {i + 1}",
                    min_value=1_000.0,
                    max_value=10_000_000.0,
                    value=100_000.0,
                    step=10_000.0,
                    key=f"cp_inv_{i}",
                )
            with c4:
                currency = st.selectbox("Devise", CURRENCIES, key=f"cp_cur_{i}", index=0)

            holdings_data.append({
                "company_name": company_name,
                "ticker": ticker,
                "investment_value": inv_value,
                "currency": currency,
            })

        submitted = st.form_submit_button("Créer le portefeuille", use_container_width=True)

    if submitted:
        if not portfolio_name.strip():
            st.error("Le nom du portefeuille est obligatoire.")
        else:
            total_inv = sum(h["investment_value"] for h in holdings_data)
            valid = [h for h in holdings_data if h["ticker"] in COMPANIES]
            if not valid:
                st.error("Aucune société valide sélectionnée.")
            else:
                port_holdings = [
                    {
                        "ticker": h["ticker"],
                        "company_name": h["company_name"],
                        "weight": h["investment_value"] / total_inv,
                        "investment_value": h["investment_value"],
                        "currency": h["currency"],
                    }
                    for h in valid
                ]
                st.session_state["user_portfolios"].append({
                    "id": str(uuid.uuid4())[:8],
                    "name": portfolio_name.strip(),
                    "holdings": port_holdings,
                    "currency": valid[0]["currency"],
                    "created_at": date.today().isoformat(),
                    "total_investment": total_inv,
                })
                st.success(f"Portefeuille « {portfolio_name.strip()} » créé avec {len(port_holdings)} position(s).")

# ── TAB 2 — Import ─────────────────────────────────────────────────────────────
with tab_import:
    st.markdown("<div class='section-header'>Importer un portefeuille</div>", unsafe_allow_html=True)

    st.markdown(
        "<div style='background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);"
        "border-radius:10px;padding:14px 18px;font-size:0.83rem;color:#94a3b8;margin-bottom:20px'>"
        "<div style='font-weight:600;color:#e2e8f0;margin-bottom:6px'>Format requis</div>"
        "Votre fichier CSV ou JSON doit contenir les colonnes suivantes :<br>"
        "<code style='color:#6366f1'>company_name</code> &nbsp;"
        "<code style='color:#6366f1'>isin_code</code> &nbsp;"
        "<code style='color:#6366f1'>sector</code> &nbsp;"
        "<code style='color:#6366f1'>investment_value</code>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Template download
    template_csv_rows = ["company_name,isin_code,sector,investment_value"]
    for t, co in COMPANIES.items():
        template_csv_rows.append(f"{co.name},{co.isin},{co.sector},100000")
    template_csv = "\n".join(template_csv_rows)

    col_dl, _ = st.columns([3, 9])
    with col_dl:
        st.download_button(
            "Télécharger le modèle CSV",
            data=template_csv,
            file_name="modele_portefeuille.csv",
            mime="text/csv",
        )

    import_name = st.text_input(
        "Nom du portefeuille importé",
        placeholder="Mon import ESG",
        key="imp_name",
    )
    uploaded = st.file_uploader("Déposez votre fichier CSV ou JSON", type=["csv", "json"])

    if uploaded and import_name.strip():
        try:
            if uploaded.name.endswith(".csv"):
                df_import = pd.read_csv(uploaded)
            else:
                raw = json.loads(uploaded.read())
                df_import = pd.DataFrame(raw if isinstance(raw, list) else [raw])

            required = {"company_name", "isin_code", "sector", "investment_value"}
            missing_cols = required - set(df_import.columns)
            if missing_cols:
                st.error(f"Colonnes manquantes : {', '.join(sorted(missing_cols))}")
            else:
                errors: list[str] = []
                matched: list[dict[str, object]] = []
                for _, row in df_import.iterrows():
                    match_ticker = None
                    for t, co in COMPANIES.items():
                        if (co.isin == str(row["isin_code"])
                                or co.name.lower() == str(row["company_name"]).lower()):
                            match_ticker = t
                            break
                    if match_ticker is None:
                        errors.append(f"{row['company_name']} — société non trouvée dans la plateforme.")
                    else:
                        matched.append({
                            "ticker": match_ticker,
                            "company_name": COMPANIES[match_ticker].name,
                            "investment_value": float(row["investment_value"]),
                        })

                for err in errors:
                    st.warning(err)

                if matched:
                    total_inv = sum(float(h["investment_value"]) for h in matched)
                    port_holdings = [
                        {**h, "weight": float(h["investment_value"]) / total_inv, "currency": "USD"}
                        for h in matched
                    ]
                    st.success(f"{len(port_holdings)} position(s) validée(s). Poids calculés automatiquement.")

                    preview_df = pd.DataFrame([
                        {
                            "Société": h["company_name"],
                            "Montant investi": f"${float(h['investment_value']):,.0f}",
                            "Poids": f"{float(h['weight']) * 100:.1f}%",
                        }
                        for h in port_holdings
                    ])
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

                    if st.button("Confirmer l'import", key="confirm_import"):
                        st.session_state["user_portfolios"].append({
                            "id": str(uuid.uuid4())[:8],
                            "name": import_name.strip(),
                            "holdings": port_holdings,
                            "currency": "USD",
                            "created_at": date.today().isoformat(),
                            "total_investment": total_inv,
                        })
                        st.success(f"Portefeuille « {import_name.strip()} » importé avec succès.")

        except Exception as exc:
            st.error(f"Erreur lors de la lecture du fichier : {exc}")

# ── TAB 3 — List ───────────────────────────────────────────────────────────────
with tab_list:
    st.markdown("<div class='section-header'>Mes portefeuilles</div>", unsafe_allow_html=True)
    user_ports = st.session_state.get("user_portfolios", [])

    if not user_ports:
        st.markdown(
            "<div style='text-align:center;padding:48px 0;color:#334155'>"
            "<div style='font-size:2rem;font-weight:300;color:#1e293b'>—</div>"
            "<div style='margin-top:10px;font-size:0.9rem'>Aucun portefeuille créé.<br>"
            "Utilisez les onglets Créer ou Importer pour commencer.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        for pf in user_ports:
            holdings = pf["holdings"]
            total_inv = pf["total_investment"]
            weighted_esg = sum(
                h["weight"] * (company_scores[h["ticker"]].final_score
                               if h["ticker"] in company_scores else 0)
                for h in holdings
            )

            with st.expander(
                f"{pf['name']}  ·  {len(holdings)} positions  ·  Créé le {pf['created_at']}",
                expanded=False,
            ):
                m1, m2 = st.columns(2)
                m1.metric("Score ESG Pondéré", f"{weighted_esg:.1f} / 100")
                m2.metric("Capital Total", f"${total_inv:,.0f}")

                rows = []
                for h in holdings:
                    t = h["ticker"]
                    cs = company_scores.get(t)
                    rows.append({
                        "Société":        h["company_name"],
                        "Poids":          f"{h['weight'] * 100:.1f}%",
                        "Montant":        f"${float(h['investment_value']):,.0f}",
                        "Score ESG":      f"{cs.final_score:.1f}" if cs else "—",
                        "Risque":         RISK_LEVELS.get(t, "—"),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                st.markdown(
                    "<style>.danger-btn button{background:transparent!important;"
                    "border:1px solid #ef4444!important;color:#ef4444!important;"
                    "font-size:0.78rem!important;padding:4px 12px!important;"
                    "border-radius:6px!important;}</style>",
                    unsafe_allow_html=True,
                )
                _, btn_col = st.columns([10, 2])
                with btn_col:
                    st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                    if st.button("Supprimer", key=f"del_{pf['id']}", use_container_width=True):
                        st.session_state["user_portfolios"] = [
                            p for p in st.session_state["user_portfolios"]
                            if p["id"] != pf["id"]
                        ]
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
