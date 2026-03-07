#!/usr/bin/env python3
"""
Generate a week of posts via Claude API and write to Google Sheet for review.
Run weekly (e.g., Sunday morning) via GitHub Actions or manually.

Sheet columns:
  Day | Date | Time | Content | Type | Image Prompt | Category | Status | Notes | Post URL

Status values:
  pending   = just generated, awaiting review
  approved  = reviewed and approved for posting
  edited    = content was edited by Brendan
  rejected  = skip this post
  posted    = successfully posted
  failed    = posting failed
"""

import os
import sys
import json
import random
import requests
import gspread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_SHEETS_CREDS = os.environ.get("GOOGLE_SHEETS_CREDS")  # JSON string of service account
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")  # Google Sheet ID from the URL

ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
TZ = ZoneInfo("America/New_York")

POSTS_PER_DAY = 4
IMAGE_RATIO = 0.25
DAYS_AHEAD = 7
POST_WINDOW_START = 10  # 10 AM ET
POST_WINDOW_END = 16    # 4 PM ET


def load_topics():
    """Load topics from topics.yaml"""
    import yaml
    topics_path = Path(__file__).parent / "topics.yaml"
    if not topics_path.exists():
        print("ERROR: topics.yaml not found!")
        sys.exit(1)
    with open(topics_path) as f:
        return yaml.safe_load(f)


def get_sheet_client():
    """Authenticate with Google Sheets"""
    if GOOGLE_SHEETS_CREDS:
        creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        # Fallback to local file
        creds_path = Path(__file__).parent / "google-creds.json"
        if not creds_path.exists():
            print("ERROR: No Google credentials found!")
            print("Set GOOGLE_SHEETS_CREDS env var or place google-creds.json in project root")
            sys.exit(1)
        gc = gspread.service_account(filename=str(creds_path))
    return gc


def get_existing_posts(worksheet):
    """Get all existing content from the sheet to avoid repeats"""
    try:
        records = worksheet.get_all_records()
        return [r.get("Content", "") for r in records if r.get("Content")]
    except Exception:
        return []


def generate_posts_for_day(topics_data, date, existing_posts):
    """Generate posts for a specific day using Claude API"""
    
    num_posts = POSTS_PER_DAY
    num_image_posts = max(1, round(num_posts * IMAGE_RATIO))
    num_text_posts = num_posts - num_image_posts
    
    # Build topics context
    topics_str = ""
    for category in topics_data.get("categories", []):
        topics_str += f"\n### {category['name']}\n"
        topics_str += f"Description: {category.get('description', '')}\n"
        if "subtopics" in category:
            topics_str += f"Subtopics: {', '.join(category['subtopics'])}\n"
        if "angles" in category:
            topics_str += f"Angles: {', '.join(category['angles'])}\n"
    
    voice = topics_data.get("voice", {})
    voice_str = f"""
Tone: {voice.get('tone', 'casual, direct, no-BS')}
Style: {voice.get('style_notes', '')}
Avoid: {voice.get('avoid', '')}
Format: {voice.get('format_preferences', '')}
"""
    
    # Recent posts context
    recent_str = ""
    if existing_posts:
        recent_str = "\n\nDO NOT repeat or closely resemble these recent posts:\n"
        for i, post in enumerate(existing_posts[-30:], 1):
            recent_str += f"  {i}. {post[:100]}\n"
    
    prompt = f"""Generate exactly {num_posts} tweets for {date.strftime('%A, %B %d, %Y')}.

TOPICS:
{topics_str}

VOICE & STYLE:
{voice_str}
{recent_str}

REQUIREMENTS:
- {num_text_posts} TEXT-ONLY posts and {num_image_posts} IMAGE posts
- Every post MUST be under 280 characters (count carefully!)
- For IMAGE posts, include "image_prompt" with a detailed AI image generation prompt
- Pick from DIFFERENT topic categories
- Mix types: hot takes, observations, questions, contrarian views, tips, stories
- No hashtag spam (0-1 max, only if natural)
- Make each post feel distinctly different in structure and energy

Return ONLY a JSON array:
[
  {{"content": "tweet text", "type": "text", "topic_category": "category name", "engagement_hook": "why this works"}},
  {{"content": "tweet text", "type": "image", "image_prompt": "detailed prompt", "topic_category": "category name", "engagement_hook": "why this works"}}
]

CRITICAL: Every post under 280 characters. ONLY output the JSON array."""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    
    text = resp.json()["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    
    posts = json.loads(text)
    
    # Validate
    for post in posts:
        if len(post["content"]) > 280:
            post["content"] = post["content"][:277] + "..."
    
    return posts


def calculate_times(date, num_posts):
    """Calculate evenly spaced post times for a day"""
    window_minutes = (POST_WINDOW_END - POST_WINDOW_START) * 60
    interval = window_minutes // (num_posts + 1)
    
    times = []
    for i in range(1, num_posts + 1):
        offset = interval * i + random.randint(-10, 10)
        offset = max(0, min(offset, window_minutes))
        
        post_time = datetime(
            date.year, date.month, date.day,
            POST_WINDOW_START, 0, 0, tzinfo=TZ
        ) + timedelta(minutes=offset)
        times.append(post_time)
    
    return times


def write_to_sheet(gc, all_rows):
    """Write generated posts to Google Sheet"""
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    # Get or create the worksheet
    try:
        worksheet = spreadsheet.worksheet("Posts")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title="Posts", rows=200, cols=10)
    
    # Check if headers exist
    try:
        existing = worksheet.get_all_values()
    except Exception:
        existing = []
    
    headers = ["Day", "Date", "Time", "Content", "Type", "Image Prompt", "Category", "Status", "Notes", "Post URL"]
    
    if not existing:
        worksheet.append_row(headers, value_input_option="RAW")
        # Format header row
        worksheet.format("A1:J1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True},
        })
        next_row = 2
    else:
        next_row = len(existing) + 1
    
    # Append all rows
    rows_to_add = []
    for row in all_rows:
        rows_to_add.append([
            row["day"],
            row["date"],
            row["time"],
            row["content"],
            row["type"],
            row.get("image_prompt", ""),
            row.get("category", ""),
            "pending",  # Status
            "",         # Notes
            "",         # Post URL
        ])
    
    if rows_to_add:
        worksheet.append_rows(rows_to_add, value_input_option="RAW")
    
    # Set column widths for readability
    try:
        requests_body = {
            "requests": [
                {"updateDimensionProperties": {
                    "range": {"sheetId": worksheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4},
                    "properties": {"pixelSize": 400}, "fields": "pixelSize"
                }},
                {"updateDimensionProperties": {
                    "range": {"sheetId": worksheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6},
                    "properties": {"pixelSize": 300}, "fields": "pixelSize"
                }},
            ]
        }
        spreadsheet.batch_update(requests_body)
    except Exception:
        pass  # Not critical
    
    return len(rows_to_add)


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    if not SHEET_ID:
        print("ERROR: GOOGLE_SHEET_ID not set")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"📝 Weekly Post Generator")
    print(f"📅 Generating {DAYS_AHEAD} days × {POSTS_PER_DAY} posts/day = {DAYS_AHEAD * POSTS_PER_DAY} posts")
    print(f"{'='*60}\n")
    
    topics = load_topics()
    gc = get_sheet_client()
    
    # Get existing posts from sheet to avoid repeats
    try:
        spreadsheet = gc.open_by_key(SHEET_ID)
        try:
            worksheet = spreadsheet.worksheet("Posts")
            existing_posts = get_existing_posts(worksheet)
        except gspread.exceptions.WorksheetNotFound:
            existing_posts = []
    except Exception:
        existing_posts = []
    
    all_rows = []
    today = datetime.now(TZ).date()
    
    # Start from tomorrow (or today if before posting window)
    now = datetime.now(TZ)
    if now.hour < POST_WINDOW_START:
        start_date = today
    else:
        start_date = today + timedelta(days=1)
    
    for day_offset in range(DAYS_AHEAD):
        date = start_date + timedelta(days=day_offset)
        day_name = date.strftime("%A")
        
        print(f"🧠 Generating posts for {day_name}, {date.strftime('%b %d')}...")
        
        try:
            posts = generate_posts_for_day(topics, date, existing_posts)
            times = calculate_times(date, len(posts))
            
            for post, post_time in zip(posts, times):
                row = {
                    "day": day_name,
                    "date": date.strftime("%Y-%m-%d"),
                    "time": post_time.strftime("%I:%M %p"),
                    "content": post["content"],
                    "type": post["type"],
                    "image_prompt": post.get("image_prompt", ""),
                    "category": post.get("topic_category", ""),
                }
                all_rows.append(row)
                existing_posts.append(post["content"])  # Track for dedup
                
                print(f"  ✅ [{post['type'].upper()}] {post['content'][:60]}...")
            
        except Exception as e:
            print(f"  ❌ Error generating for {day_name}: {e}")
            continue
        
        # Small delay between API calls
        import time
        time.sleep(1)
    
    # Write everything to the sheet
    print(f"\n📊 Writing {len(all_rows)} posts to Google Sheet...")
    count = write_to_sheet(gc, all_rows)
    print(f"✅ Done! {count} posts added to sheet.")
    print(f"🔗 Review at: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print(f"\nNext step: Review the sheet, change status from 'pending' to 'approved' for posts you like.")


if __name__ == "__main__":
    main()
