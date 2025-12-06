#!/usr/bin/env python3
# main.py
import json
import os
import random
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIG ----------
QUESTION_PATH = "data/examples/teacher/question_bank.json"
POSTED_IDS_PATH = "posted_ids.json"
OUTPUT_DIR = Path("out/cards")
ASSETS_DIR = Path("assets")
LOGO_PATH = ASSETS_DIR / "logo.png"         # put your logo here
BENGALI_FONT_PATH = ASSETS_DIR / "NotoSansBeng.ttf"  # optional
NUM_QUESTIONS_PER_POST = 25

PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN")
APP_NAME = "ICT Tutor Pro"
PLAY_STORE_URL = "https://play.google.com/store/search?q=ICT%20Tutor%20Pro&c=apps"
# ----------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    all_ids = [q["id"] for q in mcqs]
    available = [q for q in mcqs if q.get("id") not in already_posted]
    if len(available) < n:
        # reset posted list if not enough left
        already_posted = set()
        available = mcqs.copy()
    selected = random.sample(available, min(n, len(available)))
    return selected, already_posted


# ---------- Image generation (Style 2: Colored Premium Card) ----------
def load_font(size=36):
    try:
        if BENGALI_FONT_PATH.exists():
            return ImageFont.truetype(str(BENGALI_FONT_PATH), size)
    except Exception:
        pass
    return ImageFont.load_default()


def draw_gradient(im, top_color, bottom_color):
    # vertical gradient
    width, height = im.size
    base = Image.new('RGB', (width, height), top_color)
    top = Image.new('RGB', (width, height), bottom_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    im.paste(Image.composite(top, base, mask))


def generate_card_image(q, index, out_path):
    # card size: 1200x1200 (square)
    W, H = 1200, 1200
    im = Image.new("RGB", (W, H), (255, 255, 255))
    draw_gradient(im, (30, 58, 138), (58, 123, 213))  # blue gradient

    draw = ImageDraw.Draw(im)

    # header box
    header_h = 140
    draw.rectangle([(0, 0), (W, header_h)], fill=(10, 25, 65, 255))
    font_header = load_font(42)
    header_text = f"{APP_NAME} — MCQ #{index}"
    bbox = draw.textbbox((0, 0), header_text, font=font_header)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - w) / 2, (header_h - h) / 2), header_text, font=font_header, fill=(255, 255, 255))

    # logo if exists
    try:
        if LOGO_PATH.exists():
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((100, 100), Image.ANTIALIAS)
            lx = 40
            ly = (header_h - logo.size[1]) // 2
            im.paste(logo, (lx, ly), logo)
    except Exception as e:
        print("Logo load failed:", e)

    # question area
    font_question = load_font(40)
    question_text = q.get("question", "").replace("\n", " ")
    wrapped_q = textwrap.fill(question_text, width=28)  # tune width for readable lines

    q_y = header_h + 30
    draw.multiline_text((60, q_y), wrapped_q, font=font_question, fill=(245, 245, 245), spacing=6)

    # options
    font_option = load_font(36)
    options = q.get("options", [])
    opt_y = q_y + 220
    for opt in options:
        wrapped_opt = textwrap.fill(opt, width=40)
        draw.text((80, opt_y), wrapped_opt, font=font_option, fill=(250, 250, 250))
        opt_y += 60

    # small footer with "Answer key inside image"
    answer_text = f"Answer: {q.get('answer','')}"
    # Put answer in a colored box at bottom-right
    box_w, box_h = 420, 100
    box_x = W - box_w - 60
    box_y = H - box_h - 60
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(255, 235, 59))
    font_answer = load_font(32)
    # center the answer inside box
    aw, ah = draw.textsize(answer_text, font=font_answer)
    draw.text((box_x + (box_w - aw) / 2, box_y + (box_h - ah) / 2), answer_text, font=font_answer, fill=(0, 0, 0))

    # bottom small CTA
    cta_text = f"Download {APP_NAME} — {PLAY_STORE_URL}"
    font_cta = load_font(22)
    draw.text((60, H - 50), cta_text, font=font_cta, fill=(230, 230, 230))

    # Save
    im = im.filter(ImageFilter.SHARPEN)
    im.save(out_path, format="PNG", optimize=True)
    print("Saved card:", out_path)


# ---------- Facebook upload helpers ----------
def upload_photo_get_id(image_path):
    url = f"https://graph.facebook.com/{PAGE_ID}/photos"
    files = {"source": open(image_path, "rb")}
    data = {
        "published": "false",
        "access_token": ACCESS_TOKEN
    }
    resp = requests.post(url, files=files, data=data)
    try:
        j = resp.json()
    except:
        j = {"error": "invalid response", "text": resp.text}
    print("upload_photo:", j)
    if "id" in j:
        return j["id"]
    raise RuntimeError(f"Upload failed: {j}")


def create_feed_with_attached_photos(photo_ids, message):
    url = f"https://graph.facebook.com/{PAGE_ID}/feed"
    data = {
        "message": message,
        "access_token": ACCESS_TOKEN
    }
    # Graph API wants attached_media[0] = {"media_fbid":"ID"} style
    for idx, pid in enumerate(photo_ids):
        data[f"attached_media[{idx}]"] = json.dumps({"media_fbid": pid})
    resp = requests.post(url, data=data)
    try:
        j = resp.json()
    except:
        j = {"error": "invalid response", "text": resp.text}
    print("create_feed:", j)
    return j


def main():
    if not PAGE_ID or not ACCESS_TOKEN:
        print("FB_PAGE_ID and FB_PAGE_TOKEN must be set in environment/secrets.")
        return

    mcqs = load_questions()
    posted = load_posted_ids()
    selected, posted = pick_questions(mcqs, posted, NUM_QUESTIONS_PER_POST)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    folder = OUTPUT_DIR / f"post_{timestamp}"
    folder.mkdir(parents=True, exist_ok=True)

    image_paths = []
    for i, q in enumerate(selected, start=1):
        out_file = folder / f"mcq_{q.get('id')}.png"
        generate_card_image(q, i, out_file)
        image_paths.append(str(out_file))

    # upload each image with published=false, collect ids
    photo_ids = []
    for img in image_paths:
        try:
            pid = upload_photo_get_id(img)
            photo_ids.append(pid)
        except Exception as e:
            print("Error uploading", img, e)

    # Prepare post message (no answers here)
    msg_lines = [
        f"📚 {APP_NAME} থেকে আজকের MCQ সেট ({len(photo_ids)} টি)",
        "",
        f"📱 আরও MCQ অনুশীলনের জন্য ডাউনলোড করো: {PLAY_STORE_URL}",
        "",
        "#ICTTutorPro #ICT #HSC #ictsunnysir #Honours #MCQ #ICTBoardExam #Bangladesh #Education"
    ]
    message = "\n".join(msg_lines)

    if photo_ids:
        res = create_feed_with_attached_photos(photo_ids, message)
        print("Final post response:", res)
        # update posted ids set
        for q in selected:
            posted.add(q.get("id"))
        save_posted_ids(posted)
    else:
        print("No photos uploaded; aborting post.")


if __name__ == "__main__":
    main()
