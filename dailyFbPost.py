#!/usr/bin/env python3
# main.py
import json
import os
import random
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIG ----------
QUESTION_PATH = "data/examples/teacher/question_bank.json"
POSTED_IDS_PATH = "posted_ids.json"

NUM_QUESTIONS_PER_POST = 25

PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN")
APP_NAME = "ICT Tutor Pro"
PLAY_STORE_URL = "https://play.google.com/store/search?q=ICT%20Tutor%20Pro&c=apps"
# ----------------------------


def load_questions():
    with open(QUESTION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict) and "mcqs" in data:
            return data["mcqs"]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("question_bank.json format not recognized")


def load_posted_ids():
    if os.path.exists(POSTED_IDS_PATH):
        with open(POSTED_IDS_PATH, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()


def save_posted_ids(ids_set):
    with open(POSTED_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(list(ids_set), f, ensure_ascii=False, indent=2)


def pick_questions(mcqs, already_posted, n):
    available = [q for q in mcqs if q.get("id") not in already_posted]

    if len(available) < n:
        # reset if needed
        already_posted = set()
        available = mcqs.copy()

    selected = random.sample(available, min(n, len(available)))
    return selected, already_posted


# ---------- Facebook helpers ----------

def post_feed_message(message):
    url = f"https://graph.facebook.com/{PAGE_ID}/feed"
    data = {
        "message": message,
        "access_token": ACCESS_TOKEN
    }
    resp = requests.post(url, data=data)
    try:
        return resp.json()
    except:
        return {"error": resp.text}


def main():
    if not PAGE_ID or not ACCESS_TOKEN:
        print("FB_PAGE_ID and FB_PAGE_TOKEN must be set in environment/secrets.")
        return

    mcqs = load_questions()
    posted = load_posted_ids()

    selected, posted = pick_questions(mcqs, posted, NUM_QUESTIONS_PER_POST)

    # Build MCQ text block
    lines = [
        f"📚 আজকের {NUM_QUESTIONS_PER_POST} টি ICT MCQ — {APP_NAME}\n",
    ]

    for idx, q in enumerate(selected, start=1):
        lines.append(f"❓ প্রশ্ন {idx}: {q.get('question','')}")
        opts = q.get("options", [])
        for opt in opts:
            lines.append(f"➡️ {opt}")
        lines.append(f"✔ সঠিক উত্তর: {q.get('answer','')}\n")

    # CTA + Hashtags
    lines.append(f"📲 আরও MCQ অনুশীলনের জন্য অ্যাপ ডাউনলোড করো:\n{PLAY_STORE_URL}\n")
    lines.append("#ICTTutorPro #ICT #HSC #MCQ #Bangladesh #Education")

    message = "\n".join(lines)

    # Post to Facebook
    res = post_feed_message(message)
    print("Post Response:", res)

    # save posted ids
    for q in selected:
        posted.add(q.get("id"))
    save_posted_ids(posted)


if __name__ == "__main__":
    main()
