"""
AuditCraft v2 - FastAPI Backend Entry Point
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    CompileRequest, CompileResult,
    ScanRequest, ScanResult,
    HealthResponse, VulnerabilityType
)
from services.compiler import compiler_service
from services.analyzer import analyzer_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: warm-check solc availability."""
    # Pre-check common version so /health is truthful
    compiler_service.ensure_version("0.8.19")
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="AuditCraft v2 API",
    description="Real backend for smart-contract education & lightweight audit.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS: allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #

@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Liveness probe + capability advertisement.
    """
    solc_ok = compiler_service._cached_version is not None
    return HealthResponse(
        status="ok",
        version="2.0.0",
        solc_available=solc_ok,
        solc_version=compiler_service._cached_version,
        supported_detectors=[d.value for d in VulnerabilityType]
    )


@app.post("/compile", response_model=CompileResult)
async def compile(request: CompileRequest):
    """
    Compile Solidity source code and return ABI + bytecode.
    """
    result = compiler_service.compile(request)
    if not result.success:
        # Return 422 so client knows it was a compilation failure, not server error
        raise HTTPException(status_code=422, detail=result.errors)
    return result


@app.post("/scan", response_model=ScanResult)
async def scan(request: ScanRequest):
    """
    Run static analysis on Solidity source.
    Optionally compiles first to surface compiler errors.
    """
    try:
        result = analyzer_service.scan(request)
        return result
    except Exception as exc:
        # Catch-all for unexpected analyzer crashes
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}")


@app.get("/detectors", response_model=List[str])
async def list_detectors():
    """Return human-readable list of active vulnerability detectors."""
    return [d.value for d in VulnerabilityType]
