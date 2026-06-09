"""PDF report builder for the ESG platform's source-traceability page."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

from esg_data.fixtures import COMPANIES, EMISSIONS, FINANCIAL_METRICS
from esg_data.fixtures.sources import COMPANY_META
from esg_data.reporting.text_report import build_text_report


def build_pdf(ticker: str, year: int) -> bytes:
    """Generate a formatted PDF estimate report and return its bytes."""
    meta = COMPANY_META[ticker]
    co = COMPANIES.get(ticker)
    em = EMISSIONS.get(ticker)
    fm = FINANCIAL_METRICS.get(ticker, {})
    cs = None

    # Build a minimal PDF report with layout and branding matching the old page.
    _REPLACEMENTS: dict[str, str] = {
        "—": " - ",
        "–": " - ",
        "…": "...",
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "₂": "2",
        "·": ".",
    }

    def _s(text: str) -> str:
        for ch, rep in _REPLACEMENTS.items():
            text = text.replace(ch, rep)
        return text.encode("latin-1", "replace").decode("latin-1")

    INDIGO = (99, 102, 241)
    AMBER = (245, 158, 11)
    GREEN = (34, 197, 94)
    DARK = (30, 41, 59)
    GRAY = (100, 116, 139)
    LGRAY = (241, 245, 249)
    WHITE = (255, 255, 255)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)
    W = pdf.w - 36

    pdf.set_fill_color(*INDIGO)
    pdf.rect(0, 0, pdf.w, 42, "F")

    pdf.set_xy(18, 7)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*WHITE)
    pdf.cell(W - 30, 8, _s(meta["name"]), ln=True)

    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(210, 212, 255)
    pdf.cell(
        W - 30,
        6,
        _s(f"Ticker : {ticker}   |   Exercice {year}   |   {meta['sector']}"),
        ln=True,
    )

    pdf.set_xy(pdf.w - 52, 9)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(34, 6, "RAPPORT ESTIME", border=1, align="C")
    pdf.set_xy(pdf.w - 52, 17)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(34, 5, _s(f"Genere le {date.today().isoformat()}"), align="C")

    pdf.ln(22)

    def section(title: str) -> None:
        pdf.ln(4)
        pdf.set_fill_color(*LGRAY)
        pdf.set_text_color(*INDIGO)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(W, 7, _s(f"  {title.upper()}"), fill=True, ln=True)
        pdf.ln(2)

    def row(label: str, value: str, shade: bool = False) -> None:
        pdf.set_fill_color(248, 250, 252 if shade else WHITE)
        pdf.set_text_color(*GRAY)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(W * 0.45, 6, _s(f"  {label}"), fill=True)
        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(W * 0.55, 6, _s(value), fill=True, ln=True)

    def kpi_trio(items: list[tuple[str, str, tuple[int, int, int]]]) -> None:
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

    section("Informations generales")
    if co:
        rows_info = [
            ("Societe", _s(meta["name"])),
            ("Secteur", meta["sector"]),
            ("Pays", "Mauritanie"),
            ("ISIN", _s(co.isin)),
            ("Site web", meta["website"]),
            ("Source des donnees", meta["data_source"]),
            ("Niveau de fiabilite", f"{meta['confidence']}%"),
        ]
        for j, (lbl, val) in enumerate(rows_info):
            row(lbl, val, shade=(j % 2 == 0))

    if fm:
        section("Donnees financieres")
        kpi_trio(
            [
                ("Capitalisation (" + str(year) + ")", f"${fm.get('market_cap', 0) / 1e6:.0f}M", INDIGO),
                ("Chiffre d'affaires", f"${fm.get('revenue', 0) / 1e6:.0f}M", INDIGO),
                ("Effectif", f"{int(fm.get('employees', 0)):,}", INDIGO),
            ]
        )

    if em:
        section("Empreinte carbone  (tCO2e)")
        total_em = em.scope_1 + em.scope_2 + em.total_scope_3
        rows_em = [
            ("Scope 1 - Emissions directes", f"{em.scope_1:,.0f} tCO2e"),
            ("Scope 2 - Energie indirecte", f"{em.scope_2:,.0f} tCO2e"),
            ("Scope 3 - Chaine de valeur", f"{em.total_scope_3:,.0f} tCO2e"),
            ("Total toutes sources", f"{total_em:,.0f} tCO2e"),
            ("Source", em.source),
            ("Niveau de confiance", f"{em.confidence * 100:.0f}%"),
        ]
        for j, (lbl, val) in enumerate(rows_em):
            row(lbl, val, shade=(j % 2 == 0))

    if cs:
        section("Scores ESG  (Methodologie Default ESG v1.0.0)")
        env = cs.pillar("environment")
        soc = cs.pillar("social")
        gov = cs.pillar("governance")
        kpi_trio(
            [
                ("Environnement (40%)", f"{env.score:.1f}/100" if env else "-", GREEN),
                ("Social (30%)", f"{soc.score:.1f}/100" if soc else "-", INDIGO),
                ("Gouvernance (30%)", f"{gov.score:.1f}/100" if gov else "GREEN"),
            ]
        )
        pdf.set_fill_color(*INDIGO)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(W, 9, _s(f"  Score Global ESG : {cs.final_score:.1f} / 100"), fill=True, ln=True)

    pdf.ln(6)
    section("Methodologie & licence")
    meth_rows = [
        ("Ponderations piliers", "Environnement 40%  |  Social 30%  |  Gouvernance 30%"),
        ("Donnees manquantes", "Mediane sectorielle (configurable YAML)"),
        ("Normalisation", "z-score puis clip [0, 100]"),
        ("Licence", "Apache 2.0 - Open Source"),
        ("Version methodologie", "Default ESG v1.0.0"),
        ("Date de generation", date.today().isoformat()),
    ]
    for j, (lbl, val) in enumerate(meth_rows):
        row(lbl, val, shade=(j % 2 == 0))

    pdf.set_y(-14)
    pdf.set_draw_color(*LGRAY)
    pdf.line(18, pdf.get_y(), pdf.w - 18, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(W / 2, 5, "Plateforme ESG Mauritanie - Open Source  |  Apache 2.0")
    pdf.cell(W / 2, 5, f"Page {pdf.page_no()}", align="R")

    return bytes(pdf.output())
