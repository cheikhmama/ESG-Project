"""Top navbar + sidebar navigation — enterprise ESG Platform.

Architecture
------------
* A fixed <nav> element is appended to document.body (bypasses stHeader).
* Sidebar width is controlled entirely by CSS/JS — Streamlit's native sidebar
  toggle buttons are moved off-screen (still in DOM but invisible).
* Hamburger button toggles ``html.esg-sb-collapsed`` class:
    expanded  → 240 px (icon + label)
    collapsed →  72 px (icon only + CSS tooltip on hover)
* State is persisted in localStorage (key ``_esg_sb``).
* MutationObserver re-applies width after Streamlit's re-render resets it.
"""

from __future__ import annotations

import re

import streamlit as st
import streamlit.components.v1 as components

from streamlit_app.utils.styling import current_theme

# ── Navigation: (section, [(label, url-slug, icon-key)]) ─────────────────────
_NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("Analyse", [
        ("Tableau de Bord",   "",                "grid"),
        ("Sociétés",          "1_Entreprises",   "building"),
    ]),
    ("Portefeuilles", [
        ("Portefeuilles",     "2_Portfolios",    "briefcase"),
        ("Mes Portefeuilles", "3_My_Portfolios", "folder"),
        ("Comparaison",       "4_Comparison",    "scale"),
    ]),
    ("Outils", [
        ("Analyse ESG",       "5_Explainability","chart"),
        ("Sources",           "6_Source",        "database"),
    ]),
]

# ── SVG icons (Feather-style 16x16) ─────────────────────────────────────────
_I: dict[str, str] = {
    "grid": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<rect x="3" y="3" width="7" height="7" rx="1"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1"/></svg>'
    ),
    "building": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<path d="M3 21h18M5 21V5a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v16M9 21v-8h6v8"/></svg>'
    ),
    "briefcase": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<rect x="2" y="7" width="20" height="14" rx="2"/>'
        '<path d="M16 7V5a2 2 0 0 0-4 0v2"/></svg>'
    ),
    "folder": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
        '</svg>'
    ),
    "scale": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<line x1="12" y1="3" x2="12" y2="21"/>'
        '<path d="M3 9l9-6 9 6"/>'
        '<path d="M3 9a3 3 0 0 0 6 0L6 3 3 9z"/>'
        '<path d="M15 9a3 3 0 0 0 6 0l-3-6-3 6z"/></svg>'
    ),
    "chart": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<rect x="3" y="12" width="4" height="9"/>'
        '<rect x="10" y="5" width="4" height="16"/>'
        '<rect x="17" y="8" width="4" height="13"/></svg>'
    ),
    "database": (
        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        ' stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
        '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
    ),
}

# ── Fixed SVGs ────────────────────────────────────────────────────────────────
_LOGO_SVG = (
    '<svg width="20" height="16" viewBox="0 0 26 22" fill="none">'
    '<rect x="0" y="12" width="6" height="10" rx="1.5" fill="#0ea672"/>'
    '<rect x="8" y="6" width="6" height="16" rx="1.5" fill="#2d7aed"/>'
    '<rect x="16" y="0" width="6" height="22" rx="1.5" fill="#7c5cbf"/>'
    '<circle cx="21" cy="0" r="2.5" fill="#e89e0c" opacity="0.9"/>'
    '</svg>'
)
_BELL_SVG = (
    '<svg width="14" height="14" fill="none" stroke="currentColor"'
    ' stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">'
    '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>'
    '<path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
)
_SEARCH_SVG = (
    '<svg width="12" height="12" fill="none" stroke="currentColor"'
    ' stroke-width="2" stroke-linecap="round" viewBox="0 0 24 24">'
    '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>'
)
_MENU_SVG = (
    '<svg width="14" height="14" fill="none" stroke="currentColor"'
    ' stroke-width="1.8" stroke-linecap="round" viewBox="0 0 24 24">'
    '<line x1="3" y1="6" x2="21" y2="6"/>'
    '<line x1="3" y1="12" x2="21" y2="12"/>'
    '<line x1="3" y1="18" x2="21" y2="18"/></svg>'
)

# ── Theme palettes ────────────────────────────────────────────────────────────
_NAVBAR_DARK = {
    "bg": "#090f1e", "border": "rgba(255,255,255,0.06)",
    "icon": "#4a6070", "hover_bg": "rgba(255,255,255,0.07)",
    "hover_fg": "#c8d8ec", "accent": "#2d7aed",
}
_NAVBAR_LIGHT = {
    "bg": "#f0f4f8", "border": "rgba(0,0,0,0.08)",
    "icon": "#4a6070", "hover_bg": "rgba(0,0,0,0.05)",
    "hover_fg": "#0a1628", "accent": "#2d7aed",
}

# ── Static CSS (injected once via st.markdown) ────────────────────────────────
_CSS = """
<style>
/* ── Strip Streamlit chrome ──────────────────────────────────── */
[data-testid="stDeployButton"],
[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stMainMenuButton"],
[data-testid="stMainMenu"],
[data-testid="stToolbarActions"],
#MainMenu, footer { display: none !important; }

/* ── Collapse stHeader — replaced by our fixed <nav> ────────── */
[data-testid="stHeader"] {
    height: 0 !important; min-height: 0 !important;
    padding: 0 !important; overflow: hidden !important;
}

/* ── Streamlit sidebar toggles — off-screen, JS-clickable ───── */
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] {
    position: fixed !important; top: -200px !important;
    left: -200px !important; opacity: 0 !important;
    pointer-events: none !important; z-index: -1 !important;
}

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    transition: width 230ms ease, min-width 230ms ease !important;
    overflow: visible !important;
    position: relative !important;
}
/* Outermost scroll container — clearance for the 48px fixed navbar */
[data-testid="stSidebar"] > div:first-child {
    overflow-x: hidden !important;
    overflow-y: auto !important;
    padding-top: 52px !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 0 !important;
    height: 100vh !important;
    box-sizing: border-box !important;
}
/* Inner wrappers — zero out their own padding so it doesn't stack */
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    padding: 0 !important;
    margin: 0 !important;
}
/* Hide the empty auto-nav container Streamlit renders even with showSidebarNavigation=false */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavSeparator"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
}
[data-testid="stSidebar"] iframe { display: none !important; }

/* ── Main content ────────────────────────────────────────────── */
.main .block-container {
    padding-top: 56px !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}
section[data-testid="stMain"] {
    flex: 1 1 0% !important;
    min-width: 0 !important;
}

/* ── Nav section labels ──────────────────────────────────────── */
.esg-nav-section {
    font-size: 0.58rem; font-weight: 700;
    color: rgba(200,216,236,0.18); text-transform: uppercase;
    letter-spacing: 0.16em; padding: 0 0 4px 20px;
    white-space: nowrap; overflow: hidden;
    transition: opacity 200ms ease, padding 200ms ease;
}
.esg-nav-div {
    height: 1px; background: rgba(255,255,255,0.04);
    margin: 6px 10px; transition: margin 200ms ease;
}

/* ── Nav links ───────────────────────────────────────────────── */
.esg-nav-link {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 10px 7px 20px; margin: 1px 6px;
    border-radius: 6px; text-decoration: none !important;
    color: rgba(200,216,236,0.42); font-size: 0.82rem;
    font-weight: 500; letter-spacing: 0.003em; line-height: 1.4;
    position: relative; white-space: nowrap;
    transition: color 0.15s, background 0.15s,
                padding 220ms ease, gap 220ms ease, justify-content 220ms ease;
}
.esg-nav-link:hover {
    background: rgba(255,255,255,0.04) !important;
    color: rgba(200,216,236,0.80) !important;
    text-decoration: none !important;
}
.esg-nav-link.esg-nav-active {
    background: rgba(45,122,237,0.10) !important;
    color: #7ab8f5 !important; font-weight: 600;
}
.esg-nav-link.esg-nav-active .esg-nav-icon { color: #2d7aed; }

/* ── Icon ────────────────────────────────────────────────────── */
.esg-nav-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px; flex-shrink: 0;
    color: rgba(200,216,236,0.32);
    transition: color 0.15s;
}
.esg-nav-link:hover .esg-nav-icon { color: rgba(200,216,236,0.60); }

/* ── Label ───────────────────────────────────────────────────── */
.esg-nav-label {
    flex: 1; overflow: hidden; text-overflow: ellipsis;
    opacity: 1; max-width: 180px;
    transition: opacity 180ms ease, max-width 220ms ease;
}

/* ── Tooltip (collapsed only) ────────────────────────────────── */
.esg-nav-tip {
    display: none;
    position: absolute; left: calc(100% + 8px); top: 50%;
    transform: translateY(-50%);
    background: #1a2840; border: 1px solid rgba(255,255,255,0.09);
    color: #c8d8ec; padding: 4px 10px; border-radius: 5px;
    font-size: 0.76rem; white-space: nowrap;
    z-index: 9999990; pointer-events: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.45);
}

/* ── Footer ──────────────────────────────────────────────────── */
.esg-nav-footer {
    padding: 12px 14px 16px 20px;
    border-top: 1px solid rgba(255,255,255,0.04);
    transition: padding 220ms ease;
}
.esg-nav-meta { font-size: 0.6rem; color: rgba(200,216,236,0.18); line-height: 1.5; }
.esg-nav-badge {
    display: inline-block; background: rgba(45,122,237,0.12);
    color: rgba(122,184,245,0.70); border-radius: 3px;
    font-size: 0.56rem; font-weight: 600; padding: 1px 5px;
    letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 3px;
}

/* ══════════════════════════════════════════════════
   COLLAPSED STATE  (class toggled on <html> by JS)
   ══════════════════════════════════════════════════ */
html.esg-sb-collapsed .esg-nav-label {
    opacity: 0 !important; max-width: 0 !important; overflow: hidden !important;
}
html.esg-sb-collapsed .esg-nav-section {
    opacity: 0 !important; font-size: 0 !important;
    padding-top: 4px !important; padding-bottom: 2px !important;
}
html.esg-sb-collapsed .esg-nav-div { margin: 4px 8px !important; }
html.esg-sb-collapsed .esg-nav-link {
    justify-content: center !important;
    padding: 9px 0 !important; margin: 2px 6px !important; gap: 0 !important;
}
html.esg-sb-collapsed .esg-nav-icon {
    width: 20px !important; height: 20px !important;
}
html.esg-sb-collapsed .esg-nav-link:hover .esg-nav-tip { display: block !important; }
html.esg-sb-collapsed .esg-nav-footer {
    padding: 10px 6px !important; justify-content: center !important;
    display: flex !important;
}
html.esg-sb-collapsed .esg-nav-footer .esg-nav-badge,
html.esg-sb-collapsed .esg-nav-footer .esg-nav-meta { display: none !important; }

/* ── Navbar two-section layout ───────────────────────────────── */
/* Left section: always matches sidebar width so brand never
   intrudes into the content column.                            */
._esg_nbl {
    width: 240px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 0 0 8px;
    transition: width 230ms ease;
    overflow: hidden;
    box-sizing: border-box;
}
html.esg-sb-collapsed ._esg_nbl { width: 72px !important; }

/* Right section: fills remaining viewport width = main content */
._esg_nbr {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px 0 8px;
    min-width: 0;
    overflow: hidden;
}

/* ── Navbar page-name chip (visible only when sidebar collapsed) ─ */
._esg_pname {
    opacity: 0;
    max-width: 0;
    overflow: hidden;
    white-space: nowrap;
    flex-shrink: 0;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    transition: opacity 220ms ease, max-width 240ms ease;
}
html.esg-sb-collapsed ._esg_pname {
    opacity: 1 !important;
    max-width: 240px !important;
}

/* ── Thin vertical divider between brand and search ─────────── */
._esg_sep {
    width: 1px; height: 18px;
    background: rgba(255,255,255,0.07);
    flex-shrink: 0;
}

/* ── Current-page title bar (below navbar, main content side) ── */
#_esg_curtitle {
    position: fixed;
    top: 48px; left: 72px; right: 0;
    height: 34px;
    display: none;
    align-items: center;
    padding: 0 20px;
    gap: 8px;
    background: rgba(9,15,30,0.97);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    z-index: 99000;
    font-size: 0.81rem;
    font-weight: 600;
    color: rgba(200,216,236,0.60);
    letter-spacing: 0.01em;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    pointer-events: none;
    opacity: 0;
    transition: opacity 220ms ease;
}
html.esg-sb-collapsed #_esg_curtitle {
    display: flex !important;
    opacity: 1 !important;
}
html.esg-sb-collapsed .main .block-container {
    padding-top: 84px !important;
}
</style>
"""


def _sidebar_html() -> str:
    """Build HTML for all nav sections and custom link elements."""
    parts: list[str] = []
    for i, (section, items) in enumerate(_NAV_GROUPS):
        if i > 0:
            parts.append('<div class="esg-nav-div"></div>')
        parts.append(f'<div class="esg-nav-section">{section}</div>')
        for label, slug, icon in items:
            # Streamlit 1.36+ strips leading digits+underscore from page filenames
            # e.g. "1_Entreprises" → href "/Entreprises"
            bare = re.sub(r'^\d+_', '', slug) if slug else ""
            href = "/" if not bare else f"/{bare}"
            slug_attr = slug if slug else "__root__"
            parts.append(
                f'<a href="{href}" class="esg-nav-link"'
                f' data-slug="{slug_attr}">'
                f'<span class="esg-nav-icon">{_I[icon]}</span>'
                f'<span class="esg-nav-label">{label}</span>'
                f'<span class="esg-nav-tip">{label}</span>'
                f'</a>'
            )
    parts.append(
        '<div class="esg-nav-footer">'
        '<div class="esg-nav-badge">v1.0.0</div>'
        '<div class="esg-nav-meta">Apache 2.0 \xb7 Open Source</div>'
        '</div>'
    )
    return "\n".join(parts)


def _inject_js(theme: str) -> None:
    """Inject navbar + sidebar state manager via a hidden sidebar iframe."""
    c = _NAVBAR_DARK if theme == "dark" else _NAVBAR_LIGHT
    next_t = "light" if theme == "dark" else "dark"
    t_icon = "&#9728;" if theme == "dark" else "&#9789;"
    t_tip  = "Mode clair" if theme == "dark" else "Mode sombre"
    b_title = "#c8d8ec" if theme == "dark" else "#0a1628"
    b_sub   = "rgba(200,216,236,0.28)" if theme == "dark" else "rgba(10,22,40,0.38)"

    if theme == "dark":
        s_bg  = "rgba(255,255,255,0.05)"
        s_bd  = "rgba(255,255,255,0.09)"
        s_cl  = "rgba(200,216,236,0.50)"
        s_ph  = "rgba(200,216,236,0.22)"
        s_fb  = "rgba(45,122,237,0.50)"
        s_fbg = "rgba(45,122,237,0.07)"
        s_sh  = "rgba(45,122,237,0.14)"
        s_fc  = "rgba(200,216,236,0.90)"
        k_cl  = "rgba(200,216,236,0.22)"
        k_bg  = "rgba(255,255,255,0.07)"
        k_bd  = "rgba(255,255,255,0.12)"
    else:
        s_bg  = "rgba(0,0,0,0.05)"
        s_bd  = "rgba(0,0,0,0.10)"
        s_cl  = "rgba(10,22,40,0.55)"
        s_ph  = "rgba(10,22,40,0.28)"
        s_fb  = "rgba(45,122,237,0.60)"
        s_fbg = "rgba(45,122,237,0.06)"
        s_sh  = "rgba(45,122,237,0.16)"
        s_fc  = "rgba(10,22,40,0.90)"
        k_cl  = "rgba(10,22,40,0.28)"
        k_bg  = "rgba(0,0,0,0.06)"
        k_bd  = "rgba(0,0,0,0.10)"

    components.html(
        f"""<script>
(function() {{
  var d  = window.parent.document;
  var pW = window.parent;
  var SK = '_esg_sb';

  /* ── State helpers ───────────────────────────────────────────── */
  var col = localStorage.getItem(SK) === '1';

  function _w() {{ return col ? '72px' : '240px'; }}

  function _applyWidth() {{
    var sb = d.querySelector('[data-testid="stSidebar"]');
    if (!sb) return;
    var w = _w();
    sb.style.setProperty('width',     w, 'important');
    sb.style.setProperty('min-width', w, 'important');
    sb.style.setProperty('max-width', w, 'important');
  }}

  function _applyClass() {{
    d.documentElement.classList.toggle('esg-sb-collapsed', col);
  }}

  function _apply() {{ _applyClass(); _applyWidth(); }}

  function _toggle() {{
    col = !col;
    localStorage.setItem(SK, col ? '1' : '0');
    _apply();
    _updatePageName();
    _updateCurTitle();
  }}

  /* ── Active link ─────────────────────────────────────────────── */
  function _markActive() {{
    var path = pW.location.pathname;
    d.querySelectorAll('.esg-nav-link').forEach(function(a) {{
      var slug = a.getAttribute('data-slug') || '';
      var hit;
      if (slug === '__root__') {{
        hit = (path === '/');
      }} else {{
        var bare = slug.replace(/^\\d+_/, '');
        hit = path === '/' + slug || path === '/' + bare ||
              path.endsWith('/' + slug) || path.endsWith('/' + bare);
      }}
      a.classList.toggle('esg-nav-active', hit);
    }});
  }}

  /* ── Page name chip in navbar (collapsed state) ──────────────── */
  function _updatePageName() {{
    var el = d.getElementById('_esg_pn');
    if (!el) return;
    var active = d.querySelector('.esg-nav-link.esg-nav-active');
    var lbl = '';
    if (active) {{
      var ln = active.querySelector('.esg-nav-label');
      lbl = ln ? ln.textContent.trim() : '';
    }}
    el.textContent = lbl;
  }}

  /* ── Current-page title bar in main content (collapsed state) ── */
  function _buildCurTitle() {{
    if (!d.getElementById('_esg_curtitle')) {{
      var ct = d.createElement('div');
      ct.id = '_esg_curtitle';
      d.body.appendChild(ct);
    }}
  }}

  function _updateCurTitle() {{
    _buildCurTitle();
    var el = d.getElementById('_esg_curtitle');
    if (!el) return;
    var active = d.querySelector('.esg-nav-link.esg-nav-active');
    var lbl = '';
    if (active) {{
      var ln = active.querySelector('.esg-nav-label');
      lbl = ln ? ln.textContent.trim() : '';
    }}
    el.innerHTML = lbl
      ? '<span style="font-size:0.6rem;opacity:0.35;margin-right:2px">▸</span>'
        + '<span>' + lbl + '</span>'
      : '';
  }}

  /* ── Navbar CSS ──────────────────────────────────────────────── */
  var oc = d.getElementById('_esg_ncs'); if (oc) oc.remove();
  var cs = d.createElement('style'); cs.id = '_esg_ncs';
  cs.textContent =
    '._esg_nb{{display:inline-flex!important;align-items:center!important;' +
    'justify-content:center!important;width:30px!important;height:30px!important;' +
    'background:transparent!important;border:1px solid {c["border"]}!important;' +
    'border-radius:6px!important;color:{c["icon"]}!important;cursor:pointer!important;' +
    'text-decoration:none!important;flex-shrink:0!important;outline:none!important;' +
    'transition:background .12s,color .12s,border-color .12s!important;}}' +
    '._esg_nb:hover{{background:{c["hover_bg"]}!important;color:{c["hover_fg"]}!important;' +
    'border-color:{c["accent"]}!important;text-decoration:none!important;}}' +
    '._esg_srch{{flex:1!important;max-width:420px!important;' +
    'margin:0!important;position:relative!important;}}' +
    '._esg_srch input{{width:100%!important;height:34px!important;' +
    'background:{s_bg}!important;border:1px solid {s_bd}!important;' +
    'border-radius:20px!important;padding:0 46px 0 36px!important;' +
    'font-size:0.775rem!important;font-family:inherit!important;' +
    'color:{s_cl}!important;outline:none!important;box-sizing:border-box!important;' +
    'transition:border-color .18s,background .18s,box-shadow .18s!important;}}' +
    '._esg_srch input:focus{{border-color:{s_fb}!important;' +
    'background:{s_fbg}!important;' +
    'box-shadow:0 0 0 3px {s_sh}!important;color:{s_fc}!important;}}' +
    '._esg_srch input::placeholder{{color:{s_ph}!important;}}' +
    '._esg_srch .si{{position:absolute!important;left:13px!important;' +
    'top:50%!important;transform:translateY(-50%)!important;' +
    'color:{s_ph}!important;pointer-events:none!important;}}' +
    '._esg_srch .sk{{position:absolute!important;right:12px!important;' +
    'top:50%!important;transform:translateY(-50%)!important;' +
    'font-size:0.55rem!important;font-family:inherit!important;' +
    'color:{k_cl}!important;background:{k_bg}!important;' +
    'border:1px solid {k_bd}!important;' +
    'border-radius:4px!important;padding:2px 6px!important;' +
    'pointer-events:none!important;letter-spacing:0.05em!important;}}' +
    '._esg_pname{{color:{b_title}!important;}}' +
    '._esg_av{{width:26px!important;height:26px!important;border-radius:50%!important;' +
    'background:linear-gradient(135deg,#2d7aed,#7c5cbf)!important;' +
    'color:#fff!important;font-size:0.58rem!important;font-weight:700!important;' +
    'display:inline-flex!important;align-items:center!important;justify-content:center!important;' +
    'cursor:pointer!important;flex-shrink:0!important;letter-spacing:0.04em!important;' +
    'border:1px solid rgba(255,255,255,0.14)!important;}}' +
    '._esg_dot{{position:absolute!important;top:4px!important;right:4px!important;' +
    'width:6px!important;height:6px!important;border-radius:50%!important;' +
    'background:#e53e3e!important;border:1px solid {c["bg"]}!important;}}';
  d.head.appendChild(cs);

  /* ── Build navbar (once) ─────────────────────────────────────── */
  var nav = d.getElementById('_esg_nav');
  if (!nav) {{
    nav = d.createElement('nav');
    nav.id = '_esg_nav';
    d.body.insertBefore(nav, d.body.firstChild);

    /* Left section — sidebar-width; holds hamburger + brand */
    var nbl = d.createElement('div');
    nbl.className = '_esg_nbl';
    nav.appendChild(nbl);

    var mb = d.createElement('button');
    mb.className = '_esg_nb'; mb.title = 'Menu';
    mb.innerHTML = '{_MENU_SVG}';
    mb.addEventListener('click', _toggle);
    nbl.appendChild(mb);

    var br = d.createElement('div');
    br.id = '_esg_br';
    nbl.appendChild(br);

    /* Right section — content-width; holds search + actions */
    var nbr = d.createElement('div');
    nbr.className = '_esg_nbr';
    nav.appendChild(nbr);

    var sp = d.createElement('div');
    sp.className = '_esg_sep';
    nbr.appendChild(sp);

    var pn = d.createElement('div');
    pn.id = '_esg_pn';
    pn.className = '_esg_pname';
    nbr.appendChild(pn);

    var sr = d.createElement('div');
    sr.className = '_esg_srch';
    sr.innerHTML =
      '<span class="si">{_SEARCH_SVG}</span>' +
      '<input type="text" placeholder="Rechercher sociétés, portefeuilles…"/>' +
      '<span class="sk">⌘K</span>';
    nbr.appendChild(sr);

    var rs = d.createElement('div');
    rs.id = '_esg_rs';
    rs.style.cssText = 'display:flex;align-items:center;gap:6px;margin-left:auto;flex-shrink:0;';
    nbr.appendChild(rs);
  }}

  /* ── Re-apply theme-dependent parts every render ─────────────── */
  nav.style.cssText =
    'position:fixed;top:0;left:0;right:0;height:48px;z-index:999999;' +
    'display:flex;align-items:stretch;gap:0;padding:0;' +
    'background:{c["bg"]};border-bottom:1px solid {c["border"]};box-sizing:border-box;';

  d.getElementById('_esg_br').style.cssText =
    'display:flex;align-items:center;gap:9px;flex-shrink:0;';
  d.getElementById('_esg_br').innerHTML =
    '{_LOGO_SVG}' +
    '<div style="line-height:1">' +
      '<div style="font-size:0.88rem;font-weight:700;color:{b_title};' +
        'letter-spacing:-0.01em;line-height:1.2">ESG Platform</div>' +
      '<div style="font-size:0.54rem;color:{b_sub};letter-spacing:0.14em;' +
        'text-transform:uppercase;margin-top:1px">Mauritanie \xb7 Alpha</div>' +
    '</div>';

  d.getElementById('_esg_rs').innerHTML =
    '<button class="_esg_nb" title="Notifications" style="position:relative">' +
      '{_BELL_SVG}<span class="_esg_dot"></span>' +
    '</button>' +
    '<div class="_esg_av" title="Med Aloueimin">MA</div>' +
    '<a href="?theme={next_t}" class="_esg_nb" title="{t_tip}">{t_icon}</a>';

  /* ── Strip top spacing Streamlit injects via inline styles ──────── */
  function _applySpacing() {{
    var sbInner = d.querySelector('[data-testid="stSidebar"] > div:first-child');
    if (sbInner) sbInner.style.setProperty('padding-top', '52px', 'important');
    var sbC = d.querySelector('[data-testid="stSidebarContent"]');
    if (sbC) {{
      sbC.style.setProperty('padding-top', '0', 'important');
      sbC.style.setProperty('margin-top', '0', 'important');
    }}
    var sbUser = d.querySelector('[data-testid="stSidebarUserContent"]');
    if (sbUser) {{
      sbUser.style.setProperty('padding', '0', 'important');
      sbUser.style.setProperty('margin', '0', 'important');
    }}
    var sbNav = d.querySelector('[data-testid="stSidebarNav"]');
    if (sbNav) sbNav.style.setProperty('display', 'none', 'important');
  }}

  /* ── MutationObserver: re-apply width + spacing after Streamlit re-renders ─ */
  if (!pW._esgObs) {{
    var sb0 = d.querySelector('[data-testid="stSidebar"]');
    if (sb0) {{
      pW._esgObs = new MutationObserver(function() {{ _applyWidth(); _applySpacing(); }});
      pW._esgObs.observe(sb0, {{ attributes: true, attributeFilter: ['style'] }});
    }}
  }}

  _apply();
  _applySpacing();
  _markActive();
  _updatePageName();
  _updateCurTitle();
}})();
</script>""",
        height=0,
    )


def render_sidebar_nav() -> None:
    """Render navbar + sidebar. Call once per page after apply_global_styles()."""
    if "ui_theme" not in st.session_state:
        st.session_state["ui_theme"] = st.query_params.get("theme", "dark")

    st.markdown(_CSS, unsafe_allow_html=True)

    with st.sidebar:
        _inject_js(current_theme())
        st.markdown(_sidebar_html(), unsafe_allow_html=True)
