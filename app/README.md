# MedExtractAI Backend

Production-ready FastAPI backend for medical document analysis, expert discovery, similarity search, and what-if simulation.

## Quickstart

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your secrets

# 4. Run with Docker Compose (includes Postgres + Redis)
docker-compose up -d

# Or run directly
uvicorn src.main:app --reload
```

Open http://localhost:8000/docs for API documentation.
