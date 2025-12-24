# Patent Editor Server

Run the server with the following command,
> `uvicorn app.__main__:app --reload`

#### Document Management: 
Create, update, list, and switch between patent document versions.

#### AI Features:

- Rephrase Claims (/ai/rewrite) - rewrites selected claims for clarity.
- Analyze Patent (/ai/analyze) - gives a score (0-100) + highlights potential rejection issues.
- Real-time Suggestions (WebSocket /ws) - streams AI suggestions as the document is being edited.

#### Database: 
In-memory SQLite DB with seeded patents (resets on restart).

<hr>

## Overview

This backend powers the Patent Editor application.
It provides a FastAPI-based service for managing patent documents with version control and using LLM to rewrite claims, analyze patent quality, and stream live suggestions.

## Project Layout
```
app
├── __main__.py          # FastAPI app, routes, and WebSocket handlers
├── models.py            # SQLAlchemy DB models
├── schemas.py           # Pydantic schema objects
├── ai_extended.py       # Extended AI functionality (rewrite + analysis)
├── internal
│   ├── ai.py            # Core LLM client integration
│   ├── data.py          # Seed patent data
│   └── db.py            # Database utilities (SQLite, sessions, etc.)
```
<hr>

## Setup Instructions

### Environment Setup

1. Create virtual environment `python -m venv env`

1. Activate environment

    Linux / Mac - `source env/bin/activate`

    Windows - `env\Scripts\activate`

### Install dependencies

> `pip install -r requirements.txt`

### Configure API Key

Create a **".env"** file in the project root (see .env.example) and add the OpenAI API key.

```
OPENAI_API_KEY=<api_key_here>
OPENAI_MODEL=gpt-3.5-turbo-1106   # Default if not set
```

### Run the Server
> `uvicorn app.__main__:app --reload`


The backend will start at:
> `http://localhost:8000`

<hr>

## Database

- Uses SQLite (in-memory).
- Automatically initialized on server startup.
- Seeded with 2 sample patent documents.
- Reset occurs every time the backend restarts.

<hr>

## API Endpoints

### Document Versioning

- `GET /document/{id}` - Get current version of a document.

- `POST /documents/{id}/versions` - Create a new version (auto-increments version number).

- `GET /documents/{id}/versions` - List all versions of a document.

- `GET /documents/{id}/versions/{version_number}` - Retrieve a specific version.

- `PATCH /documents/{id}/versions/{version_number}` - Update version content.

- `PATCH /documents/{id}/switch/{version_number}` - Switch active version for a document.

### AI Features

- `POST /ai/rewrite` - Rewrites a selected claim using wider document context.

- `POST /ai/analyze` - Analyzes document → returns { score, problems[] }.

- `WS /ws` → Streams AI suggestions in real-time as edits are made.

<hr>

## Development Notes

Unit tests should be placed in a top-level tests/ directory. Run tests with the following command.

> `pytest -v`

<hr>
