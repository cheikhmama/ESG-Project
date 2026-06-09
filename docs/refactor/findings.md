# Findings — logic/visual issues spotted during the refactor

> Behaviour-affecting issues found while restructuring presentation. Per the
> task constraints, **no scoring math, data values, or business behaviour is
> changed without explicit approval.** Each entry records the issue and its
> disposition.

---

## F-001 — Light theme is broken on several pages (approved to fix)

**Severity:** High · **Status:** Approved to fix during colour centralisation.

The app ships a complete light palette (`streamlit_app/utils/styling.py:94-142`)
and a theme toggle (`?theme=light`, persisted in `st.session_state["ui_theme"]`).
However, multiple pages hard-code **dark-theme-only** colour literals directly in
inline styles, so in light mode text/elements render with near-invisible or
wrong colours.

Representative offenders:
- `streamlit_app/pages/4_Comparison.py:197-213` — table cells frozen to
  `#f1f5f9`, `#94a3b8`, `#475569` (dark-mode values) regardless of theme.
- `streamlit_app/pages/3_My_Portfolios.py:133-153, 269, 390, 488` — section
  labels frozen to `#475569`/`#e2e8f0`.
- `streamlit_app/pages/5_Explainability.py:93-96` — empty-state text frozen to
  `#334155`/`#1e293b`.
- `streamlit_app/pages/2_Portfolios.py:57` — description text frozen to
  `#64748b`.

**Disposition:** As inline hex literals are replaced by palette CSS custom
properties (`var(--esg-…)`) during the per-page migration steps, each page
becomes theme-correct automatically. Light-mode rendering will be explicitly
verified per page. No scoring/data change involved.

---

## F-002 — Orphan-wrapper `<div>` produces malformed DOM (structural, fix in place)

**Severity:** High · **Status:** Fixed as part of the relevant page steps.

`st.markdown("<div …>")` … widgets … `st.markdown("</div>")` does **not** wrap
the widgets — Streamlit renders each markdown call in its own container, leaving
an orphan opening tag and a stray closing tag.

Occurrences:
- `streamlit_app/pages/2_Portfolios.py:170-218` (clone box)
- `streamlit_app/pages/3_My_Portfolios.py:163-170` (btn-add wrapper)
- `streamlit_app/pages/3_My_Portfolios.py:246-249` (btn-rm wrapper)

**Disposition:** This is presentation structure, not business behaviour. Replaced
with valid markup (component templates / Streamlit-native containers) during the
page migration. Visual result preserved or improved.

---

<!-- Add new findings below as F-00X. Do NOT change scoring/data without asking. -->
