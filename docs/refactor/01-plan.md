# 01 — Migration Plan (Phase 1)

> Approved direction: **Option A** — stay in Streamlit; move all HTML into
> Jinja2 templates + reusable components; collapse styling into one scoped
> stylesheet with a single palette + type-scale source of truth; relocate
> leaked logic behind the data/service seam; fix the light theme as colours are
> centralised.
>
> **Prime directive:** no big-bang. Every numbered step is one PR-sized change;
> the app stays runnable after each. Execute one step at a time, pausing for
> go-ahead between steps (Phase 2).

---

## 1. Separation contract (the rules every step must uphold)

**Python (pages + helpers)** may contain ONLY:
- data access (`esg_data.services`, fixtures), scoring orchestration,
  filtering/derivation, Streamlit widget calls, and **calls to render helpers**.
- It must NOT contain HTML strings, inline `style="…"`, hex colours, or font
  sizes. The only `unsafe_allow_html` calls allowed are inside the centralised
  renderer/components.

**Presentation** lives ONLY in:
- `streamlit_app/assets/styles.css` — the single stylesheet (structural rules +
  component classes). One file, injected once per page.
- `streamlit_app/templates/*.html` — Jinja2 templates for every HTML fragment.
- `streamlit_app/components/*.py` — thin Python functions that render a template
  with typed arguments and emit it via a single shared `render()` helper.

**Single source of truth:**
- **Colour palette** — CSS custom properties in `:root` (dark) +
  `:root[data-theme="light"]` (light), generated from `tokens.py`. No hex
  literal appears anywhere except `tokens.py` and `styles.css` variable defs.
- **Type scale** — `--fs-xs … --fs-2xl`, `--space-*`, `--radius-*`,
  `--weight-*` custom properties. No raw `rem`/`px` font sizes in pages.
- **Semantic maps** (sector/risk/pillar/score colours) stay in `tokens.py` and
  are exposed to templates as token names, never raw hex in pages.

**Logic relocation target** (approved): page-local data and document builders
move to the data/reporting layer:
- `COMPANY_META`, `OFFICIAL_REPORTS` → `src/esg_data/fixtures/` (or a new
  `sources.py` fixture module).
- `_build_pdf()` (`6_Source.py`), `_build_report()` (`5_Explainability.py`) →
  `src/esg_data/reporting/` (Layer 2 — performs I/O-style document assembly,
  imports only from `esg_core`/fixtures, never from `streamlit_app`).

---

## 2. Target folder structure

```
streamlit_app/
├── app.py                      # dashboard page (thin: data + render calls)
├── bootstrap.py                # NEW: set_page_config + apply styles + nav, one call
├── pages/
│   ├── 1_Entreprises.py        # thin pages, no inline HTML/CSS
│   ├── 2_Portfolios.py
│   ├── 3_My_Portfolios.py
│   ├── 4_Comparison.py
│   ├── 5_Explainability.py
│   └── 6_Source.py
├── assets/
│   └── styles.css              # NEW: the ONE stylesheet (was _STATIC_CSS + nav _CSS)
├── templates/                  # NEW: Jinja2 fragments
│   ├── kpi.html
│   ├── card_company.html
│   ├── section_header.html
│   ├── page_header.html
│   ├── table.html
│   ├── banner.html
│   ├── chip.html
│   ├── activity_feed.html
│   ├── alerts.html
│   ├── advantage_card.html
│   └── nav/ (sidebar.html, navbar/ js stays in nav.py for now)
├── components/                 # NEW: typed render helpers (replace styling.py helpers)
│   ├── __init__.py
│   ├── render.py               # shared Jinja env + render(template, **ctx) + st.markdown
│   ├── kpi.py
│   ├── cards.py
│   ├── tables.py
│   ├── feeds.py
│   └── layout.py               # page_header, section_header
└── utils/
    ├── tokens.py               # NEW: palette + type scale → :root vars (single source)
    ├── styling.py              # SHRINKS to: theme state, score_color/label helpers, css loader
    └── nav.py                  # navbar/sidebar; CSS extracted to styles.css, palette from tokens

src/esg_data/
├── fixtures/ (+ sources.py)    # COMPANY_META, OFFICIAL_REPORTS relocated here
└── reporting/                  # NEW Layer-2: pdf_report.py, text_report.py
```

---

## 3. Ordered migration steps

Each step: **Goal · Files · Risk · Verify · Rollback.** Risk = Low/Med/High.
"Verify" always includes: `uv run ruff check`, `uv run mypy src/`,
`uv run pytest`, then load the affected page(s) in the browser in **both** dark
and light themes and confirm render is identical-or-better.

---

### Step 1 — Foundation: dependency + skeleton + CSS extraction (no visual change)
- **Goal:** Add `jinja2`; create `assets/`, `templates/`, `components/` skeleton
  and `components/render.py` (Jinja env + `render()` that calls
  `st.markdown(..., unsafe_allow_html=True)`). Move the existing `_STATIC_CSS`
  string **verbatim** into `assets/styles.css` and load it from disk in
  `apply_global_styles()`. Output must be byte-equivalent CSS.
- **Files:** `pyproject.toml`, `uv.lock`, `streamlit_app/assets/styles.css` (new),
  `streamlit_app/components/render.py` (new), `templates/` (empty placeholders),
  `streamlit_app/utils/styling.py` (load CSS from file instead of inline string).
- **Risk:** Low. Pure relocation; no rule changes.
- **Verify:** Every page renders identical to `main`. Quality gates pass.
- **Rollback:** Revert the file; `styling.py` keeps the inline string in git.

### Step 2 — Central tokens: palette + type scale as CSS custom properties
- **Goal:** Create `utils/tokens.py` holding the dark/light palettes (moved from
  `styling.py`) + a new **type scale** and spacing/radius tokens. Emit them as
  `:root` / `:root[data-theme="light"]` variables. Add `--fs-*` etc. to
  `styles.css`. No page edits yet; existing `var(--esg-…)` keep working.
- **Files:** `utils/tokens.py` (new), `utils/styling.py` (re-export palette from
  tokens for back-compat), `assets/styles.css` (add type-scale vars).
- **Risk:** Low. Additive; existing variables unchanged.
- **Verify:** Identical render; toggle theme works as before.
- **Rollback:** Revert; `styling.py` palette still in git.

### Step 3 — Component layer: migrate existing shared helpers to templates
- **Goal:** Re-implement the helpers already in `styling.py`
  (`page_header`, `dash_section`, `kpi_v2`, `kpi_card`, `company_card`) as
  Jinja templates + `components/` functions with identical signatures. Pages
  still call the same names (re-exported), so **no page edits required**.
- **Files:** `templates/{page_header,section_header,kpi,card_company}.html`,
  `components/{layout,kpi,cards}.py`, `utils/styling.py` (delegate to components).
- **Risk:** Med (touches shared helpers used by all pages).
- **Verify:** Dashboard + page 1 (cards/KPIs) render identical, both themes.
- **Rollback:** Revert components; `styling.py` helpers still in git.

### Step 4 — Migrate `app.py` (dashboard)
- **Goal:** Replace inline `_mini_bar`, `_pillar_val`, the ranking `<table>`,
  activity feed and alerts with `table`/`feeds`/`alerts` components + templates.
  Replace all hex with tokens (fixes dashboard light mode). Dedupe
  `pillar_labels` via a shared constant.
- **Files:** `app.py`, `components/tables.py`, `components/feeds.py`,
  `templates/{table,activity_feed,alerts}.html`.
- **Risk:** Med.
- **Verify:** Dashboard identical in dark; **readable in light**; filters,
  ranking order, KPI numbers unchanged.
- **Rollback:** Revert `app.py` + the touched templates.

### Step 5 — Migrate `1_Entreprises.py`
- **Goal:** Company-detail card + pillar tiles + carbon block → components/tokens.
- **Files:** `pages/1_Entreprises.py`, `components/cards.py`,
  `templates/{card_detail,pillar_tile}.html`.
- **Risk:** Low-Med.
- **Verify:** Expander cards identical, both themes; filter/search unchanged.
- **Rollback:** Revert page + templates.

### Step 6 — Migrate `2_Portfolios.py`
- **Goal:** Description text, info box, and clone box → components; **fix the
  orphan-wrapper** clone box (F-002) using a valid container/template.
- **Files:** `pages/2_Portfolios.py`, `templates/banner.html`,
  `components/cards.py`.
- **Risk:** Med (clone flow has session-state interactions — verify clone works).
- **Verify:** Catalogue + clone → "Mes Portefeuilles" round-trip works; no stray
  empty boxes; both themes.
- **Rollback:** Revert page + templates.

### Step 7 — Migrate `3_My_Portfolios.py` (largest; split in two)
- **Step 7a — kill the page-local CSS + fix button wrappers.** Move the
  `:has()` button styling (lines 45–123) into `styles.css` under scoped classes;
  replace the brittle marker-`<div>` + sibling-selector pattern and the
  orphan-wrapper btn-add/btn-rm (F-002) with a robust component approach.
  - **Files:** `pages/3_My_Portfolios.py`, `assets/styles.css`.
  - **Risk:** **High** (the +/×/currency buttons are the most fragile UI). Verify
    add/remove position, currency cycle, and create all still work.
- **Step 7b — components + tokens.** Section labels, success/preview banners,
  preview tiles → components; remove remaining hex/font literals.
  - **Files:** `pages/3_My_Portfolios.py`, `templates/{banner,section_header}.html`.
  - **Risk:** Med.
- **Verify:** Create tab (add/remove rows, currency toggle, create), Import tab
  (CSV + JSON, validation errors, preview, create), List tab (delete) — all
  functional; both themes.
- **Rollback:** Revert page (and `styles.css` button block for 7a).

### Step 8 — Migrate `4_Comparison.py`
- **Goal:** Hand-built KPI comparison `<table>` → `table` component; A/B
  "advantage" cards → single `advantage_card` component (dedupe); tokens fix
  light mode; dedupe `pillar_labels`.
- **Files:** `pages/4_Comparison.py`, `components/tables.py`,
  `templates/{table,advantage_card}.html`.
- **Risk:** Med.
- **Verify:** Deltas, colours, theme table render identical (dark) + readable
  (light); selecting A/B works.
- **Rollback:** Revert page + templates.

### Step 9 — Migrate `5_Explainability.py` + relocate report builder
- **Goal:** Section headers + "how to read" / disclaimer callouts → components;
  relocate `_build_report()` to `src/esg_data/reporting/text_report.py`
  (behaviour identical, page just calls it).
- **Files:** `pages/5_Explainability.py`, `src/esg_data/reporting/text_report.py`
  (new), `templates/banner.html`.
- **Risk:** Med (report bytes must be unchanged — assert via a quick diff of the
  generated file before/after).
- **Verify:** Tables, callouts, downloaded report content byte-identical; both
  themes.
- **Rollback:** Revert page + new reporting module.

### Step 10 — Migrate `6_Source.py` + relocate data & PDF builder
- **Goal:** Sector chips, reliability block, official/estimated report cards →
  components/tokens; relocate `COMPANY_META`/`OFFICIAL_REPORTS` to
  `src/esg_data/fixtures/sources.py`; relocate `_build_pdf()` to
  `src/esg_data/reporting/pdf_report.py`.
- **Files:** `pages/6_Source.py`, `src/esg_data/fixtures/sources.py` (new),
  `src/esg_data/reporting/pdf_report.py` (new),
  `templates/{chip,report_card}.html`.
- **Risk:** Med-High (largest logic move; PDF output must be unchanged).
- **Verify:** Company list/search, year select, official link, **PDF download
  opens and matches** previous output; both themes.
- **Rollback:** Revert page + new modules.

### Step 11 — Consolidate navbar/sidebar styling (`nav.py`)
- **Goal:** Move `nav._CSS` and the JS-string `<style>` rules into `styles.css`;
  source the navbar palette from `tokens.py` (kills the
  `_NAVBAR_DARK/_LIGHT` drift). Keep the JS behaviour (collapse/observer) but it
  no longer carries CSS. Single stylesheet now.
- **Files:** `utils/nav.py`, `assets/styles.css`, `utils/tokens.py`.
- **Risk:** **High** (navbar JS is fragile, theme-dependent). Isolated, late step.
- **Verify:** Navbar + sidebar collapse/expand, active-link highlight, theme
  toggle, page-name chip, tooltip — all work in both themes across every page.
- **Rollback:** Revert `nav.py` + `styles.css` nav block.

### Step 12 — Final sweep, dedupe, bootstrap, summary
- **Goal:** Add `bootstrap.py` to collapse the repeated
  `set_page_config + apply_global_styles + render_sidebar_nav` into one call;
  remove dead helpers; assert **zero** inline hex/font-size remain in pages
  (`grep` gate); reconcile `.streamlit/config.toml` theme with `tokens.py`.
  Write `docs/refactor/summary.md`.
- **Files:** `streamlit_app/bootstrap.py` (new), all entry files (one-line swap),
  `utils/styling.py` cleanup, `docs/refactor/summary.md`.
- **Risk:** Low-Med.
- **Verify:** Full click-through of all pages, both themes; grep gates green;
  quality gates pass.
- **Rollback:** Revert per file.

---

## 4. Cross-cutting verification checklist (run each step)

- [ ] `uv run ruff check` clean
- [ ] `uv run mypy src/` clean
- [ ] `uv run pytest` green (engine behaviour unchanged)
- [ ] Affected page(s) render identical-or-better in **dark**
- [ ] Affected page(s) **readable/correct in light**
- [ ] No new `unsafe_allow_html` outside `components/`
- [ ] No raw hex / font-size added to pages
- [ ] `docs/refactor/progress.md` entry appended

---

## 5. Risks & mitigations (summary)

| Risk | Step | Mitigation |
|---|---|---|
| Streamlit DOM selectors break buttons | 7a | Replace `:has()`+marker with component classes; verify all button actions |
| Report/PDF bytes change | 9, 10 | Diff generated output before/after; relocate logic verbatim |
| Navbar JS regressions | 11 | Isolated late step; CSS-only move, behaviour untouched |
| Theme drift between css/tokens/config | 12 | Single `tokens.py` source; reconcile `config.toml` |
| Hidden behaviour change during relocation | 9, 10 | Move code verbatim; no signature/logic edits |

> **STOP — awaiting approval of this plan before executing Step 1 (Phase 2).**
