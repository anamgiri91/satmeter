# scripts/collect_college_confidential_links.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

BASE = "https://talk.collegeconfidential.com"

CATEGORY_URLS = [
    "https://talk.collegeconfidential.com/c/paying-for-college/44",
    "https://talk.collegeconfidential.com/c/what-are-my-chances/634",
]

HEADERS = {
    "User-Agent": "TakeMeter academic research project; contact: your_email@example.com"
}


def collect_thread_links():
    rows = []

    for category_url in CATEGORY_URLS:
        print(f"Fetching {category_url}")
        res = requests.get(category_url, headers=HEADERS, timeout=20)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "/t/" not in href:
                continue

            url = urljoin(BASE, href)
            title = a.get_text(" ", strip=True)

            if not title or len(title) < 5:
                continue

            rows.append(
                {
                    "source": "college_confidential",
                    "category_url": category_url,
                    "thread_title": title,
                    "url": url,
                }
            )

        time.sleep(3)

    df = pd.DataFrame(rows).drop_duplicates(subset=["url"])
    df.to_csv("data/raw/college_confidential_thread_links.csv", index=False)
    print(f"Saved {len(df)} College Confidential thread links.")


if __name__ == "__main__":
    collect_thread_links()