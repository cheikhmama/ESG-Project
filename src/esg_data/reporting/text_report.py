"""Plain-text ESG audit report builder.

Relocated verbatim from the Streamlit explainability page so the report can be
generated (and unit-tested) without the UI. The byte layout of the produced
report is intentionally unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from esg_core.climate.portfolio_metrics import PortfolioCarbonReport


def build_text_report(
    *,
    portfolio_name: str,
    portfolio_id: str,
    weighted_score: float,
    carbon: PortfolioCarbonReport,
    esg_rows: list[dict[str, str]],
    carbon_rows: list[dict[str, str]],
    methodology_hash: str,
    scored_at: str,
    generated_at: str,
) -> bytes:
    """Render the unsigned plain-text ESG audit report as UTF-8 bytes.

    All time-varying values (``scored_at``, ``generated_at``) are passed in so
    the output is a pure function of its arguments.

    Reproducibility: deterministic; given identical arguments the returned bytes
    are byte-identical.
    """
    lines = [
        "RAPPORT ESG — BROUILLON NON SIGNÉ",
        "=" * 64,
        f"Portefeuille          : {portfolio_name}",
        f"Identifiant           : {portfolio_id}",
        f"Score ESG Pondéré     : {weighted_score:.1f} / 100",
        f"Émissions Financées   : {carbon.total_financed_emissions:,.0f} tCO₂e",
        f"Intensité Carbone     : {carbon.carbon_intensity:.1f} tCO₂e / $M investi",
        f"WACI (PCAF, /CA)     : {carbon.waci:.1f} tCO₂e / $M de CA "
        f"(couverture {carbon.waci_coverage * 100:.0f}%)",
        f"Carbon-to-Value/EVIC : {carbon.carbon_to_value:.1f} tCO₂e / $M d'EVIC",
        f"Qualité données PCAF : {carbon.data_quality.weighted_pcaf_score:.2f}/5 "
        f"(1=meilleur, 5=pire ; couverture {carbon.data_quality.coverage * 100:.0f}%)",
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
        f"Hash méthodologie    : {methodology_hash}",
        "Algorithme           : SHA-256 · JSON canonique (clés triées)",
        f"Date du scoring      : {scored_at}",
        f"Date de génération   : {generated_at}",
        "Signature            : aucune (Phase 9 non livrée)",
        "Licence plateforme   : Apache 2.0",
        "=" * 64,
    ]
    return "\n".join(lines).encode("utf-8")
