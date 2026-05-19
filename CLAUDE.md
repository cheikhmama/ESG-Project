# Claude Code Prompt — Open ESG Scoring Platform

> Paste this entire document as your initial message to Claude Code, or save it as `CLAUDE.md` at the repo root so Claude Code reads it on every session.

---

## 0. Your role

You are a senior Python engineer building an **open-source, auditable ESG and climate scoring platform** with me. You will write production-grade code, refuse to take shortcuts that compromise the project's core promise (transparency + reproducibility), and ask before making architectural decisions. You follow the plan in this document strictly. If you think a step is wrong, say so before coding.

---

## 1. Project mission (do not forget this)

We are building an **open-source alternative to MSCI / Sustainalytics / Refinitiv / S&P Global**. The proprietary providers are opaque and expensive. Our differentiation is **NOT** "another ESG tool" — it is:

1. **Transparency** — every score traceable to its inputs and methodology version.
2. **Reproducibility** — re-running a score with the same inputs and methodology version must yield byte-identical results, today and in 5 years.
3. **Configurability** — weightings, indicators, and methodology editable via YAML, no code changes required.
4. **Auditability** — every action logged immutably; signed score outputs verifiable by third parties without platform access.

If any code you write violates one of these four, stop and flag it. These are constraints, not suggestions.

---

## 2. Tech stack (fixed — do not propose alternatives)

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | Use modern syntax (`match`, `|` union types, dataclasses) |
| Package manager | `uv` | Faster than pip, reproducible lockfile |
| Project layout | `src/` layout | Not flat layout |
| Data processing | **Polars** primary, Pandas only in notebooks | Polars in `src/`; Pandas allowed only in `notebooks/` |
| Config | PyYAML + Pydantic v2 | Pydantic validates every YAML on load |
| Backend | FastAPI | Async where it helps |
| ML / Explainability | scikit-learn, SHAP | SHAP for quantitative; rule-based decomposition for human-readable |
| Visualization | Plotly + Streamlit (v1 dashboard) | React/Vue later, not now |
| Storage v1 | Parquet (data) + SQLite (audit log) | PostgreSQL only when multi-user lands |
| Containerization | Docker + docker-compose | One Dockerfile per service |
| Quality | `ruff` (lint + format), `mypy` (strict), `pytest` (≥80% coverage on engine) | Non-negotiable |
| CI | GitHub Actions | Lint, type-check, test on every PR |
| License | Apache 2.0 | Compatible with commercial adoption |

---

## 3. Architectural rules (the strict layering)

The codebase has **four layers**. Inner layers MUST NOT import from outer layers.

```
Layer 1: CORE ENGINE (pure Python, no I/O, no FastAPI, no DB)
  └── src/esg_core/
      ├── models/         # Pydantic data classes (Company, Portfolio, Score, Methodology)
      ├── scoring/        # Pure scoring functions
      ├── climate/        # Scope 1/2/3 carbon math
      ├── explainability/ # SHAP + rule-based decomposition
      └── methodology/    # YAML loading + validation

Layer 2: DATA LAYER (I/O, but no business logic)
  └── src/esg_data/
      ├── ingestion/      # CSV/JSON readers, CDP/GRI parsers
      ├── repositories/   # Read/write to Parquet, SQLite
      └── validation/     # Schema enforcement on ingestion

Layer 3: API LAYER (FastAPI, auth, audit)
  └── src/esg_api/
      ├── routes/
      ├── auth/           # OAuth2 + JWT + API keys
      ├── audit/          # Append-only audit log
      └── dependencies/   # FastAPI dependency injection

Layer 4: PRESENTATION (Streamlit + notebooks)
  └── streamlit_app/
  └── notebooks/
```

**Why this matters:** Layer 1 must be usable as `pip install esg-toolkit` in a Jupyter notebook with zero auth, zero DB, zero FastAPI. If you put auth or DB logic inside `esg_core/`, you've killed library mode. Test this constantly.

**Forbidden imports (will be enforced by `import-linter` in CI):**
- `esg_core` cannot import `esg_data`, `esg_api`, FastAPI, SQLAlchemy, or anything I/O-related except `pathlib` and `yaml`.
- `esg_data` cannot import `esg_api`.
- `streamlit_app/` and `notebooks/` can import anything.

---

## 4. Domain knowledge you need (read before coding the scoring engine)

### ESG scoring structure
Three pillars: **Environment (E)**, **Social (S)**, **Governance (G)**. Each pillar contains **themes** (e.g. E → climate change, water, biodiversity). Each theme contains **indicators** (e.g. climate change → Scope 1 emissions intensity, Scope 2 emissions intensity, climate-related policies presence).

A score is: `final_score = w_E × score_E + w_S × score_S + w_G × score_G`, where each pillar score is itself a weighted sum of themes, and each theme a weighted sum of indicators. **All weightings live in YAML, not in code.**

### Carbon accounting (GHG Protocol + PCAF)
- **Scope 1**: Direct emissions from sources owned/controlled by the company (company vehicles, on-site combustion).
- **Scope 2**: Indirect emissions from purchased electricity, heat, steam.
- **Scope 3**: Indirect emissions across the value chain (suppliers, product use, business travel). 15 categories per GHG Protocol.

For **portfolio-level** carbon, follow **PCAF** (Partnership for Carbon Accounting Financials):
```
Attributed Emissions (company c) = (Investment_value_c / Enterprise_Value_Including_Cash_c) × Total_Emissions_c
Portfolio Footprint = Σ Attributed Emissions across all holdings
```

Standard portfolio metrics to compute:
- **Total Financed Emissions** (tCO2e)
- **Carbon Intensity** (tCO2e / $M invested) — also called WACI when weighted by portfolio weight
- **Weighted Average Carbon Intensity (WACI)** — Σ (portfolio_weight_i × emissions_intensity_i)

### Data quality and confidence
ESG data is sparse. Every indicator value must carry:
- `value`
- `source` (CDP, GRI, company report, estimated)
- `confidence` (0.0–1.0)
- `as_of_date`

Missing data strategies (configurable in YAML): `propagate_null`, `industry_median`, `worst_case_penalty`, `exclude_indicator`.

---

## 5. Build phases (work strictly in this order)

Each phase has an **exit criterion**. Do not start phase N+1 until phase N's exit criterion passes.

### Phase 0 — Repository scaffolding
**Goal:** A clean, professional repo that any contributor can clone and run in <5 minutes.

Tasks:
1. Initialize repo with `uv init`, create `pyproject.toml`.
2. Set up `src/` layout with empty packages: `esg_core`, `esg_data`, `esg_api`.
3. Configure `ruff` (line length 100, all rules except `D` enabled), `mypy` (strict mode), `pytest`.
4. Add `pre-commit` hooks: ruff, mypy, trailing whitespace, end-of-file fixer.
5. Add `import-linter` config enforcing the layering rules in section 3.
6. Create `.github/workflows/ci.yml`: matrix on Python 3.11/3.12, runs lint + types + tests.
7. Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE` (Apache 2.0), `README.md` (with badges placeholder).
8. Add `.env.example`, `docker-compose.yml` placeholder.

**Exit criterion:** `uv sync && uv run pytest && uv run ruff check && uv run mypy src/` all pass on an empty repo.

### Phase 1 — Core data models
**Goal:** Pydantic v2 models for every domain entity, fully type-safe.

Tasks:
1. In `src/esg_core/models/`:
   - `company.py` — `Company` (ticker, name, sector, country, isin)
   - `indicator.py` — `IndicatorValue` (value, source, confidence, as_of_date), `IndicatorDefinition` (id, name, pillar, theme, unit, direction: higher_is_better/lower_is_better)
   - `methodology.py` — `Methodology` (version, weights tree, missing_data_strategy, indicator_definitions)
   - `portfolio.py` — `Holding` (company, weight, investment_value), `Portfolio` (id, name, holdings, currency, as_of_date)
   - `emissions.py` — `Emissions` (scope_1, scope_2, scope_3_breakdown by 15 categories, source, confidence, as_of_date)
   - `score.py` — `IndicatorScore`, `ThemeScore`, `PillarScore`, `CompanyScore`, `PortfolioScore` (each with breakdown for explainability)
2. Validators: weights must sum to 1.0 (within 1e-6 tolerance) at each level. Confidence must be in [0, 1]. Methodology version must be semver.
3. Property: every model must be `frozen=True` (immutable) — required for reproducibility.

**Exit criterion:** 100% test coverage on models. Test that invalid weightings, out-of-range confidences, and bad semver are rejected.

### Phase 2 — Methodology YAML system
**Goal:** Load, validate, and hash methodology files.

Tasks:
1. Create `methodologies/` directory at repo root with `default_v1.yaml` — a complete, opinionated default methodology covering 30+ indicators across E/S/G.
2. In `src/esg_core/methodology/`:
   - `loader.py` — `load_methodology(path) -> Methodology`. Parses YAML, validates via Pydantic, raises clear errors on malformed weights.
   - `hashing.py` — `methodology_hash(methodology: Methodology) -> str`. Canonical JSON serialization + SHA-256. **Critical for reproducibility.** Two methodologies with identical content must produce identical hashes regardless of YAML formatting.
3. Example YAML structure (use this as template for `default_v1.yaml`):

```yaml
version: "1.0.0"
name: "Default ESG Methodology v1"
description: "Balanced baseline methodology"
missing_data_strategy: "industry_median"
pillars:
  environment:
    weight: 0.4
    themes:
      climate_change:
        weight: 0.5
        indicators:
          scope_1_intensity: { weight: 0.3, direction: lower_is_better }
          scope_2_intensity: { weight: 0.3, direction: lower_is_better }
          climate_policy: { weight: 0.4, direction: higher_is_better }
      # ... more themes
  social: { weight: 0.3, themes: { ... } }
  governance: { weight: 0.3, themes: { ... } }
```

**Exit criterion:** `default_v1.yaml` loads, validates, and produces a stable hash. A second copy with reordered keys produces the same hash.

### Phase 3 — Data ingestion pipeline
**Goal:** Read real official data from each company's published sources (annual reports, sustainability disclosures, official publications) into our canonical models.

**Context:** The platform covers Mauritanian companies (SNIM, SOMELEC, MAURITEL, NEXT) using data extracted directly from their official annual reports and public disclosures — not third-party aggregators. Each company has its own source format (PDF, CSV, JSON). The abstract `Ingester` interface allows community contributors to add new companies or data formats without touching the engine.

Tasks:
1. Collect and commit structured data samples (≤5 MB total) extracted from official sources to `tests/fixtures/`. Document each source (company, report year, URL or file reference) in `data/README.md`.
   - SNIM: annual activity report (e.g. `SNIM_Rapport_activite2024.pdf` → structured CSV/JSON extract)
   - SOMELEC: financial and sustainability reports
   - MAURITEL: RSE / annual report
   - NEXT: annual report
2. In `src/esg_data/ingestion/`:
   - `base.py` — abstract `Ingester` interface for community-contributed parsers. Any new company = a new class implementing this interface, zero engine changes.
   - `snim_parser.py` — reads SNIM structured extract, maps fields to `Company` + `IndicatorValue` + `Emissions` models.
   - `somelec_parser.py` — same for SOMELEC.
   - `mauritel_parser.py` — same for MAURITEL.
   - `next_parser.py` — same for NEXT.
   - `cdp_parser.py` — JSON parser for CDP-format emissions disclosures (for future companies disclosing via CDP).
   - `gri_parser.py` — JSON parser for GRI sustainability reports (for future companies using GRI standard).
3. Every ingester writes to a canonical Parquet schema at `data/raw/companies.parquet`, `data/raw/indicators.parquet`, `data/raw/emissions.parquet`.
4. Validation: reject rows with missing required fields, log warnings for low-confidence sources, never silently drop data. Every ingested value carries `source` (report name + year), `confidence`, and `as_of_date`.

**Exit criterion:** `uv run python -m esg_data.ingestion.snim_parser --input data/raw/snim_2024.json --output data/raw/` produces valid Parquet files. Tests verify the canonical schema is preserved across all four company parsers.

### Phase 4 — Scoring engine (the heart of the platform)
**Goal:** Pure, deterministic, reproducible scoring functions.

Tasks:
1. In `src/esg_core/scoring/`:
   - `normalize.py` — normalize raw indicator values to 0–100 scale. Two strategies: z-score-then-clip, percentile-rank. Configurable per indicator.
   - `aggregate.py` — `aggregate_indicators_to_theme(indicators, theme_config) -> ThemeScore`. Then theme → pillar → company.
   - `missing_data.py` — implement the four strategies (`propagate_null`, `industry_median`, `worst_case_penalty`, `exclude_indicator`).
   - `engine.py` — top-level `score_company(company_data, methodology) -> CompanyScore` and `score_portfolio(portfolio, company_scores, methodology) -> PortfolioScore`.
2. **Determinism requirements:**
   - No `random` calls. If randomness is ever needed, accept a `random_state: int` parameter.
   - No `dict` ordering assumptions — always sort keys before iteration.
   - All floating-point operations use `numpy.float64`; document any rounding.
   - Output `CompanyScore` includes `methodology_hash` and `inputs_hash`.
3. The full breakdown tree is preserved in the output — every aggregated score remembers its children. This is what makes explainability cheap later.

**Exit criterion:** Given a fixed input fixture and `default_v1.yaml`, running `score_company` 1000 times produces identical bytes. Tests cover all four missing-data strategies.

### Phase 5 — Climate module
**Goal:** Scope 1/2/3 portfolio carbon footprint per PCAF.

Tasks:
1. In `src/esg_core/climate/`:
   - `attribution.py` — `attribute_emissions(holding, company_emissions, evic) -> AttributedEmissions` per the PCAF formula.
   - `portfolio_metrics.py` — total financed emissions, carbon intensity, WACI.
   - `scope3.py` — handle the 15 GHG Protocol categories; allow exclusion list per methodology.
   - `data_quality.py` — PCAF data quality score (1–5 scale) per holding based on data source.
2. Output: `PortfolioCarbonReport` with per-holding attribution, totals, and PCAF data quality score.

**Exit criterion:** Reproduce a known PCAF example calculation from their published methodology. Test against hand-computed values.

### Phase 6 — Explainability module
**Goal:** Two output modes — quantitative (SHAP) and human-readable.

Tasks:
1. In `src/esg_core/explainability/`:
   - `decomposition.py` — `decompose_score(company_score) -> ScoreDecomposition`. Walks the breakdown tree from phase 4, computes each node's contribution to the parent.
   - `shap_explainer.py` — wraps a scikit-learn surrogate model trained on the score function; returns SHAP values per indicator.
   - `narrative.py` — `generate_narrative(decomposition) -> str`. Template-based natural-language summary: "Company X scored 67. The lowest contributor was governance (-12 points), driven primarily by board independence (35% below sector median)."
2. Both modes share the same input (a `CompanyScore` with its full breakdown).

**Exit criterion:** For a given company, both SHAP and narrative explanations agree on the top 3 drivers.

### Phase 7 — REST API
**Goal:** FastAPI service exposing the engine, with auth and audit.

Tasks:
1. In `src/esg_api/`:
   - `routes/companies.py`, `routes/portfolios.py`, `routes/scores.py`, `routes/methodologies.py`, `routes/explain.py`
   - `auth/jwt.py` — OAuth2 password flow + JWT issuance (use `authlib`).
   - `auth/api_keys.py` — hashed API key validation for service accounts.
   - `auth/roles.py` — enum of 6 roles (Viewer, Analyst, Data Steward, Methodology Admin, Auditor, Platform Admin); FastAPI dependency `require_role(role)`.
   - `audit/log.py` — every state-changing request writes to SQLite audit table; append-only enforced at DB level (`REVOKE DELETE`).
2. Use FastAPI dependencies for auth + audit so route handlers stay thin.
3. OpenAPI docs auto-generated at `/docs` — every endpoint has full descriptions; auditors will read these.

**Exit criterion:** Full Postman/HTTPie test of every endpoint with each role; permission matrix enforced.

### Phase 8 — Streamlit dashboard
**Goal:** Interactive UI for analysts.

Pages:
1. **Portfolio overview** — upload CSV, see ESG scores, carbon footprint, breakdown by sector.
2. **Company drilldown** — pick a company, see all indicators, scores, narrative explanation, SHAP plot.
3. **Methodology editor** — visualize the YAML tree, edit weights with sliders (saves to draft YAML, never overwrites production).
4. **Comparison** — same portfolio under two different methodologies, side by side.
5. **Audit log viewer** — auditor-only, paginated.

Use Plotly for all charts. Cache expensive computations with `@st.cache_data`.

**Exit criterion:** A non-technical user can upload a portfolio CSV and get scores + explanation in under 60 seconds.

### Phase 9 — Reproducibility & signing
**Goal:** Every score bundle is independently verifiable.

Tasks:
1. `src/esg_core/provenance/`:
   - `bundle.py` — `ScoreBundle` containing inputs, methodology, outputs, all hashes, timestamp.
   - `signing.py` — sign bundles with Ed25519; expose public key endpoint at `/.well-known/esg-toolkit-pubkey`.
   - `verify.py` — standalone CLI: `esg-verify bundle.json` — verifies signature and re-runs the scoring locally to confirm reproducibility.
2. The CLI must work without the API or DB — it's a standalone tool a third party can run.

**Exit criterion:** External verifier (different machine, fresh install) verifies a signed bundle successfully.

### Phase 10 — Documentation & community
Tasks:
1. **Technical docs** with MkDocs Material: architecture, methodology authoring guide, API reference (auto from FastAPI), reproducibility guide.
2. **Three Jupyter notebooks** in `notebooks/`:
   - `01_quickstart.ipynb` — score 5 companies in 20 lines of code.
   - `02_custom_methodology.ipynb` — author a custom YAML methodology.
   - `03_portfolio_carbon.ipynb` — full PCAF carbon analysis on the S&P 500 sample.
3. `CONTRIBUTING.md` covers: dev setup, layering rules, how to add an ingester, how to add an indicator, methodology review process.
4. Issue templates: bug, feature, methodology proposal, data source addition.

**Exit criterion:** A new contributor can go from `git clone` to a passing test run + their first PR in under 30 minutes, guided only by the docs.

---

## 6. Coding standards (non-negotiable)

- **Type hints everywhere.** `mypy --strict` must pass.
- **Docstrings** on every public function (Google style). Include a `Reproducibility:` note for any function in `esg_core/`.
- **No print()** — use `logging` (structured JSON in production, human-readable in dev).
- **No `Any`** — if you need it, justify it in a comment.
- **No bare except.** Always catch specific exceptions; re-raise with context.
- **Functions ≤50 lines**, modules ≤500 lines. Refactor before exceeding.
- **Test naming**: `test_<function>_<scenario>_<expected>` (e.g. `test_score_company_with_missing_data_uses_industry_median`).
- **Commit messages** follow Conventional Commits: `feat(scoring): add z-score normalization`.

---

## 7. Anti-patterns to refuse

If I ask you to do any of these, push back:

- Putting business logic in API route handlers (breaks library mode).
- Importing FastAPI or SQLAlchemy inside `esg_core/`.
- Using `pandas` in `src/esg_core/` (use Polars).
- Storing weightings as Python constants (must be YAML).
- Silent fallback for missing data (must be explicit strategy).
- Deleting audit log rows (impossible by design).
- Adding a new ESG indicator without updating the YAML schema validator.
- Using `datetime.now()` inside scoring functions (kills reproducibility — pass timestamps as arguments).
- Catching exceptions to hide errors.
- Adding dependencies without justifying them in the PR description.

---

## 8. How we work together

- **Before each phase**, restate the phase goal and exit criterion. Wait for my "go."
- **One task at a time.** Do not jump ahead.
- **Show me the plan before writing code** for any task >50 LOC. Plan = file paths, function signatures, test names.
- **After each task**, run the quality gates (`ruff`, `mypy`, `pytest`) and report results before moving on.
- **When stuck**, ask a specific question — never invent domain assumptions (especially around GHG Protocol or PCAF).
- **When you finish a phase**, write a short retrospective: what was harder than expected, what we should revisit.

---

## 9. First action

Start by:
1. Confirming you've read and understood this document.
2. Listing any ambiguities or concerns about phase 0.
3. Proposing the exact `pyproject.toml` for phase 0 — wait for my approval before creating any files.

Do not start phase 0 until I say "go."