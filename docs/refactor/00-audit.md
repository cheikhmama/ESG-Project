# 00 — Presentation-Layer Audit (Phase 0, discovery only)

> Scope: `streamlit_app/` (Layer 4 presentation). No code changed. This document
> inventories the current state, pinpoints pain points with `file:line`
> references, and proposes a target architecture for approval.

---

## 1. Inventory

### 1.1 Files and roles

| File | LOC | Role | Data/logic? | HTML injected? | CSS injected? |
|---|---:|---|---|---|---|
| `streamlit_app/app.py` | 344 | Dashboard (KPIs, charts, ranking table, activity feed, alerts) | KPI derivation, filtering, ranking | Yes (3 sites + inline `_mini_bar`/`_pillar_val` builders) | No (uses global) |
| `streamlit_app/pages/1_Entreprises.py` | 140 | Company directory + per-company expander cards | Filtering | Yes (5) | No |
| `streamlit_app/pages/2_Portfolios.py` | 218 | Reference-portfolio catalogue, clone flow | Portfolio scoring orchestration, clone state | Yes (4) | No |
| `streamlit_app/pages/3_My_Portfolios.py` | 582 | Create / import / list personal portfolios | Heavy: position state, CSV/JSON import, validation, weight math | Yes (25) | **Yes — page-local `<style>` block (lines 45–123)** |
| `streamlit_app/pages/4_Comparison.py` | 403 | Two-portfolio side-by-side comparison | Pillar/theme aggregation, deltas | Yes (13, incl. full HTML KPI table) | No |
| `streamlit_app/pages/5_Explainability.py` | 361 | Per-portfolio ESG audit + report/PDF text builder | Table assembly, report text builder | Yes (8) | No |
| `streamlit_app/pages/6_Source.py` | 425 | Data-source traceability + per-company PDF builder | **`OFFICIAL_REPORTS` + `COMPANY_META` dicts (lines 17–56)**, full `fpdf` PDF builder | Yes (8) | No |
| `streamlit_app/utils/styling.py` | 926 | Palette tokens, CSS string, score/colour helpers, card render helpers | Score-threshold logic | Yes (helpers emit HTML) | **Yes — global `_STATIC_CSS` (lines 178–670)** |
| `streamlit_app/utils/nav.py` | 713 | Top navbar + collapsible sidebar (CSS + JS via iframe) | Nav model | Yes (sidebar HTML) | **Yes — `_CSS` block (lines 133–389) + JS-injected `<style>` (lines 549–589)** |

`unsafe_allow_html=True` call sites total **74** across the layer
(app 3, p1 5, p2 4, p3 25, p4 13, p5 8, p6 8, styling 6, nav 2).

### 1.2 Where data / logic lives (to be preserved untouched in behaviour)

- **Core engine** (`src/esg_core/`) and **data layer** (`src/esg_data/`) are
  cleanly separated and out of scope. `src/esg_data/services.py` is the proper
  Layer-2 orchestration seam the pages already call through
  (`compute_all_scores`, `build_portfolio`, `compute_portfolio_score`).
- Pages correctly delegate scoring to `services.py`. **Good** — the
  data/scoring boundary is mostly intact; the problem is almost entirely
  presentation.

### 1.3 Logic that leaked into the presentation layer

These are business/data concerns physically living in page files:

- `6_Source.py:17-56` — `OFFICIAL_REPORTS` and `COMPANY_META` (company
  metadata, report URLs, confidence levels, report years). This is **data**,
  not presentation, and overlaps conceptually with `esg_data.fixtures`.
- `6_Source.py:70-294` — `_build_pdf()`, a 224-line PDF document builder
  (fpdf). Document generation is closer to a reporting/service concern than UI.
- `5_Explainability.py:272-330` — `_build_report()` text-report builder.
- `3_My_Portfolios.py` — CSV/JSON import parsing + validation
  (`254-264`, `401-484`), weight computation (`302-316`), clone/create state.
- `app.py:47-55`, `181-190` — KPI derivation and filtering inline.

> Note: relocating these is optional for the *styling* refactor but is the
> natural place to enforce the separation contract. Flagged here; sequencing
> deferred to the plan.

---

## 2. Pain points (with `file:line`)

### 2.1 Inline HTML f-strings with embedded styles

The dominant anti-pattern: multi-line f-strings mixing data, layout and colour.

- `streamlit_app/utils/styling.py:874-926` — `company_card()` is a ~50-line HTML
  blob with ~15 inline `style="…"` attributes and interpolated palette values.
- `app.py:198-272` — `_mini_bar()`, `_pillar_val()` and the ranking-table
  builder assemble a full `<table>` as a string, row by row, with inline styles
  and `#hex`/`var(--…)` mixed.
- `4_Comparison.py:190-218` — the KPI comparison table is hand-built HTML
  (`<table>` + `<thead>` + `<tbody>`) with inline `padding`, `color`,
  `border` on every cell.
- `4_Comparison.py:360-403` — “en avance” cards duplicated almost verbatim for
  A vs B, differing only in colour.
- `3_My_Portfolios.py:329-352`, `464-473`, `487-527` — success/preview banners
  as inline-styled HTML blocks.
- `1_Entreprises.py:79-140` — company-detail card + pillar tiles built inline
  with `palette()` interpolation.
- `6_Source.py:325-416` — sector chips, reliability block, official/estimated
  report cards, all inline HTML.

### 2.2 Hard-coded colours and sizes (bypassing the palette)

- **93 hard-coded hex colours** appear in `app.py` + `pages/*.py` (outside the
  legitimate palette in `styling.py`). Top offenders: `#6366f1` ×23,
  `#22c55e` ×12, `#94a3b8` ×9, `#475569` ×8, `#e2e8f0` ×6, `#334155` ×6.
- Many are **dark-theme-only literals** (`#e2e8f0`, `#94a3b8`, `#334155`,
  `#1e293b`, `#cbd5e1`) written directly into pages — e.g.
  `4_Comparison.py:197-213`, `3_My_Portfolios.py:133-153`,
  `5_Explainability.py:93-96`. The app ships a full light palette
  (`styling.py:94-142`) and a theme toggle, but **these pages will render
  unreadable text in light mode** because the colours are frozen to dark values.
  (Logic/visual bug candidate — see findings, do not fix yet.)
- Font sizes (`0.6rem`, `0.62rem`, `0.65rem`, `0.72rem`, `0.83rem`, `1rem`,
  `1.6rem`, `1.85rem`…) are sprinkled as inline literals with no shared type
  scale. The same “section label” style (`0.62–0.65rem`, `uppercase`,
  `letter-spacing:0.12em`, `font-weight:700`, `color:#475569`) is re-typed at
  `3_My_Portfolios.py:133`, `177`, `269`, `390`, `488` and elsewhere.

### 2.3 Duplicated card / markup

- **Section-label** (small uppercase caption) reimplemented ~6× inline in
  `3_My_Portfolios.py` instead of reusing the existing `.section-header` class
  or `dash_section()` helper.
- **Success banner** (green tinted box) duplicated:
  `3_My_Portfolios.py:329-352` and `516-527`.
- **Info/format box** (indigo tinted box) duplicated:
  `3_My_Portfolios.py:364-373` and `2_Portfolios.py:173-176`.
- **“Advantage” card** duplicated A/B: `4_Comparison.py:367-375` vs `390-398`.
- **KPI cards** exist in *three* parallel implementations:
  `kpi_v2()` (`styling.py:807`), `kpi_card()` (`styling.py:840`, branches on
  theme), plus ad-hoc `st.metric()` usage in pages 1/2/3. No single source.
- **Tables** hand-built as HTML in two places (`app.py`, `4_Comparison.py`)
  while pages 2/3/4/5 use `st.dataframe`. Inconsistent table strategy.

### 2.4 CSS injected per-page / globally (bleed & conflict risk)

- `apply_global_styles()` (`styling.py:720`) injects the full `_STATIC_CSS`
  (~490 lines) on **every page load**, via `st.markdown(unsafe_allow_html)`.
  `render_sidebar_nav()` then injects `_CSS` (`nav.py:709`) **again on every
  page**, plus a third `<style>` block built inside the JS string
  (`nav.py:549-589`). Three separate stylesheets, two of them re-evaluated per
  rerun.
- `3_My_Portfolios.py:45-123` injects a **page-local `<style>`** targeting
  Streamlit internals with fragile structural selectors:
  `.element-container:has(.btn-add) + .element-container button`. These rely on
  a marker `<div class="btn-add">` (line 164) sitting immediately before the
  button’s container. This is the single most brittle construct in the codebase:
  any change in Streamlit’s DOM ordering silently breaks the `+`/`×`/currency
  buttons. It also leaks globally (no scoping) once injected.
- The **broken-wrapper pattern**: opening a `<div>` in one `st.markdown` call,
  rendering Streamlit widgets, then closing `</div>` in a *separate*
  `st.markdown`. Streamlit renders each `markdown` in its own container, so the
  wrapper **never actually contains the widgets** — the closing tag is orphaned.
  Occurrences: `2_Portfolios.py:170-218` (clone box),
  `3_My_Portfolios.py:163-170` (btn-add), `246-249` (btn-rm). These produce
  stray empty boxes / mismatched DOM and are a known source of layout glitches.
- Heavy reliance on `!important` (hundreds of occurrences in `styling.py` +
  `nav.py`) to win specificity battles against Streamlit’s own CSS — fragile and
  order-dependent.

### 2.5 Navbar / sidebar JS coupling

- `nav.py:422-701` injects a `<script>` (through a hidden sidebar iframe) that
  reaches into `window.parent.document`, mutates `<html>` classes, sets sidebar
  width with `!important`, builds a `<nav>` in `document.body`, and runs a
  `MutationObserver` to re-apply styles after every Streamlit rerender. This is
  powerful but extremely fragile, hard to test, and mixes structure + style +
  behaviour + theme tokens in one f-string. Theme colours are duplicated here
  (`_NAVBAR_DARK`/`_NAVBAR_LIGHT`, `nav.py:121-130`) instead of reusing the
  central palette.

### 2.6 Duplicated / scattered configuration

- `st.set_page_config(...)` repeated with the same args in all 7 entry files
  (`app.py:6`, each page line ~5-10).
- Theme colours defined in **three** places: `styling.py` palette,
  `nav.py` navbar palette, and `.streamlit/config.toml` `[theme]`. Risk of drift.
- `pillar_labels` dict (`environment→Environnement` …) re-declared in
  `app.py:102`, `4_Comparison.py:225`, `5_Explainability.py:204`.

---

## 3. Severity summary

| Pain point | Severity | Why |
|---|---|---|
| Page-local CSS w/ `:has()` sibling selectors (`3_My_Portfolios`) | **High** | Silently breaks on Streamlit upgrade; global leak |
| Broken-wrapper `<div>` across markdown calls | **High** | Orphan tags, layout glitches today |
| 93 hard-coded colours, dark-only literals | **High** | Light theme is broken on several pages |
| Inline HTML f-strings everywhere | Med-High | Unmaintainable, merge-conflict prone |
| 3 parallel KPI/table implementations | Medium | Inconsistent UI, duplicate fixes |
| Triple CSS injection per render | Medium | Perf + specificity wars (`!important`) |
| Navbar JS reaching into parent DOM | Medium | Fragile, untestable, theme drift |
| Logic (PDF/report/import/meta) in pages | Low-Med | Violates separation contract |

---

## 4. Proposed target architecture

### Option A — Stay in Streamlit, centralise templates + one scoped stylesheet

- Move every inline HTML f-string into **Jinja2 templates** (`templates/*.html`)
  rendered by small Python helpers; widgets stay in Streamlit.
- Collapse the three stylesheets into **one** scoped CSS file
  (`streamlit_app/assets/app.css`) injected once, with **CSS custom properties**
  as the single source of truth for palette + a defined **type scale**
  (`--fs-xs … --fs-2xl`, `--space-*`). No inline colours/sizes remain.
- One **reusable component per UI element** (`kpi`, `card`, `section_header`,
  `table`, `banner`, `chip`) in `streamlit_app/components/`.
- Keep `services.py` as the data seam; relocate page-local data
  (`COMPANY_META`, `OFFICIAL_REPORTS`) and the PDF/report builders into the
  data/reporting layer.

**Pros:** smallest, lowest-risk move; app stays runnable after every step; no new
runtime, no API contract, no build toolchain; directly fixes the four high-severity
issues. **Cons:** still bounded by Streamlit’s DOM (some `!important` and the
navbar JS remain, just consolidated and centralised); not a true UI/data split.

### Option B — FastAPI backend + React frontend

- Python keeps data/scoring/reporting only and exposes JSON over the existing
  FastAPI layer; a React app owns 100% of UI (design system, theming, routing).

**Pros:** clean, durable separation; full control of styling/accessibility;
scales to a real product UI. **Cons:** large, multi-week effort; **violates the
prime directive** (no big-bang, app-runnable-after-every-step) unless run as a
long parallel track; duplicates every page; the FastAPI layer
(`src/esg_api/`) is currently thin and would need substantial buildout;
introduces JS/TS build + deploy complexity the project doesn’t have today.

### Recommendation — **Option A now, with a B-friendly seam**

For a project meant to grow, the highest-leverage move is to **first** pay down
the presentation debt in place (Option A): it is incremental, keeps the app
running after each PR, and immediately fixes the broken light theme, the brittle
`:has()` selectors, and the orphan-wrapper bugs. Crucially, Option A **also makes
a future Option B cheaper**: by forcing the separation contract (Python = data
only; presentation = templates/components/CSS only; one palette + one type
scale), the eventual React frontend just consumes the already-clean
`services.py`/FastAPI data, rather than untangling logic from HTML first.

Recommended unless you want to commit to the React track immediately: **Option A**,
sequenced so that the data/logic relocation (PDF, report, `COMPANY_META`) lands
behind the FastAPI seam — leaving the door open to swap Streamlit for React later
without touching the engine or the service layer.

---

## 5. Open questions for approval

1. Approve **Option A** as the target? (vs committing to B now)
2. Jinja2 acceptable as a new dependency? (justified per CLAUDE.md §7)
3. In scope to relocate `COMPANY_META`/`OFFICIAL_REPORTS` and the PDF/report
   builders out of pages, or keep this refactor styling-only and defer logic
   relocation?
4. The broken light theme (§2.2) is a real visual bug — log to `findings.md`
   and fix as part of centralising colours, or leave dark-only for now?

> **STOP — awaiting approval of this audit + the recommended architecture
> before writing the Phase 1 plan or any application code.**
