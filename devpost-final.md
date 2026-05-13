# AuditCraft v2 — DevPost Final Update

## Inspiration

Smart contract security is one of the most critical challenges in Web3. Over $3.8 billion was lost to smart contract exploits in 2022 alone. Yet learning smart contract auditing requires expensive courses, complex tool setups, and access to real vulnerability databases.

AuditCraft v2 solves this by providing a browser-based sandbox with **real compilation and static analysis** — not regex guessing. We upgraded from our v1 prototype (pure frontend, pattern matching) to a full-stack platform with FastAPI backend, actual solc integration, and production deployment.

## What it does

AuditCraft v2 is an interactive smart contract security sandbox that teaches developers how to identify and fix security vulnerabilities through hands-on practice.

**Key capabilities:**
- **Real compilation**: Paste Solidity code and compile with actual solc via py-solc-x
- **Static analysis**: 8 vulnerability detectors flag issues with severity grading
- **Severity classification**: Critical / High / Medium / Low with exact line references
- **Remediation guidance**: Every finding includes explanation and suggested fix
- **Live deployment**: Running on cloud VPS at http://142.171.227.166:8000

Users paste code → click Analyze → get real findings with line numbers, severity colors, and fix recommendations.

## How we built it

We rebuilt AuditCraft as a full-stack application:

1. **Backend (FastAPI + Python)**: 
   - py-solc-x for multi-version Solidity compilation
   - Custom AST-based heuristics for vulnerability detection
   - Pydantic schemas for type-safe REST APIs
   - 5 automated tests with pytest + TestClient

2. **Frontend (Vanilla JS)**:
   - VS Code-inspired dark theme
   - Real-time API calls to backend
   - Expandable finding cards with severity color coding

3. **Infrastructure**:
   - Docker Compose orchestration
   - PostgreSQL + Redis for future data persistence
   - Nginx reverse proxy
   - Deployed on CloudCone VPS

4. **Video**: Playwright real-browser recording with Audio-first Pipeline

## Challenges we ran into

- **Backend complexity**: Moving from regex-only frontend to real compilation required integrating py-solc-x and handling multi-version compiler management
- **Deployment**: Setting up Docker, Nginx, and VPS networking for production-grade availability
- **Analyzer accuracy**: Balancing detection coverage with false positives in heuristic-based analysis
- **Video production**: First attempt used simulated rendering (rejected); second attempt used Playwright headed mode with real browser recording and Audio-first Pipeline for sync

## Accomplishments that I'm proud of

1. **Real compilation**: Actual solc integration — not regex guessing or pattern matching
2. **8 vulnerability detectors**: Reentrancy, Access Control, Overflow, Unchecked Calls, Timestamp Dependence, tx.origin, Unused Variables, Compiler Warnings
3. **Production deployment**: Live API with Docker on cloud VPS
4. **Test coverage**: 5/5 pytest passing with FastAPI TestClient
5. **Real browser demo**: Video recorded via Playwright headed mode with authentic backend calls

## What we learned

Building a real backend taught us that:
- Security education tools need real compilation to be credible
- FastAPI + Pydantic dramatically reduces API bugs compared to untyped approaches
- Docker makes deployment reproducible across environments
- Test coverage is essential for hackathon demos
- Audio-first Pipeline (generate audio first, measure duration, then record video) solves sync issues

## What's next for AuditCraft v2

- **Slither integration**: Plug in formal static analysis for production-grade detection
- **Multi-file support**: Analyze projects with imports and libraries
- **User authentication**: Track learning progress across sessions
- **PDF report export**: Generate professional audit reports
- **Advanced detectors**: Flash loan attacks, oracle manipulation, governance exploits
- **Certification pathway**: Structured curriculum with verifiable credentials

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
- Playwright

## Try it out

- **Live Demo**: http://142.171.227.166:8000
- **GitHub**: https://github.com/yuzengbaao/auditcraft-v2
- **Video**: https://youtu.be/CZOjSuQ0-4A

## Update Note

This is an upgraded submission from our original v1 prototype. v2 adds a real FastAPI backend with solc compilation, production Docker deployment, comprehensive testing, and a re-recorded demo video with authentic browser capture.
