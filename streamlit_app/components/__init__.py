"""Presentation components — Jinja templates rendered into Streamlit.

This package holds the *only* place where HTML is produced. Pages call
component functions (e.g. ``page_header``, ``kpi``) and never build markup
strings themselves. Each function renders a template from ``templates/`` via
:func:`render`.
"""
