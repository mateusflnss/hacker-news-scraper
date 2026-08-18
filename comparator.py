# This comparator exists to prove that the scraper works.
# It pulls the same data from the official API and diffs it against our scrape.
# A successful run shows 100% match. This is how we catch markup changes early.


import argparse
import html
import requests
import pandas as pd
from time import sleep

API_URL = "https://hacker-news.firebaseio.com/v0"
INPUT_CSV = "HN_output.csv"
MATCHED_ROWS_CSV = "HN_OUTPUT_MATCHES.csv"
MATCHED_TITLES_CSV = "HN_OUTPUT_MATCHES_titles.csv"
ITEMS_PER_PAGE = 30
API_DELAY = 0.1


def get_api_top_stories(n):
    response = requests.get(f"{API_URL}/topstories.json", timeout=10)
    response.raise_for_status()
    items = []
    for story_id in response.json()[:n]:
        item = requests.get(f"{API_URL}/item/{story_id}.json", timeout=10).json()
        sleep(API_DELAY)  # Be polite and avoid hitting the API too quickly
        items.append(item)
    return items


def normalize_title(title):
    # The API can hand back HTML-escaped titles (&#x27; and friends) while
    # BeautifulSoup already decoded the scraped side. Unescape both so the
    # two sets stay comparable.
    return html.unescape(str(title)).strip().lower()


def main():
    parser = argparse.ArgumentParser(
        description="Compare scraped Hacker News titles against the official API"
    )
    parser.add_argument("--n", type=int, default=90,
                        help="Number of top stories to pull from the API (default: 90)")
    args = parser.parse_args()

    if not 1 <= args.n <= 500:
        parser.error("--n must be between 1 and 500")

    top_stories = get_api_top_stories(args.n)
    api_titles = {normalize_title(story["title"]) for story in top_stories}

    df = pd.read_csv(INPUT_CSV)
    df = df.dropna(subset=["title"])
    csv_titles = {normalize_title(title) for title in df["title"]}

    # Sorted, not a raw set: set iteration order is randomized per process, so
    # writing a set straight to CSV made every run look like a full diff.
    matches = sorted(api_titles & csv_titles)
    only_api = sorted(api_titles - csv_titles)
    only_csv = sorted(csv_titles - api_titles)

    print(f"API titles:     {len(api_titles)} (top {args.n})")
    print(f"Scraped titles: {len(csv_titles)} (from {INPUT_CSV})")
    print(f"Matches:        {len(matches)}")
    for title in matches:
        print(f"  - {title}")

    if only_api:
        print(f"\nIn API but not scraped ({len(only_api)}):")
        for title in only_api:
            print(f"  - {title}")
    if only_csv:
        print(f"\nScraped but not in API top {args.n} ({len(only_csv)}):")
        for title in only_csv:
            print(f"  - {title}")

    # The usual cause of a lopsided diff is a scrape that covered fewer ranks
    # than --n asks for. Point at the fix instead of leaving it a mystery.
    pages_needed = -(-args.n // ITEMS_PER_PAGE)
    if len(csv_titles) < args.n:
        print(f"\nHint: --n {args.n} covers ranks 1-{args.n}, which needs {pages_needed} "
              f"scraped pages but {INPUT_CSV} has {len(csv_titles)} titles.")
        print(f"      Re-run: python test.py --start 1 --stop {pages_needed}")

    pd.DataFrame({"title": matches}).to_csv(MATCHED_TITLES_CSV, index=False)
    df_matches = df[df["title"].apply(normalize_title).isin(matches)]
    df_matches.to_csv(MATCHED_ROWS_CSV, index=False)

    if len(df_matches) != len(matches):
        print(f"\nNote: {len(df_matches)} matched rows for {len(matches)} unique titles "
              f"(duplicate titles in {INPUT_CSV}).")
    print(f"\nWrote {MATCHED_TITLES_CSV} and {MATCHED_ROWS_CSV}.")


if __name__ == "__main__":
    main()
