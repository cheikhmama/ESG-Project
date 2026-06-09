from esg_data.reporting.pdf_report import build_pdf


def test_build_pdf_returns_pdf_bytes() -> None:
    pdf_bytes = build_pdf("SNIM", 2024)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500
