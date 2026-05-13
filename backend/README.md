# AuditCraft v2 Backend

Real backend for smart-contract education & lightweight audit.

## Overview

AuditCraft v2 provides a FastAPI-based REST API for:
- **Compilation**: Compile Solidity source code to ABI and bytecode via `py-solc-x`
- **Static Analysis**: Detect common vulnerabilities using regex + structural heuristics
- **Health Probes**: Liveness checks with capability advertisement

## Quick Start

### Local Development (pip + uvicorn)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### Docker Deployment

```bash
cd auditcraft-v2
docker compose up --build
```

This starts:
- **Backend** on `http://localhost:8000`
- **PostgreSQL** on `localhost:5432`
- **Redis** on `localhost:6379`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness + capability advertisement |
| POST | `/compile` | Compile Solidity source → ABI + bytecode |
| POST | `/scan` | Run static analysis on Solidity source |
| GET | `/detectors` | List supported vulnerability detectors |

### Example: Scan a Contract

```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "pragma solidity ^0.8.0; contract Vuln { function withdraw() external { msg.sender.call{value: 1 ether}(\"\"); } }",
    "version": "0.8.19",
    "run_compiler": false
  }'
```

## Directory Structure

```
backend/
├── main.py              # FastAPI entry point
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image
├── pytest.ini           # Test configuration
├── README.md            # This file
├── models/
│   └── schemas.py       # Pydantic request/response models
├── services/
│   ├── compiler.py      # Solidity compilation service (py-solc-x)
│   └── analyzer.py      # Static analysis engine
└── tests/
    └── test_api.py      # pytest + TestClient tests
```

## Testing

```bash
cd backend
pytest
```

Tests use `TestClient` and skip real `solc` compilation via `run_compiler=False` to avoid SSL/download issues in CI.

## Tech Stack

- **FastAPI** 0.115 — Web framework
- **Pydantic** 2.9 — Data validation
- **py-solc-x** 2.0 — Solidity compiler management
- **pytest** — Testing framework
- **PostgreSQL** 14 — Data persistence (future)
- **Redis** 7 — Caching / task queue (future)
