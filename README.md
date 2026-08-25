# The 24/7 Intelligent Code Reviewer

A submission-ready full-stack prototype for automated, always-on code review.

## Features

- Authenticated user registration/login with secure password hashing.
- Multi-language review support for Python, JavaScript/TypeScript, Java, C/C++, Go, SQL, and generic code.
- Bug, security, performance, readability, and architecture findings.
- Standardized quality score from 1–10.
- Historical review CSV ingestion and rule matching.
- Persistent per-user review/session history with SQLite.
- Growth and optimization trend dashboard.
- Review detail page with code, findings, recommendations, and historical insights.
- REST API suitable for extending to an LLM-backed review engine.
- Responsive UI with no external frontend build step.

## Run locally

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

Demo account:
- Email: demo@example.com
- Password: Demo@123

A SQLite database is created automatically in `data/reviewer.db`.
Historical rules are loaded from `data/historical_reviews.csv`.

## API

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/reviews`
- `GET /api/reviews`
- `GET /api/reviews/{id}`
- `GET /api/dashboard`
- `POST /api/historical/import`

## Architecture

```text
Browser
  |
  v
FastAPI + Jinja/Static UI
  |
  +--> Review Engine
  |      +--> Language rules
  |      +--> Security checks
  |      +--> Performance checks
  |      +--> Architecture checks
  |      +--> Historical rule matcher
  |
  +--> SQLAlchemy / SQLite
         +--> Users
         +--> Reviews
         +--> Findings
         +--> HistoricalRules
```

## Extending to a production LLM reviewer

The review engine is deliberately separated in `app/reviewer.py`. A production implementation can add an LLM provider behind the same interface while retaining deterministic security checks, score normalization, historical grounding, and persistence.

## Notes

This is a practical project prototype, not a sandboxed arbitrary-code execution service. Submitted source is analyzed as text and is never executed by the server.
