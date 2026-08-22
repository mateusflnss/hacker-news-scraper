# HN Data Pipeline

A complete data pipeline that scrapes [Hacker News](https://news.ycombinator.com) stories, stores them in a relational database, and serves them through a REST API built with FastAPI.

**Live demo:** https://hn-data-pipeline.onrender.com/stories/ — interactive docs at [`/docs`](https://hn-data-pipeline.onrender.com/docs)
*(hosted on Render's free tier — first request after idle may take ~30s to cold start)*

## Features

- **Web scraper** that extracts stories from HN listing pages (title, URL, domain, points, author, age, comment count)
- **REST API** with filtering (by domain and minimum points), pagination, and story lookup by database ID or HN ID
- **Batch insertion endpoint** protected by API key — duplicate entries are skipped individually without failing the whole batch
- **Domain analytics**: distinct domains and a ranking of the most frequent ones
- **Data validation** script that cross-checks scraped results against the official Hacker News API
- **Automated tests** with pytest, running against an in-memory SQLite database via FastAPI dependency overrides
- **Layered architecture** (API → CRUD → database) for separation of concerns

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| API | FastAPI |
| ORM / models | SQLModel (SQLAlchemy + Pydantic) |
| Database | SQLite (development) · PostgreSQL (production) |
| Scraping | Requests + BeautifulSoup |
| Testing | pytest + FastAPI TestClient |
| Deploy | Render (environment-based configuration) |

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/stories/` | List stories with optional `domain` and `min_points` filters, plus `limit`/`offset` pagination |
| `GET` | `/stories/{story_id}` | Get a story by database ID |
| `GET` | `/stories/by-hn-id/{hn_id}` | Get a story by its Hacker News ID |
| `GET` | `/domains` | List distinct domains |
| `GET` | `/top-domains` | Domains ranked by number of stories |
| `POST` | `/stories/batch` | Insert multiple stories at once (requires `X_API_Key` header) |

Full request/response schemas are available in the auto-generated OpenAPI docs at `/docs`.

## Project structure

```
├── api.py          # FastAPI app and route definitions
├── crud.py         # Database operations (insert, queries, aggregations)
├── db.py           # Engine and session management
├── model.py        # SQLModel table definitions
├── schemas.py      # Pydantic request schemas
├── scraper.py      # HN scraper (feeds the batch endpoint)
├── conftest.py     # Shared pytest fixtures (test DB + client)
├── test_stories.py # API integration tests
├── compose.yaml    # Docker Compose config for local development
├── Dockerfile      # Docker image build instructions
└── requirements.txt
```

## Running locally

### Option 1: Using Docker Compose

This is the easiest way to run the API locally.

```bash
# 1. Clone and enter the project
git clone https://github.com/mateusflnss/hn-data-pipeline.git
cd hn-data-pipeline

# 2. Set environment variables (see .env.example)
#    API_KEY       — key required by the batch insertion endpoint
#    DATABASE_URL  — optional; defaults to local SQLite (hn.db)

# 3. Start the API in a Docker container
docker compose up --build
```


### Option 2: Using Docker (API only)

If you want to run only the API container (e.g., connecting to an external PostgreSQL):
```bash
docker pull ghcr.io/mateusflnss/hn-data-pipeline:latest
docker run -p 8000:8000 ghcr.io/mateusflnss/hn-data-pipeline:latest
```

### Option 3: Without Docker (Python virtual environment)

Requirements: Python 3.14+, pip, and PostgreSQL (optional).

```bash
# 1. Clone and enter the project
git clone https://github.com/mateusflnss/hn-data-pipeline.git
cd hn-data-pipeline

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Set environment variables (see .env.example)
#    API_KEY       — key required by the batch insertion endpoint
#    DATABASE_URL  — optional; defaults to local SQLite (hn.db)

# 4. Start the API
uvicorn api:app --reload
```

The interactive documentation will be available at `https://localhost:8000/docs`.

## Running the scraper

```bash
python scraper.py
```

The scraper collects stories from the HN listing pages and sends them to the API's batch endpoint. A separate validation script compares the scraped data against the official HN API to verify accuracy.

## Running the tests

```bash
pytest -v
```

Tests run against an in-memory SQLite database using FastAPI's dependency override mechanism — no real data is touched, and every test starts from a clean state.

## Design decisions

- **Layered architecture**: routes only handle HTTP concerns and delegate to the CRUD layer, which is the only code that talks to the database. This keeps each layer independently testable.
- **Resilient batch inserts**: a duplicate or malformed story in a batch is reported in the response (`skipped` / `errors`) instead of aborting the entire request.
- **Environment-based configuration**: the same codebase runs on SQLite locally and PostgreSQL in production, switched by `DATABASE_URL`.