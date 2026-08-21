# HN Data Pipeline

Data pipeline for Hacker News: scraper → API → database.

## What it does

- Scrapes Hacker News front pages (with pagination and rate-limit handling)
- Sends scraped data to a FastAPI REST API
- Stores data in a SQLite database (SQLModel)
- Serves data through REST endpoints (`/stories`, `/domains`, `/top-domains`)

## Tech stack

- Python
- FastAPI
- SQLModel / SQLite
- Requests / BeautifulSoup
- Git

