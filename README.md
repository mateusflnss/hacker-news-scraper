# Hacker News Scraper — with Self-Validation

A Python scraper for the [Hacker News](https://news.ycombinator.com/) front pages that
**verifies its own output against the official Firebase API**.

Most scraping portfolios show you a script that produces a CSV. The hard part of
production scraping isn't producing a CSV — it's knowing whether the CSV is *correct*.
This project ships a second tool that answers that question, and the current
build reconciles **90 / 90 titles** against the official API with zero drift.

---

## What it does

| Script | Role |
| --- | --- |
| `scraper.py` | Scrapes HN listing pages into `HN_output.csv` / `HN_output.xlsx` |
| `comparator.py` | Pulls the same ranks from the official API and diffs them against the scrape |

The scraper parses the rendered HTML. The comparator hits
`hacker-news.firebaseio.com/v0` — an entirely independent source of truth — and reports
exactly which titles matched, which the API had that the scrape missed, and which the
scrape had that the API didn't. A parser that quietly breaks on a markup change gets
caught on the next run instead of six weeks later.

---

## Install

```bash
pip install requests beautifulsoup4 lxml pandas openpyxl
```

Tested on Python 3.14 with requests 2.33, bs4 4.14, pandas 3.0, openpyxl 3.1.

---

## Usage

Scrape the first three pages (ranks 1–90):

```bash
python scraper.py --start 1 --stop 3
```

Then validate that scrape against the API's top 90:

```bash
python comparator.py --n 90
```

Keep the two aligned: **each HN page holds 30 stories**, so `--n 90` expects
`--stop 3`. If they drift apart the comparator detects it and prints the exact
command to fix it, rather than reporting a mysterious shortfall.

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `scraper.py --start` | `1` | First page, 1-indexed |
| `scraper.py --stop` | `3` | Last page, inclusive |
| `comparator.py --n` | `90` | How many top stories to pull from the API (1–500) |

---

## Output schema

`HN_output.csv` and `HN_output.xlsx`, one row per story:

| Column | Description |
| --- | --- |
| `title` | Story headline |
| `link` | Target URL (may be a relative `item?id=` link for text posts) |
| `domain` | Source domain, blank for self-posts |
| `points` | Score, `0` for job listings |
| `author` | Submitter username, blank for job listings |
| `age` | Relative age string, e.g. `3 hours ago` |
| `comments_link` | Relative link to the discussion thread |
| `comments_text` | Raw comment-count text, e.g. `142 comments` or `discuss` |
| `comments_amount` | Parsed integer count, `0` when there are none |

`comparator.py` additionally writes `HN_OUTPUT_MATCHES.csv` (the full validated rows)
and `HN_OUTPUT_MATCHES_titles.csv` (just the matched titles).

---

## Engineering notes

The problems this codebase actually solves — the ones that only show up against a live
site:

**HN pages are 1-indexed.** `?p=0` is not "page zero." HN answers it with
`HTTP 429 Sorry.` — reproducibly, even from an otherwise idle client. A `--start 0`
default therefore burned one page every run and returned 60 rows where 90 were
expected. Page numbering is validated at parse time now, with the reason in the error.

**A dropped page must not look like clean output.** Older versions swallowed request
failures, wrote a short CSV, and exited `0`. Silent truncation is the worst failure mode
in scraping, because the damage surfaces downstream as a data problem rather than a
scrape problem. Failed pages are now collected, reported by number, and force a non-zero
exit.

**Rate limiting is the normal case, not the exception.** Back-to-back requests reliably
draw 429s. The scraper spaces pages by 2s and retries throttled pages with escalating
backoff before giving up.

**Never write a `set` straight to CSV.** Python randomizes string hashing per process, so
serializing a set produces a different row order on every run — two identical scrapes
diff as 100% changed. All set output is sorted before it's written.

**Normalize both sides of a comparison identically.** The API can return HTML-escaped
titles (`&#x27;`) while BeautifulSoup has already decoded the scraped side, so an
apostrophe silently breaks a match. Both sides run through `html.unescape` → `strip` →
`lower`.

**Job listings are structurally different.** They carry no score and no author, so
per-field extraction is guarded individually rather than assuming a uniform row shape.

---

## Politeness and ethics

Only public, unauthenticated pages are read. Requests are spaced and capped, the
`User-Agent` identifies the project with a contact address, and throttling is respected
with backoff rather than routed around. There is no attempt to defeat any bot-detection
measure. Adjust `REQUEST_DELAY` upward for larger crawls.

Hacker News publishes an [official API](https://github.com/HackerNews/API) — for
production use, prefer it. This project scrapes deliberately, as a demonstration of
extraction and validation technique.

---

## Possible extensions

- Persist to SQLite/Postgres with a run timestamp, to track rank movement over time
- Async fetching with a concurrency cap for larger page ranges
- Schedule the comparator in CI and alert when the match rate drops below a threshold
- Resolve `age` into absolute UTC timestamps
