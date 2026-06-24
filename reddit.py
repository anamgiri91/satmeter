"""
reddit_collect.py

Pulls comments from r/ApplyingToCollege into an UNLABELED CSV for you to
annotate yourself. Requires your own Reddit API credentials (free tier,
meant for personal projects / academic research):

    1. Go to https://www.reddit.com/prefs/apps
    2. Click "create another app", choose type = "script"
    3. Note the client_id (under the app name) and client_secret

Usage:
    pip install praw --break-system-packages
    export REDDIT_CLIENT_ID=your_client_id
    export REDDIT_CLIENT_SECRET=your_client_secret
    export REDDIT_USER_AGENT="takemeter-collector/0.1 by <your_reddit_username>"
    python reddit_collect.py
"""

import os
import csv
import time
import praw

SUBREDDIT = "ApplyingToCollege"

# Point this at specific threads rather than relying only on search —
# decision megathreads, financial aid stickies, and chance-me threads each
# have a much higher hit rate for a specific label than random sampling.
# Paste the submission ID (the part of the URL right after /comments/).
SUBMISSION_IDS = [
    # "abc123",
]

# Used to find more threads of each high-yield type.
SEARCH_QUERIES = [
    "financial aid",
    "chance me",
    "Common Data Set",
    "decision thread",
]

OUTPUT_PATH = "takemeter_raw_comments.csv"
SEARCH_LIMIT_PER_QUERY = 30  # number of threads to pull per search query


def get_reddit():
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )


def is_usable(comment):
    if comment.body in ("[deleted]", "[removed]"):
        return False
    if len(comment.body.strip()) < 15:
        return False
    if comment.author is None:  # deleted accounts
        return False
    return True


def collect_from_submission(reddit, submission_id, rows, seen_ids):
    submission = reddit.submission(id=submission_id)
    submission.comments.replace_more(limit=0)  # skip "load more comments" stubs
    for comment in submission.comments.list():
        if comment.id in seen_ids or not is_usable(comment):
            continue
        rows.append({
            "comment_id": comment.id,
            "thread_title": submission.title,
            "permalink": f"https://reddit.com{comment.permalink}",
            "text": comment.body.replace("\n", " ").strip(),
            "score": comment.score,
            "created_utc": comment.created_utc,
            "label": "",          # fill in during annotation
            "label_source": "",   # human_reviewed / llm_prelabel
        })
        seen_ids.add(comment.id)


def collect_from_search(reddit, query, rows, seen_ids):
    for submission in reddit.subreddit(SUBREDDIT).search(query, limit=SEARCH_LIMIT_PER_QUERY, sort="top"):
        collect_from_submission(reddit, submission.id, rows, seen_ids)
        time.sleep(0.5)  # stay comfortably under the 100 req/min free-tier limit


def main():
    reddit = get_reddit()
    rows, seen_ids = [], set()

    for sub_id in SUBMISSION_IDS:
        collect_from_submission(reddit, sub_id, rows, seen_ids)
        time.sleep(0.5)

    for query in SEARCH_QUERIES:
        collect_from_search(reddit, query, rows, seen_ids)

    if not rows:
        print("No comments collected — check SUBMISSION_IDS / SEARCH_QUERIES.")
        return

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Collected {len(rows)} comments -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()