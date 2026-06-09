"""Jinja2 rendering seam for Streamlit components.

A single, autoescaping Jinja environment loads templates from the sibling
``templates/`` directory. ``render`` returns the rendered HTML string;
``render_into`` injects it into the page via ``st.markdown``.

Keeping every ``unsafe_allow_html=True`` call behind this module means the
HTML surface is auditable in one place, and templates — not Python f-strings —
own all markup.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


@lru_cache(maxsize=1)
def _env() -> Environment:
    """Return the shared Jinja environment, built once per process."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render(template_name: str, /, **context: Any) -> str:
    """Render ``template_name`` from ``templates/`` to an HTML string."""
    return _env().get_template(template_name).render(**context)


def render_into(template_name: str, /, **context: Any) -> None:
    """Render a template and inject it into the current Streamlit container."""
    st.markdown(render(template_name, **context), unsafe_allow_html=True)
