#!/usr/bin/env python3
"""
Generate weekly posts for all accounts into Google Sheet tabs.
Each account gets its own tab. Run weekly via GitHub Actions or manually.

Tabs: Posts (brendanwardai) | EveryFreeTool | WhatIfs
"""

import os
import sys
import json
import random
import time
import requests
import yaml
import gspread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
GOOGLE_SHEETS_CREDS = os.environ.get("GOOGLE_SHEETS_CREDS")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
TZ = ZoneInfo("America/New_York")
DAYS_AHEAD = 7

SITES_CONFIG = Path(__file__).parent / "sites_config.yaml"
TOPICS_FILE = Path(__file__).parent / "topics.yaml"


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_sheet_client():
    if GOOGLE_SHEETS_CREDS:
        return gspread.service_account_from_dict(json.loads(GOOGLE_SHEETS_CREDS))
    creds_path = Path(__file__).parent / "google-creds.json"
    if creds_path.exists():
        return gspread.service_account(filename=str(creds_path))
    print("ERROR: No Google credentials found!")
    sys.exit(1)


def get_or_create_tab(spreadsheet, tab_name):
    """Get existing tab or create new one"""
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=200, cols=11)
        headers = ["Day", "Date", "Time", "Content", "Type", "Image Prompt", "Image Preview", "Category", "Status", "Notes", "Post URL"]
        ws.append_row(headers, value_input_option="RAW")
        return ws


def get_existing_content(worksheet):
    """Get existing post content to avoid repeats"""
    try:
        all_values = worksheet.get_all_values()
        if len(all_values) < 2:
            return []
        headers = all_values[0]
        content_idx = headers.index("Content") if "Content" in headers else 3
        return [row[content_idx] for row in all_values[1:] if len(row) > content_idx and row[content_idx]]
    except Exception:
        return []


def generate_image_preview(prompt):
    """Generate image via Leonardo Seedream 4.5, return URL"""
    if not LEONARDO_API_KEY:
        return ""
    try:
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
                "parameters": {"width": 1024, "height": 1024, "prompt": prompt, "quantity": 1},
                "public": False,
            },
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
                    print(f"    🎨 Image ready")
                    return imgs[0]["url"]
                break
            elif g.get("status") == "FAILED":
                break
        return ""
    except Exception as e:
        print(f"    ⚠️  Image error: {e}")
        return ""


def calculate_times(date, num_posts, start_hour=9, end_hour=19):
    """Calculate evenly spaced post times"""
    window = (end_hour - start_hour) * 60
    interval = window // (num_posts + 1)
    times = []
    for i in range(1, num_posts + 1):
        offset = interval * i + random.randint(-10, 10)
        offset = max(0, min(offset, window))
        t = datetime(date.year, date.month, date.day, start_hour, 0, 0, tzinfo=TZ) + timedelta(minutes=offset)
        times.append(t)
    return times


# ─── CLAUDE GENERATION ────────────────────────────────────────────────────────

def generate_posts_claude(prompt_context, num_posts, image_ratio):
    """Call Claude API to generate posts"""
    num_image = max(1, round(num_posts * image_ratio))
    num_text = num_posts - num_image
    
    prompt = f"""{prompt_context}

REQUIREMENTS:
- Generate exactly {num_text} TEXT-ONLY posts and {num_image} IMAGE posts
- Every post MUST be under 280 characters (URLs and hashtags count toward limit!)
- For IMAGE posts, include "image_prompt" with a detailed, visually striking prompt for Seedream 4.5
- Pick from DIFFERENT topic categories
- Mix types: recommendations, hot takes, questions, observations
- CRITICAL URL RULE: NEVER link to whatifs.fun/games/ — this URL does NOT exist and returns a 404. Always link to either whatifs.fun (homepage) or whatifs.fun/[specific-game-slug]/ for individual games. Example correct URLs: whatifs.fun/snake-game/, whatifs.fun/reflex-test/, whatifs.fun/spend-a-billion/
- Add 1-2 relevant hashtags to EVERY post for discoverability. Place them naturally at the end. Use niche-specific hashtags that people actually search (e.g. #FreeTools #SaaS #IndieGames #BrowserGames #AI #ColdEmail #StartupLife #BuildInPublic). Never use more than 2 hashtags per post.
- Today's date: {datetime.now().strftime('%A, %B %d, %Y')}

Return ONLY a JSON array:
[{{"content": "tweet text", "type": "text", "category": "cat name"}}, {{"content": "tweet", "type": "image", "image_prompt": "detailed prompt", "category": "cat name"}}]

CRITICAL: Every post under 280 characters. ONLY output the JSON array."""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
        json={"model": ANTHROPIC_MODEL, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]},
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
    for p in posts:
        if len(p["content"]) > 280:
            p["content"] = p["content"][:277] + "..."
    return posts


# ─── BRENDANWARDAI GENERATION ─────────────────────────────────────────────────

def generate_brendanwardai(date, existing):
    """Generate posts for @brendanwardai using topics.yaml"""
    topics_data = yaml.safe_load(open(TOPICS_FILE))
    
    topics_str = ""
    for cat in topics_data.get("categories", []):
        topics_str += f"\n### {cat['name']}\n{cat.get('description', '')}\n"
        if "subtopics" in cat:
            topics_str += f"Subtopics: {', '.join(cat['subtopics'])}\n"
        if "angles" in cat:
            topics_str += f"Angles: {', '.join(cat['angles'])}\n"
    
    voice = topics_data.get("voice", {})
    voice_str = f"Tone: {voice.get('tone', '')}\nStyle: {voice.get('style_notes', '')}\nAvoid: {voice.get('avoid', '')}\nFormat: {voice.get('format_preferences', '')}"
    
    recent = ""
    if existing:
        recent = "\nDO NOT repeat these:\n" + "\n".join(f"  - {p[:80]}" for p in existing[-20:])
    
    context = f"""Generate 4 tweets for {date.strftime('%A, %B %d, %Y')} for a founder/AI expert X account.

TOPICS:\n{topics_str}\n\nVOICE:\n{voice_str}\n{recent}"""
    
    return generate_posts_claude(context, 4, 0.25)


# ─── SITE GENERATION ─────────────────────────────────────────────────────────

def generate_site_posts(site, date, existing):
    """Generate posts for a site account"""
    voice = site.get("voice", {})
    
    topics_str = ""
    for cat in site.get("categories", []):
        topics_str += f"\n### {cat['name']}\n{cat.get('description', '')}\n"
        if "subtopics" in cat:
            topics_str += f"Subtopics: {', '.join(cat['subtopics'])}\n"
        if "angles" in cat:
            topics_str += f"Angles: {', '.join(cat['angles'])}\n"
    
    links_str = ""
    for link in site.get("site_links", []):
        links_str += f"  - {link['url']} ({link['context']})\n"
    
    recent = ""
    if existing:
        recent = "\nDO NOT repeat these:\n" + "\n".join(f"  - {p[:80]}" for p in existing[-20:])
    
    context = f"""Generate 5 tweets for {date.strftime('%A, %B %d, %Y')} for the X account promoting {site['website']}.

WEBSITE: {site['website']}

TOPICS:\n{topics_str}

VOICE:
Tone: {voice.get('tone', '')}
Style: {voice.get('style_notes', '')}
Avoid: {voice.get('avoid', '')}
Format: {voice.get('format_preferences', '')}

SITE LINKS (include in 2-3 posts naturally):
{links_str}
{recent}"""
    
    return generate_posts_claude(context, 5, 0.4)


# ─── WRITE TO SHEET ──────────────────────────────────────────────────────────

def write_posts_to_tab(spreadsheet, tab_name, all_rows):
    """Write generated posts to a specific Sheet tab"""
    ws = get_or_create_tab(spreadsheet, tab_name)
    
    rows_to_add = []
    for row in all_rows:
        rows_to_add.append([
            row["day"], row["date"], row["time"], row["content"],
            row["type"], row.get("image_prompt", ""), row.get("image_preview", ""),
            row.get("category", ""), "pending", "", "",
        ])
    
    if rows_to_add:
        ws.append_rows(rows_to_add, value_input_option="RAW")
    
    return len(rows_to_add)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def process_account(spreadsheet, tab_name, generate_fn, posts_per_day, image_ratio, start_hour, end_hour):
    """Generate a week of posts for one account and write to Sheet tab"""
    ws = get_or_create_tab(spreadsheet, tab_name)
    existing = get_existing_content(ws)
    
    now = datetime.now(TZ)
    start_date = now.date() + timedelta(days=1) if now.hour >= start_hour else now.date()
    
    all_rows = []
    for day_offset in range(DAYS_AHEAD):
        date = start_date + timedelta(days=day_offset)
        day_name = date.strftime("%A")
        
        print(f"  🧠 {day_name}, {date.strftime('%b %d')}...")
        
        try:
            posts = generate_fn(date, existing)
            times = calculate_times(date, len(posts), start_hour, end_hour)
            
            for post, post_time in zip(posts, times):
                image_preview = ""
                if post["type"] == "image" and post.get("image_prompt") and LEONARDO_API_KEY:
                    print(f"    🎨 Generating image preview...")
                    image_preview = generate_image_preview(post["image_prompt"])
                
                row = {
                    "day": day_name,
                    "date": date.strftime("%Y-%m-%d"),
                    "time": post_time.strftime("%I:%M %p"),
                    "content": post["content"],
                    "type": post["type"],
                    "image_prompt": post.get("image_prompt", ""),
                    "image_preview": image_preview,
                    "category": post.get("category", ""),
                }
                all_rows.append(row)
                existing.append(post["content"])
                
                print(f"    ✅ [{post['type'].upper()}] {post['content'][:60]}...")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        time.sleep(1)
    
    count = write_posts_to_tab(spreadsheet, tab_name, all_rows)
    print(f"  📊 {count} posts written to '{tab_name}' tab")
    return count


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set"); sys.exit(1)
    if not SHEET_ID:
        print("ERROR: GOOGLE_SHEET_ID not set"); sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"📝 Weekly Post Generator — All Accounts")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    gc = get_sheet_client()
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    total = 0
    
    # ── @brendanwardai ────────────────────────────────────────────────────
    print(f"\n🐦 @brendanwardai (Posts tab)")
    count = process_account(
        spreadsheet, "Posts",
        generate_brendanwardai,
        posts_per_day=4, image_ratio=0.25,
        start_hour=10, end_hour=16,
    )
    total += count
    
    # ── Site accounts ─────────────────────────────────────────────────────
    if SITES_CONFIG.exists():
        sites_data = yaml.safe_load(open(SITES_CONFIG))
        defaults = sites_data.get("defaults", {})
        
        for site in sites_data.get("sites", []):
            name = site["name"]
            print(f"\n🌐 {name} ({site['upload_post_profile']})")
            
            count = process_account(
                spreadsheet, name,
                lambda date, existing, s=site: generate_site_posts(s, date, existing),
                posts_per_day=defaults.get("posts_per_day", 5),
                image_ratio=defaults.get("image_post_ratio", 0.4),
                start_hour=defaults.get("posting_window_start_hour", 9),
                end_hour=defaults.get("posting_window_end_hour", 19),
            )
            total += count
    
    print(f"\n{'='*60}")
    print(f"✅ Done! {total} total posts generated across all accounts")
    print(f"🔗 Review: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
