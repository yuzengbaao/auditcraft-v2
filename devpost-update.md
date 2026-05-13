# DevPost Update — AuditCraft v2

## Project Name
AuditCraft v2 — Smart Contract Security Sandbox

## Tagline
Learn smart contract security with real compilation and static analysis. Paste code, detect vulnerabilities, master defense.

## What it does
AuditCraft v2 is an interactive educational platform that teaches developers how to identify and fix security vulnerabilities in Solidity smart contracts.

Key improvements over v1:
- **Real backend**: FastAPI with py-solc-x for actual Solidity compilation
- **Static analysis**: 8 vulnerability detectors (Reentrancy, Access Control, Overflow, etc.)
- **Live deployment**: Running on cloud VPS with Docker
- **Severity grading**: Critical/High/Medium/Low with line-by-line references
- **Remediation hints**: Every finding includes explanation and fix suggestion

## How we built it
We built AuditCraft v2 as a full-stack application:

1. **Backend**: FastAPI (Python) with py-solc-x for multi-version Solidity compilation, custom AST-based heuristics for vulnerability detection, and Pydantic schemas for type-safe APIs.
2. **Frontend**: Vanilla JavaScript with a VS Code-inspired dark theme, calling the backend via REST API for real-time analysis.
3. **Infrastructure**: Docker Compose orchestration with PostgreSQL and Redis, deployed on CloudCone VPS.
4. **Testing**: pytest + FastAPI TestClient with 5 automated tests covering health, scan, compile, and detectors endpoints.

## Challenges we ran into
- **Backend complexity**: Moving from regex-only frontend to real compilation required integrating py-solc-x and handling version management.
- **Deployment**: Setting up Docker, Nginx, and VPS networking for production-grade availability.
- **Analyzer accuracy**: Balancing detection coverage with false positives in heuristic-based analysis.

## Accomplishments
1. **Real compilation**: Actual solc integration, not regex guessing
2. **8 vulnerability detectors**: Reentrancy, Access Control, Overflow, Unchecked Calls, Timestamp Dependence, tx.origin, Unused Variables, Compiler Warnings
3. **Production deployment**: Live API at http://142.171.227.166:8000
4. **Test coverage**: 5/5 pytest passing
5. **Docker deployment**: One-command setup with docker-compose

## What we learned
Building a real backend taught us that:
- Security education tools need real compilation to be credible
- FastAPI + Pydantic dramatically reduces API bugs
- Docker makes deployment reproducible
- Test coverage is essential for hackathon demos

## What's next
- Add Slither integration for formal static analysis
- Multi-file project support
- User authentication and scan history
- PDF report export
- Flash loan and oracle manipulation detectors

## Built With
- FastAPI
- Python
- py-solc-x
- Docker
- Vanilla JavaScript
- pytest
- PostgreSQL
- Redis
- Nginx

## Try it out
- **Live API**: http://142.171.227.166:8000
- **GitHub**: https://github.com/yuzengbaao/auditcraft-v2
- **Video**: https://youtu.be/CZOjSuQ0-4A
