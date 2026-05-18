# ESG Toolkit

[![CI](https://github.com/your-org/esg-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/esg-toolkit/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

An open-source, auditable ESG and climate scoring platform — a transparent
alternative to MSCI, Sustainalytics, and Refinitiv.

## Why?

Proprietary ESG scores are opaque and expensive. Every score this platform
produces is:

- **Traceable** — to its exact inputs and methodology version
- **Reproducible** — same inputs + same methodology = byte-identical output, always
- **Configurable** — all weightings live in YAML; no code changes required
- **Auditable** — immutable audit log; signed outputs verifiable without platform access

## Quick start

```bash
pip install esg-toolkit          # core scoring library only
pip install esg-toolkit[all]     # full platform (API + ML + dashboard)
```

## Development setup

```bash
git clone https://github.com/your-org/esg-toolkit
cd esg-toolkit
uv sync --extra dev
uv run pre-commit install
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full setup and contribution guidelines.

## Status

Under active development. See [CLAUDE.md](CLAUDE.md) for the build plan.

**Current phase: Phase 0 — Repository scaffolding**

| Phase | Description | Status |
|---|---|---|
| 0 | Repository scaffolding | ✅ Complete |
| 1 | Core data models | ⏳ Next |
| 2 | Methodology YAML system | — |
| 3 | Data ingestion pipeline | — |
| 4 | Scoring engine | — |
| 5 | Climate / PCAF module | — |
| 6 | Explainability | — |
| 7 | REST API | — |
| 8 | Streamlit dashboard | — |
| 9 | Reproducibility & signing | — |
| 10 | Documentation & community | — |

## License

Apache 2.0 — see [LICENSE](LICENSE).
