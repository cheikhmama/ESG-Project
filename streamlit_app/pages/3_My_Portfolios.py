"""Page 3 — Gestion des portefeuilles personnels."""

import json
import uuid
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Mes Portefeuilles — ESG Platform", page_icon="◆", layout="wide", initial_sidebar_state="expanded")

from esg_data.fixtures import COMPANIES, RISK_LEVELS
from streamlit_app.components import layout
from streamlit_app.utils.nav import render_sidebar_nav
from streamlit_app.utils.styling import apply_global_styles, page_header

apply_global_styles()
render_sidebar_nav()


@st.cache_data(ttl=3600)
def _get_scores():  # type: ignore[no-untyped-def]
    from esg_data.services import compute_all_scores

    return compute_all_scores()


scores_data = _get_scores()
company_scores = scores_data["company_scores"]

if "user_portfolios" not in st.session_state:
    st.session_state["user_portfolios"] = []

_CURRENCIES = ["USD", "EUR", "MRU"]

_NAME_TO_TICKER: dict[str, str] = {co.name: t for t, co in COMPANIES.items()}
_NAME_TO_TICKER.update({t: t for t in COMPANIES})

page_header("Mes Portefeuilles", "Créez et gérez vos portefeuilles personnels.")

tab_create, tab_import, tab_list = st.tabs(["Créer", "Importer", "Mes portefeuilles"])

# ── TAB 1 — Création manuelle ──────────────────────────────────────────────────
with tab_create:
    # ── Session state ──────────────────────────────────────────────────────────
    if "pos_ids" not in st.session_state:
        st.session_state["pos_ids"] = [0]
    if "pos_next_id" not in st.session_state:
        st.session_state["pos_next_id"] = 1

    # ── Nom du portefeuille ────────────────────────────────────────────────────
    layout.field_label("Nom du portefeuille")
    portfolio_name = st.text_input(
        "Nom",
        placeholder="Ex : Portefeuille ESG Mauritanie 2026",
        key="cp_name",
        label_visibility="collapsed",
    )

    # ── Colonnes partagées (header + rows utilisent les mêmes proportions) ──────
    _COLS = [0.28, 3, 1.8, 3, 0.4]  # badge | société | secteur | montant+devise | ×
    layout.vspace("lg")

    # Header "Positions" + bouton "+" — layout indépendant, titre à gauche / + à droite
    n = len(st.session_state["pos_ids"])
    h_title, h_spacer, h_add = st.columns([6, 3, 1])
    with h_title:
        layout.positions_header(n)
    with h_add:
        if n < len(COMPANIES) and st.button("+", key="add_pos", help="Ajouter une position"):
            st.session_state["pos_ids"].append(st.session_state["pos_next_id"])
            st.session_state["pos_next_id"] += 1

    # Libellés colonnes — même grille
    layout.vspace("sm")
    lb, lco, lsec, linv, lrm = st.columns(_COLS)
    for col, label in zip([lco, lsec, linv], ["Société", "Secteur", "Montant / Devise"]):
        with col:
            layout.column_label(label)

    # ── Lignes de positions ────────────────────────────────────────────────────
    _PLACEHOLDER = "— Choisir une société —"
    company_options = [_PLACEHOLDER] + [co.name for co in COMPANIES.values()]
    holdings_data = []
    to_remove = None

    for i, pid in enumerate(st.session_state["pos_ids"]):
        c_num, c_co, c_sec, c_inv, c_rm = st.columns(_COLS)

        with c_num:
            layout.position_number(i + 1)
        with c_co:
            company_name = st.selectbox(
                "Société",
                options=company_options,
                key=f"pos_{pid}_company",
                label_visibility="collapsed",
            )

        is_selected = company_name != _PLACEHOLDER
        ticker = _NAME_TO_TICKER.get(company_name, "") if is_selected else ""
        sector = COMPANIES[ticker].sector if ticker in COMPANIES else "—"

        # Force session state so the disabled field always reflects current company choice
        st.session_state[f"pos_{pid}_sec"] = sector
        with c_sec:
            st.text_input(
                "Secteur", disabled=True, label_visibility="collapsed", key=f"pos_{pid}_sec"
            )
        with c_inv:
            sub_amt, sub_cur = st.columns([3, 1])
            with sub_amt:
                inv_value = st.number_input(
                    "Montant",
                    min_value=1_000.0,
                    max_value=10_000_000.0,
                    value=100_000.0,
                    step=10_000.0,
                    key=f"pos_{pid}_inv",
                    label_visibility="collapsed",
                )
            with sub_cur:
                _cur_key = f"pos_{pid}_cur_val"
                if _cur_key not in st.session_state:
                    st.session_state[_cur_key] = "USD"
                _cur_val = st.session_state[_cur_key]
                if st.button(
                    _cur_val,
                    key=f"pos_{pid}_cur_btn",
                    help="Cliquer pour changer la devise (USD → EUR → MRU)",
                ):
                    _idx = _CURRENCIES.index(_cur_val)
                    st.session_state[_cur_key] = _CURRENCIES[(_idx + 1) % len(_CURRENCIES)]
                currency = st.session_state[_cur_key]
        with c_rm:
            if len(st.session_state["pos_ids"]) > 1 and st.button(
                "×", key=f"pos_{pid}_remove", help="Supprimer"
            ):
                to_remove = pid

        if is_selected:
            holdings_data.append(
                {
                    "company_name": company_name,
                    "ticker": ticker,
                    "investment_value": inv_value,
                    "currency": currency,
                }
            )

    if to_remove is not None:
        st.session_state["pos_ids"].remove(to_remove)
        st.rerun()

    # ── Répartition en temps réel ─────────────────────────────────────────────
    total_preview = sum(h["investment_value"] for h in holdings_data)
    if total_preview > 0 and len(holdings_data) > 1:
        layout.field_label("Répartition", variant="rep")
        preview_cols = st.columns(len(holdings_data))
        for col, h in zip(preview_cols, holdings_data):
            pct = h["investment_value"] / total_preview * 100
            with col:
                layout.allocation_tile(f"{pct:.1f}%", h["company_name"].split()[0])

    # ── Bouton créer ───────────────────────────────────────────────────────────
    layout.vspace("lg")
    if st.button(
        "Créer le portefeuille", key="cp_submit", type="primary", use_container_width=True
    ):
        n_empty = len(st.session_state["pos_ids"]) - len(holdings_data)
        if not portfolio_name.strip():
            st.error("Le nom du portefeuille est obligatoire.")
        elif not holdings_data:
            st.error("Veuillez sélectionner au moins une société avant de créer.")
        else:
            if n_empty > 0:
                st.info(
                    f"{n_empty} position(s) sans société ignorée(s) — portefeuille créé avec {len(holdings_data)} position(s)."
                )
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
                new_port = {
                    "id": str(uuid.uuid4())[:8],
                    "name": portfolio_name.strip(),
                    "holdings": port_holdings,
                    "currency": valid[0]["currency"],
                    "created_at": date.today().isoformat(),
                    "total_investment": total_inv,
                }
                st.session_state["user_portfolios"].append(new_port)
                # Réinitialiser les positions pour le prochain portefeuille
                st.session_state["pos_ids"] = [0]
                st.session_state["pos_next_id"] = 1
                layout.success_banner(
                    f"Portefeuille « {new_port['name']} » créé — "
                    "consultez l'onglet Mes portefeuilles",
                    count=len(port_holdings),
                    capital=f"${total_inv:,.0f}",
                    holdings=[
                        {
                            "name": h["company_name"].split()[0],
                            "pct": f"{h['weight'] * 100:.1f}%",
                        }
                        for h in port_holdings
                    ],
                )

# ── TAB 2 — Import ─────────────────────────────────────────────────────────────
with tab_import:
    layout.section_label("Importer un portefeuille")

    # Format card + template download
    col_info, col_dl = st.columns([3, 1])
    with col_info:
        layout.info_card(
            "Champs requis",
            ["company_name", "isin_code", "sector", "investment_value"],
        )
    with col_dl:
        template_csv_rows = ["company_name,isin_code,sector,investment_value"]
        for t, co in COMPANIES.items():
            template_csv_rows.append(f"{co.name},{co.isin},{co.sector},100000")
        st.download_button(
            "Télécharger le modèle",
            data="\n".join(template_csv_rows),
            file_name="modele_portefeuille.csv",
            mime="text/csv",
            use_container_width=True,
        )

    layout.vspace("md")

    # ── File picker ────────────────────────────────────────────────────────────
    layout.field_label("Fichier")
    uploaded = st.file_uploader(
        "Fichier",
        type=["csv", "json"],
        label_visibility="collapsed",
        help="Formats acceptés : CSV ou JSON",
    )

    if uploaded is not None:
        # ── Parse file ─────────────────────────────────────────────────────────
        try:
            if uploaded.name.endswith(".csv"):
                df_import = pd.read_csv(uploaded)
            else:
                raw = json.loads(uploaded.read())
                df_import = pd.DataFrame(raw if isinstance(raw, list) else [raw])
        except Exception as exc:
            st.error(f"Impossible de lire le fichier : {exc}")
            df_import = None

        if df_import is not None:
            required = {"company_name", "isin_code", "sector", "investment_value"}
            missing_cols = required - set(df_import.columns)

            if missing_cols:
                # Missing required columns — block creation
                st.error(
                    f"Fichier invalide — colonnes manquantes : "
                    f"{', '.join(f'`{c}`' for c in sorted(missing_cols))}"
                )
            else:
                # ── Match rows against platform companies ───────────────────
                errors_imp: list[str] = []
                matched: list[dict[str, str | float]] = []
                for _, row in df_import.iterrows():
                    match_ticker = None
                    for t, co in COMPANIES.items():
                        if (
                            co.isin == str(row["isin_code"])
                            or co.name.lower() == str(row["company_name"]).lower()
                        ):
                            match_ticker = t
                            break
                    if match_ticker is None:
                        errors_imp.append(str(row["company_name"]))
                    else:
                        matched.append(
                            {
                                "ticker": match_ticker,
                                "company_name": COMPANIES[match_ticker].name,
                                "investment_value": float(row["investment_value"]),
                            }
                        )

                # Unrecognised rows
                if errors_imp:
                    st.warning(
                        f"{len(errors_imp)} ligne(s) ignorée(s) — société(s) non trouvée(s) "
                        f"dans la plateforme : {', '.join(errors_imp)}"
                    )

                if not matched:
                    st.error("Aucune société reconnue dans ce fichier.")
                else:
                    # ── Preview ────────────────────────────────────────────
                    total_inv = sum(float(h["investment_value"]) for h in matched)
                    port_holdings = [
                        {**h, "weight": float(h["investment_value"]) / total_inv, "currency": "USD"}
                        for h in matched
                    ]

                    layout.preview_header("Aperçu", len(port_holdings), f"${total_inv:,.0f}")
                    preview_df = pd.DataFrame(
                        [
                            {
                                "Société": h["company_name"],
                                "Montant investi": f"${float(h['investment_value']):,.0f}",
                                "Poids": f"{float(h['weight']) * 100:.1f}%",
                            }
                            for h in port_holdings
                        ]
                    )
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

                    # ── Name + create ──────────────────────────────────────
                    layout.field_label("Nom du portefeuille", variant="imp")
                    import_name = st.text_input(
                        "Nom",
                        placeholder="Ex : Import ESG Mauritanie 2026",
                        key="imp_name",
                        label_visibility="collapsed",
                    )

                    if st.button(
                        "Créer ce portefeuille",
                        key="confirm_import",
                        type="primary",
                        use_container_width=True,
                        disabled=not import_name.strip(),
                    ):
                        st.session_state["user_portfolios"].append(
                            {
                                "id": str(uuid.uuid4())[:8],
                                "name": import_name.strip(),
                                "holdings": port_holdings,
                                "currency": "USD",
                                "created_at": date.today().isoformat(),
                                "total_investment": total_inv,
                            }
                        )
                        layout.success_banner(
                            f"Portefeuille « {import_name.strip()} » créé",
                            subtitle="Consultez l'onglet « Mes portefeuilles » "
                            "pour le visualiser et l'analyser.",
                        )

# ── TAB 3 — List ───────────────────────────────────────────────────────────────
with tab_list:
    layout.section_label("Mes portefeuilles")
    user_ports = st.session_state.get("user_portfolios", [])

    if not user_ports:
        layout.empty_state()
    else:
        for pf in user_ports:
            holdings = pf["holdings"]
            total_inv = pf["total_investment"]
            weighted_esg = sum(
                h["weight"]
                * (company_scores[h["ticker"]].final_score if h["ticker"] in company_scores else 0)
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
                    rows.append(
                        {
                            "Société": h["company_name"],
                            "Poids": f"{h['weight'] * 100:.1f}%",
                            "Montant": f"${float(h['investment_value']):,.0f}",
                            "Score ESG": f"{cs.final_score:.1f}" if cs else "—",
                            "Risque": RISK_LEVELS.get(t, "—"),
                        }
                    )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                _, btn_col = st.columns([10, 2])
                with btn_col:
                    if st.button("Supprimer", key=f"del_{pf['id']}", use_container_width=True):
                        st.session_state["user_portfolios"] = [
                            p for p in st.session_state["user_portfolios"] if p["id"] != pf["id"]
                        ]
                        st.rerun()
