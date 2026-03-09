#!/usr/bin/env python3
"""
Post approved content from Google Sheet to X via Upload Post API.
Run daily via GitHub Actions cron.

Reads rows where:
  - Date = today
  - Status = "approved" or "edited"
Posts them via Upload Post API with scheduled times, then updates status to "posted".
"""

import os
import sys
import json
import time
import requests
import gspread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
UPLOAD_POST_API_KEY = os.environ.get("UPLOAD_POST_API_KEY")
UPLOAD_POST_USER = os.environ.get("UPLOAD_POST_USER", "@brendanwardai")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
GOOGLE_SHEETS_CREDS = os.environ.get("GOOGLE_SHEETS_CREDS")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

UPLOAD_POST_BASE = "https://api.upload-post.com/api"
LEONARDO_API_BASE = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_MODEL_ID = "6b645e3a-d64f-4341-a6d8-7a3f79d62571"  # Phoenix 1.0

TZ = ZoneInfo("America/New_York")


def get_sheet_client():
    """Authenticate with Google Sheets"""
    if GOOGLE_SHEETS_CREDS:
        creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        creds_path = Path(__file__).parent / "google-creds.json"
        if not creds_path.exists():
            print("ERROR: No Google credentials found!")
            sys.exit(1)
        gc = gspread.service_account(filename=str(creds_path))
    return gc


def generate_image(prompt):
    """Generate image via Leonardo.ai Seedream 4.5, return URL"""
    if not LEONARDO_API_KEY:
        print("  ⚠️  No Leonardo API key, skipping image")
        return None
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
    }
    
    resp = requests.post(
        "https://cloud.leonardo.ai/api/rest/v2/generations",
        headers=headers,
        json={
            "model": "seedream-4.5",
            "parameters": {
                "width": 1024,
                "height": 1024,
                "prompt": prompt,
                "quantity": 1,
            },
            "public": False,
        },
        timeout=30,
    )
    resp.raise_for_status()
    generation_id = resp.json()["generate"]["generationId"]
    
    for attempt in range(15):
        time.sleep(5)
        status_resp = requests.get(
            f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
            headers=headers, timeout=15,
        )
        status_resp.raise_for_status()
        gen_data = status_resp.json()["generations_by_pk"]
        
        if gen_data.get("status") == "COMPLETE":
            images = gen_data.get("generated_images", [])
            if images:
                return images[0]["url"]
            break
        elif gen_data.get("status") == "FAILED":
            break
    
    return None


def download_image(url, filename):
    """Download image to local file"""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    filepath = Path(__file__).parent / filename
    with open(filepath, "wb") as f:
        f.write(resp.content)
    return str(filepath)


def post_text(content, scheduled_time=None):
    """Post text tweet via Upload Post"""
    data = {
        "user": UPLOAD_POST_USER,
        "platform[]": "x",
        "title": content,
    }
    if scheduled_time:
        data["scheduled_date"] = scheduled_time
        data["timezone"] = "America/New_York"
    
    resp = requests.post(
        f"{UPLOAD_POST_BASE}/upload_text",
        headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
        data=data, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def post_photo(content, image_path, scheduled_time=None):
    """Post photo tweet via Upload Post"""
    data = {
        "user": UPLOAD_POST_USER,
        "platform[]": "x",
        "title": content,
    }
    if scheduled_time:
        data["scheduled_date"] = scheduled_time
        data["timezone"] = "America/New_York"
    
    with open(image_path, "rb") as img:
        resp = requests.post(
            f"{UPLOAD_POST_BASE}/upload_photos",
            headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
            data=data,
            files={"image": ("image.jpg", img, "image/jpeg")},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()


def parse_scheduled_datetime(date_str, time_str):
    """Convert sheet date + time to ISO format for scheduling"""
    try:
        # Parse "2026-03-08" + "10:30 AM" into ISO datetime
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
        dt = dt.replace(tzinfo=TZ)
        return dt.isoformat()
    except ValueError:
        return None


def main():
    if not UPLOAD_POST_API_KEY:
        print("ERROR: UPLOAD_POST_API_KEY not set")
        sys.exit(1)
    if not SHEET_ID:
        print("ERROR: GOOGLE_SHEET_ID not set")
        sys.exit(1)
    
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"📤 Daily Post Runner")
    print(f"📅 Posting approved content for {today}")
    print(f"{'='*60}\n")
    
    gc = get_sheet_client()
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    try:
        worksheet = spreadsheet.worksheet("Posts")
    except gspread.exceptions.WorksheetNotFound:
        print("ERROR: 'Posts' worksheet not found in sheet!")
        sys.exit(1)
    
    records = worksheet.get_all_values()
    
    # Parse header row and data rows manually (avoids gspread duplicate header bug)
    if len(records) < 2:
        print(f"📭 Sheet is empty or has no data rows.")
        return
    
    headers = records[0]
    
    # Find today's approved posts
    to_post = []
    for i, row_values in enumerate(records[1:], start=2):  # start=2 for row number (1-indexed, skip header)
        row = dict(zip(headers, row_values + [''] * (len(headers) - len(row_values))))
        status = str(row.get("Status", "")).strip().lower()
        date = str(row.get("Date", "")).strip()
        
        if date == today and status in ("approved", "edited"):
            to_post.append({"row_num": i, **row})
    
    if not to_post:
        print(f"📭 No approved posts for {today}.")
        print(f"   Make sure posts in the sheet have Status = 'approved'")
        return
    
    print(f"📋 Found {len(to_post)} approved posts for today\n")
    
    posted = 0
    failed = 0
    
    for post_data in to_post:
        content = post_data.get("Content", "")
        post_type = str(post_data.get("Type", "text")).lower()
        image_prompt = post_data.get("Image Prompt", "")
        time_str = post_data.get("Time", "")
        row_num = post_data["row_num"]
        
        print(f"--- Row {row_num} ---")
        print(f"📝 {content[:70]}...")
        
        # Calculate scheduled time
        scheduled = parse_scheduled_datetime(today, time_str) if time_str else None
        if scheduled:
            print(f"⏰ Scheduled for: {time_str}")
        
        try:
            if post_type == "image" and image_prompt:
                # Generate image
                print(f"🎨 Generating image...")
                image_url = generate_image(image_prompt)
                
                if image_url:
                    image_path = download_image(image_url, f"post_img_{row_num}.jpg")
                    result = post_photo(content, image_path, scheduled)
                    Path(image_path).unlink(missing_ok=True)
                else:
                    print("  ⚠️  Image failed, posting as text")
                    result = post_text(content, scheduled)
            else:
                result = post_text(content, scheduled)
            
            # Extract post URL from response
            post_url = ""
            if result.get("success"):
                x_result = result.get("results", {}).get("x", {})
                post_url = x_result.get("url", "")
            
            # Update sheet: status → posted, add URL
            status_col = 9   # Column I = Status
            url_col = 11      # Column K = Post URL
            worksheet.update_cell(row_num, status_col, "posted")
            if post_url:
                worksheet.update_cell(row_num, url_col, post_url)
            
            print(f"✅ Posted! {post_url}")
            posted += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Update sheet with failure
            worksheet.update_cell(row_num, 9, "failed")
            worksheet.update_cell(row_num, 10, str(e)[:200])
            failed += 1
        
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"✅ Done: {posted} posted, {failed} failed out of {len(to_post)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
