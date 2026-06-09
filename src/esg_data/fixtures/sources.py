"""Source metadata and official report references for Mauritanian companies."""

from __future__ import annotations

OFFICIAL_REPORTS: dict[str, dict[int, str]] = {
    "SNIM": {
        2024: "https://snim.com/sites/default/files/SNIM_Rapport_activite2024_Ang.pdf",
    },
}

COMPANY_META: dict[str, dict[str, object]] = {
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
