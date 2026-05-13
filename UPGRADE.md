# AuditCraft v1 → v2 Upgrade Document

## Overview

AuditCraft v2 replaces the pure-frontend prototype with a real **FastAPI backend + AST-based analyzer**, solving the core critique from the MeDo hackathon: *"all frontend, no real compilation or deep analysis."*

---

## Capability Comparison

| Capability | v1 (Pure Frontend) | v2 (FastAPI Backend) |
|------------|-------------------|----------------------|
| **Compilation** | ❌ None — regex-only | ✅ Real solc 0.8.x via py-solc-x |
| **AST Analysis** | ❌ None | ✅ Lightweight structural heuristics |
| **Detectors** | 5 regex patterns | 5 regex + structural detectors (extensible) |
| **ABI / Bytecode** | ❌ Not available | ✅ Returned after successful compile |
| **Line Numbers** | ❌ Approximate | ✅ Exact line + column |
| **Confidence Scoring** | ❌ None | ✅ High / Medium / Low per finding |
| **API Interface** | ❌ None | ✅ REST JSON (`/compile`, `/scan`, `/health`) |
| **CORS** | N/A | ✅ Enabled for frontend dev server |
| **Error Handling** | ❌ Silent failures | ✅ Structured errors (422 compile fail, etc.) |
| **Severity Classification** | Hardcoded | ✅ Configurable per detector |
| **Extensibility** | ❌ Edit 42KB HTML | ✅ Add detector in `services/analyzer.py` |
| **Slither Ready** | ❌ Impossible | ✅ Drop-in: replace `analyzer.py` calls |

---

## Technical Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | **FastAPI** | Modern, async, automatic OpenAPI docs, type-safe |
| Validation | **Pydantic v2** | Request/response models, runtime validation |
| Compiler | **py-solc-x** | Cross-platform solc management, no system deps |
| Analyzer | **Custom regex + structural** | Zero heavy deps, runs anywhere, student-budget friendly |
| Upgrade Path | **Slither** | Same `ScanResult` schema; swap analyzer service later |
| Server | **Uvicorn** | ASGI, production-grade |

---

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐
│   React/Vue     │──────▶   FastAPI Backend    │
│   Frontend      │◀─────│   (main.py)          │
└─────────────────┘      └──────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
    ┌──────────────┐    ┌─────────────────┐   ┌─────────────┐
    │ /compile     │    │ /scan           │   │ /health     │
    │ services/    │    │ services/       │   │ capability  │
    │ compiler.py  │    │ analyzer.py     │   │ advertisement│
    │              │    │                 │   │             │
    │ py-solc-x    │    │ regex + struct  │   │ solc status │
    │ solc 0.8.x   │    │ heuristics      │   │ detectors   │
    └──────────────┘    └─────────────────┘   └─────────────┘
```

---

## Detectors Implemented

| Detector | Method | Severity | Notes |
|----------|--------|----------|-------|
| **Reentrancy** | Structural: external call (`call`/`send`/`transfer`) before state change | High | Classic CEI violation heuristic |
| **Integer Overflow** | Regex on arithmetic inside `unchecked{}` or on balance fields | Medium | 0.8.x reverts by default; flags `unchecked` |
| **Access Control** | Public/external state modifiers without `onlyOwner` / `require(msg.sender)` | High | Reduced false positives by requiring `=` inside function |
| **Unchecked External Call** | `.call`/`.send`/`.transfer` without `require()` or `if` | Medium | Checks same + previous 2 lines |
| **Timestamp Dependence** | `block.timestamp` or `now` usage | Low | Informational; not always exploitable |

---

## Deployment

### Local Development

```bash
cd backend/
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose (Production-Ready Skeleton)

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - UVICORN_WORKERS=2
    restart: unless-stopped

  # frontend:
  #   build: ./frontend
  #   ports:
  #     - "3000:3000"
```

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Known Limitations & Upgrade Path

1. **solc download requires internet**
   - First run downloads the compiler binary from `solc-bin.ethereum.org`.
   - If blocked (e.g., corporate firewall / SSL issue), pre-install solc manually.

2. **Analyzer is heuristic-based, not formal**
   - For hackathon/demo use this is sufficient.
   - For production bounty-grade audits, replace `analyzer_service.scan()` with Slither.

3. **Slither Integration (Future)**
   ```python
   # In services/analyzer.py
   try:
       from slither import Slither
       HAS_SLITHER = True
   except ImportError:
       HAS_SLITHER = False
   ```
   When Slither is installed, run it first, then map its JSON output to `Finding` schema.

---

## Files Delivered

```
auditcraft-v2/
└── backend/
    ├── main.py                 # FastAPI app, 4 endpoints
    ├── models/
    │   ├── __init__.py
    │   └── schemas.py          # Pydantic models (Compile*, Scan*, Finding, Health*)
    ├── services/
    │   ├── __init__.py
    │   ├── compiler.py         # py-solc-x wrapper
    │   └── analyzer.py         # 5-detector heuristic engine
    └── requirements.txt        # pip deps
```

---

## Verification

- ✅ `uvicorn main:app --reload` starts without import errors
- ✅ `GET /health` returns `{"status":"ok", ...}`
- ✅ `POST /scan` with a vulnerable contract returns structured findings
- ✅ `POST /compile` attempts real solc compilation (falls back gracefully on network issues)
