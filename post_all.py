#!/usr/bin/env python3
"""
post_all.py - Multi-account Twitter poster
Uses /api/upload_text for text, /api/upload_photos for images.
Marks posts as 'scheduling' BEFORE sending to Upload Post to prevent duplicates.
"""

import os
import sys
import json
import time
import datetime
import requests
import gspread
from pathlib import Path

UPLOAD_POST_API_KEY = os.environ.get("UPLOAD_POST_API_KEY", "")
UPLOAD_POST_USER = os.environ.get("UPLOAD_POST_USER", "")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH", "google-creds.json")

UPLOAD_POST_BASE = "https://api.upload-post.com/api"
LEONARDO_V2_URL = "https://cloud.leonardo.ai/api/rest/v2/generations"
LEONARDO_V1_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"

TAB_TO_PROFILE = {
    "Posts": os.environ.get("UPLOAD_POST_USER", "@brendanwardai"),
    "EveryFreeTool": "@EveryFreeTool",
    "WhatIfs": "@ifswhat91839",
}


def get_sheet():
    creds_path = Path(__file__).parent / GOOGLE_CREDS_PATH
    if not creds_path.exists():
        creds_json = os.environ.get("GOOGLE_SHEETS_CREDS", "")
        if creds_json:
            creds_path = Path("/tmp/google-creds.json")
            with open(creds_path, "w") as f:
                f.write(creds_json)
        else:
            print("ERROR: No Google credentials found")
            sys.exit(1)
    gc = gspread.service_account(filename=str(creds_path))
    return gc.open_by_key(GOOGLE_SHEET_ID)


def post_text(content, profile, scheduled_date=None):
    data = {
        "user": profile,
        "platform[]": "x",
        "title": content,
    }
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
        data["timezone"] = "America/New_York"
    resp = requests.post(
        f"{UPLOAD_POST_BASE}/upload_text",
        headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
        data=data,
        timeout=60,
    )
    if resp.status_code >= 400:
        print(f"    Text post error ({resp.status_code}): {resp.text[:300]}")
    resp.raise_for_status()
    return resp.json()


def post_photo(content, image_url, profile, scheduled_date=None):
    img_resp = requests.get(image_url, timeout=30)
    img_resp.raise_for_status()
    tmp_path = Path(__file__).parent / "tmp_photo.jpg"
    with open(tmp_path, "wb") as f:
        f.write(img_resp.content)

    data = {
        "user": profile,
        "platform[]": "x",
        "title": content,
    }
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
        data["timezone"] = "America/New_York"

    with open(tmp_path, "rb") as img:
        resp = requests.post(
            f"{UPLOAD_POST_BASE}/upload_photos",
            headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
            data=data,
            files={"photos[]": ("photo.jpg", img, "image/jpeg")},
            timeout=60,
        )
    tmp_path.unlink(missing_ok=True)
    if resp.status_code >= 400:
        print(f"    Photo post error ({resp.status_code}): {resp.text[:300]}")
    resp.raise_for_status()
    return resp.json()


def post_thread(tweets, profile, tab_name, ws, headers, thread_rows, scheduled_date=None):
    posted_count = 0
    for i, tweet in enumerate(tweets):
        row_num = thread_rows[i]["row_num"] if i < len(thread_rows) else None
        status_col = headers.index("Status") + 1 if "Status" in headers else len(headers)

        # Mark as scheduling BEFORE sending
        if row_num:
            ws.update_cell(row_num, status_col, "scheduling")

        try:
            if scheduled_date and i == 0:
                result = post_text(tweet, profile, scheduled_date)
            elif scheduled_date and i > 0:
                try:
                    dt = datetime.datetime.strptime(scheduled_date, "%Y-%m-%d %H:%M")
                    dt = dt + datetime.timedelta(minutes=i * 2)
                    offset_time = dt.strftime("%Y-%m-%d %H:%M")
                    result = post_text(tweet, profile, offset_time)
                except Exception:
                    result = post_text(tweet, profile)
            else:
                result = post_text(tweet, profile)

            if row_num:
                ws.update_cell(row_num, status_col, "posted")
            posted_count += 1
            print(f"    Thread {i+1}/{len(tweets)} posted")
            time.sleep(3)
        except Exception as e:
            print(f"    Thread tweet {i+1} failed: {e}")
            if row_num:
                ws.update_cell(row_num, status_col, f"failed: {str(e)[:50]}")
    return posted_count


def generate_image_fresh(prompt, model="nano-banana-2"):
    if not LEONARDO_API_KEY:
        return ""
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
    }
    payload = {
        "model": model,
        "parameters": {
            "width": 1024,
            "height": 1024,
            "prompt": prompt,
            "quantity": 1,
        },
        "public": False,
    }
    try:
        resp = requests.post(LEONARDO_V2_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        gen_id = None
        if "generate" in data:
            gen_id = data["generate"]["generationId"]
        elif "sdGenerationJob" in data:
            gen_id = data["sdGenerationJob"]["generationId"]
        if not gen_id:
            return ""
        for attempt in range(20):
            time.sleep(4)
            s = requests.get(f"{LEONARDO_V1_URL}/{gen_id}", headers=headers, timeout=15)
            s.raise_for_status()
            g = s.json()["generations_by_pk"]
            if g.get("status") == "COMPLETE":
                images = g.get("generated_images", [])
                if images:
                    return images[0]["url"]
                break
            elif g.get("status") == "FAILED":
                break
        return ""
    except Exception as e:
        print(f"    Image error: {e}")
        return ""


def get_scheduled_datetime(date_str, time_str):
    now = datetime.datetime.now()
    try:
        scheduled = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        scheduled = datetime.datetime.strptime(f"{date_str} 12:00", "%Y-%m-%d %H:%M")
    if scheduled <= now:
        scheduled = now + datetime.timedelta(minutes=10)
    return scheduled.strftime("%Y-%m-%d %H:%M")


def process_tab(spreadsheet, tab_name, profile, today):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"  Tab '{tab_name}' not found, skipping")
        return 0, 0

    records_raw = ws.get_all_values()
    if len(records_raw) < 2:
        print(f"  {tab_name}: No data rows")
        return 0, 0

    headers = records_raw[0]
    records = []
    for r in records_raw[1:]:
        padded = r + [''] * (len(headers) - len(r))
        records.append(dict(zip(headers, padded)))

    to_post = []
    thread_tweets = []

    for i, row in enumerate(records):
        row_num = i + 2
        status = str(row.get("Status", "")).strip().lower()
        date = str(row.get("Date", "")).strip()
        post_type = str(row.get("Type", "")).strip().lower()

        # Only pick up "approved" or "edited" — skip "posted", "failed", "scheduling"
        if date == today and status in ("approved", "edited"):
            if post_type == "thread":
                thread_tweets.append({"row_num": row_num, **row})
            else:
                to_post.append({"row_num": row_num, **row})

    if not to_post and not thread_tweets:
        print(f"  {tab_name}: No approved posts for {today}")
        return 0, 0

    posted = 0
    failed = 0
    status_col = headers.index("Status") + 1 if "Status" in headers else len(headers)

    for row in to_post:
        content = row.get("Content", "").strip()
        post_type = row.get("Type", "text").strip().lower()
        time_str = row.get("Time", "12:00").strip()
        image_preview = row.get("Image Preview", "").strip()
        image_prompt = row.get("Image Prompt", "").strip()
        row_num = row["row_num"]

        if not content:
            continue

        scheduled = get_scheduled_datetime(today, time_str)
        print(f"  Posting [{post_type}] scheduled {scheduled}: {content[:60]}...")

        # MARK AS SCHEDULING BEFORE SENDING — prevents duplicates if script runs twice
        ws.update_cell(row_num, status_col, "scheduling")

        try:
            if post_type == "image":
                img_url = None
                if image_preview and image_preview.startswith("http"):
                    img_url = image_preview
                elif image_prompt:
                    print(f"    Generating fresh image...")
                    img_url = generate_image_fresh(image_prompt, model="nano-banana-2")

                if img_url:
                    try:
                        result = post_photo(content, img_url, profile, scheduled)
                    except Exception as e:
                        print(f"    Photo scheduled failed: {e}, trying without schedule...")
                        try:
                            result = post_photo(content, img_url, profile)
                        except Exception as e2:
                            print(f"    Photo failed completely: {e2}, falling back to text")
                            result = post_text(content, profile, scheduled)
                else:
                    print(f"    No image available, posting as text")
                    result = post_text(content, profile, scheduled)
            else:
                result = post_text(content, profile, scheduled)

            # Mark as posted AFTER success
            ws.update_cell(row_num, status_col, "posted")
            posted += 1
            print(f"    Posted successfully")

        except Exception as e:
            print(f"    Failed: {e}")
            ws.update_cell(row_num, status_col, f"failed: {str(e)[:50]}")
            failed += 1

        time.sleep(2)

    # Handle thread posts
    if thread_tweets:
        print(f"  Posting thread ({len(thread_tweets)} tweets)...")
        tweets = [t.get("Content", "").strip() for t in thread_tweets if t.get("Content", "").strip()]
        first_time = thread_tweets[0].get("Time", "12:00").strip()
        scheduled = get_scheduled_datetime(today, first_time)
        thread_posted = post_thread(tweets, profile, tab_name, ws, headers, thread_tweets, scheduled)
        posted += thread_posted
        if thread_posted < len(thread_tweets):
            failed += len(thread_tweets) - thread_posted

    return posted, failed


def main():
    if not UPLOAD_POST_API_KEY:
        print("ERROR: UPLOAD_POST_API_KEY not set")
        sys.exit(1)
    if not GOOGLE_SHEET_ID:
        print("ERROR: GOOGLE_SHEET_ID not set")
        sys.exit(1)

    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"Posting approved content for {today}")
    print()

    spreadsheet = get_sheet()
    total_posted = 0
    total_failed = 0

    for tab_name, profile in TAB_TO_PROFILE.items():
        print(f"=== {tab_name} -> {profile} ===")
        posted, failed = process_tab(spreadsheet, tab_name, profile, today)
        total_posted += posted
        total_failed += failed
        print()

    print(f"=== SUMMARY ===")
    print(f"Posted: {total_posted}")
    print(f"Failed: {total_failed}")
    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
