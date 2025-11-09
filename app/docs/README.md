# MedExtractAI 2.0

Production-ready, security-first platform for medical document analysis, expert discovery, similarity search, and what-if simulation, with tamper-evident auditing and AuraQuan ZK-proof folding.

## Quickstart

1) python -m venv .venv && source .venv/bin/activate
2) pip install -r requirements.txt
3) cp .env.example .env && edit secrets
4) make dev (or: uvicorn src.main:app --reload)

Open http://localhost:8000/docs
