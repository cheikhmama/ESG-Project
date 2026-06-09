from __future__ import annotations

from esg_core.climate.data_quality import PortfolioDataQualityReport
from esg_core.climate.portfolio_metrics import PortfolioCarbonReport
from esg_data.reporting.text_report import build_text_report


def test_build_text_report_deterministic_and_contains_expected_lines() -> None:
    carbon = PortfolioCarbonReport(
        portfolio_id="test-123",
        total_financed_emissions=1_234.0,
        carbon_intensity=12.3,
        waci=45.6,
        carbon_to_value=78.9,
        per_holding=[],
        total_investment_value=1_000_000.0,
        waci_coverage=0.80,
        data_quality=PortfolioDataQualityReport(
            weighted_pcaf_score=1.23,
            coverage=0.75,
            per_holding=[],
        ),
    )
    esg_rows = [
        {
            "Société": "ACME",
            "Poids": "12.3%",
            "Environnement": "90.0",
            "Social": "80.0",
            "Gouvernance": "70.0",
            "Score ESG": "80.0",
        }
    ]
    carbon_rows = [
        {
            "Société": "ACME",
            "Scope 1 (tCO₂e)": "10",
            "Scope 2 (tCO₂e)": "20",
            "Scope 3 (tCO₂e)": "30",
            "Total (tCO₂e)": "60",
        }
    ]

    output = build_text_report(
        portfolio_name="Test Portefeuille",
        portfolio_id="test-123",
        weighted_score=80.0,
        carbon=carbon,
        esg_rows=esg_rows,
        carbon_rows=carbon_rows,
        methodology_hash="abc123",
        scored_at="2026-06-09 00:00 UTC",
        generated_at="2026-06-09 00:05 UTC",
    )

    assert isinstance(output, bytes)
    assert output.startswith(b"RAPPORT ESG")
    assert "Score ESG Pondéré     : 80.0 / 100".encode() in output
    assert "Hash méthodologie    : abc123".encode() in output
    assert "Date de génération   : 2026-06-09 00:05 UTC".encode() in output
    assert output == build_text_report(
        portfolio_name="Test Portefeuille",
        portfolio_id="test-123",
        weighted_score=80.0,
        carbon=carbon,
        esg_rows=esg_rows,
        carbon_rows=carbon_rows,
        methodology_hash="abc123",
        scored_at="2026-06-09 00:00 UTC",
        generated_at="2026-06-09 00:05 UTC",
    )
