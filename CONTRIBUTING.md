# Contributing to ESG Toolkit

Thank you for contributing. This guide covers everything you need to go from
`git clone` to a passing test run and your first PR.

---

## 1. Development setup

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/your-org/esg-toolkit
cd esg-toolkit

# Install all dev dependencies and the project in editable mode
uv sync --extra dev

# Install pre-commit hooks (runs ruff, mypy, import-linter on every commit)
uv run pre-commit install

# Verify everything works
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
uv run lint-imports
```

---

## 2. Architecture — the four-layer rule

The codebase is split into four layers. **Inner layers must never import from
outer layers.** This rule is enforced by `import-linter` in CI and on every commit.

```
Layer 1: esg_core   — pure Python, no I/O, no FastAPI, no DB, no pandas
Layer 2: esg_data   — I/O only (Parquet, SQLite); no business logic
Layer 3: esg_api    — FastAPI routes, auth, audit; thin handlers only
Layer 4: streamlit_app / notebooks — can import anything
```

**Forbidden imports (will fail CI):**

| Module | Cannot import |
|---|---|
| `esg_core` | `esg_data`, `esg_api`, `fastapi`, `sqlalchemy`, `pandas` |
| `esg_data` | `esg_api`, `fastapi` |

If you need to add a dependency to `esg_core`, make sure it is pure Python
with zero I/O side effects. Justify it in your PR description.

---

## 3. Code standards

All of these are enforced by pre-commit hooks and CI — fix them before opening a PR.

- **Type hints everywhere.** `mypy --strict` must pass on `src/`.
- **No `print()`** — use `logging` (structured JSON in production).
- **No `Any`** — if unavoidable, add an inline `# type: ignore[...]` with a comment explaining why.
- **No bare `except`.** Always catch specific exceptions and re-raise with context.
- **Functions ≤ 50 lines**, modules ≤ 500 lines.
- **Polars in `src/`; pandas only in `notebooks/`.** This is a hard rule, not a preference.
- **All weightings in YAML.** Never hard-code ESG weights or indicator lists as Python constants.
- **No `datetime.now()` in scoring functions.** Pass timestamps as arguments for reproducibility.
- Line length: 100 characters.

### Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scoring): add z-score normalization strategy
fix(methodology): reject non-semver version strings
docs(api): document /scores endpoint response schema
test(climate): add PCAF attribution fixture
```

Scope must be one of: `core`, `data`, `api`, `dashboard`, `scoring`, `climate`,
`methodology`, `explainability`, `docs`, `ci`, `deps`.

---

## 4. Adding an ingester *(available from Phase 3)*

> This section will be expanded once the ingestion pipeline is implemented.

Ingesters live in `src/esg_data/ingestion/`. Each ingester:
1. Extends the abstract `Ingester` base class from `base.py`.
2. Reads a source format (CSV, JSON, XML, API).
3. Maps source fields to canonical `Company`, `IndicatorValue`, and `Emissions` models.
4. Writes validated Parquet files to `data/raw/`.

---

## 5. Adding an indicator *(available from Phase 2)*

> This section will be expanded once the methodology YAML system is implemented.

Every new indicator requires **two** changes:
1. Add it to the appropriate theme in `methodologies/default_v1.yaml` with a weight and direction.
2. Add a parser or mapping in the relevant ingester.

Never add an indicator in Python code without a corresponding YAML entry — this is enforced by the schema validator.

---

## 6. Methodology review process *(available from Phase 2)*

Changes to `methodologies/default_v1.yaml` that affect scores require a
`methodology proposal` issue before a PR. Use the issue template to document:
- Which indicator(s) change and why
- Evidence base (academic paper, regulatory guidance, industry standard)
- Impact on existing scores (run the comparison notebook)

---

## 7. Running the full quality suite

```bash
uv run pytest                          # tests + coverage
uv run ruff check src/ tests/          # linting
uv run ruff format --check src/ tests/ # formatting
uv run mypy src/                       # type checking
uv run lint-imports                    # layer boundary enforcement
```

All five must pass before a PR can be merged.

---

## 8. Pull request checklist

- [ ] `uv run pytest` passes (≥ 80% coverage on `esg_core` from Phase 1 onward)
- [ ] `uv run mypy src/` passes with no errors
- [ ] `uv run lint-imports` passes
- [ ] New public functions have Google-style docstrings
- [ ] Any function in `esg_core/` has a `Reproducibility:` note in its docstring
- [ ] No new dependency added without justification in the PR description
- [ ] Commit messages follow Conventional Commits

---

## 9. Getting help

Open a [GitHub Discussion](https://github.com/your-org/esg-toolkit/discussions)
for questions, or file an issue using the appropriate template.
