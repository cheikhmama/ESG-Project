"""Design tokens — the single source of truth for the dashboard's visual scale.

Two kinds of token live here:

* **Palettes** (:data:`DARK` / :data:`LIGHT`) — colour values that change with the
  active theme. They are emitted per-run as ``--esg-*`` custom properties by
  :func:`streamlit_app.utils.styling.apply_global_styles`.
* **Static scale** (:data:`FONT_SIZE`, :data:`FONT_WEIGHT`, :data:`LINE_HEIGHT`,
  :data:`SPACE`, :data:`RADIUS`) — theme-independent values emitted once as
  ``--fs-*`` / ``--fw-*`` / ``--lh-*`` / ``--space-*`` / ``--radius-*`` custom
  properties by :func:`static_tokens_css`.

No colour or font-size literal should appear anywhere else in the presentation
layer; everything references these tokens via ``var(--…)``.
"""

from __future__ import annotations

# ── Palettes (theme-dependent) ────────────────────────────────────────────────

DARK: dict[str, str] = {
    "bg":                   "#07111f",
    "secondary_bg":         "#0c1829",
    "panel":                "#0d1829",
    "panel_border":         "#1b2d47",
    "panel_hover_border":   "#2d5090",
    "panel_hover_shadow":   "rgba(45,122,237,0.08)",
    "text":                 "#c8d8ec",
    "text_heading":         "#dce8f8",
    "text_muted":           "#506070",
    "text_sub":             "#354860",
    "accent":               "#2d7aed",
    "accent_alt":           "#7c5cbf",
    "track":                "rgba(255,255,255,0.06)",
    "kpi_bg":               "#0c1829",
    "kpi_border":           "#1b2d47",
    "kpi_hover_shadow":     "rgba(45,122,237,0.10)",
    "section_color":        "#2d7aed",
    "section_border":       "rgba(45,122,237,0.18)",
    "divider":              "#141f30",
    "input_bg":             "rgba(255,255,255,0.04)",
    "input_border":         "#1b2d47",
    "input_focus":          "rgba(45,122,237,0.50)",
    "input_focus_shadow":   "rgba(45,122,237,0.12)",
    "btn_bg":               "rgba(255,255,255,0.04)",
    "btn_border":           "#1b2d47",
    "btn_hover_bg":         "rgba(255,255,255,0.07)",
    "btn_hover_border":     "#2d5090",
    "metric_bg":            "#0c1829",
    "metric_border":        "#1b2d47",
    "metric_label":         "#506070",
    "metric_value":         "#dce8f8",
    "tab_inactive":         "#506070",
    "tab_active":           "#2d7aed",
    "tab_hover":            "#8aa8c8",
    "df_border":            "#1b2d47",
    "expander_bg":          "#0c1829",
    "expander_border":      "#1b2d47",
    "expander_text":        "#c8d8ec",
    "expander_divider":     "#141f30",
    "select_bg":            "rgba(255,255,255,0.04)",
    "file_border":          "rgba(45,122,237,0.35)",
    "sidebar_bg":           "linear-gradient(180deg, #090f1e 0%, #060b16 100%)",
    "sidebar_border":       "#111d30",
    "scrollbar":            "rgba(45,122,237,0.28)",
    # chart helpers
    "chart_text":           "#506070",
    "chart_grid":           "rgba(255,255,255,0.04)",
    "chart_bg":             "rgba(0,0,0,0)",
}

LIGHT: dict[str, str] = {
    "bg":                   "#f1f5f9",
    "secondary_bg":         "#e2e8f0",
    "panel":                "#ffffff",
    "panel_border":         "rgba(0,0,0,0.08)",
    "panel_hover_border":   "rgba(99,102,241,0.40)",
    "panel_hover_shadow":   "rgba(99,102,241,0.10)",
    "text":                 "#0f172a",
    "text_heading":         "#0f172a",
    "text_muted":           "#475569",
    "text_sub":             "#94a3b8",
    "accent":               "#6366f1",
    "accent_alt":           "#7c3aed",
    "track":                "rgba(0,0,0,0.06)",
    "kpi_bg":               "#ffffff",
    "kpi_border":           "rgba(99,102,241,0.22)",
    "kpi_hover_shadow":     "rgba(99,102,241,0.15)",
    "section_color":        "#4f46e5",
    "section_border":       "rgba(79,70,229,0.18)",
    "divider":              "rgba(0,0,0,0.08)",
    "input_bg":             "#ffffff",
    "input_border":         "rgba(0,0,0,0.12)",
    "input_focus":          "rgba(99,102,241,0.50)",
    "input_focus_shadow":   "rgba(99,102,241,0.10)",
    "btn_bg":               "#f8fafc",
    "btn_border":           "rgba(0,0,0,0.12)",
    "btn_hover_bg":         "#e2e8f0",
    "btn_hover_border":     "rgba(0,0,0,0.20)",
    "metric_bg":            "#ffffff",
    "metric_border":        "rgba(0,0,0,0.08)",
    "metric_label":         "#64748b",
    "metric_value":         "#0f172a",
    "tab_inactive":         "#64748b",
    "tab_active":           "#6366f1",
    "tab_hover":            "#334155",
    "df_border":            "rgba(0,0,0,0.08)",
    "expander_bg":          "#ffffff",
    "expander_border":      "rgba(0,0,0,0.08)",
    "expander_text":        "#334155",
    "expander_divider":     "rgba(0,0,0,0.07)",
    "select_bg":            "#ffffff",
    "file_border":          "rgba(99,102,241,0.35)",
    "sidebar_bg":           "linear-gradient(180deg, #312e81 0%, #1e1b4b 100%)",
    "sidebar_border":       "rgba(255,255,255,0.10)",
    "scrollbar":            "rgba(99,102,241,0.35)",
    # chart helpers
    "chart_text":           "#475569",
    "chart_grid":           "rgba(0,0,0,0.07)",
    "chart_bg":             "rgba(0,0,0,0)",
}

# Custom-property names emitted for each palette key, in declaration order.
PALETTE_VARS: dict[str, str] = {
    "bg":                 "--esg-bg",
    "panel":              "--esg-panel",
    "panel_border":       "--esg-panel-border",
    "panel_hover_border": "--esg-panel-hover-border",
    "panel_hover_shadow": "--esg-panel-hover-shadow",
    "text":               "--esg-text",
    "text_heading":       "--esg-text-heading",
    "text_muted":         "--esg-text-muted",
    "text_sub":           "--esg-text-sub",
    "accent":             "--esg-accent",
    "accent_alt":         "--esg-accent-alt",
    "kpi_bg":             "--esg-kpi-bg",
    "kpi_border":         "--esg-kpi-border",
    "kpi_hover_shadow":   "--esg-kpi-hover-shadow",
    "section_color":      "--esg-section-color",
    "section_border":     "--esg-section-border",
    "divider":            "--esg-divider",
    "track":              "--esg-track",
    "input_bg":           "--esg-input-bg",
    "input_border":       "--esg-input-border",
    "input_focus":        "--esg-input-focus",
    "input_focus_shadow": "--esg-input-focus-shadow",
    "btn_bg":             "--esg-btn-bg",
    "btn_border":         "--esg-btn-border",
    "btn_hover_bg":       "--esg-btn-hover-bg",
    "btn_hover_border":   "--esg-btn-hover-border",
    "metric_bg":          "--esg-metric-bg",
    "metric_border":      "--esg-metric-border",
    "metric_label":       "--esg-metric-label",
    "metric_value":       "--esg-metric-value",
    "tab_inactive":       "--esg-tab-inactive",
    "tab_active":         "--esg-tab-active",
    "tab_hover":          "--esg-tab-hover",
    "df_border":          "--esg-df-border",
    "expander_bg":        "--esg-expander-bg",
    "expander_border":    "--esg-expander-border",
    "expander_text":      "--esg-expander-text",
    "expander_divider":   "--esg-expander-divider",
    "select_bg":          "--esg-select-bg",
    "file_border":        "--esg-file-border",
    "sidebar_bg":         "--esg-sidebar-bg",
    "sidebar_border":     "--esg-sidebar-border",
    "scrollbar":          "--esg-scrollbar",
}

# ── Static scale (theme-independent) ──────────────────────────────────────────
# A type scale distilled from the literals already in use across the app so that
# adopting a token in a later step is a visual no-op. Values are in ``rem``.

FONT_SIZE: dict[str, str] = {
    "3xs":  "0.55rem",
    "2xs":  "0.6rem",
    "xs":   "0.65rem",
    "sm":   "0.72rem",
    "md":   "0.78rem",
    "base": "0.83rem",
    "lg":   "0.9rem",
    "xl":   "1rem",
    "2xl":  "1.1rem",
    "3xl":  "1.3rem",
    "4xl":  "1.65rem",
    "5xl":  "2rem",
}

FONT_WEIGHT: dict[str, str] = {
    "regular":   "400",
    "medium":    "500",
    "semibold":  "600",
    "bold":      "700",
    "extrabold": "800",
}

LINE_HEIGHT: dict[str, str] = {
    "tight":   "1.15",
    "snug":    "1.3",
    "normal":  "1.5",
    "relaxed": "1.7",
}

SPACE: dict[str, str] = {
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "5": "1.5rem",
    "6": "2rem",
}

RADIUS: dict[str, str] = {
    "xs": "3px",
    "sm": "5px",
    "md": "8px",
    "lg": "10px",
    "xl": "14px",
    "pill": "9999px",
}


def _emit(prefix: str, scale: dict[str, str]) -> str:
    return "\n".join(f"        --{prefix}-{k}: {v};" for k, v in scale.items())


def static_tokens_css() -> str:
    """Return the ``:root`` block declaring the theme-independent scale tokens."""
    blocks = "\n".join(
        [
            _emit("fs", FONT_SIZE),
            _emit("fw", FONT_WEIGHT),
            _emit("lh", LINE_HEIGHT),
            _emit("space", SPACE),
            _emit("radius", RADIUS),
        ]
    )
    return f"    :root {{\n{blocks}\n    }}"


def palette_css(p: dict[str, str]) -> str:
    """Return the ``:root`` block declaring the active palette's ``--esg-*`` vars."""
    lines = "\n".join(f"        {var}: {p[key]};" for key, var in PALETTE_VARS.items())
    return f"    :root {{\n{lines}\n    }}"
