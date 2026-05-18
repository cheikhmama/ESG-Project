"""Page 6 — Provenance, méthodologie et référentiels."""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Source — ESG Platform", page_icon="◆", layout="wide")

from streamlit_app.utils.styling import apply_global_styles

apply_global_styles()


@st.cache_data(ttl=3600)
def _get_hash() -> str:
    from streamlit_app.utils.scoring_engine import compute_all_scores
    return str(compute_all_scores()["methodology_hash"])


methodology_hash = _get_hash()

st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;"
    "margin-bottom:2px'>Source et Provenance</h1>"
    "<p style='color:#475569;font-size:0.88rem;margin-bottom:28px'>"
    "Traçabilité complète de la méthodologie, des données et des référentiels appliqués.</p>",
    unsafe_allow_html=True,
)

# ── Publication metadata ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Informations de Publication</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="esg-card">
            <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:700;margin-bottom:16px">Responsabilité</div>
            <table style="width:100%;font-size:0.84rem;border-collapse:collapse">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b;width:48%">Direction Responsable</td>
                    <td style="color:#e2e8f0;font-weight:500">Direction du Développement Durable</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b">Directeur Signataire</td>
                    <td style="color:#e2e8f0;font-weight:500">Directeur RSE</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b">Date de Publication</td>
                    <td style="color:#e2e8f0;font-weight:500">15 / 04 / 2026</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b">N° de Publication Légale</td>
                    <td style="color:#6366f1;font-weight:600;font-family:monospace">CSRD-2025-MR0001</td>
                </tr>
                <tr>
                    <td style="padding:10px 0;color:#64748b">Enregistrement Système</td>
                    <td style="color:#e2e8f0;font-weight:500">18 / 05 / 2026 · 10:23 UTC</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="esg-card">
            <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:700;margin-bottom:16px">Empreinte Numérique</div>
            <table style="width:100%;font-size:0.84rem;border-collapse:collapse">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b;width:48%">Empreinte Méthodologie</td>
                    <td style="color:#22c55e;font-family:monospace;font-size:0.72rem;
                                word-break:break-all">{methodology_hash}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b">Version</td>
                    <td style="color:#e2e8f0;font-weight:500">Default ESG v1.0.0</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b">Algorithme</td>
                    <td style="color:#e2e8f0;font-weight:500">SHA-256</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05)">
                    <td style="padding:10px 0;color:#64748b">Sérialisation</td>
                    <td style="color:#e2e8f0;font-weight:500">JSON canonique — clés triées</td>
                </tr>
                <tr>
                    <td style="padding:10px 0;color:#64748b">Licence</td>
                    <td style="color:#6366f1;font-weight:600">Apache 2.0</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Data sources ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Sources de Données</div>", unsafe_allow_html=True)

df_sources = pd.DataFrame([
    {"Société": "SNIM",     "Source": "Rapport Annuel 2024",     "Type": "Rapport entreprise", "Fiabilité": "75%", "Date": "31/12/2024"},
    {"Société": "SOMELEC",  "Source": "Rapport Annuel 2024",     "Type": "Rapport entreprise", "Fiabilité": "70%", "Date": "31/12/2024"},
    {"Société": "MAURITEL", "Source": "Estimation Sectorielle",  "Type": "Estimation",         "Fiabilité": "55%", "Date": "31/12/2024"},
    {"Société": "NEXT",     "Source": "Estimation Sectorielle",  "Type": "Estimation",         "Fiabilité": "60%", "Date": "31/12/2024"},
])
st.dataframe(df_sources, use_container_width=True, hide_index=True)

# ── Methodology architecture ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Architecture de la Notation ESG</div>", unsafe_allow_html=True)

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown(
        """
        <div class="esg-card">
            <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:700;margin-bottom:14px">Structure des Piliers</div>
            <div style="font-size:0.84rem;line-height:2">
                <div style="color:#22c55e;font-weight:700">Environnement — 40%</div>
                <div style="padding-left:14px;color:#64748b;font-size:0.8rem">
                    Changement Climatique (50%) · Eau (25%) · Biodiversité (15%) · Déchets (10%)
                </div>
                <div style="color:#3b82f6;font-weight:700;margin-top:6px">Social — 30%</div>
                <div style="padding-left:14px;color:#64748b;font-size:0.8rem">
                    Pratiques RH (40%) · Droits Humains (30%) · Communauté (30%)
                </div>
                <div style="color:#8b5cf6;font-weight:700;margin-top:6px">Gouvernance — 30%</div>
                <div style="padding-left:14px;color:#64748b;font-size:0.8rem">
                    Structure du Conseil (40%) · Transparence (35%) · Anti-Corruption (25%)
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        """
        <div class="esg-card">
            <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:700;margin-bottom:14px">Données Manquantes</div>
            <div style="font-size:0.84rem;color:#94a3b8;line-height:1.9">
                <span style="color:#e2e8f0;font-weight:600">Stratégie appliquée :</span>
                Médiane sectorielle<br>
                <br>
                Lorsqu'un indicateur est absent, la valeur médiane du groupe pair est substituée.
                Cette stratégie est configurable sans modification de code.<br>
                <br>
                <span style="color:#64748b;font-size:0.8rem">
                    Alternatives disponibles : propagation nulle ·
                    pénalité maximale · exclusion avec renormalisation
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Reproducibility guarantees ─────────────────────────────────────────────────
st.markdown("<div class='section-header'>Garanties de Reproductibilité</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="esg-card">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;font-size:0.83rem;color:#94a3b8">
            <div style="padding:10px;background:rgba(255,255,255,0.02);border-radius:8px">
                <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Modèles immuables</div>
                Tous les objets de données sont <code>frozen=True</code> — aucune modification possible après création.
            </div>
            <div style="padding:10px;background:rgba(255,255,255,0.02);border-radius:8px">
                <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Précision numérique</div>
                Calculs en <code>numpy.float64</code> avec précision documentée à chaque étape.
            </div>
            <div style="padding:10px;background:rgba(255,255,255,0.02);border-radius:8px">
                <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Empreinte SHA-256</div>
                Hash de la méthodologie attaché à chaque score — vérifiable par un tiers sans accès à la plateforme.
            </div>
            <div style="padding:10px;background:rgba(255,255,255,0.02);border-radius:8px">
                <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Timestamps explicites</div>
                Jamais <code>datetime.now()</code> dans le moteur de scoring — horodatage passé en argument.
            </div>
            <div style="padding:10px;background:rgba(255,255,255,0.02);border-radius:8px">
                <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">JSON canonique</div>
                Clés triées, sans espace — deux méthodologies identiques produisent le même hash, indépendamment du formatage YAML.
            </div>
            <div style="padding:10px;background:rgba(255,255,255,0.02);border-radius:8px">
                <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Lockfile de dépendances</div>
                <code>uv.lock</code> — dépendances figées à l'octet près pour chaque version publiée.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Standards reference ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Référentiels Appliqués</div>", unsafe_allow_html=True)

st.dataframe(
    pd.DataFrame([
        {"Référentiel": "GHG Protocol",  "Périmètre": "Émissions Scope 1, 2, 3 (15 catégories)", "Statut": "Complet"},
        {"Référentiel": "PCAF",          "Périmètre": "Attribution carbone portefeuille (EVIC)",  "Statut": "Complet"},
        {"Référentiel": "CSRD",          "Périmètre": "Structure de reporting ESG",               "Statut": "Partiel"},
        {"Référentiel": "GRI Standards", "Périmètre": "Indicateurs sociaux et gouvernance",       "Statut": "Partiel"},
        {"Référentiel": "TCFD",          "Périmètre": "Risques climatiques et scénarios",         "Statut": "Prévu"},
        {"Référentiel": "SFDR",          "Périmètre": "Indicateurs PAI",                          "Statut": "Prévu"},
    ]),
    use_container_width=True,
    hide_index=True,
)
