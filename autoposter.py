#!/usr/bin/env python3
"""
Twitter/X Autoposter
Generates content via Claude API, images via Leonardo.ai, posts via Upload Post API.
Designed to run daily via GitHub Actions cron.
"""

import os
import sys
import json
import time
import random
import requests
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
UPLOAD_POST_API_KEY = os.environ.get("UPLOAD_POST_API_KEY")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
UPLOAD_POST_USER = os.environ.get("UPLOAD_POST_USER", "test")

ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
LEONARDO_MODEL_ID = "6b645e3a-d64f-4341-a6d8-7a3f79d62571"  # Leonardo Phoenix 1.0
LEONARDO_API_BASE = "https://cloud.leonardo.ai/api/rest/v1"

UPLOAD_POST_BASE = "https://api.upload-post.com/api"

LOG_FILE = Path(__file__).parent / "post_log.json"
TOPICS_FILE = Path(__file__).parent / "topics.yaml"
CONFIG_FILE = Path(__file__).parent / "config.yaml"


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def load_config():
    """Load posting config from config.yaml"""
    import yaml
    config_path = CONFIG_FILE
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    # Defaults
    return {
        "posts_per_day": 4,
        "image_post_ratio": 0.25,  # 25% of posts get images
        "posting_window_start_hour": 10,  # 10am ET
        "posting_window_end_hour": 16,    # 4pm ET
        "timezone": "America/New_York",
        "platform": "x",
    }


def load_topics():
    """Load topics from topics.yaml"""
    import yaml
    topics_path = TOPICS_FILE
    if not topics_path.exists():
        print("ERROR: topics.yaml not found!")
        sys.exit(1)
    with open(topics_path) as f:
        return yaml.safe_load(f)


def load_post_log():
    """Load previous post log to avoid repeats"""
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_post_log(log):
    """Save post log"""
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, default=str)


def get_recent_posts(log, days=7):
    """Get posts from the last N days to avoid repetition"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for post in log.get("posts", []):
        try:
            post_date = datetime.fromisoformat(post["created_at"])
            if post_date > cutoff:
                recent.append(post["content"])
        except (KeyError, ValueError):
            continue
    return recent


# ─── CLAUDE API: CONTENT GENERATION ──────────────────────────────────────────

def generate_posts(topics_data, config, recent_posts):
    """Use Claude API to generate today's posts"""
    
    num_posts = config.get("posts_per_day", 4)
    image_ratio = config.get("image_post_ratio", 0.25)
    num_image_posts = max(1, round(num_posts * image_ratio))
    num_text_posts = num_posts - num_image_posts
    
    # Build the topics context
    topics_str = ""
    for category in topics_data.get("categories", []):
        topics_str += f"\n### {category['name']}\n"
        topics_str += f"Description: {category.get('description', '')}\n"
        if "subtopics" in category:
            topics_str += f"Subtopics: {', '.join(category['subtopics'])}\n"
        if "angles" in category:
            topics_str += f"Angles/approaches: {', '.join(category['angles'])}\n"
    
    # Build voice/style guidelines
    voice = topics_data.get("voice", {})
    voice_str = f"""
Tone: {voice.get('tone', 'casual, direct, no-BS')}
Style notes: {voice.get('style_notes', 'Write like a founder who has been through it. No corporate speak. No motivational poster energy. Real talk.')}
Do NOT: {voice.get('avoid', 'Use hashtags excessively, be preachy, use generic advice, start with "Just", use emoji spam')}
Format preferences: {voice.get('format_preferences', 'Mix of short punchy tweets (1-2 sentences), medium observations (2-3 sentences), and occasional longer threads broken into tweet-length paragraphs')}
"""
    
    # Recent posts to avoid repetition
    recent_str = ""
    if recent_posts:
        recent_str = "\n\nRECENT POSTS (do NOT repeat similar ideas):\n"
        for i, post in enumerate(recent_posts[-20:], 1):
            recent_str += f"{i}. {post[:100]}...\n" if len(post) > 100 else f"{i}. {post}\n"
    
    prompt = f"""You are a social media content creator for an X/Twitter account. Generate exactly {num_posts} posts for today.

TOPIC CATEGORIES:
{topics_str}

VOICE & STYLE:
{voice_str}
{recent_str}

REQUIREMENTS:
- Generate exactly {num_text_posts} TEXT-ONLY posts and {num_image_posts} IMAGE posts
- For IMAGE posts, include an "image_prompt" field with a detailed prompt for AI image generation (the image should complement or illustrate the tweet - think infographics, visual metaphors, dramatic scenes, data visualizations)
- Each post must be under 280 characters (this is critical - count carefully)
- Make each post feel unique in structure and approach
- Mix up the types: hot takes, observations, questions, contrarian views, practical tips, stories
- Pick from DIFFERENT topic categories - don't cluster on one topic
- No hashtags unless they're genuinely part of the sentence
- Today's date for context: {datetime.now().strftime('%A, %B %d, %Y')}

Respond with ONLY a JSON array. Each element should have:
- "content": the tweet text (MUST be under 280 characters)
- "type": either "text" or "image"  
- "image_prompt": (only for type "image") a detailed image generation prompt
- "topic_category": which category this falls under
- "engagement_hook": brief note on why this should get engagement

Example format:
[
  {{"content": "Your tweet here", "type": "text", "topic_category": "AI", "engagement_hook": "contrarian take"}},
  {{"content": "Another tweet", "type": "image", "image_prompt": "A dramatic split-screen showing...", "topic_category": "Startups", "engagement_hook": "visual data point"}}
]

CRITICAL: Every single post MUST be under 280 characters. Count carefully. Output ONLY the JSON array, no other text."""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }
    
    print(f"🧠 Generating {num_posts} posts via Claude API...")
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    
    data = resp.json()
    text = data["content"][0]["text"]
    
    # Clean up the response - strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # Remove first line
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    
    posts = json.loads(text)
    
    # Validate character counts
    for post in posts:
        if len(post["content"]) > 280:
            print(f"⚠️  Post too long ({len(post['content'])} chars), truncating: {post['content'][:50]}...")
            # Try to truncate gracefully
            post["content"] = post["content"][:277] + "..."
    
    print(f"✅ Generated {len(posts)} posts")
    return posts


# ─── LEONARDO.AI: IMAGE GENERATION ───────────────────────────────────────────

def generate_image(prompt):
    """Generate an image via Leonardo.ai API, return the image URL"""
    if not LEONARDO_API_KEY:
        print("⚠️  No Leonardo API key, skipping image generation")
        return None
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
    }
    
    # Create generation
    gen_payload = {
        "height": 1024,
        "width": 1024,
        "modelId": LEONARDO_MODEL_ID,
        "prompt": prompt,
        "num_images": 1,
        "alchemy": True,
        "presetStyle": "DYNAMIC",
    }
    
    print(f"🎨 Generating image via Leonardo.ai...")
    resp = requests.post(
        f"{LEONARDO_API_BASE}/generations",
        headers=headers,
        json=gen_payload,
        timeout=30,
    )
    resp.raise_for_status()
    
    generation_id = resp.json()["sdGenerationJob"]["generationId"]
    print(f"   Generation ID: {generation_id}")
    
    # Poll for completion (max 60 seconds)
    for attempt in range(12):
        time.sleep(5)
        status_resp = requests.get(
            f"{LEONARDO_API_BASE}/generations/{generation_id}",
            headers=headers,
            timeout=15,
        )
        status_resp.raise_for_status()
        gen_data = status_resp.json()["generations_by_pk"]
        
        status = gen_data.get("status")
        if status == "COMPLETE":
            images = gen_data.get("generated_images", [])
            if images:
                url = images[0]["url"]
                print(f"✅ Image generated: {url[:80]}...")
                return url
            break
        elif status == "FAILED":
            print("❌ Image generation failed")
            return None
        print(f"   Waiting... ({attempt + 1}/12)")
    
    print("❌ Image generation timed out")
    return None


def download_image(url, filename="temp_image.jpg"):
    """Download image from URL to local file"""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    filepath = Path(__file__).parent / filename
    with open(filepath, "wb") as f:
        f.write(resp.content)
    return str(filepath)


# ─── UPLOAD POST: POSTING TO X/TWITTER ───────────────────────────────────────

def post_text(content, scheduled_date=None):
    """Post a text tweet via Upload Post API"""
    headers = {
        "Authorization": f"Apikey {UPLOAD_POST_API_KEY}",
    }
    
    data = {
        "user": UPLOAD_POST_USER,
        "platform[]": "x",
        "title": content,
    }
    
    if scheduled_date:
        data["scheduled_date"] = scheduled_date.isoformat()
        data["timezone"] = "America/New_York"
    
    print(f"📤 Posting text to X: \"{content[:60]}...\"")
    resp = requests.post(
        f"{UPLOAD_POST_BASE}/upload_text",
        headers=headers,
        data=data,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"✅ Posted! Response: {json.dumps(result, indent=2)[:200]}")
    return result


def post_photo(content, image_path, scheduled_date=None):
    """Post a photo tweet via Upload Post API"""
    headers = {
        "Authorization": f"Apikey {UPLOAD_POST_API_KEY}",
    }
    
    data = {
        "user": UPLOAD_POST_USER,
        "platform[]": "x",
        "title": content,
    }
    
    if scheduled_date:
        data["scheduled_date"] = scheduled_date.isoformat()
        data["timezone"] = "America/New_York"
    
    with open(image_path, "rb") as img_file:
        files = {"image": ("image.jpg", img_file, "image/jpeg")}
        
        print(f"📤 Posting photo to X: \"{content[:60]}...\"")
        resp = requests.post(
            f"{UPLOAD_POST_BASE}/upload_photos",
            headers=headers,
            data=data,
            files=files,
            timeout=60,
        )
    
    resp.raise_for_status()
    result = resp.json()
    print(f"✅ Posted with image! Response: {json.dumps(result, indent=2)[:200]}")
    return result


# ─── SCHEDULING LOGIC ────────────────────────────────────────────────────────

def calculate_post_times(num_posts, config):
    """Calculate scheduled times for today's posts spread across the posting window"""
    from zoneinfo import ZoneInfo
    
    tz = ZoneInfo(config.get("timezone", "America/New_York"))
    now = datetime.now(tz)
    
    start_hour = config.get("posting_window_start_hour", 10)
    end_hour = config.get("posting_window_end_hour", 16)
    
    # If we're past the window, schedule for tomorrow
    if now.hour >= end_hour:
        base_date = now.date() + timedelta(days=1)
    else:
        base_date = now.date()
    
    # Calculate evenly spaced times within the window
    window_minutes = (end_hour - start_hour) * 60
    interval = window_minutes // (num_posts + 1)
    
    times = []
    for i in range(1, num_posts + 1):
        minutes_offset = interval * i + random.randint(-10, 10)  # Add some randomness
        minutes_offset = max(0, min(minutes_offset, window_minutes))
        
        post_time = datetime(
            base_date.year, base_date.month, base_date.day,
            start_hour, 0, 0, tzinfo=tz
        ) + timedelta(minutes=minutes_offset)
        
        # If this time is in the past, move to next available slot
        if post_time <= now:
            post_time = now + timedelta(minutes=5 * (i + 1))
        
        times.append(post_time)
    
    return times


# ─── MAIN EXECUTION ──────────────────────────────────────────────────────────

def run_test_post(text=None):
    """Post a single test tweet immediately"""
    if not UPLOAD_POST_API_KEY:
        print("ERROR: UPLOAD_POST_API_KEY not set")
        sys.exit(1)
    
    if not text:
        text = "testing 1 2 3... the machines are learning to post on their own. this is either the beginning of something great or the plot of a bad movie. 🤖"
    
    result = post_text(text)
    print(f"\n🎉 Test post sent! Check @brendanwardai on X.")
    return result


def run_daily():
    """Full daily run: generate content, create images, schedule posts"""
    # Validate env vars
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not UPLOAD_POST_API_KEY:
        missing.append("UPLOAD_POST_API_KEY")
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🚀 Twitter Autoposter - Daily Run")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Load everything
    config = load_config()
    topics = load_topics()
    log = load_post_log()
    recent = get_recent_posts(log)
    
    # Generate content
    posts = generate_posts(topics, config, recent)
    
    # Calculate posting schedule
    post_times = calculate_post_times(len(posts), config)
    
    # Process each post
    results = []
    for i, (post, scheduled_time) in enumerate(zip(posts, post_times)):
        print(f"\n--- Post {i+1}/{len(posts)} ---")
        print(f"📝 Content: {post['content']}")
        print(f"⏰ Scheduled: {scheduled_time.strftime('%I:%M %p %Z')}")
        print(f"📂 Category: {post.get('topic_category', 'unknown')}")
        
        try:
            if post["type"] == "image" and post.get("image_prompt"):
                # Generate and post with image
                image_url = generate_image(post["image_prompt"])
                if image_url:
                    image_path = download_image(image_url, f"post_image_{i}.jpg")
                    result = post_photo(post["content"], image_path, scheduled_time)
                    # Clean up
                    Path(image_path).unlink(missing_ok=True)
                else:
                    # Fallback to text post if image fails
                    print("⚠️  Image failed, falling back to text post")
                    result = post_text(post["content"], scheduled_time)
            else:
                result = post_text(post["content"], scheduled_time)
            
            # Log the post
            log_entry = {
                "content": post["content"],
                "type": post["type"],
                "category": post.get("topic_category", ""),
                "scheduled_for": scheduled_time.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "upload_post_response": result,
            }
            results.append(log_entry)
            
        except Exception as e:
            print(f"❌ Error posting: {e}")
            results.append({
                "content": post["content"],
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        
        # Small delay between API calls
        if i < len(posts) - 1:
            time.sleep(2)
    
    # Save log
    log["posts"].extend(results)
    save_post_log(log)
    
    # Summary
    success_count = sum(1 for r in results if "error" not in r)
    print(f"\n{'='*60}")
    print(f"✅ Daily run complete: {success_count}/{len(posts)} posts scheduled")
    print(f"{'='*60}\n")


def run_preview():
    """Generate posts without actually posting them - for review"""
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    config = load_config()
    topics = load_topics()
    log = load_post_log()
    recent = get_recent_posts(log)
    
    posts = generate_posts(topics, config, recent)
    post_times = calculate_post_times(len(posts), config)
    
    print(f"\n{'='*60}")
    print(f"📋 PREVIEW - Posts for today (NOT posted)")
    print(f"{'='*60}\n")
    
    for i, (post, t) in enumerate(zip(posts, post_times), 1):
        print(f"[{i}] {t.strftime('%I:%M %p')} | {post['type'].upper()}")
        print(f"    {post['content']}")
        if post.get("image_prompt"):
            print(f"    🎨 Image: {post['image_prompt'][:80]}...")
        print(f"    📂 {post.get('topic_category', '')} | Hook: {post.get('engagement_hook', '')}")
        print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter/X Autoposter")
    parser.add_argument("command", choices=["daily", "test", "preview"],
                        help="daily=full run, test=single test post, preview=generate without posting")
    parser.add_argument("--text", type=str, help="Custom text for test post")
    
    args = parser.parse_args()
    
    if args.command == "daily":
        run_daily()
    elif args.command == "test":
        run_test_post(args.text)
    elif args.command == "preview":
        run_preview()
