# AuditCraft v2 — Smart Contract Security Sandbox

> An educational, browser-based sandbox for analyzing Solidity smart contract security. Paste code, click **Analyze**, and get instant static-analysis findings with severity ratings, line references, and remediation hints.

---

## 📸 Screenshot

![AuditCraft v2 Screenshot]([Screenshot Placeholder])

---

## 🚀 Quick Start

### 1. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### 2. Open the Frontend

```bash
# Option A: simply open the file in your browser
open frontend/index.html

# Option B: serve via any static server (enables fetch without CORS warnings in some browsers)
cd frontend
python -m http.server 3000
# Then visit http://localhost:3000
```

> **Note:** The frontend uses `fetch()` to call `http://localhost:8000`. The backend already has CORS configured (`allow_origins=["*"]`) for local development.

---

## 🏗️ Project Structure

```
auditcraft-v2/
├── README.md                 # This file
├── .gitignore                # Git ignore rules
├── docker-compose.yml        # Full stack orchestration
├── backend/                  # FastAPI REST API
│   ├── main.py               # FastAPI entry point
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Backend container image
│   ├── pytest.ini            # Test configuration
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response models
│   ├── services/
│   │   ├── compiler.py       # py-solc-x compilation service
│   │   └── analyzer.py       # Static analysis engine
│   └── tests/
│       └── test_api.py       # pytest + TestClient suite
└── frontend/                 # Vanilla JS single-page app
    ├── index.html            # Single-file HTML shell
    ├── app.js                # API calls + DOM rendering
    └── style.css             # VS Code–inspired dark theme
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI 0.115 + Pydantic 2.9 + py-solc-x 2.0 |
| Frontend | Vanilla JavaScript (ES6) + CSS3 |
| Testing | pytest + FastAPI TestClient |
| Infrastructure | Docker + Docker Compose |
| Data (future) | PostgreSQL 14 + Redis 7 |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness probe + capability advertisement |
| `POST` | `/compile` | Compile Solidity source → ABI + bytecode |
| `POST` | `/scan` | Run static analysis, return findings list |
| `GET` | `/detectors` | List supported vulnerability detectors |

### Example Request

```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "pragma solidity ^0.8.0; contract Vuln { function withdraw() external { msg.sender.call{value: 1 ether}(\"\"); } }",
    "version": "0.8.19",
    "run_compiler": false
  }'
```

### Example Response

```json
{
  "success": true,
  "findings": [
    {
      "id": "REENTRANCY-001",
      "title": "Reentrancy in withdraw()",
      "vulnerability_type": "Reentrancy",
      "severity": "High",
      "line": 7,
      "column": 8,
      "contract": "Vuln",
      "function": "withdraw",
      "description": "External call before state update allows reentrant withdrawal.",
      "recommendation": "Use Checks-Effects-Interactions pattern or ReentrancyGuard.",
      "code_snippet": "msg.sender.call{value: 1 ether}(\"\");",
      "confidence": "High"
    }
  ],
  "summary": {},
  "compiler_output": null,
  "scan_time_ms": 42,
  "detectors_run": ["Reentrancy"]
}
```

---

## 🐳 Docker Deployment

Spin up the entire stack (backend + PostgreSQL + Redis) with one command:

```bash
docker compose up --build
```

Services:
- **Backend** → `http://localhost:8000`
- **PostgreSQL** → `localhost:5432`
- **Redis** → `localhost:6379`

To run in detached mode:

```bash
docker compose up --build -d
```

To stop:

```bash
docker compose down
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest -v
```

Tests use `TestClient` and skip real `solc` compilation (`run_compiler=false`) to avoid SSL/download issues in CI.

### Manual Frontend Test

1. Start backend (`uvicorn main:app --port 8000`)
2. Open `frontend/index.html` in a browser
3. Click **Load Sample** → **Analyze**
4. Verify findings appear with correct severity colors

---

## 🎨 Severity Colors

| Severity | Color | Hex |
|----------|-------|-----|
| Critical | 🔴 Red | `#f14c4c` |
| High | 🟠 Orange | `#ff8800` |
| Medium | 🟡 Yellow | `#ffcc00` |
| Low | 🔵 Blue | `#4fc1ff` |
| Info | ⚪ Gray | `#858585` |

---

## 📋 Roadmap

- [ ] Add more detectors (delegatecall, flash-loan susceptibility, etc.)
- [ ] Upload `.sol` files directly
- [ ] Export findings to PDF / JSON
- [ ] Multi-file project support
- [ ] User authentication & scan history

---

## 📄 License

MIT — Built for educational and research purposes.
