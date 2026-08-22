from urllib import parse

import requests
from bs4 import BeautifulSoup
from time import sleep
import argparse
import sys
from datetime import datetime
import pandas as pd
from crud import add_story
from db import engine, init_db
from model import Story
from sqlmodel import Session
import os
from dotenv import load_dotenv

load_dotenv()
API_SECRET_KEY = os.getenv("API_KEY")


init_db()


BASE_URL = "https://news.ycombinator.com/"

DEFAULT_OUTPUT = "HN_output"

REQUEST_DELAY = 31  # seconds between pages; 

headers = {
    "User-Agent": "Mozilla/5.0 (educational scraping project; contact: mateusfelipe.do.nascimento@gmail.com)"
}
data = []

parser = argparse.ArgumentParser(description="Scrape Hacker News")

parser.add_argument("--start", type=int, default=3, help="First page to scrape, 1-indexed (default: 1)")
parser.add_argument("--stop", type=int, default=200, help="Last page to scrape, inclusive (default: 3)")
parser.add_argument("--output-name", type=str, default=DEFAULT_OUTPUT, 
                    help=f"Base name for output files (default: {DEFAULT_OUTPUT})")
parser.add_argument("--output-csv", type=bool, default=False, help=f"Whether to output CSV file (default: False)")
parser.add_argument("--output-excel", type=bool, default=False, help=f"Whether to output Excel file (default: False)")

args = parser.parse_args()

# Define os nomes dos arquivos baseado no argumento
output_csv = f"{args.output_name}.csv"
output_excel = f"{args.output_name}.xlsx"

print(f"Output files: {output_csv} and {output_excel}")

# HN pages are 1-indexed: ?p=1 is ranks 1-30, ?p=2 is 31-60, and so on.
# ?p=0 is not "page zero" -- HN answers it with HTTP 429, so it only ever
# produced a skipped page and a short dataset.
if args.start < 1:
    parser.error("--start must be at least 1 (Hacker News pages are 1-indexed; ?p=0 returns HTTP 429)")
if args.stop < args.start:
    parser.error("--stop must be greater than or equal to --start")

def fetch_page(page, attempts=3):
    url = f"{BASE_URL}?p={page}"
    for attempt in range(1, attempts + 1):
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            wait = REQUEST_DELAY * attempt
            print(f"Rate limited on page {page}, retrying in {wait}s ({attempt}/{attempts}).")
            sleep(wait)
            continue
        response.raise_for_status()
        return response
    raise requests.RequestException(f"gave up after {attempts} attempts (HTTP 429)")

def parse_data(response):
    soup = BeautifulSoup(response.text, "lxml")
    items = soup.select("tr.athing")
    thisData = []
    for item in items:
        hn_id = item.get("id", "")
        title_tag = item.select_one("span.titleline a")
        title = title_tag.get_text(strip=True) if title_tag else ""
        link = title_tag["href"] if title_tag else ""
        domain = item.select_one("span.sitestr").get_text(strip=True) if item.select_one("span.sitestr") else ""
        next_item = item.find_next_sibling("tr")
        points = next_item.select_one("span.score").get_text(strip=True).split()[0] if next_item.select_one("span.score") else "0"
        author = next_item.select_one("a.hnuser").get_text(strip=True) if next_item.select_one("a.hnuser") else ""
        age_tag = next_item.select_one("span.age")
        age = age_tag.get_text(strip=True) if age_tag else ""
        scraped_at = datetime.now().isoformat()


        comments_tag = None
        for i in next_item.select('a[href*="item?id="]'):
            text = i.get_text(strip=True)
            if "comment" in text or "discuss" in text:
                comments_tag = i
                break


        comments_link = comments_tag["href"] if comments_tag else ""
        comments_text = comments_tag.get_text(strip=True) if comments_tag else ""
        comments_amount = comments_text.split()[0] if comments_text and comments_text != "discuss" else "0"
        thisData.append({
            "hn_id": hn_id,
            "title": title,
            "url": link,
            "domain": domain,
            "points": points,
            "author": author,
            "age": age,
            "scraped_at": scraped_at,
            "comments_link": comments_link,
            "comments_text": comments_text,
            "comments_amount": comments_amount
        })
    return thisData

failed_pages = []


def post_data(stories_batch):
    post_headers = {"X_API_Key": API_SECRET_KEY} if API_SECRET_KEY else {}
    response = requests.post("https://hn-data-pipeline.onrender.com/stories/batch", json=stories_batch, headers=post_headers)

    if response.status_code == 200:
        print("batch sent successfully")
    else:
        print(f"failed to send batch. Status : {response.status_code}")
        print(response.text)
    return response


for current_page in range(args.start, args.stop + 1):
    try:
        response = fetch_page(current_page)
        thisData = parse_data(response)
        print(f"Scraped page {current_page} with {len(thisData)} items.")
        data.extend(thisData)

        post_data(thisData)  
    except requests.RequestException as e:
        print(f"Failed on page {current_page}: {e}")
        failed_pages.append(current_page)
    if current_page < args.stop:
        sleep(REQUEST_DELAY)

if (args.output_csv or args.output_excel) and data:
    df = pd.DataFrame(data)
    if args.output_csv:
        df.to_csv(output_csv, index=False)
    if args.output_excel:
        df.to_excel(output_excel, index=False)
    
# A dropped page silently shrinks the dataset, which is exactly what makes a
# short scrape look like a comparison bug later. Say so, and exit non-zero.
if failed_pages:
    print(f"WARNING: {len(failed_pages)} page(s) failed: {failed_pages}. Output is incomplete.")
    sys.exit(1)
