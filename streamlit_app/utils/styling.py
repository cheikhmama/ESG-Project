"""Shared styling utilities — no emojis, professional financial-platform look."""

from __future__ import annotations

import streamlit as st

SECTOR_COLORS: dict[str, str] = {
    "Mining & Metals":    "#ef4444",
    "Utilities":          "#f97316",
    "Telecommunications": "#3b82f6",
    "Technology":         "#22c55e",
}

RISK_COLORS: dict[str, str] = {
    "High":   "#ef4444",
    "Medium": "#f59e0b",
    "Low":    "#22c55e",
}

PILLAR_COLORS: dict[str, str] = {
    "environment": "#22c55e",
    "social":      "#3b82f6",
    "governance":  "#8b5cf6",
}

_COUNTRY_NAMES: dict[str, str] = {
    "MR": "Mauritanie",
    "MA": "Maroc",
    "SN": "Sénégal",
    "CI": "Côte d'Ivoire",
    "FR": "France",
    "US": "États-Unis",
    "GB": "Royaume-Uni",
    "DE": "Allemagne",
}


def country_name(code: str) -> str:
    """Return the French country name for an ISO 3166-1 alpha-2 code."""
    return _COUNTRY_NAMES.get(code.upper(), code)


def score_color(score: float) -> str:
    if score >= 70:
        return "#22c55e"
    if score >= 50:
        return "#f59e0b"
    return "#ef4444"


def score_label(score: float) -> str:
    if score >= 70:
        return "Élevé"
    if score >= 50:
        return "Moyen"
    return "Faible"


def apply_global_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide Streamlit chrome — keep sidebar toggle visible */
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stMainMenuButton"] { display: none !important; }
[data-testid="stAppHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}
/* Sidebar expand button (when sidebar is collapsed) */
[data-testid="stExpandSidebarButton"] {
    visibility: visible !important;
    display: flex !important;
}
/* Sidebar collapse button (inside sidebar) */
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    display: flex !important;
}

/* App background */
.stApp {
    background: linear-gradient(145deg, #0c1321 0%, #111827 50%, #0c1321 100%);
    color: #e2e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0c1321 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] p {
    color: #64748b;
    font-size: 0.78rem;
}

/* Glass card */
.esg-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 16px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.esg-card:hover {
    border-color: rgba(99,102,241,0.3);
    box-shadow: 0 4px 20px rgba(99,102,241,0.08);
}

/* KPI box */
.kpi-box {
    background: rgba(99,102,241,0.07);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 14px;
    padding: 22px 18px;
    text-align: center;
    height: 100%;
}
.kpi-value {
    font-size: 1.95rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin-bottom: 2px;
}
.kpi-label {
    font-size: 0.64rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
    margin-top: 6px;
}
.kpi-sub {
    font-size: 0.73rem;
    color: #475569;
    margin-top: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Section header — uppercase label with left accent */
.section-header {
    font-size: 0.63rem;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin: 36px 0 16px 0;
    padding: 0 0 8px 10px;
    border-bottom: 1px solid rgba(99,102,241,0.15);
    border-left: 3px solid #6366f1;
}

/* Pill / badge */
.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    line-height: 1.6;
}

/* Buttons — neutral ghost style (like download / upload buttons) */
.stButton > button {
    background: rgba(255,255,255,0.05);
    color: #e2e8f0;
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 8px 18px;
    letter-spacing: 0.01em;
    transition: all 0.15s;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.09);
    border-color: rgba(255,255,255,0.22);
}
.stButton > button:focus {
    box-shadow: 0 0 0 2px rgba(99,102,241,0.4);
    outline: none;
}
/* Primary type — purple gradient accent */
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 2px 12px rgba(99,102,241,0.3) !important;
}
[data-testid="baseButton-primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 18px rgba(99,102,241,0.45) !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.72rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
}

/* Tabs */
[data-testid="stTabs"] button {
    font-weight: 600;
    font-size: 0.84rem;
    color: #64748b;
    border-bottom: 2px solid transparent;
    padding: 10px 18px;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #6366f1;
    border-bottom-color: #6366f1;
}
[data-testid="stTabs"] button:hover {
    color: #94a3b8;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06) !important;
}

/* Expander */
details {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}
details > summary {
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    padding: 14px 18px !important;
    font-size: 0.9rem !important;
    list-style: none;
}
details[open] > summary {
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}

/* Inputs */
.stTextInput input, .stNumberInput input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border: 1px dashed rgba(99,102,241,0.35);
    border-radius: 10px;
    padding: 8px;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 10px;
    border: none;
}

/* Divider */
hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 24px 0;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(99,102,241,0.3);
    border-radius: 3px;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, sublabel: str = "") -> None:
    sub = f"<div class='kpi-sub'>{sublabel}</div>" if sublabel else ""
    st.markdown(
        f"<div class='kpi-box'>"
        f"<div class='kpi-value'>{value}</div>"
        f"<div class='kpi-label'>{label}</div>"
        f"{sub}"
        f"</div>",
        unsafe_allow_html=True,
    )


def company_card(
    ticker: str,
    name: str,
    sector: str,
    score: float,
    carbon: float,
    risk: str,
    mc: float,
) -> None:
    sc = score_color(score)
    rc = RISK_COLORS.get(risk, "#94a3b8")
    sk = SECTOR_COLORS.get(sector, "#6366f1")
    sl = score_label(score)
    st.markdown(
        f"""
        <div class="esg-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
                <div style="flex:1;min-width:0">
                    <div style="font-size:1.05rem;font-weight:700;color:#f1f5f9;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{name}</div>
                    <div style="margin-top:7px;display:flex;gap:5px;flex-wrap:wrap">
                        <span style="background:{sk}18;color:{sk};padding:2px 9px;
                                     border-radius:5px;font-size:0.71rem;font-weight:600">{sector}</span>
                        <span style="background:{rc}15;color:{rc};padding:2px 9px;
                                     border-radius:5px;font-size:0.71rem;font-weight:600">Risque {risk}</span>
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0">
                    <div style="font-size:1.85rem;font-weight:800;color:{sc};line-height:1">{score:.1f}</div>
                    <div style="font-size:0.6rem;color:{sc};opacity:0.75;text-transform:uppercase;
                                letter-spacing:0.06em;margin-top:1px">{sl}</div>
                </div>
            </div>
            <div style="display:flex;gap:28px;margin-top:14px;padding-top:12px;
                        border-top:1px solid rgba(255,255,255,0.05)">
                <div>
                    <div style="font-size:0.6rem;color:#475569;text-transform:uppercase;
                                letter-spacing:0.09em;font-weight:600">Empreinte Carbone</div>
                    <div style="font-weight:600;color:#cbd5e1;font-size:0.88rem;margin-top:3px">{carbon/1000:.1f}K tCO₂e</div>
                </div>
                <div>
                    <div style="font-size:0.6rem;color:#475569;text-transform:uppercase;
                                letter-spacing:0.09em;font-weight:600">Capitalisation</div>
                    <div style="font-weight:600;color:#cbd5e1;font-size:0.88rem;margin-top:3px">${mc/1e6:.0f}M</div>
                </div>
                <div style="margin-left:auto">
                    <div style="font-size:0.6rem;color:#475569;text-transform:uppercase;
                                letter-spacing:0.09em;font-weight:600">Symbole</div>
                    <div style="font-weight:700;color:#6366f1;font-size:0.88rem;margin-top:3px">{ticker}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
