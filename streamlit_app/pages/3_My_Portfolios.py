"""Page 3 — Gestion des portefeuilles personnels."""

import json
import uuid
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Mes Portefeuilles — ESG Platform", page_icon="◆", layout="wide")

from esg_data.fixtures import COMPANIES, RISK_LEVELS
from streamlit_app.utils.styling import apply_global_styles

apply_global_styles()


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
    # CSS spécifique à cet onglet
    st.markdown(
        """
        <style>
        /* Cacher les boutons +/- du champ montant */
        [data-testid="stNumberInputStepUp"],
        [data-testid="stNumberInputStepDown"] { display: none !important; }

        /* Bouton "+" — sélecteur sibling correct pour Streamlit */
        .element-container:has(.btn-add) + .element-container button,
        .element-container:has(.btn-add) ~ .element-container:first-of-type button {
            background: rgba(99,102,241,0.12) !important;
            border: 1.5px solid #6366f1 !important;
            color: #6366f1 !important;
            border-radius: 50% !important;
            width: 34px !important;
            height: 34px !important;
            min-height: unset !important;
            padding: 0 !important;
            font-size: 1.3rem !important;
            font-weight: 300 !important;
            line-height: 1 !important;
            transition: all 0.18s ease !important;
        }
        .element-container:has(.btn-add) + .element-container button:hover,
        .element-container:has(.btn-add) + .element-container button:focus,
        .element-container:has(.btn-add) + .element-container button:active {
            background: #6366f1 !important;
            border-color: #6366f1 !important;
            color: white !important;
            transform: scale(1.1) !important;
            box-shadow: 0 0 0 4px rgba(99,102,241,0.25), 0 4px 16px rgba(99,102,241,0.4) !important;
        }

        /* Bouton "×" — sélecteur sibling correct pour Streamlit */
        .element-container:has(.btn-rm) + .element-container button {
            background: transparent !important;
            border: 1px solid rgba(239,68,68,0.4) !important;
            color: #ef4444 !important;
            border-radius: 50% !important;
            width: 28px !important;
            height: 28px !important;
            min-height: unset !important;
            padding: 0 !important;
            font-size: 0.8rem !important;
            opacity: 0.75;
            transition: all 0.15s ease !important;
        }
        .element-container:has(.btn-rm) + .element-container button:hover {
            background: rgba(239,68,68,0.1) !important;
            border-color: #ef4444 !important;
            opacity: 1;
            transform: scale(1.1) !important;
            box-shadow: 0 0 0 3px rgba(239,68,68,0.2) !important;
        }

        /* Badge devise — bouton cycle compact USD/EUR/MRU */
        .element-container:has(.cur-badge) + .element-container button {
            background: rgba(99,102,241,0.08) !important;
            border: 1px solid rgba(99,102,241,0.25) !important;
            color: #818cf8 !important;
            border-radius: 6px !important;
            font-size: 0.7rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.06em !important;
            padding: 0 !important;
            min-height: 38px !important;
            height: 38px !important;
            width: 100% !important;
            transition: all 0.15s !important;
        }
        .element-container:has(.cur-badge) + .element-container button:hover {
            background: rgba(99,102,241,0.18) !important;
            border-color: rgba(99,102,241,0.5) !important;
            color: #a5b4fc !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Session state ──────────────────────────────────────────────────────────
    if "pos_ids" not in st.session_state:
        st.session_state["pos_ids"] = [0]
    if "pos_next_id" not in st.session_state:
        st.session_state["pos_next_id"] = 1

    # ── Nom du portefeuille ────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;color:#475569;text-transform:uppercase;"
        "letter-spacing:0.12em;font-weight:700;margin-bottom:6px'>Nom du portefeuille</div>",
        unsafe_allow_html=True,
    )
    portfolio_name = st.text_input(
        "Nom",
        placeholder="Ex : Portefeuille ESG Mauritanie 2026",
        key="cp_name",
        label_visibility="collapsed",
    )

    # ── Colonnes partagées (header + rows utilisent les mêmes proportions) ──────
    _COLS = [0.28, 3, 1.8, 3, 0.4]  # badge | société | secteur | montant+devise | ×
    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

    # Header "Positions" + bouton "+" — layout indépendant, titre à gauche / + à droite
    n = len(st.session_state["pos_ids"])
    h_title, h_spacer, h_add = st.columns([6, 3, 1])
    with h_title:
        st.markdown(
            f"<div style='font-size:1rem;font-weight:700;color:#e2e8f0;"
            f"letter-spacing:-0.01em;display:flex;align-items:center;gap:10px;padding-top:14px'>"
            f"Positions"
            f"<span style='font-size:0.68rem;font-weight:700;color:#6366f1;"
            f"background:rgba(99,102,241,0.14);padding:2px 10px;border-radius:20px'>"
            f"{n}</span></div>",
            unsafe_allow_html=True,
        )
    with h_add:
        if n < len(COMPANIES):
            st.markdown(
                "<div class='btn-add' style='display:flex;justify-content:flex-end;padding-top:4px;padding-bottom:6px'>",
                unsafe_allow_html=True,
            )
            if st.button("+", key="add_pos", help="Ajouter une position"):
                st.session_state["pos_ids"].append(st.session_state["pos_next_id"])
                st.session_state["pos_next_id"] += 1
            st.markdown("</div>", unsafe_allow_html=True)

    # Libellés colonnes — même grille
    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    lb, lco, lsec, linv, lrm = st.columns(_COLS)
    for col, label in zip([lco, lsec, linv], ["Société", "Secteur", "Montant / Devise"]):
        col.markdown(
            f"<div style='font-size:0.62rem;color:#475569;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.1em'>{label}</div>",
            unsafe_allow_html=True,
        )

    # ── Lignes de positions ────────────────────────────────────────────────────
    _PLACEHOLDER = "— Choisir une société —"
    company_options = [_PLACEHOLDER] + [co.name for co in COMPANIES.values()]
    holdings_data = []
    to_remove = None

    for i, pid in enumerate(st.session_state["pos_ids"]):
        c_num, c_co, c_sec, c_inv, c_rm = st.columns(_COLS)

        with c_num:
            st.markdown(
                f"<div style='width:26px;height:26px;border-radius:50%;"
                f"background:linear-gradient(135deg,#6366f1,#8b5cf6);"
                f"display:flex;align-items:center;justify-content:center;"
                f"font-size:0.72rem;font-weight:700;color:white;margin-top:8px'>"
                f"{i + 1}</div>",
                unsafe_allow_html=True,
            )
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
                st.markdown('<div class="cur-badge"></div>', unsafe_allow_html=True)
                if st.button(
                    _cur_val,
                    key=f"pos_{pid}_cur_btn",
                    help="Cliquer pour changer la devise (USD → EUR → MRU)",
                ):
                    _idx = _CURRENCIES.index(_cur_val)
                    st.session_state[_cur_key] = _CURRENCIES[(_idx + 1) % len(_CURRENCIES)]
                currency = st.session_state[_cur_key]
        with c_rm:
            if len(st.session_state["pos_ids"]) > 1:
                st.markdown('<div class="btn-rm">', unsafe_allow_html=True)
                if st.button("×", key=f"pos_{pid}_remove", help="Supprimer"):
                    to_remove = pid
                st.markdown("</div>", unsafe_allow_html=True)

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
        st.markdown(
            "<div style='margin-top:20px;font-size:0.65rem;color:#475569;"
            "text-transform:uppercase;letter-spacing:0.12em;font-weight:700;"
            "margin-bottom:10px'>Répartition</div>",
            unsafe_allow_html=True,
        )
        preview_cols = st.columns(len(holdings_data))
        for col, h in zip(preview_cols, holdings_data):
            pct = h["investment_value"] / total_preview * 100
            col.markdown(
                f"<div style='text-align:center;background:rgba(99,102,241,0.07);"
                f"border:1px solid rgba(99,102,241,0.15);"
                f"border-radius:10px;padding:10px 6px'>"
                f"<div style='font-size:1.1rem;font-weight:800;color:#6366f1'>{pct:.1f}%</div>"
                f"<div style='font-size:0.65rem;color:#64748b;margin-top:2px'>"
                f"{h['company_name'].split()[0]}</div></div>",
                unsafe_allow_html=True,
            )

    # ── Bouton créer ───────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
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
                st.markdown(
                    f"""
                    <div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);
                                border-radius:10px;padding:16px 20px;margin-top:12px">
                        <div style="color:#22c55e;font-weight:700;margin-bottom:8px">
                            Portefeuille « {
                        new_port["name"]
                    } » créé — consultez l'onglet Mes portefeuilles
                        </div>
                        <div style="font-size:0.83rem;color:#94a3b8;line-height:1.9">
                            {len(port_holdings)} position(s) &nbsp;·&nbsp;
                            Capital total : <b style="color:#e2e8f0">${total_inv:,.0f}</b><br>
                            {
                        "".join(
                            f"<span style='margin-right:14px'>{h['company_name'].split()[0]} "
                            f"<b style='color:#6366f1'>{h['weight'] * 100:.1f}%</b></span>"
                            for h in port_holdings
                        )
                    }
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ── TAB 2 — Import ─────────────────────────────────────────────────────────────
with tab_import:
    st.markdown(
        "<div class='section-header'>Importer un portefeuille</div>", unsafe_allow_html=True
    )

    # Format card + template download
    col_info, col_dl = st.columns([3, 1])
    with col_info:
        st.markdown(
            "<div style='background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);"
            "border-radius:10px;padding:14px 18px;font-size:0.83rem;color:#94a3b8'>"
            "<div style='font-weight:600;color:#e2e8f0;margin-bottom:6px'>Champs requis</div>"
            "<code style='color:#6366f1'>company_name</code> &nbsp;"
            "<code style='color:#6366f1'>isin_code</code> &nbsp;"
            "<code style='color:#6366f1'>sector</code> &nbsp;"
            "<code style='color:#6366f1'>investment_value</code>"
            "</div>",
            unsafe_allow_html=True,
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

    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)

    # ── File picker ────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;color:#475569;text-transform:uppercase;"
        "letter-spacing:0.12em;font-weight:700;margin-bottom:6px'>Fichier</div>",
        unsafe_allow_html=True,
    )
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
                matched: list[dict[str, object]] = []
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

                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:14px'>"
                        f"<span style='font-size:0.65rem;color:#22c55e;text-transform:uppercase;"
                        f"letter-spacing:0.12em;font-weight:700'>Aperçu</span>"
                        f"<span style='font-size:0.75rem;color:#475569'>"
                        f"{len(port_holdings)} position(s) &nbsp;·&nbsp; Capital : "
                        f"<b style='color:#e2e8f0'>${total_inv:,.0f}</b></span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
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
                    st.markdown(
                        "<div style='font-size:0.65rem;color:#475569;text-transform:uppercase;"
                        "letter-spacing:0.12em;font-weight:700;margin:18px 0 6px'>Nom du portefeuille</div>",
                        unsafe_allow_html=True,
                    )
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
                        st.markdown(
                            f"<div style='background:rgba(34,197,94,0.08);"
                            f"border:1px solid rgba(34,197,94,0.25);border-radius:10px;"
                            f"padding:16px 20px;margin-top:12px'>"
                            f"<div style='color:#22c55e;font-weight:700;margin-bottom:4px'>"
                            f"Portefeuille « {import_name.strip()} » créé</div>"
                            f"<div style='font-size:0.82rem;color:#94a3b8'>"
                            f"Consultez l'onglet <b style='color:#e2e8f0'>Mes portefeuilles</b> "
                            f"pour le visualiser et l'analyser.</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

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
