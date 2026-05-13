# Social Content — AuditCraft v2 (Build with MeDo Hackathon)

---

## 1. Announcement Post (#BuiltWithMeDo)

🚀 Just shipped **AuditCraft v2** for #BuiltWithMeDo!

An interactive smart contract security sandbox where you paste Solidity code and get real vulnerability detection — not regex guessing, actual solc compilation + AST analysis.

✅ 8 detectors (Reentrancy, Access Control, Overflow, etc.)
✅ Live at http://142.171.227.166:8000
✅ FastAPI + Docker + VPS deployment

Learn by doing. Break things safely.

#SmartContracts #Solidity #Web3Security #Hackathon

🎥 Video: https://youtu.be/CZOjSuQ0-4A
🔗 GitHub: https://github.com/yuzengbaao/auditcraft-v2

---

## 2. Technical Deep Dive (FastAPI + Docker + VPS)

**How AuditCraft v2 actually works under the hood:**

1. Paste Solidity → FastAPI receives it via REST
2. py-solc-x compiles with your chosen compiler version
3. Custom AST heuristics walk the parsed contract
4. 8 detectors flag issues with severity + line refs
5. Returns JSON → frontend renders inline annotations

Infra: Docker Compose (FastAPI + PostgreSQL + Redis) behind Nginx on a CloudCone VPS. One command to spin up anywhere.

Testing: 5/5 pytest passing with FastAPI TestClient.

No framework magic. Just real compilation and real analysis.

#FastAPI #Docker #DevOps #Python

---

## 3. Call to Action (Community Choice Voting)

We built AuditCraft v2 to make smart contract security learnable — not just readable.

If you think security education deserves real tools (not just tutorials), drop us a vote on DevPost:

[DevPost voting link placeholder]

Every vote = more reason to add Slither integration, multi-file support, and PDF reports next.

#BuiltWithMeDo #CommunityChoice #Web3Security

---

## 4. Behind the Scenes (v1 → v2 Upgrade Story)

**v1:** Regex on the frontend. Looked cool. Was wrong often.

**v2:** Real solc compilation. AST traversal. Severity grading. Docker deployment.

The lesson: security education tools have to be credible. If you're teaching someone to find bugs, your tool can't be guessing.

Biggest refactor: ripping out all frontend regex and building a FastAPI backend with py-solc-x. Suddenly every detection had a real line number and a real compiler to back it up.

Still heuristic-based, but now the heuristics run on actual bytecode-level info. Next step: plug in Slither for formal static analysis.

#BuildInPublic #SmartContracts #LessonsLearned

---
