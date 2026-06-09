"""Report builders (text, PDF) for the ESG platform's presentation layer.

These live in the data layer (not ``esg_core``) because they format
already-computed scores for human consumption — they are I/O-shaped output, not
scoring logic. Builders are pure: timestamps are passed in, never read from the
clock, so output is reproducible and testable.
"""

from __future__ import annotations

from esg_data.reporting.pdf_report import build_pdf
from esg_data.reporting.text_report import build_text_report

__all__ = ["build_text_report", "build_pdf"]
