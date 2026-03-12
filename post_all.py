#!/usr/bin/env python3
"""
Post approved content from ALL Sheet tabs to X via Upload Post API.
Handles @brendanwardai, EveryFreeTool, and WhatIfs.
Smart scheduling + correct photo upload + no duplicate posts.
"""

import os
import sys
import json
import time
import requests
import yaml
import gspread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

UPLOAD_POST_API_KEY = os.environ.get("UPLOAD_POST_API_KEY")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
GOOGLE_SHEETS_CREDS = os.environ.get("GOOGLE_SHEETS_CREDS")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

SITES_CONFIG = Path(__file__).parent / "sites_config.yaml"
TZ = ZoneInfo("America/New_York")

TAB_PROFILES = {
    "Posts": os.environ.get("UPLOAD_POST_USER", "@brendanwardai"),
}


def get_sheet_client():
    if GOOGLE_SHEETS_CREDS:
        return gspread.service_account_from_dict(json.loads(GOOGLE_SHEETS_CREDS))
    creds_path = Path(__file__).parent / "google-creds.json"
    if creds_path.exists():
        return gspread.service_account(filename=str(creds_path))
    print("ERROR: No Google credentials found!")
    sys.exit(1)


def load_site_profiles():
    profiles = dict(TAB_PROFILES)
    if SITES_CONFIG.exists():
        data = yaml.safe_load(open(SITES_CONFIG))
        for site in data.get("sites", []):
            profiles[site["name"]] = site["upload_post_profile"]
    return profiles


def smart_schedule(date_str, time_str, stagger=0):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
        dt = dt.replace(tzinfo=TZ)
    except ValueError:
        return None
    now = datetime.now(TZ)
    if dt > now:
        return dt.isoformat()
    new_time = now + timedelta(minutes=3 + (stagger * 3))
    return new_time.isoformat()


def generate_image_fresh(prompt):
    if not LEONARDO_API_KEY:
        return None
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
    }
    try:
        resp = requests.post(
            "https://cloud.leonardo.ai/api/rest/v2/generations",
            headers=headers,
            json={"model": "seedream-4.5", "parameters": {"width": 1024, "height": 1024, "prompt": prompt, "quantity": 1}, "public": False},
            timeout=30,
        )
        resp.raise_for_status()
        gen_id = resp.json()["generate"]["generationId"]
        for _ in range(15):
            time.sleep(5)
            s = requests.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}", headers=headers, timeout=15)
            s.raise_for_status()
            g = s.json()["generations_by_pk"]
            if g.get("status") == "COMPLETE":
                imgs = g.get("generated_images", [])
                if imgs:
                    return imgs[0]["url"]
                break
            elif g.get("status") == "FAILED":
                break
        return None
    except Exception as e:
        print(f"    ⚠️  Image gen error: {e}")
        return None


def post_text(content, profile, scheduled_date=None):
    data = {"user": profile, "platform[]": "x", "title": content}
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
        data["timezone"] = "America/New_York"
    resp = requests.post(
        "https://api.upload-post.com/api/upload_text",
        headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
        data=data, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def post_photo(content, image_url, profile, scheduled_date=None):
    """Download image from URL then upload using photos[] field"""
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
            "https://api.upload-post.com/api/upload_photos",
            headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
            data=data,
            files={"photos[]": ("photo.jpg", img, "image/jpeg")},
            timeout=60,
        )

    tmp_path.unlink(missing_ok=True)

    result = resp.json()

    # Check if it actually succeeded even if status code is weird
    if result.get("success"):
        return result

    # If scheduling caused the issue, retry without scheduling
    if resp.status_code == 400 and scheduled_date:
        print(f"    ⚠️  Photo scheduling issue, retrying immediate...")
        img_resp2 = requests.get(image_url, timeout=30)
        img_resp2.raise_for_status()
        with open(tmp_path, "wb") as f:
            f.write(img_resp2.content)

        data.pop("scheduled_date", None)
        data.pop("timezone", None)
        with open(tmp_path, "rb") as img:
            resp2 = requests.post(
                "https://api.upload-post.com/api/upload_photos",
                headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
                data=data,
                files={"photos[]": ("photo.jpg", img, "image/jpeg")},
                timeout=60,
            )
        tmp_path.unlink(missing_ok=True)
        result2 = resp2.json()
        if result2.get("success"):
            return result2
        resp2.raise_for_status()

    resp.raise_for_status()
    return result


def try_post_with_image(content, image_preview, image_prompt, profile, scheduled, tab_name, row_idx):
    """Try to post with image. Only falls back to text if photo completely fails."""
    img_url = None
    if image_preview and image_preview.startswith("http"):
        img_url = image_preview
    elif image_prompt:
        print(f"    🎨 Generating fresh image...")
        img_url = generate_image_fresh(image_prompt)

    if not img_url:
        print(f"    ⚠️  No image available, posting as text")
        return post_text(content, profile, scheduled)

    # Try photo post — DO NOT fall back to text if photo succeeds
    try:
        result = post_photo(content, img_url, profile, scheduled)
        if result.get("success"):
            print(f"    🖼️  Photo posted successfully")
            return result
    except Exception as e:
        print(f"    ⚠️  Photo failed: {e}")

    # Only reach here if photo truly failed — post as text
    print(f"    ⚠️  Photo failed completely, posting as text instead")
    return post_text(content, profile, scheduled)


def process_tab(spreadsheet, tab_name, profile):
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"  ⚠️  Tab '{tab_name}' not found, skipping")
        return 0, 0

    all_values = worksheet.get_all_values()
    if len(all_values) < 2:
        print(f"  📭 No data in '{tab_name}'")
        return 0, 0

    headers = all_values[0]
    today = datetime.now(TZ).strftime("%Y-%m-%d")

    def col_idx(name):
        try:
            return headers.index(name)
        except ValueError:
            return -1

    date_idx = col_idx("Date")
    status_idx = col_idx("Status")
    content_idx = col_idx("Content")
    type_idx = col_idx("Type")
    time_idx = col_idx("Time")
    img_prompt_idx = col_idx("Image Prompt")
    img_preview_idx = col_idx("Image Preview")
    url_idx = col_idx("Post URL")
    notes_idx = col_idx("Notes")

    if date_idx < 0 or status_idx < 0 or content_idx < 0:
        print(f"  ⚠️  Tab '{tab_name}' missing required columns")
        return 0, 0

    posted = 0
    failed = 0
    stagger = 0

    for row_idx, row in enumerate(all_values[1:], start=2):
        while len(row) < len(headers):
            row.append("")

        date_val = row[date_idx].strip()
        status_val = row[status_idx].strip().lower()

        if date_val != today or status_val not in ("approved", "edited"):
            continue

        content = row[content_idx]
        post_type = row[type_idx].lower() if type_idx >= 0 else "text"
        time_val = row[time_idx] if time_idx >= 0 else ""
        image_prompt = row[img_prompt_idx] if img_prompt_idx >= 0 else ""
        image_preview = row[img_preview_idx] if img_preview_idx >= 0 else ""

        print(f"  📝 Row {row_idx}: {content[:60]}...")

        stagger += 1
        scheduled = smart_schedule(today, time_val, stagger)
        if scheduled:
            sched_dt = datetime.fromisoformat(scheduled)
            print(f"  ⏰ Scheduled: {sched_dt.strftime('%I:%M %p')}")

        try:
            if post_type == "image" and (image_prompt or image_preview):
                result = try_post_with_image(content, image_preview, image_prompt, profile, scheduled, tab_name, row_idx)
            else:
                result = post_text(content, profile, scheduled)

            post_url = ""
            if result.get("success"):
                x_result = result.get("results", {}).get("x", {})
                post_url = x_result.get("url", "")

            worksheet.update_cell(row_idx, status_idx + 1, "posted")
            if url_idx >= 0 and post_url:
                worksheet.update_cell(row_idx, url_idx + 1, post_url)

            print(f"  ✅ Posted! {post_url}")
            posted += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            worksheet.update_cell(row_idx, status_idx + 1, "failed")
            if notes_idx >= 0:
                worksheet.update_cell(row_idx, notes_idx + 1, str(e)[:200])
            failed += 1

        time.sleep(2)

    return posted, failed


def main():
    if not UPLOAD_POST_API_KEY:
        print("ERROR: UPLOAD_POST_API_KEY not set")
        sys.exit(1)
    if not SHEET_ID:
        print("ERROR: GOOGLE_SHEET_ID not set")
        sys.exit(1)

    today = datetime.now(TZ).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"📤 Daily Post Runner — All Accounts")
    print(f"📅 Posting approved content for {today}")
    print(f"{'='*60}")

    gc = get_sheet_client()
    spreadsheet = gc.open_by_key(SHEET_ID)
    profiles = load_site_profiles()

    total_posted = 0
    total_failed = 0

    for tab_name, profile in profiles.items():
        print(f"\n🐦 {tab_name} → {profile}")
        p, f = process_tab(spreadsheet, tab_name, profile)
        total_posted += p
        total_failed += f
        if p == 0 and f == 0:
            print(f"  📭 No approved posts for {today}")

    print(f"\n{'='*60}")
    print(f"✅ Done: {total_posted} posted, {total_failed} failed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
