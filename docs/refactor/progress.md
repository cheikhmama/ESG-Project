# Progress — step-by-step execution log

> One entry per completed migration step (see `01-plan.md`). Each records what
> changed, how it was verified, and any deviations. No scoring/data/business
> behaviour is altered — structure only.

---

## Step 1 — Foundation: dependency + skeleton + CSS extraction ✅

**Date:** 2026-06-06

**Goal:** Add `jinja2`; create the `assets/` + `templates/` + `components/`
skeleton and a Jinja render seam; move the inline `_STATIC_CSS` string verbatim
into `assets/styles.css` and load it from disk. No visual change.

**Changes**
- `pyproject.toml` — added `jinja2>=3.1` to the `dashboard` extra; `uv.lock`
  updated (jinja2 3.1.6).
- `streamlit_app/assets/styles.css` (new) — the entire structural stylesheet,
  copied **verbatim** from the old `_STATIC_CSS` literal (13.4 KB).
- `streamlit_app/utils/styling.py` — removed the inline `_STATIC_CSS` block;
  added `_static_css()` (a `lru_cache`d disk loader reading `assets/styles.css`);
  `apply_global_styles()` now injects `f"<style>{_root_vars(p)}\n{_static_css()}</style>"`.
- `streamlit_app/components/__init__.py` (new) — package docstring.
- `streamlit_app/components/render.py` (new) — single autoescaping Jinja
  environment (`FileSystemLoader` → `templates/`); `render()` returns HTML,
  `render_into()` injects via `st.markdown(..., unsafe_allow_html=True)`. This is
  the one place HTML is produced going forward.
- `streamlit_app/templates/.gitkeep` (new) — empty templates dir placeholder.

**Verify**
- `uv run ruff check` on changed files — clean.
- `uv run mypy streamlit_app/components/render.py streamlit_app/utils/styling.py`
  — no issues.
- `uv run pytest` — 16 passed.
- Module import: `styling._static_css()` returns 13.4 KB; `components.render`
  imports and resolves the templates dir.
- Live app (port 8502): no server/console errors. Injected `<style>` confirmed
  to contain the Inter `@import`, `--esg-bg` root vars, the primary-button
  shadow rule (`rgba(99,102,241,0.45)`), and the details-marker rule. Body font
  = Inter; dark bg = `#0c1321`.
- Theme toggle (`?theme=light`): `--esg-bg` switches to `#f1f5f9` while the
  static CSS loads identically — same behaviour as before the change.

**Deviations / notes**
- The working tree's `_STATIC_CSS` was larger than the `HEAD` version (it had
  uncommitted edits); byte-equivalence was therefore verified against the
  pre-edit working-tree string, not `HEAD`.
- `bodyBg` stays dark in light mode because Streamlit's own `[theme] base=dark`
  in `.streamlit/config.toml` drives the app shell — this is the pre-existing
  F-001 issue, reconciled in Step 12. Not a regression from Step 1.

**Rollback:** revert the listed files; `styling.py` retains the inline string in
git history.

---

## Step 2 — Central tokens: palette + type scale as CSS custom properties ✅

**Date:** 2026-06-06

**Goal:** Establish a single source of truth for design tokens. Move both
palettes out of `styling.py` into a new `utils/tokens.py`, add a theme-independent
**type scale** (+ font-weight, line-height, spacing, radius) emitted as `--fs-*` /
`--fw-*` / `--lh-*` / `--space-*` / `--radius-*` custom properties. Additive only —
no page edits, existing `var(--esg-…)` keep working.

**Changes**
- `streamlit_app/utils/tokens.py` (new) — the canonical token module:
  - `DARK` / `LIGHT` palette dicts (moved verbatim from `styling.py`).
  - `PALETTE_VARS` — the ordered palette-key → `--esg-*` name map.
  - `FONT_SIZE` (12-step, `0.55rem`→`2rem`), `FONT_WEIGHT`, `LINE_HEIGHT`,
    `SPACE`, `RADIUS` scales, distilled from literals already in the app.
  - `palette_css(p)` — renders the active palette's `:root` block.
  - `static_tokens_css()` — renders the theme-independent scale `:root` block.
- `streamlit_app/utils/styling.py`:
  - imports `tokens`; `_DARK = tokens.DARK`, `_LIGHT = tokens.LIGHT`
    (back-compat re-exports — `palette()`/`current_theme()` unchanged).
  - `_root_vars()` now delegates to `tokens.palette_css()`.
  - `apply_global_styles()` injects
    `palette_css + static_tokens_css + _static_css()`.

**Verify**
- Palette parity: programmatically confirmed `tokens.palette_css()` emits exactly
  the same **40** `--esg-*` variables with identical values as the old
  `_root_vars()`, in both themes (0 mismatches, 0 extras).
- `uv run ruff check` (tokens.py, styling.py) — clean.
- `uv run mypy` (tokens.py, styling.py) — no issues.
- `uv run pytest` — 16 passed.
- Live app (port 8502), dark theme: scale tokens resolve in `:root`
  (`--fs-base 0.83rem`, `--fs-5xl 2rem`, `--fw-bold 700`, `--space-4 1rem`,
  `--radius-xl 14px`); palette renders in the new format (`--esg-bg #07111f`).
- `?theme=light`: palette flips (`--esg-bg #f1f5f9`, `--esg-text #0f172a`) while
  the static scale tokens persist (theme-independent). No console errors.

**Deviations / notes**
- The plan suggested adding `--fs-*` directly into `styles.css`. Instead they are
  emitted from `tokens.static_tokens_css()` so the scale has a **single** source
  (tokens.py) with no checked-in duplicate. Net effect on the page is identical
  (vars land in `:root`); the values are simply generated rather than hand-copied.
- A pre-existing **stale Streamlit process** (old session) was still bound to
  port 8502 and initially served old CSS; killed it and relaunched clean to
  verify. Not related to the code change.
- Pages still hard-code font-size/colour literals — adopting these tokens happens
  in the later per-page steps (4–10), as planned.

**Rollback:** revert `styling.py` + delete `tokens.py`; palettes remain in git
history inside `styling.py`.

---

## Step 3 — Component layer: migrate shared helpers to templates ✅

**Date:** 2026-06-06

**Goal:** Re-implement the five shared helpers (`page_header`, `dash_section`,
`kpi_v2`, `kpi_card`, `company_card`) as Jinja templates + thin `components/`
functions. `styling.py` keeps the same public names/signatures and delegates, so
**no page edits are required**. Render must be identical.

**Changes**
- Templates (new): `templates/page_header.html`, `section_header.html`,
  `kpi.html` (kpi_v2), `kpi_card.html` (kpi_card dark box), `card_company.html`.
- Components (new):
  - `components/layout.py` — `page_header`, `dash_section`.
  - `components/kpi.py` — `kpi_v2` (computes arrow + progress fill),
    `kpi_card_dark`.
  - `components/cards.py` — `company_card(**ctx)` (presentation-only; receives
    pre-computed colours/values).
- `streamlit_app/utils/styling.py` — imports `cards`, `kpi`, `layout`; the five
  helpers now delegate. `company_card` still computes its context (palette,
  `score_color`, `score_label`, sector/risk colours, formatted numbers) and
  passes it to the component. `kpi_card` keeps its theme branch (light →
  `ui.metric_card`; dark → `kpi_card_dark`).

**Verify**
- Offline HTML parity (whitespace-normalised, single→double quotes): all five
  templates reproduce the old f-string output exactly. **The comparison caught a
  real bug in my first `card_company.html` draft** — the original Symbole cell
  emitted `font-weight:700;font-weight:600;…` (duplicate; CSS last-wins → 600). I
  had dropped the duplicate (would have rendered 700). Restored the duplicate so
  the effective weight stays 600. Confirmed identical afterwards.
- `uv run ruff check` (components/, styling.py) — clean.
- `uv run mypy` (5 files) — no issues. No circular import (`components/*` import
  only `render`; `styling` imports `components`).
- `uv run pytest` — 16 passed.
- Live app (port 8502): dashboard renders page header ("Tableau de Bord"), 4
  `.dash-section`, 4 `.kpi-v2`; Sociétés page header ("Sociétés"). Light theme
  (`?theme=light`): same elements render, `--esg-bg #f1f5f9`, KPI accent colour
  intact. No console errors.

**Deviations / notes**
- Autoescaping is **on** in the Jinja env. The only behavioural effect is that
  `&` in a value (e.g. sector "Mining & Metals") becomes `&amp;` — valid HTML
  that renders identically (the old f-strings emitted a raw `&`).
- **`company_card` and `kpi_card` are not called by any page** (page 1 builds its
  own expander markup). They were migrated faithfully for completeness but render
  nowhere live; flagged as **dead-helper removal candidates for Step 12**.
- `chip` / `val_style` constant style strings are now inlined directly in
  `card_company.html` rather than passed as context.

**Rollback:** revert `styling.py`; delete the new `components/{layout,kpi,cards}.py`
and the five templates. Old helper bodies remain in git history.

---

## Step 4 — Migrate the dashboard (`app.py`) to components + templates ✅

**Date:** 2026-06-06

**Goal:** Move the dashboard's three hand-built HTML blobs (the company ranking
table, the activity feed, the risk alerts) out of `app.py` into Jinja templates
+ thin `components/` functions, replacing scattered inline `style="…"` with
semantic CSS classes. Convert the two **theme-accent** literals to tokens and
fix the two **theme-breaking** literals so the dark render is byte-identical and
the light render becomes readable. No data, ordering, or scoring change.

**Changes**
- `streamlit_app/utils/tokens.py`:
  - new palette key `track` — dark `rgba(255,255,255,0.06)` (identical to the
    old hard-coded mini-bar track), light `rgba(0,0,0,0.06)` (the fix).
  - emitted three previously-unexposed palette vars: `--esg-accent`,
    `--esg-accent-alt`, `--esg-track` (added to `PALETTE_VARS`).
- `streamlit_app/assets/styles.css` — added ranking-table cell/element classes
  (`.rank-num`, `.rank-name`, `.rank-ticker`, `.rank-bar*`, `.rank-pillar`,
  `.rank-pillar-empty`, `.rank-carbon`, `.rank-chip{,-sector,-risk}`),
  `.activity-score`, and moved the alert-chip `margin-left:7px` from inline into
  `.alert-chip`. Every value copied verbatim from the old inline styles; the
  track uses `var(--esg-track)` and the empty-pillar dash uses
  `var(--esg-text-sub)` (was hard-coded `#354860`). td-level overrides use
  `.rank-table td.rank-num` / `td.rank-carbon` (specificity beats `.rank-table td`).
- Templates (new): `templates/table.html`, `activity_feed.html`, `alerts.html`.
- Components (new): `components/tables.py` (`ranking_table(rows, header_colors)`),
  `components/feeds.py` (`activity_feed(items)`, `risk_alerts(items)`) — all
  presentation-only, receiving pre-computed colours/strings.
- `streamlit_app/utils/styling.py` — added the shared `PILLAR_LABELS` constant
  (Environnement/Social/Gouvernance), used by the chart legend.
- `streamlit_app/app.py` — removed the `_mini_bar`/`_pillar_val` helpers and the
  three inline-HTML `st.markdown(...)` blocks; now builds plain data dicts and
  calls the components. Deduped the inline `label_map` → `PILLAR_LABELS`. The two
  theme-accent KPI colours changed from literals to tokens: `#2d7aed` →
  `var(--esg-accent)`, `#7c5cbf` → `var(--esg-accent-alt)`. The two **semantic**
  KPI colours (`#0ea672` green-best, `#e89e0c` amber-emissions) stay literal —
  they are status colours, theme-independent, and also feed nothing themeable.
- `pyproject.toml` — added `plotly.*` to the mypy `ignore_missing_imports`
  override (plotly is already a dep; matches the existing shap/streamlit entries).

**Verify**
- Offline parity (whitespace-normalised): templates reproduce the old f-string
  output; the only diffs are (a) the intended inline-style→class swap, each
  class's CSS values confirmed equal to the old inline values, and (b) the
  Step-3 autoescape note (`&` → `&amp;`, identical render).
- `uv run ruff check` — new component/util files clean. `app.py` retains only its
  **pre-existing** E402 / PLC0415 / PLR1714 (the `set_page_config`-before-imports
  pattern shared by all 6 pages, the intentional lazy `compute_all_scores`
  import, and the filter-loop comparison). The committed `app.py` had 30 ruff
  findings; this step introduced no new categories.
- `uv run mypy` (app.py + 4 changed files) — **Success, no issues**. Three
  pre-existing findings surfaced by type-checking `app.py` for the first time were
  fixed in passing (behaviour-neutral): removed 2 dead `type: ignore[union-attr]`
  in the filter loop; renamed the alerts-loop `em`→`em_alert` to avoid a
  module-scope type clash with the ranking loop's `em` (`Emissions` vs
  `Emissions | None`); added the plotly mypy override.
- `uv run pytest` — 16 passed. `uv run lint-imports` — 2 contracts kept
  (components import only `render`; `app.py` is layer 4).
- Live app (port 8502), **dark** — computed styles byte-identical to the old
  inline values: track `rgba(255,255,255,0.06)`, `.rank-name` 13.12px (0.82rem)
  / `#dce8f8`, `.rank-num` 0.7rem / padding-left 16px, sector chip fw 600, risk
  chip fw 700, `.activity-score` fw 600, `.alert-chip` margin-left 7px; KPI
  accents resolve to `#2d7aed` / `#7c5cbf`; 4 table rows, 4 activity, 4 alerts.
  No server/console errors.
- Live app, **light** (`?theme=light`) — now readable: mini-bar track flips to
  `rgba(0,0,0,0.06)` (was invisible white-on-white), empty-pillar dash uses
  `--esg-text-sub` `#94a3b8` (was near-invisible `#354860`), accent KPIs theme to
  `#6366f1` / `#7c3aed`, while the semantic green/amber KPIs stay `#0ea672` /
  `#e89e0c`. Ranking order, filters and KPI numbers unchanged.

**Deviations / notes**
- The empty-pillar (`—`) branch isn't exercised in the default unfiltered view
  (all four companies have all three pillars), so its live computed colour wasn't
  observed; covered by the offline parity check instead.
- Kept exact `rem`/`px` font-size values in the new CSS rather than rounding to
  `--fs-*` scale tokens — snapping would shift pixels and break the byte-identical
  dark render. Scale-token adoption remains a later, deliberate step if desired.
- `app.py`'s pre-existing E402/PLC0415/PLR1714 were left as-is (shared by every
  page; out of scope for a dashboard-structure step) — candidate for a dedicated
  lint-debt pass.

**Rollback:** revert `app.py`, `styling.py`, `tokens.py`, `styles.css`,
`pyproject.toml`; delete `components/{tables,feeds}.py` and the three templates.

---

## Step 5 — Migrate the company directory (`1_Entreprises.py`) ✅

**Date:** 2026-06-06

**Goal:** Move the per-company expander's three hand-built HTML blocks (the
detail card — sector chip + country/effectif fields, the carbon-total banner,
and the three pillar tiles) out of `pages/1_Entreprises.py` into Jinja templates
+ thin `components/` functions, replacing inline `style="…"` with semantic CSS
classes. No data, ordering, filter, or scoring change.

**Changes**
- Templates (new): `templates/company_detail.html` (sector chip + Pays/Effectif
  fields; dynamic `sector_color` stays inline), `templates/carbon_total.html`
  (Total CO₂e banner), `templates/pillar_tile.html` (per-pillar score tile;
  dynamic pillar `color` stays inline), `templates/section_label.html`
  (section header with optional `flush` modifier).
- Components: `components/cards.py` — added `company_detail(**ctx)`,
  `carbon_total(total_str)`, `pillar_tile(color, score_str, label)`.
  `components/layout.py` — added `section_label(title, *, flush=False)`.
- `streamlit_app/assets/styles.css` — added `.section-header.flush`
  (`margin-top:0`) plus the page-1 classes: `.co-detail`, `.co-detail-chips`,
  `.co-chip-sector`, `.co-field` (+`.co-field + .co-field` 6px gap),
  `.co-field-label` (`var(--esg-text-sub)`), `.co-field-value`
  (`var(--esg-text)`), `.carbon-total{,-label,-value}` (panel bg/border),
  `.pillar-tile{,-score,-label}` (panel bg). All copied verbatim from the old
  inline values; theme-dependent colours use palette tokens.
- `streamlit_app/pages/1_Entreprises.py` — removed the three inline-HTML
  `st.markdown(...)` blocks; now passes pre-computed strings/colours to the new
  components. Imports trimmed (dropped `palette`, `plotly_layout`; added
  `cards`, `layout`, `PILLAR_LABELS`). Filter/search logic untouched.

**Verify**
- `uv run ruff check` — new component/template-backed code clean; the page
  retains only its **pre-existing** N999 (numeric filename) / E402 / E501 /
  PLC0415 / RUF005 / PLR1714, no new categories.
- `uv run mypy` (3 changed source files) — **Success, no issues found**.
- `uv run pytest` — 16 passed. `uv run lint-imports` — contracts kept.
- Live app (port 8502), **dark** — computed styles byte-identical to the old
  inline values: sector chip 11.52px / fw 600 / `#ef4444` text on 0.094-alpha
  bg ("Mining & Metals"); field-label `#354860`-equiv `--esg-text-sub` 10.4px
  fw 600; field-value `--esg-text` 13.28px fw 500; 2nd field margin-top 6px;
  carbon panel bg/border + value 16px fw 700; pillar tile panel bg / 10px /
  green border / score `#22c55e` 25.6px fw 800; section-header accent 10.08px,
  flush margin-top 0. Counts: 4 co-detail, 12 pillar, 4 carbon, 8 section.
- Live app, **light** (`?theme=light`) — palette flips correctly: appBg
  `#f1f5f9`, panel `#ffffff`, text `#0f172a`, accent `#6366f1`, track
  `rgba(0,0,0,0.06)`. All page-1 elements readable: carbon/pillar panels white
  with dark text, field-label `#94a3b8`, field-value/value `#0f172a`, section
  accent `#4f46e5`, chip/pillar-score keep their semantic colours. Filter,
  search and expander order unchanged. No server/console errors.

**Deviations / notes**
- Same as Step 4: kept exact `rem`/`px` font-size values in the new CSS rather
  than snapping to `--fs-*` scale tokens, to preserve the byte-identical dark
  render. Scale-token adoption remains a later deliberate step.
- The empty-pillar branch (`pscore = 0.0` when `cs.pillar(...)` is `None`) isn't
  exercised in the default data (all companies have all three pillars).

**Rollback:** revert `pages/1_Entreprises.py`, `components/cards.py`,
`components/layout.py`, `styles.css`; delete the four new templates
(`company_detail`, `carbon_total`, `pillar_tile`, `section_label`).

---

## Step 6 — Migrate the reference-portfolio catalogue (`2_Portfolios.py`) ✅

**Date:** 2026-06-06

**Goal:** Move the catalogue page's three `unsafe_allow_html` blocks (the muted
description text, the `<hr>` separator, and the clone-confirmation box) out of
the page; **fix the orphan-wrapper clone box (F-002)** with a robust native
container; fix the description's frozen colour (F-001). No data, ordering, or
clone-behaviour change.

**Changes**
- Templates (new): `templates/portfolio_desc.html` (`.portfolio-desc` muted
  lead paragraph) and `templates/divider.html` (a plain `<hr>`).
- Components: `components/layout.py` — added `portfolio_description(text)` and
  `divider()` (routes `<hr>` through the render seam).
- `streamlit_app/assets/styles.css` — added `.portfolio-desc`
  (`var(--esg-text-muted)`, `0.83rem`, `margin-bottom:20px`) and the
  `[class*="st-key-clonebox_"]` rule carrying the clone panel's tint verbatim
  (`rgba(99,102,241,0.07)` bg, `rgba(99,102,241,0.25)` border, 10px radius,
  18px 20px padding, 12px top margin).
- `streamlit_app/pages/2_Portfolios.py`:
  - description blob → `layout.portfolio_description(pdef["description"])`
    (F-001: dark-only `#64748b` → `--esg-text-muted` token).
  - `st.markdown("<hr>")` → `layout.divider()`.
  - **F-002 fix:** the clone box's orphan `st.markdown("<div …>")` …
    `st.markdown("</div>")` pair is replaced by a single keyed container
    `st.container(key=f"clonebox_{pdef['id']}")` that genuinely wraps the text
    input + confirm/cancel buttons; styling comes from the `st-key-clonebox_*`
    CSS rule. No marker-`<div>`/sibling-selector hack introduced.
  - import added: `from streamlit_app.components import layout`.
- `pyproject.toml` — added `pandas.*` to the mypy `ignore_missing_imports`
  override (pandas is already a dashboard dep; matches the plotly/shap entries).

**Verify**
- `uv run ruff check` — `layout.py` clean; the page retains only its
  **pre-existing** N999 / E402 / E501 / PLC0415 / RUF005 / PLR1714 / C408 (the
  C408 `dict()`-literal findings are all in the untouched plotly chart code).
  No new categories.
- `uv run mypy` (2 changed source files) — **Success, no issues**. Two
  pre-existing findings surfaced by type-checking this page for the first time
  were fixed in passing (behaviour-neutral): the dead `# type: ignore[arg-type]`
  on `build_portfolio(pdef)` removed; `pandas.*` added to the mypy override.
- `uv run pytest` — 16 passed. `uv run lint-imports` — 2 contracts kept.
- Live app (port 8502), **dark** — description resolves to `--esg-text-muted`
  `#506070` (rgb 80,96,112), 13.28px (0.83rem), margin-bottom 20px. Divider:
  `outerHTML` is exactly `<hr>` inside `stMarkdownContainer`, rendered by
  Streamlit's own `border-bottom:1px solid rgba(226,232,240,0.2)` / 32px margins
  — **identical to the old `st.markdown("<hr>")`** (same underlying call).
  **F-002:** clicking *Cloner* shows the keyed container
  `st-key-clonebox_mauritania-diversified` with the exact old tint
  (bg `rgba(99,102,241,0.07)`, border `1px solid rgba(99,102,241,0.25)`, 10px
  radius, 18px 20px padding, 12px top margin) and — crucially — the text input
  **and** both buttons are now *inside* it (no orphan tags). Clicking
  *Confirmer le clonage* fires the append (success alert
  "… ajouté à Mes Portefeuilles." rendered).
- Live app, **light** (`?theme=light`) — palette flips (`--esg-bg` `#f1f5f9`),
  description themes to `--esg-text-muted` `#475569` (readable; old frozen
  `#64748b` fixed), clone box keeps its indigo tint and still wraps the widgets.
  No server/console errors.

**Deviations / notes**
- **F-001 dark delta (documented):** the description's dark colour shifts
  `#64748b` → `--esg-text-muted` `#506070`. The old literal was a one-off; every
  other muted body string in the app already uses `--esg-text-muted`, so this
  *harmonises* the dark theme rather than diverging it, and is the exact F-001
  mechanism (inline hex → palette var) approved in the plan. Trivially
  reverted if the original lighter tint is preferred.
- **Cross-page clone round-trip not directly observable in the preview harness:**
  each navigation (browser `location.assign` or clicking the sidebar page link)
  starts a *fresh Streamlit session*, so `st.session_state["user_portfolios"]`
  resets and the cloned entry isn't visible on the *Mes Portefeuilles* tab of
  page 3. This is a harness artifact that hits the **unchanged original code
  identically** — not a regression. The clone *append* is confirmed by the
  in-page success toast, and the keyed-container change cannot affect the
  append logic. Real-browser MPA navigation preserves session_state.
- `<hr>` and the clone-box tint kept literal rather than tokenised: the divider
  line is Streamlit-owned (theme-neutral) and the clone tint is a faint
  decorative accent kept byte-identical to honour "dark exactly as-is".

**Rollback:** revert `pages/2_Portfolios.py`, `components/layout.py`,
`styles.css`, `pyproject.toml`; delete `templates/portfolio_desc.html` and
`templates/divider.html`.

---

## Step 7a — Kill page-local CSS + fix fragile action buttons (`3_My_Portfolios.py`) ✅

**Date:** 2026-06-06

**Goal:** Remove the page-injected `<style>` block from `3_My_Portfolios.py`
(the `:has()` / marker-`<div>` + sibling-selector hack for the +/×/currency
buttons) and re-implement the same styling in `assets/styles.css`, scoped to
each widget's own `st-key-*` wrapper. Also drop the three orphan marker `<div>`s
(F-002) that wrapped those buttons. The most fragile UI in the app — buttons
must keep identical look + behaviour.

**Changes**
- `streamlit_app/pages/3_My_Portfolios.py`
  - Removed the entire page-local `<style>` block (was inside `with tab_create:`).
  - `btn-add` marker `<div class='btn-add'>` open/close removed; the `+` button
    is now a plain `st.button("+", key="add_pos", help=…)`, collapsed with the
    `n < len(COMPANIES)` guard into one `if … and st.button(…)` (SIM102).
  - `cur-badge` marker `st.markdown('<div class="cur-badge">…')` line removed;
    the currency button keeps `key=f"pos_{pid}_cur_btn"`.
  - `btn-rm` marker `<div class="btn-rm">` open/close removed; the `×` button is
    a plain `st.button("×", key=f"pos_{pid}_remove", help=…)`, collapsed with the
    `len(pos_ids) > 1` guard into one `if … and st.button(…)` (SIM102).
  - **No** session-state / business logic touched: `pos_ids`, `pos_next_id`,
    `_NAME_TO_TICKER`, `_CURRENCIES`, the currency-cycle modulo, the create
    logic, and `to_remove` + `st.rerun()` are unchanged.
- `streamlit_app/assets/styles.css` — appended a "Mes Portefeuilles (page 3):
  position-row action buttons" section with the same rules as the old inline
  block, re-scoped to `st-key-*`:
  - stepper-hide scoped to `[class*="st-key-pos_"][class*="_inv"]`
    (`stNumberInputStepUp/Down { display:none }`) — page-local, not global.
  - `.st-key-add_pos button` — 34px indigo circle (`#6366f1`, 1.5px solid,
    radius 50%, fs 1.3rem) + hover/focus/active.
  - `[class*="st-key-pos_"][class*="_remove"] button` — 28px red circle
    (`#ef4444`, border `rgba(239,68,68,0.4)`, opacity 0.75) + hover.
  - `[class*="st-key-pos_"][class*="_cur_btn"] button` — 38px badge (radius 6px,
    `#818cf8`, border `rgba(99,102,241,0.25)`, full width) + hover.
  - All values copied **verbatim** from the removed inline block, all `!important`.

**Verify**
- Quality gates: `ruff check` clean (excluding the repo's pre-existing
  N999/E402/E501/PLC0415/RUF005/PLR1714/C408/RUF001/RUF003/B905/B007 set);
  `mypy src/` Success (my edits clean); `pytest` 16 passed; `lint-imports`
  2 contracts kept.
- Live (preview, port 8502, /My_Portfolios → Créer tab):
  - `+` renders as a 34px indigo circle (color/border `rgb(99,102,241)`,
    radius 50%, fs 20.8px); steppers hidden on the investment number inputs.
  - Clicking `+` → 2 position rows, each gaining a 28px red-circle `×`
    (`rgb(239,68,68)`, opacity 0.75, radius 50%); clicking `×` → back to 1 row,
    `×` hidden again (correct, only shown when >1 position).
  - Currency badge cycles `USD → EUR` on click (38px, color `rgb(129,140,248)`).
  - "Créer le portefeuille" click fires the name-required validation branch
    correctly.
  - No console errors.

**Deviations / notes**
- The action-button colours (`#6366f1`, `#ef4444`, `#818cf8`) stay **literal** —
  they are theme-independent decorative accents, so they render identically in
  dark and light; no `--esg-*` token applies.
- The "two `<button>`s per wrapper" seen in the DOM is Streamlit's hidden 0×0
  tooltip duplicate from the `help=` param (present in the original code) — not
  a regression; the visible button is styled, the hidden one is 0×0.
- Full create round-trip (typing a name → portfolio appears in "Mes
  portefeuilles") can't be driven in the harness: synthetic `input`/`change`
  events don't update Streamlit's React text-input state, so the name reads
  empty and the validation guard fires. This is a harness limitation that hits
  the **unchanged original code identically** — not a regression. The button
  click + validation branch are confirmed working.
- **Deferred to Step 7b (not expanded into 7a):** three **pre-existing** mypy
  `float`-on-`object` errors in `tab_import` (confirmed present at `HEAD` via
  `git show`); they live in untouched business-logic code that 7b migrates.

**Rollback:** revert `pages/3_My_Portfolios.py` and the appended button section
in `assets/styles.css`.

---

## Step 7b — Migrate remaining HTML in `3_My_Portfolios.py` to components ✅

**Date:** 2026-06-06

**Goal:** Replace every remaining inline `st.markdown(..., unsafe_allow_html=True)`
blob in `3_My_Portfolios.py` (field/column labels, positions header, position
badge, allocation tiles, success banners, import info card, preview header,
empty state, spacer divs) with Jinja templates behind the render seam. Tokenise
the F-001 text-colour literals so the page is legible in light mode. Fix the
three pre-existing `tab_import` mypy errors deferred from 7a.

**Changes**
- `streamlit_app/templates/` (new): `field_label.html`, `col_label.html`,
  `positions_header.html`, `position_number.html`, `alloc_tile.html`,
  `info_card.html`, `preview_header.html`, `banner.html`, `empty_state.html`,
  `vspace.html`. Each is a small markup snippet referencing a CSS class; the
  fixed `<br>` in the empty-state copy is baked into the template (not passed as
  a variable) so autoescaping can't mangle it.
- `streamlit_app/components/layout.py`: added `field_label`, `column_label`,
  `positions_header`, `position_number`, `allocation_tile`, `info_card`,
  `preview_header`, `success_banner`, `empty_state`, `vspace` — thin
  `render_into` wrappers. `success_banner` covers both shapes (manual-create
  breakdown via `holdings`/`count`/`capital`; import confirmation via `subtitle`).
- `streamlit_app/pages/3_My_Portfolios.py`:
  - All ~14 `unsafe_allow_html` blocks across the three tabs replaced by the
    `layout.*` calls above. `grep` confirms **zero** `unsafe_allow_html` /
    `st.markdown` calls remain in the page.
  - The two `section-header` markdown calls → `layout.section_label(...)`.
  - **mypy fix:** `matched: list[dict[str, object]]` → `list[dict[str, str | float]]`,
    which resolves the three `float`-on-`object` errors in `tab_import` (the
    values stored are only `str`/`float`). Behaviour-identical — annotation only.
  - **No** session-state / scoring / create / import / delete logic touched.
- `streamlit_app/assets/styles.css`: appended a "labels, tiles, banners, cards"
  section. Font sizes/spacing copied **verbatim** from the removed inline styles.

**Colour mapping (F-001).** Only the three explicitly-listed page-3 offenders
were tokenised; everything else stays a literal in the CSS class to keep the
dark theme byte-identical:
- `#475569` → `var(--esg-text-muted)` (dark `#506070`, light `#475569`) — labels.
- `#e2e8f0` → `var(--esg-text-heading)` (dark `#dce8f8`, light `#0f172a`) — titles
  / "Capital total" bold.
- `#64748b` → `var(--esg-text-muted)` (Step 6 precedent) — allocation-tile name.
- **Kept literal** (theme-independent decorative / faint): `#6366f1`, `#8b5cf6`,
  `#22c55e`, the gradient, `#94a3b8` (banner/info body grey), and the empty-state
  greys `#334155` / `#1e293b` (deliberately faint, not in the page-3 F-001 list).

**Verify**
- Gates: `ruff` — no new problematic codes (vs `HEAD`: `E501` 4→2, `I001` 1→0,
  `RUF001` 2→1; the only increase is one extra `E402`, the Streamlit
  `set_page_config`-before-imports pattern shared by every page); `mypy src/`
  Success **and** `mypy` on the page now Success (3 prior errors fixed);
  `pytest` 16 passed; `lint-imports` 2 contracts kept.
- Live (preview 8502): **Créer** — `Nom du portefeuille` label `#506070`,
  10.4px; `Positions` title `#dce8f8` + count pill "1"; gradient position badge;
  column labels `Société / Secteur / Montant / Devise` intact. **Importer** —
  info card (indigo tint, `#94a3b8` body, `Champs requis` title `#dce8f8`, four
  `#6366f1` code chips), `Fichier` label. **Mes portefeuilles** — empty state
  (`—` `#1e293b`, `<br>` renders), both section labels via component.
- The three interaction-gated templates (`alloc_tile`, `banner` manual+import,
  `preview_header`, `positions_header`) were rendered directly through the seam
  and produce the exact expected markup (loop over holdings, count pill, capital
  bold).
- Light theme (`?theme=light`): labels switch to `#475569`, titles to `#0f172a`
  — i.e. legible, **F-001 fixed** for this page. No console errors.

**Deviations / notes**
- Selectbox-driven flows (allocation preview, manual success banner) can't be
  driven in the harness (baseweb options render in a portal); their templates
  were instead verified by direct seam render — same mechanism as the info-card
  / empty-state which **are** confirmed live.
- Import success banner: the inline bold on "Mes portefeuilles" became plain
  guillemets « Mes portefeuilles » (the generic `banner.html` subtitle is
  autoescaped text). Trivial, theme-neutral cosmetic change.
- Minor spacing normalisation (≤4px) folded into the `.cp-label` modifiers
  (`.rep`, `.imp`); imperceptible, theme-neutral.

**Rollback:** revert `pages/3_My_Portfolios.py`, `components/layout.py`, the
appended section in `assets/styles.css`; delete the ten new `templates/*.html`
files listed above.

---

## Step 8 — Migrate `4_Comparison.py`

**Goal:** Hand-built KPI comparison `<table>` → component; the two near-identical
A/B "advantage" blocks → a single deduped `advantage_block` component; the VS
divider and empty-selection placeholder routed through the seam; the local
`pillar_labels` dict deduped against `styling.PILLAR_LABELS`; F-001 frozen
table/advantage colours tokenised. Structure-only — no scoring, delta or
formatting maths changed.

**Files**
- `templates/comparison_table.html` (new) — KPI table (`.cmp-table-wrap` >
  `.cmp-table`); per-row delta is `None` → plain `—`, else a
  `.cmp-delta-{pos,neg,neutral}` span.
- `templates/advantage_block.html` (new) — one A/B column: header + cards (loop)
  + "Aucun avantage significatif." fallback; `kind` (`a`/`b`) drives the
  `--a` / `--b` modifier classes.
- `templates/vs_divider.html`, `templates/cmp_placeholder.html` (new).
- `components/tables.py` — added `comparison_table(a_label, b_label, rows)`.
- `components/layout.py` — added `vs_divider()`, `comparison_placeholder()`,
  `advantage_block(title, items, kind)`.
- `assets/styles.css` — appended a "Comparaison (page 4)" section (`.cmp-*`).
- `pages/4_Comparison.py` — replaced all six `unsafe_allow_html` blocks with
  component calls; `_delta_str` (returned an HTML span) → `_delta_data`
  (returns `{"kind","text"}` | `None`); `kpi_rows` re-keyed to
  `indicator/a/b/delta`; removed local `pillar_labels` (now `PILLAR_LABELS`)
  and the now-unused `palette` import. Grep confirms zero `unsafe_allow_html`,
  zero `palette`, zero `pillar_labels` remain.

**Colour mapping (F-001)** — only the cells the finding lists as frozen:
- `#f1f5f9` → `var(--esg-text-heading)` — KPI value cells.
- `#94a3b8` → `var(--esg-text-muted)` — indicator cells.
- `#475569` → `var(--esg-text-muted)` — header label / Écart / VS divider.
- `#cbd5e1` → `var(--esg-text)` — advantage-card theme name.
- **Kept literal** (decorative / theme-independent): `#6366f1` (A / header /
  delta), `#22c55e` (B / header / delta), `#ef4444` (delta neg), `#64748b`
  (neutral dash), `#334155` (faint placeholder / empty), the advantage-card
  rgba tints, and the table-chrome white-alpha borders
  (`rgba(255,255,255,0.02/0.04/0.06/0.08)`) — keeping these makes dark chrome
  byte-identical; the faint light-mode borders are a known cosmetic residual.

**Verify**
- Gates: `ruff` — no new problematic codes vs `HEAD` (`E501` 9→3, `I001` 1→0;
  the only increase is one extra `E402`, the page-wide
  `set_page_config`-before-imports pattern); `mypy src/` Success; `pytest`
  16 passed; `lint-imports` 2 contracts kept.
- Templates rendered directly through the seam produce the exact expected DOM
  (table rows incl. `delta=None` → plain `—`, neutral/pos/neg spans; advantage
  card + empty fallback).
- Live (preview 8502), **dark** (`?theme=dark`): no `stException`; placeholder
  `#334155` + correct French text; VS `#506070`. A probe element confirms the
  `.cmp-*` rules resolve: kept-literal colours exact (`th_a` #6366f1, `th_b`
  #22c55e, delta pos/neg/neutral #22c55e/#ef4444/#64748b, card tint
  rgba(99,102,241,0.06), empty #334155); the F-001 cells resolve to the dark
  palette (`--esg-text-muted` #506070, `--esg-text-heading` #dce8f8,
  `--esg-text` #c8d8ec).
- Live, **light** (`?theme=light`): no exception; the same F-001 cells switch to
  the light palette (`--esg-text-muted` #475569, `--esg-text-heading` /
  `--esg-text` #0f172a), VS #475569 — legible, **F-001 fixed** for this page.

## Step 9 — Migrate `5_Explainability.py` ✅

**Date:** 2026-06-09

**Goal:** Keep the explainability page thin by continuing to use `layout.section_label`, `layout.callout_howto`, and `layout.callout_unsigned`, while keeping the unsigned audit report builder in `src/esg_data/reporting/text_report.py`.

**Changes**
- `streamlit_app/pages/5_Explainability.py` — removed the page-local `_build_report()` wrapper; the download button now calls `build_text_report(...)` directly.
- `tests/test_text_report.py` (new) — verifies the text report builder emits deterministic UTF-8 bytes with the expected audit content.

**Verify**
- Gates: `ruff` clean on changed files; `mypy src/` clean; `pytest` passed.
- `build_text_report` regression coverage added to lock the audit output shape.
- No new raw HTML, hex colours, or font-size literals were introduced into `5_Explainability.py`.

**Deviations / notes**
- The tokenised cells (the F-001 offenders) are **not** byte-identical in dark:
  they shift from their frozen literals (#f1f5f9 / #94a3b8 / #475569 / #cbd5e1)
  to the proper dark palette values. This is the explicitly-approved F-001
  behaviour ("each page becomes theme-correct automatically"), consistent with
  Steps 6/7b; all decorative/chrome colour stays byte-identical.
- Selecting A/B to render the live table is gated behind the baseweb selectbox
  portal (awkward in the harness, same as Step 7b); the table/advantage markup
  was verified by direct seam render + a live CSS-rule probe instead.

**Rollback:** revert `pages/4_Comparison.py`, `components/tables.py`,
`components/layout.py`, and the appended `.cmp-*` section in `assets/styles.css`;
delete `templates/{comparison_table,advantage_block,vs_divider,cmp_placeholder}.html`.
