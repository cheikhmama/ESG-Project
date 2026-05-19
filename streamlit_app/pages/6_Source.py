"""Page 6 — Sources de données par entreprise (traçabilité)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from datetime import date

import streamlit as st

st.set_page_config(page_title="Sources — ESG Platform", page_icon="◆", layout="wide")

from streamlit_app.utils.styling import apply_global_styles, SECTOR_COLORS
from streamlit_app.data.companies_data import COMPANIES, EMISSIONS, FINANCIAL_METRICS

apply_global_styles()

# ── Official published reports ─────────────────────────────────────────────────
OFFICIAL_REPORTS: dict[str, dict[int, str]] = {
    "SNIM": {
        2024: "https://snim.com/sites/default/files/SNIM_Rapport_activite2024_Ang.pdf",
    },
}

COMPANY_META: dict[str, dict] = {
    "SNIM": {
        "name": "Société Nationale Industrielle et Minière",
        "sector": "Mining & Metals",
        "website": "https://www.snim.com",
        "confidence": 75,
        "data_source": "Rapport d'entreprise",
        "report_years": [2024, 2023, 2022],
    },
    "SOMELEC": {
        "name": "Société Mauritanienne d'Électricité",
        "sector": "Utilities",
        "website": "https://www.somelec.mr",
        "confidence": 70,
        "data_source": "Rapport d'entreprise",
        "report_years": [2024, 2023, 2022],
    },
    "MAURITEL": {
        "name": "Mauritanienne de Télécommunications",
        "sector": "Telecommunications",
        "website": "https://www.mauritel.mr",
        "confidence": 55,
        "data_source": "Estimation sectorielle",
        "report_years": [2024, 2023, 2022],
    },
    "NEXT": {
        "name": "Next Informatique",
        "sector": "Technology",
        "website": "https://www.next.mr",
        "confidence": 60,
        "data_source": "Estimation sectorielle",
        "report_years": [2024, 2023],
    },
}


@st.cache_data(ttl=3600)
def _get_scores() -> dict:  # type: ignore[return]
    from streamlit_app.utils.scoring_engine import compute_all_scores
    return compute_all_scores()


scores_data = _get_scores()
company_scores = scores_data["company_scores"]


def _build_pdf(ticker: str, year: int) -> bytes:
    """Generate a formatted PDF estimated report and return its bytes."""
    from fpdf import FPDF

    meta = COMPANY_META[ticker]
    co = COMPANIES.get(ticker)
    em = EMISSIONS.get(ticker)
    fm = FINANCIAL_METRICS.get(ticker, {})
    cs = company_scores.get(ticker)

    # ── Latin-1 sanitizer — Helvetica only supports ISO-8859-1 ────────────
    _REPLACEMENTS = {
        "—": " - ",   # em dash —
        "–": " - ",   # en dash –
        "…": "...",   # ellipsis …
        "‘": "'",     # left single quote
        "’": "'",     # right single quote
        "“": '"',     # left double quote
        "”": '"',     # right double quote
        "₂": "2",     # subscript 2 (CO₂)
        "·": ".",     # middle dot
    }

    def _s(text: str) -> str:
        for ch, rep in _REPLACEMENTS.items():
            text = text.replace(ch, rep)
        return text.encode("latin-1", "replace").decode("latin-1")

    # ── Colour palette ─────────────────────────────────────────────────────
    INDIGO = (99, 102, 241)
    AMBER  = (245, 158, 11)
    GREEN  = (34, 197, 94)
    DARK   = (30, 41, 59)
    GRAY   = (100, 116, 139)
    LGRAY  = (241, 245, 249)
    WHITE  = (255, 255, 255)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    W = pdf.w - 36  # usable width

    # ── Header band ────────────────────────────────────────────────────────
    pdf.set_fill_color(*INDIGO)
    pdf.rect(0, 0, pdf.w, 42, "F")

    pdf.set_xy(18, 7)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*WHITE)
    name_safe = _s(meta["name"])
    pdf.cell(W - 30, 8, name_safe, ln=True)

    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(210, 212, 255)
    pdf.cell(W - 30, 6, _s(f"Ticker : {ticker}   |   Exercice {year}   |   {meta['sector']}"), ln=True)

    pdf.set_xy(pdf.w - 52, 9)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(34, 6, "RAPPORT ESTIME", border=1, align="C")
    pdf.set_xy(pdf.w - 52, 17)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(34, 5, _s(f"Genere le {date.today().isoformat()}"), align="C")

    pdf.ln(22)

    # ── Helper closures ────────────────────────────────────────────────────
    def section(title: str) -> None:
        pdf.ln(4)
        pdf.set_fill_color(*LGRAY)
        pdf.set_text_color(*INDIGO)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(W, 7, _s(f"  {title.upper()}"), fill=True, ln=True)
        pdf.ln(2)

    def row(label: str, value: str, shade: bool = False) -> None:
        if shade:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(*WHITE)
        pdf.set_text_color(*GRAY)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(W * 0.45, 6, _s(f"  {label}"), fill=True)
        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(W * 0.55, 6, _s(value), fill=True, ln=True)

    def kpi_trio(items: list[tuple[str, str, tuple]]) -> None:
        box_w = W / len(items)
        start_x = 18.0
        top_y = pdf.get_y()
        for i, (label, value, color) in enumerate(items):
            x = start_x + i * box_w
            pdf.set_xy(x, top_y)
            pdf.set_fill_color(245, 247, 255)
            pdf.rect(x, top_y, box_w - 2, 18, "F")
            pdf.set_xy(x + 2, top_y + 2)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*color)
            pdf.cell(box_w - 4, 7, _s(value), align="C")
            pdf.set_xy(x + 2, top_y + 10)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*GRAY)
            pdf.cell(box_w - 4, 5, _s(label), align="C")
        pdf.set_y(top_y + 22)

    # ── Warning box ────────────────────────────────────────────────────────
    pdf.set_fill_color(255, 251, 235)
    pdf.set_draw_color(*AMBER)
    pdf.set_line_width(0.5)
    pdf.rect(18, pdf.get_y(), W, 16, "FD")
    pdf.set_xy(20, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*AMBER)
    pdf.cell(W - 4, 5, "AVERTISSEMENT - RAPPORT ESTIME", ln=True)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*DARK)
    disclaimer = _s(
        "Ce rapport est genere a partir des donnees collectees sur le site officiel "
        "de l'entreprise et des indicateurs analyses par la Plateforme ESG Mauritanie. "
        "Il ne remplace pas un rapport officiel publie par l'entreprise."
    )
    pdf.multi_cell(W - 4, 4.5, disclaimer)
    pdf.ln(4)

    # ── General info ───────────────────────────────────────────────────────
    section("Informations generales")
    if co:
        rows_info = [
            ("Societe", name_safe),
            ("Secteur", meta["sector"]),
            ("Pays", "Mauritanie"),
            ("ISIN", _s(co.isin)),
            ("Site web", meta["website"]),
            ("Source des donnees", meta["data_source"]),
            ("Niveau de fiabilite", f"{meta['confidence']}%"),
        ]
        for j, (lbl, val) in enumerate(rows_info):
            row(lbl, val, shade=(j % 2 == 0))

    # ── Financial data ─────────────────────────────────────────────────────
    if fm:
        section("Donnees financieres")
        kpi_trio([
            (f"Capitalisation ({year})",
             f"${fm.get('market_cap', 0)/1e6:.0f}M",
             INDIGO),
            ("Chiffre d'affaires",
             f"${fm.get('revenue', 0)/1e6:.0f}M",
             INDIGO),
            ("Effectif",
             f"{int(fm.get('employees', 0)):,}",
             INDIGO),
        ])

    # ── Carbon footprint ───────────────────────────────────────────────────
    if em:
        section("Empreinte carbone  (tCO2e)")
        total_em = em.scope_1 + em.scope_2 + em.total_scope_3
        rows_em = [
            ("Scope 1 - Emissions directes",      f"{em.scope_1:,.0f} tCO2e"),
            ("Scope 2 - Energie indirecte",        f"{em.scope_2:,.0f} tCO2e"),
            ("Scope 3 - Chaine de valeur",         f"{em.total_scope_3:,.0f} tCO2e"),
            ("Total toutes sources",               f"{total_em:,.0f} tCO2e"),
            ("Source",                             em.source),
            ("Niveau de confiance",                f"{em.confidence * 100:.0f}%"),
        ]
        for j, (lbl, val) in enumerate(rows_em):
            bold_total = (lbl == "Total toutes sources")
            if j % 2 == 0:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(*WHITE)
            pdf.set_text_color(*GRAY)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(W * 0.55, 6, f"  {lbl}", fill=True)
            pdf.set_text_color(*GREEN if bold_total else DARK)
            pdf.set_font("Helvetica", "B" if bold_total else "B", 8)
            pdf.cell(W * 0.45, 6, val, fill=True, ln=True)

    # ── ESG scores ─────────────────────────────────────────────────────────
    if cs:
        section("Scores ESG  (Methodologie Default ESG v1.0.0)")
        env = cs.pillar("environment")
        soc = cs.pillar("social")
        gov = cs.pillar("governance")
        kpi_trio([
            ("Environnement (40%)",
             f"{env.score:.1f}/100" if env else "-",
             (34, 197, 94)),
            ("Social (30%)",
             f"{soc.score:.1f}/100" if soc else "-",
             (59, 130, 246)),
            ("Gouvernance (30%)",
             f"{gov.score:.1f}/100" if gov else "-",
             (139, 92, 246)),
        ])
        pdf.set_fill_color(*INDIGO)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(W, 9, _s(f"  Score Global ESG : {cs.final_score:.1f} / 100"), fill=True, ln=True)

    # ── Methodology footer ─────────────────────────────────────────────────
    pdf.ln(6)
    section("Methodologie & licence")
    meth_rows = [
        ("Ponderations piliers", "Environnement 40%  |  Social 30%  |  Gouvernance 30%"),
        ("Donnees manquantes",   "Mediane sectorielle (configurable YAML)"),
        ("Normalisation",        "z-score puis clip [0, 100]"),
        ("Licence",              "Apache 2.0 - Open Source"),
        ("Version methodologie", "Default ESG v1.0.0"),
        ("Date de generation",   date.today().isoformat()),
    ]
    for j, (lbl, val) in enumerate(meth_rows):
        row(lbl, val, shade=(j % 2 == 0))

    # ── Page footer ────────────────────────────────────────────────────────
    pdf.set_y(-14)
    pdf.set_draw_color(*LGRAY)
    pdf.line(18, pdf.get_y(), pdf.w - 18, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(W / 2, 5, "Plateforme ESG Mauritanie - Open Source  |  Apache 2.0")
    pdf.cell(W / 2, 5, f"Page {pdf.page_no()}", align="R")

    return bytes(pdf.output())


# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Sources</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Traçabilité des données — rapport officiel ou rapport estimé toujours disponible.</p>",
    unsafe_allow_html=True,
)

search = st.text_input(" ", placeholder="Recherche", key="src_search", label_visibility="collapsed")

filtered = {
    k: v for k, v in COMPANY_META.items()
    if not search
    or search.lower() in v["name"].lower()
    or search.lower() in k.lower()
    or search.lower() in v["sector"].lower()
}

st.caption(f"**{len(filtered)}** entreprise(s)")

# ── Company list ───────────────────────────────────────────────────────────────
for ticker, meta in filtered.items():
    sk = SECTOR_COLORS.get(meta["sector"], "#6366f1")
    conf = meta["confidence"]
    conf_color = "#22c55e" if conf >= 70 else "#f59e0b" if conf >= 55 else "#ef4444"

    with st.expander(f"{meta['name']}  ({ticker})  ·  {meta['sector']}", expanded=False):

        top_l, top_r = st.columns([4, 1])
        with top_l:
            st.markdown(
                f"<div style='display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:18px'>"
                f"<span style='background:{sk}18;color:{sk};padding:3px 10px;"
                f"border-radius:5px;font-size:0.71rem;font-weight:600'>{meta['sector']}</span>"
                f"<a href='{meta['website']}' target='_blank' "
                f"style='color:#6366f1;font-size:0.83rem;font-weight:600;text-decoration:none'>"
                f"Site officiel &#8599;</a>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with top_r:
            st.markdown(
                f"<div style='text-align:right'>"
                f"<div style='font-size:0.58rem;color:#475569;text-transform:uppercase;"
                f"letter-spacing:0.1em;font-weight:600;margin-bottom:3px'>Fiabilité</div>"
                f"<div style='font-size:1.25rem;font-weight:800;color:{conf_color}'>{conf}%</div>"
                f"<div style='font-size:0.67rem;color:#475569;margin-top:1px'>{meta['data_source']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        _raw_year = st.selectbox(
            "Année du rapport",
            meta["report_years"],
            index=0,
            key=f"src_{ticker}_year",
        )
        sel_year: int = _raw_year if _raw_year is not None else meta["report_years"][0]

        has_official = ticker in OFFICIAL_REPORTS and sel_year in OFFICIAL_REPORTS[ticker]
        col_off, col_est = st.columns(2)

        # ── Rapport officiel ──────────────────────────────────────────────
        with col_off:
            st.markdown(
                "<div style='font-size:0.6rem;color:#22c55e;text-transform:uppercase;"
                "letter-spacing:0.13em;font-weight:700;margin-bottom:10px;"
                "padding-bottom:5px;border-bottom:1px solid rgba(34,197,94,0.2)'>"
                "Rapport Officiel</div>",
                unsafe_allow_html=True,
            )
            if has_official:
                url = OFFICIAL_REPORTS[ticker][sel_year]
                st.markdown(
                    f"<a href='{url}' target='_blank' "
                    f"style='display:flex;align-items:center;justify-content:space-between;"
                    f"gap:10px;background:rgba(34,197,94,0.07);"
                    f"border:1px solid rgba(34,197,94,0.25);border-radius:8px;"
                    f"padding:12px 14px;text-decoration:none;color:#e2e8f0;"
                    f"font-size:0.83rem;font-weight:600'>"
                    f"<span style='display:flex;align-items:center;gap:8px'>"
                    f"<span>&#128196;</span>Rapport Annuel {sel_year}</span>"
                    f"<span style='color:#22c55e;font-size:0.75rem;white-space:nowrap'>PDF &#8599;</span>"
                    f"</a>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='font-size:0.7rem;color:#475569;margin-top:6px;padding:0 4px'>"
                    "Publié directement par l'entreprise.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:rgba(255,255,255,0.02);"
                    f"border:1px solid rgba(255,255,255,0.07);border-radius:8px;"
                    f"padding:12px 14px;color:#475569;font-size:0.82rem'>"
                    f"Non publié pour {int(sel_year)}.<br>"
                    f"<span style='font-size:0.71rem;color:#334155;margin-top:4px;display:block'>"
                    f"L'entreprise n'a pas diffusé de rapport officiel pour cet exercice.</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # ── Rapport estimé — PDF ──────────────────────────────────────────
        with col_est:
            st.markdown(
                "<div style='font-size:0.6rem;color:#f59e0b;text-transform:uppercase;"
                "letter-spacing:0.13em;font-weight:700;margin-bottom:10px;"
                "padding-bottom:5px;border-bottom:1px solid rgba(245,158,11,0.2)'>"
                "Rapport Estimé — Plateforme</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='background:rgba(245,158,11,0.05);"
                f"border:1px solid rgba(245,158,11,0.2);border-radius:8px;"
                f"padding:12px 14px;font-size:0.82rem;color:#cbd5e1;margin-bottom:10px'>"
                f"<div style='font-weight:600;color:#e2e8f0;margin-bottom:4px'>"
                f"Rapport {sel_year} — Données plateforme</div>"
                f"Généré à partir des données du site officiel et des indicateurs "
                f"analysés par la plateforme. Format PDF.</div>",
                unsafe_allow_html=True,
            )
            pdf_bytes = _build_pdf(ticker, sel_year)
            st.download_button(
                label=f"Télécharger le rapport estimé {sel_year} (PDF)",
                data=pdf_bytes,
                file_name=f"rapport_estime_{ticker}_{sel_year}.pdf",
                mime="application/pdf",
                key=f"dl_{ticker}_{sel_year}",
                use_container_width=True,
            )
