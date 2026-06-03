"""FastAPI application entry point.

Run with:
    uv run uvicorn esg_api.main:app --reload --port 8000

Swagger UI: http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from esg_api.routes import companies, explain, methodologies, portfolios, scores

app = FastAPI(
    title="ESG Platform API",
    description=(
        "Open-source, auditable ESG and climate scoring platform for Mauritanian companies. "
        "Every score is traceable to its inputs and methodology version."
    ),
    version="0.1.0",
    contact={"name": "ESG Toolkit Contributors"},
    license_info={"name": "Apache 2.0"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

_PREFIX = "/api/v1"

app.include_router(companies.router, prefix=_PREFIX)
app.include_router(scores.router, prefix=_PREFIX)
app.include_router(portfolios.router, prefix=_PREFIX)
app.include_router(methodologies.router, prefix=_PREFIX)
app.include_router(explain.router, prefix=_PREFIX)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": "ESG Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health", tags=["Health"])
def health() -> dict[str, str]:
    """Service health check."""
    return {"status": "ok"}
