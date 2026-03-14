#!/usr/bin/env python3
"""
generate_all.py — Multi-account Twitter content generator
Generates posts for all configured accounts and writes to Google Sheets.
Supports different image models per account, thread generation, and content mix enforcement.
"""

import os
import sys
import json
import random
import time
import datetime
import requests
import gspread
import yaml
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH", "google-creds.json")

ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
LEONARDO_V2_URL = "https://cloud.leonardo.ai/api/rest/v2/generations"
LEONARDO_V1_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"


def load_config():
    config_path = Path(__file__).parent / "sites_config.yaml"
    if not config_path.exists():
        print("ERROR: sites_config.yaml not found")
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_game_urls():
    game_path = Path(__file__).parent / "game-urls.yaml"
    if game_path.exists():
        with open(game_path) as f:
            return yaml.safe_load(f)
    return None


def load_topics():
    topics_path = Path(__file__).parent / "topics.yaml"
    if topics_path.exists():
        with open(topics_path) as f:
            return yaml.safe_load(f)
    return None


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


def get_or_create_tab(spreadsheet, tab_name, headers):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=200, cols=len(headers))
        ws.append_row(headers)
        print(f"  Created tab: {tab_name}")
    existing = ws.get_all_values()
    if not existing or existing[0] != headers:
        if existing:
            ws.delete_rows(1)
        ws.insert_row(headers, 1)
    return ws


def generate_posts_with_claude(site_config, defaults, day_date, game_urls=None):
    posts_per_day = defaults.get("posts_per_day", 8)
    image_ratio = defaults.get("image_post_ratio", 0.35)
    num_image_posts = max(1, round(posts_per_day * image_ratio))
    num_text_posts = posts_per_day - num_image_posts

    voice = site_config.get("voice", {})
    categories = site_config.get("categories", [])
    site_links = site_config.get("site_links", [])
    content_mix = site_config.get("content_mix_instructions", "")
    site_name = site_config["name"]
    website = site_config.get("website", "")

    links_text = "\n".join([f"  - {l['url']} -- use when: {l['context']}" for l in site_links])

    cats_text = ""
    for cat in categories:
        cats_text += f"\n  Category: {cat['name']}\n"
        cats_text += f"  Description: {cat.get('description', '')}\n"
        cats_text += f"  Subtopics: {', '.join(cat.get('subtopics', []))}\n"
        angles = cat.get('angles', [])
        if angles:
            cats_text += f"  Angles: {'; '.join(angles)}\n"

    game_urls_text = ""
    if game_urls and site_name == "WhatIfs":
        all_games = []
        for category, slugs in game_urls.get("games_by_category", {}).items():
            for slug in slugs:
                all_games.append(f"whatifs.fun/{slug}/")
        sample_games = random.sample(all_games, min(40, len(all_games)))
        game_urls_text = f"""
AVAILABLE GAME URLs (use these exact URLs in posts):
""" + "\n".join("  - " + g for g in sample_games) + """

CRITICAL: NEVER link to whatifs.fun/games/ — this URL does NOT exist.
Always link to whatifs.fun or whatifs.fun/[specific-game-slug]/ for individual games.
"""

    system_prompt = f"""You are the social media brain for {site_name} ({website}).
Your ONLY job is to write tweets that get people to visit {website}.

VOICE:
Tone: {voice.get('tone', 'casual and engaging')}
Style: {voice.get('style_notes', '')}
Avoid: {voice.get('avoid', '')}
Format preferences: {voice.get('format_preferences', '')}

CONTENT MIX RULES:
{content_mix}

AVAILABLE SITE LINKS (use the most relevant one for each post):
{links_text}

CATEGORIES AND TOPICS:
{cats_text}
{game_urls_text}

CRITICAL RULES:
1. Every post MUST connect back to {website} — either with a direct link, a reference to the site, or a hook that makes people check the bio.
2. Include 1-2 relevant hashtags per post (not spammy).
3. Keep posts under 280 characters. Most should be 150-250 characters.
4. Use lowercase for casual tone. No ALL CAPS unless for emphasis on one word.
5. Make every post feel like a real human wrote it, not AI.
6. Vary the structure — short and punchy, medium with a hook, questions.
7. NEVER repeat the same format or opening across posts.
8. For image posts, write a vivid image generation prompt for an eye-catching visual."""

    user_prompt = f"""Generate exactly {posts_per_day} tweets for {site_name} to post on {day_date}.

{num_text_posts} should be TEXT ONLY posts.
{num_image_posts} should be IMAGE posts (include an image_prompt for each).

Follow the content mix rules strictly.

Return ONLY a JSON array. No other text. No markdown backticks. Each item:
{{"content": "the tweet text with any URLs", "type": "text" or "image", "image_prompt": "vivid description for image generation (only for image posts, omit for text)", "category": "which content category this falls into"}}

IMPORTANT:
- Make sure URLs in tweets point to REAL pages on {website}
- Each post must be completely unique in structure and angle
- Do NOT start multiple posts the same way
- Image prompts should describe vibrant, eye-catching visuals"""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        posts = json.loads(text)
        if not isinstance(posts, list):
            posts = [posts]
        return posts[:posts_per_day]
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"  Claude API error: {e}")
        return []


def generate_thread_with_claude(site_config, defaults, day_date, game_urls=None):
    voice = site_config.get("voice", {})
    thread_config = site_config.get("thread_config", {})
    site_links = site_config.get("site_links", [])
    site_name = site_config["name"]
    website = site_config.get("website", "")
    thread_length = defaults.get("thread_length", 5)

    topic_ideas = thread_config.get("topic_ideas", [])
    chosen_topic = random.choice(topic_ideas) if topic_ideas else f"best of {website}"
    links_text = "\n".join([f"  - {l['url']}" for l in site_links[:10]])

    game_urls_text = ""
    if game_urls and site_name == "WhatIfs":
        all_games = []
        for category, slugs in game_urls.get("games_by_category", {}).items():
            for slug in slugs:
                all_games.append(f"whatifs.fun/{slug}/")
        sample_games = random.sample(all_games, min(20, len(all_games)))
        game_urls_text = "\nGAME URLs to include:\n" + "\n".join("  - " + g for g in sample_games)

    system_prompt = f"""You write viral Twitter threads for {site_name} ({website}).
Voice: {voice.get('tone', 'casual')}
Style: {voice.get('style_notes', '')}
{game_urls_text}

RULES:
1. First tweet must hook — bold claim, surprising stat, or provocative question.
2. Each tweet builds with a specific example, tool, or game.
3. Include direct URLs to {website} in at least 3 tweets.
4. Last tweet: CTA — follow, bookmark, or visit site.
5. Under 280 characters each.
6. Sound human, not brand.
7. Include 1-2 hashtags on first tweet only."""

    user_prompt = f"""Write a {thread_length}-tweet thread about: "{chosen_topic}"
Date: {day_date}
Available links:
{links_text}

Return ONLY a JSON array of strings. No markdown. No backticks. Number them like "1/" "2/" etc."""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 3000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=90,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        thread = json.loads(text)
        if isinstance(thread, list):
            return thread[:thread_length + 2]
        return []
    except Exception as e:
        print(f"  Thread generation error: {e}")
        return []


def generate_image(prompt, model="seedream-4.5"):
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
            status_resp = requests.get(f"{LEONARDO_V1_URL}/{gen_id}", headers=headers, timeout=15)
            status_resp.raise_for_status()
            gen_data = status_resp.json()["generations_by_pk"]
            if gen_data.get("status") == "COMPLETE":
                images = gen_data.get("generated_images", [])
                if images:
                    url = images[0]["url"]
                    print(f"    Image ready ({model}): {url[:60]}...")
                    return url
                break
            elif gen_data.get("status") == "FAILED":
                break
        return ""
    except Exception as e:
        print(f"    Image error ({model}): {e}")
        return ""


def generate_post_times(num_posts, start_hour, end_hour):
    window_minutes = (end_hour - start_hour) * 60
    slot_size = window_minutes // num_posts
    times = []
    for i in range(num_posts):
        slot_start = start_hour * 60 + i * slot_size
        slot_end = slot_start + slot_size - 10
        minute = random.randint(slot_start, max(slot_start, slot_end))
        h, m = divmod(minute, 60)
        times.append(f"{h:02d}:{m:02d}")
    return times


def generate_for_site(spreadsheet, site_config, defaults, dates, game_urls=None):
    site_name = site_config["name"]
    image_model = site_config.get("image_model", "seedream-4.5")
    posts_per_day = defaults.get("posts_per_day", 8)
    start_hour = defaults.get("posting_window_start_hour", 9)
    end_hour = defaults.get("posting_window_end_hour", 20)
    thread_day = defaults.get("thread_day", "wednesday")

    headers = ["Day", "Date", "Time", "Content", "Type", "Image Prompt", "Image Preview", "Category", "Status"]
    ws = get_or_create_tab(spreadsheet, site_name, headers)

    existing = ws.get_all_values()
    existing_dates = set()
    if len(existing) > 1:
        for row in existing[1:]:
            if len(row) > 1 and row[1]:
                existing_dates.add(row[1])

    all_rows = []

    for day_date in dates:
        date_str = day_date.strftime("%Y-%m-%d")
        day_name = day_date.strftime("%A")

        if date_str in existing_dates:
            print(f"  Skip {site_name} {date_str} (already exists)")
            continue

        print(f"  Generating {posts_per_day} posts for {site_name} -- {day_name} {date_str}")

        posts = generate_posts_with_claude(site_config, defaults, date_str, game_urls)
        if not posts:
            print(f"  No posts generated for {date_str}")
            continue

        times = generate_post_times(len(posts), start_hour, end_hour)

        for i, post in enumerate(posts):
            content = post.get("content", "")
            post_type = post.get("type", "text")
            image_prompt = post.get("image_prompt", "")
            category = post.get("category", "")
            image_preview = ""

            if post_type == "image" and image_prompt:
                print(f"    Generating image ({image_model})...")
                image_preview = generate_image(image_prompt, model=image_model)

            post_time = times[i] if i < len(times) else f"{start_hour + i}:00"
            all_rows.append([day_name, date_str, post_time, content, post_type, image_prompt, image_preview, category, "pending"])

        if day_name.lower() == thread_day.lower():
            print(f"  Generating weekly thread for {site_name}...")
            thread = generate_thread_with_claude(site_config, defaults, date_str, game_urls)
            if thread:
                thread_start_hour = random.randint(11, 14)
                thread_start_min = random.randint(0, 30)
                for t_idx, tweet in enumerate(thread):
                    t_min = thread_start_min + (t_idx * 3)
                    t_hour = thread_start_hour + t_min // 60
                    t_min = t_min % 60
                    all_rows.append([day_name, date_str, f"{t_hour:02d}:{t_min:02d}", tweet, "thread", "", "", "thread", "pending"])
                print(f"    Thread: {len(thread)} tweets")

        time.sleep(2)

    if all_rows:
        ws.append_rows(all_rows, value_input_option="RAW")
        print(f"  {site_name}: {len(all_rows)} rows written")
    else:
        print(f"  {site_name}: No new rows")


def generate_for_brendan(spreadsheet, defaults, dates):
    topics = load_topics()
    if not topics:
        print("  No topics.yaml found, skipping @brendanwardai")
        return

    posts_per_day = 4
    start_hour = defaults.get("posting_window_start_hour", 9)
    end_hour = defaults.get("posting_window_end_hour", 20)

    headers_list = ["Day", "Date", "Time", "Content", "Type", "Image Prompt", "Image Preview", "Category", "Status"]
    ws = get_or_create_tab(spreadsheet, "Posts", headers_list)

    existing = ws.get_all_values()
    existing_dates = set()
    if len(existing) > 1:
        for row in existing[1:]:
            if len(row) > 1 and row[1]:
                existing_dates.add(row[1])

    all_rows = []
    topic_areas = topics.get("topics", [])
    topic_list = "\n".join([f"- {t}" for t in topic_areas]) if isinstance(topic_areas, list) else str(topic_areas)
    voice_notes = topics.get("voice", "direct, founder perspective, no bs, short punchy tweets about AI, cold email, startups, building in public")

    for day_date in dates:
        date_str = day_date.strftime("%Y-%m-%d")
        day_name = day_date.strftime("%A")

        if date_str in existing_dates:
            print(f"  Skip Posts {date_str} (already exists)")
            continue

        print(f"  Generating {posts_per_day} posts for @brendanwardai -- {day_name} {date_str}")

        num_image = max(1, round(posts_per_day * 0.25))
        num_text = posts_per_day - num_image

        try:
            resp = requests.post(
                ANTHROPIC_API_URL,
                headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 2500,
                    "system": f"You write tweets for @brendanwardai -- a founder who builds AI-powered marketing systems.\nVoice: {voice_notes}\nTopics: {topic_list}\n\nRules:\n1. Under 280 chars. Most 150-250.\n2. Lowercase casual tone.\n3. Sound human, not AI.\n4. 1-2 relevant hashtags per tweet.\n5. Mix hot takes, observations, tips, engagement posts.\n6. Be direct and opinionated.",
                    "messages": [{"role": "user", "content": f"Generate {posts_per_day} tweets for {date_str}.\n{num_text} text only, {num_image} with images.\nReturn ONLY a JSON array: [{{\"content\":\"tweet\",\"type\":\"text|image\",\"image_prompt\":\"for images only\",\"category\":\"topic\"}}]"}],
                },
                timeout=90,
            )
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"].strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            posts = json.loads(text)
        except Exception as e:
            print(f"  Error generating for brendanwardai: {e}")
            continue

        times = generate_post_times(len(posts), start_hour, end_hour)

        for i, post in enumerate(posts):
            content = post.get("content", "")
            post_type = post.get("type", "text")
            image_prompt = post.get("image_prompt", "")
            category = post.get("category", "")
            image_preview = ""
            if post_type == "image" and image_prompt:
                print(f"    Generating image (seedream-4.5)...")
                image_preview = generate_image(image_prompt, model="seedream-4.5")
            post_time = times[i] if i < len(times) else f"{start_hour + i}:00"
            all_rows.append([day_name, date_str, post_time, content, post_type, image_prompt, image_preview, category, "pending"])

        time.sleep(2)

    if all_rows:
        ws.append_rows(all_rows, value_input_option="RAW")
        print(f"  @brendanwardai: {len(all_rows)} rows written")
    else:
        print(f"  @brendanwardai: No new rows")


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    if not GOOGLE_SHEET_ID:
        print("ERROR: GOOGLE_SHEET_ID not set")
        sys.exit(1)

    config = load_config()
    defaults = config.get("defaults", {})
    sites = config.get("sites", [])
    game_urls = load_game_urls()

    today = datetime.date.today()
    dates = [today + datetime.timedelta(days=i) for i in range(7)]

    print(f"Generating posts for {today} through {dates[-1]}")
    print(f"  Posts per day: {defaults.get('posts_per_day', 8)}")
    print(f"  Sites: {', '.join(s['name'] for s in sites)}")
    print()

    spreadsheet = get_sheet()

    print("=" * 50)
    print("@brendanwardai")
    generate_for_brendan(spreadsheet, defaults, dates)
    print()

    for site in sites:
        print("=" * 50)
        print(f"{site['name']} ({site.get('upload_post_profile', '')})")
        generate_for_site(spreadsheet, site, defaults, dates, game_urls)
        print()

    print("=" * 50)
    print(f"All done! Check your Google Sheet to review and approve posts.")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")


if __name__ == "__main__":
    main()
