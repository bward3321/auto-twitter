#!/usr/bin/env python3
"""
mega_update.py — Run this from inside your auto-twitter repo folder.
It updates all files with the new system: 8 posts/day, Lucid Origin for EveryFreeTool,
thread support, better content prompts, and pushes to GitHub.
"""

import os
import subprocess

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO_DIR)

print("🚀 MEGA UPDATE: Upgrading Twitter Autoposter")
print("=" * 50)

# ── 1. Pull latest ──────────────────────────────────────────────────────────
print("\n📥 Pulling latest from GitHub...")
subprocess.run(["git", "pull", "origin", "main"], check=False)

# ── 2. Write sites_config.yaml ──────────────────────────────────────────────
print("📝 Writing updated sites_config.yaml...")
with open("sites_config.yaml", "w") as f:
    f.write(r'''defaults:
  posts_per_day: 8
  image_post_ratio: 0.35
  posting_window_start_hour: 9
  posting_window_end_hour: 20
  timezone: "America/New_York"
  thread_day: "wednesday"
  thread_length: 5

sites:

  - name: "EveryFreeTool"
    upload_post_profile: "@EveryFreeTool"
    website: "everyfreetool.com"
    image_model: "lucid-origin"

    voice:
      tone: "helpful, slightly nerdy, genuinely excited about free tools, always driving value back to the site"
      style_notes: >
        You are the Twitter account for everyfreetool.com — the internet's best collection of 100% free browser tools.
        Your job is to get people to visit everyfreetool.com by showing them they're overpaying for tools that have free alternatives.
        Every post should leave the reader thinking 'wait, there's a free version of that?' or 'I need to check this out.'
        Write like someone who finds obscure free tools so others dont have to.
        Enthusiastic but not salesy. Lowercase is fine. Keep it conversational.
        NEVER end a post randomly — every post should either link to the site, reference the site, or set up the value prop.
      avoid: >
        Sounding like a generic ad. Hashtag spam. Emoji overload.
        Generic productivity hack vibes. Posts that dont connect back to the site at all.
        Ending posts without a hook or CTA. Random observations with no tie-in.
      format_preferences: >
        Short punchy tool recommendations with direct URL.
        Stop paying for X when Y exists for free format.
        Hot takes on paid vs free that make people curious.
        Did you know format with link. Before/after comparisons.

    content_mix:
      tool_spotlights: 0.40
      anti_saas_takes: 0.30
      engagement_viral: 0.20
      image_showcase: 0.10

    content_mix_instructions: >
      Follow this content mix for every batch of posts:

      TOOL SPOTLIGHTS (40% of posts): Direct promotion of a specific tool on everyfreetool.com.
      Format: highlight what the tool does, mention what people currently pay for, then link directly.
      Examples:
      - 'stop paying $20/month for canva pro when everyfreetool.com/image-tools has a free background remover that works just as well'
      - 'you can convert any file to PDF for free at everyfreetool.com/pdf-tools. no signup, no watermark, no bs'
      - 'just found out people pay $15/month for a QR code generator. everyfreetool.com/developer-tools has one for free. forever.'
      Always include a direct URL to the relevant tool category page.

      ANTI-SAAS HOT TAKES (30% of posts): Opinions about overpriced software that make people think about free alternatives.
      These dont need a direct link but they MUST end with a hook that points back to the concept of free tools.
      Examples:
      - 'adobe charges $55/month for photoshop. in 2026. and most people use 3% of its features. the free tools have caught up. people just dont know yet.'
      - 'the SaaS industrys biggest fear is people realizing 80% of what they pay for has a free alternative'
      - 'hot take: most paid tools are just free tools with better marketing and a credit card form'
      End with a thought that makes people curious, not just a random statement.

      ENGAGEMENT/VIRAL (20% of posts): Questions, polls, debates that grow the audience.
      Examples:
      - 'name a tool youre embarrassed you still pay for'
      - 'whats one SaaS subscription youd cancel immediately if a free alternative existed?'
      These build community and get replies/retweets.

      IMAGE SHOWCASE (10% of posts): Visual posts showing tools in action or comparison graphics.

    categories:
      - name: "Free Tool Discoveries"
        description: "Highlighting specific free tools on everyfreetool.com"
        subtopics:
          - PDF tools and converters
          - Image editing and background removal
          - Developer and coding tools
          - Writing and grammar tools
          - Finance calculators and tools
          - Video and audio converters
          - SEO analysis tools
          - File conversion tools
          - Social media tools
          - QR code generators
        angles:
          - "Direct links to specific tools on everyfreetool.com with clear value prop"
          - "Stop paying for X when this free tool does the same thing"
          - "Side by side paid vs free comparison with the free option winning"
          - "I just saved $X/month by switching to this free tool"

      - name: "Anti-SaaS Takes"
        description: "Hot takes on overpriced SaaS and why free alternatives win"
        subtopics:
          - SaaS pricing is out of control
          - Features that should be free
          - Open source vs paid tools
          - Why simple tools beat bloated platforms
          - The subscription fatigue epidemic
          - Tools that used to be free and now charge
        angles:
          - "Contrarian takes on popular paid tools that end with a free alternative hook"
          - "Real cost breakdowns showing how much people waste on subscriptions"
          - "Why the tools industry is broken and free tools are the answer"

      - name: "Engagement and Community"
        description: "Posts designed to get replies, retweets, and grow the audience"
        subtopics:
          - Tool recommendation requests
          - Paid vs free debates
          - Subscription confession posts
          - Would you switch challenges
        angles:
          - "Questions that get people sharing their tool stacks"
          - "Debates about paid vs free that drive engagement"

    site_links:
      - url: "https://everyfreetool.com"
        context: "general site link, use for broad posts"
      - url: "https://everyfreetool.com/pdf-tools"
        context: "when talking about PDF tools, converters, editors"
      - url: "https://everyfreetool.com/image-tools"
        context: "when talking about image editing, background removal, resizing"
      - url: "https://everyfreetool.com/developer-tools"
        context: "when talking about developer tools, JSON, code formatting, QR codes"
      - url: "https://everyfreetool.com/writing-tools"
        context: "when talking about writing, grammar, text tools"
      - url: "https://everyfreetool.com/finance-tools"
        context: "when talking about finance, calculators, budgeting"
      - url: "https://everyfreetool.com/seo-tools"
        context: "when talking about SEO, keywords, meta tags"
      - url: "https://everyfreetool.com/video-audio-tools"
        context: "when talking about video/audio conversion, editing"
      - url: "https://everyfreetool.com/social-media-tools"
        context: "when talking about social media tools, hashtags, captions"
      - url: "https://everyfreetool.com/conversion-tools"
        context: "when talking about file conversion, unit conversion"

    thread_config:
      frequency: "weekly"
      topic_ideas:
        - "10 tools youre overpaying for (and the free alternatives)"
        - "I replaced my entire $200/month SaaS stack with free tools. heres how."
        - "the ultimate free tool stack for startups (save $500/month)"
        - "free tools that are actually BETTER than the paid version"
        - "every PDF tool you need, completely free (thread)"
        - "the free image editing stack that rivals photoshop"
        - "tools that went from free to paid and the free alternatives that replaced them"
        - "the hidden free tools most people dont know exist"

  - name: "WhatIfs"
    upload_post_profile: "@ifswhat91839"
    website: "whatifs.fun"
    image_model: "seedream-4.5"

    voice:
      tone: "playful, curious, slightly chaotic, internet-native humor, always driving people to play games"
      style_notes: >
        You are the Twitter account for whatifs.fun — a site full of addictive browser games and what-if experiments.
        Your job is to get people to click through and play games on whatifs.fun.
        Every post should make someone think 'I need to try this' or 'I bet I could beat that.'
        Write like someone who makes weird browser games and loves it.
        The vibe is 'what if we made a game about that.'
        Playful, fun, sometimes absurd. Think neal.fun energy.
        NEVER end a post randomly — always hook back to a game or the site.
        Use lowercase. Keep it light and fun.
      avoid: >
        Being corporate or salesy. Download our app energy.
        Hashtag spam. Being too serious.
        Posts that dont connect back to any game or the site.
        Random gaming observations with no tie-in.
      format_preferences: >
        What if you could hooks with game link.
        I bet you cant beat X challenges with link.
        Short game descriptions that create curiosity.
        Score sharing hooks. Fun hypothetical questions tied to games.
        Bored at work try this energy.

    content_mix:
      game_spotlights: 0.40
      challenge_hooks: 0.25
      engagement_viral: 0.20
      what_if_questions: 0.15

    content_mix_instructions: >
      Follow this content mix for every batch of posts:

      GAME SPOTLIGHTS (40% of posts): Direct promotion of a specific game on whatifs.fun.
      Always include the direct game URL. Make the game sound irresistible.
      Examples:
      - 'this typing speed test just humbled me. thought i was fast. i was not. whatifs.fun/typing-speed-test/'
      - 'nuclear simulation where you pick a city and watch what happens. i played for 45 minutes. whatifs.fun/nuclear-simulation/'
      - 'how average are you? this quiz tells you exactly where you fall. brutally honest. whatifs.fun/how-average-are-you/'

      CHALLENGE HOOKS (25% of posts): Competitive posts that dare people to beat a score or try something.
      Examples:
      - 'i got 43ms on the reflex test. bet you cant break 50. whatifs.fun/reflex-test/'
      - 'nobody can draw a perfect circle. prove me wrong. whatifs.fun/perfect-circle/'
      - 'the chimp test will make you question your own intelligence. i scored 7. whatifs.fun/chimp-test/'

      ENGAGEMENT/VIRAL (20% of posts): Fun questions and debates that grow the audience.
      Examples:
      - 'whats the most addictive browser game youve ever played?'
      - 'would you rather know your exact life expectancy or your IQ?'
      - 'flash games were peak internet. what was your go-to?'

      WHAT IF QUESTIONS (15% of posts): Hypothetical questions tied to games on the site.
      Examples:
      - 'what if you could simulate a pandemic and see how fast it spreads? oh wait you can. whatifs.fun/pandemic-simulator/'
      - 'what if you had to survive in space with limited oxygen? whatifs.fun/survive-in-space/'

    categories:
      - name: "Game Spotlights"
        description: "Promoting specific games on whatifs.fun"
        subtopics:
          - Reflex and reaction games
          - Memory and brain tests
          - Simulation games
          - Puzzle and strategy games
          - Typing and speed games
          - Quiz and trivia games
          - Classic arcade games
          - Idle and clicker games
        angles:
          - "Direct links to specific games with hook that creates curiosity"
          - "Bored at work try this energy"
          - "I bet you cant beat my score hooks"
          - "This game just humbled me format"

      - name: "Challenge Posts"
        description: "Competitive posts that dare people to play"
        subtopics:
          - Score challenges on specific games
          - Can you beat this challenges
          - Prove me wrong dares
          - Time-based challenges
        angles:
          - "Post a score and dare followers to beat it"
          - "Nobody can do X prove me wrong"
          - "The hardest game on the internet challenge"

      - name: "What If Questions"
        description: "Hypothetical questions that tie into games"
        subtopics:
          - Survival hypotheticals
          - Science what-ifs
          - History what-ifs
          - Would you rather scenarios
        angles:
          - "Tie hypotheticals directly to playable games on the site"
          - "Make people curious enough to click through"

      - name: "Internet and Gaming Culture"
        description: "Takes on gaming, internet culture, and browser games"
        subtopics:
          - Why browser games are making a comeback
          - Flash game nostalgia
          - Simple games vs AAA games
          - The psychology of addictive games
        angles:
          - "Hot takes that position browser games as the future"
          - "Nostalgia posts that drive engagement"

    site_links:
      - url: "https://whatifs.fun"
        context: "general site link"
      - url: "https://whatifs.fun/reflex-test/"
        context: "reaction time, reflexes, speed"
      - url: "https://whatifs.fun/typing-speed-test/"
        context: "typing, speed, WPM"
      - url: "https://whatifs.fun/nuclear-simulation/"
        context: "nuclear, simulation, destruction"
      - url: "https://whatifs.fun/how-average-are-you/"
        context: "personality, average, quiz"
      - url: "https://whatifs.fun/perfect-circle/"
        context: "drawing, precision, challenge"
      - url: "https://whatifs.fun/memory-test/"
        context: "memory, brain, cognitive"
      - url: "https://whatifs.fun/chimp-test/"
        context: "intelligence, memory, chimps"
      - url: "https://whatifs.fun/pandemic-simulator/"
        context: "pandemic, virus, simulation"
      - url: "https://whatifs.fun/snake-game/"
        context: "classic, arcade, snake"
      - url: "https://whatifs.fun/2048-game/"
        context: "puzzle, numbers, addictive"
      - url: "https://whatifs.fun/iq-test/"
        context: "IQ, intelligence, brain"
      - url: "https://whatifs.fun/personality-test/"
        context: "personality, quiz, self-discovery"
      - url: "https://whatifs.fun/color-blind-test/"
        context: "color, vision, eyes"
      - url: "https://whatifs.fun/impossible-quiz/"
        context: "impossible, hard, challenge"
      - url: "https://whatifs.fun/life-expectancy/"
        context: "life, death, expectancy"
      - url: "https://whatifs.fun/spend-a-billion/"
        context: "money, spending, billion"
      - url: "https://whatifs.fun/aim-trainer/"
        context: "aim, FPS, gaming skills"
      - url: "https://whatifs.fun/stock-simulator/"
        context: "stocks, trading, money"
      - url: "https://whatifs.fun/trolley-problem/"
        context: "ethics, morality, trolley"
      - url: "https://whatifs.fun/survive-in-space/"
        context: "space, survival, astronaut"
      - url: "https://whatifs.fun/earthquake-simulator/"
        context: "earthquake, disaster, simulation"
      - url: "https://whatifs.fun/speed-click-test/"
        context: "clicking, speed, CPS"
      - url: "https://whatifs.fun/higher-or-lower/"
        context: "guessing, numbers, game"
      - url: "https://whatifs.fun/word-guess/"
        context: "words, wordle, guessing"
      - url: "https://whatifs.fun/mental-age/"
        context: "mental age, brain, quiz"

    thread_config:
      frequency: "weekly"
      topic_ideas:
        - "10 browser games that are way more addictive than they should be (thread)"
        - "the best free browser games to play when youre bored at work"
        - "games that will make you question your own intelligence"
        - "the hardest games on the internet can you beat them all?"
        - "browser games that feel like they should cost money but are completely free"
        - "games that reveal something about your personality"
        - "the most satisfying games on the internet (thread)"
''')
print("  ✅ sites_config.yaml updated")


# ── 3. Write generate_all.py ────────────────────────────────────────────────
print("📝 Writing updated generate_all.py...")
# Read from the file we'll create
GENERATE_ALL_CODE = '''#!/usr/bin/env python3
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

    links_text = "\\n".join([f"  - {l['url']} -- use when: {l['context']}" for l in site_links])

    cats_text = ""
    for cat in categories:
        cats_text += f"\\n  Category: {cat['name']}\\n"
        cats_text += f"  Description: {cat.get('description', '')}\\n"
        cats_text += f"  Subtopics: {', '.join(cat.get('subtopics', []))}\\n"
        angles = cat.get('angles', [])
        if angles:
            cats_text += f"  Angles: {'; '.join(angles)}\\n"

    game_urls_text = ""
    if game_urls and site_name == "WhatIfs":
        all_games = []
        for category, slugs in game_urls.get("games_by_category", {}).items():
            for slug in slugs:
                all_games.append(f"whatifs.fun/{slug}/")
        sample_games = random.sample(all_games, min(40, len(all_games)))
        game_urls_text = f"""
AVAILABLE GAME URLs (use these exact URLs in posts):
""" + "\\n".join("  - " + g for g in sample_games) + """

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
            text = text.split("\\n", 1)[1] if "\\n" in text else text[3:]
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
    links_text = "\\n".join([f"  - {l['url']}" for l in site_links[:10]])

    game_urls_text = ""
    if game_urls and site_name == "WhatIfs":
        all_games = []
        for category, slugs in game_urls.get("games_by_category", {}).items():
            for slug in slugs:
                all_games.append(f"whatifs.fun/{slug}/")
        sample_games = random.sample(all_games, min(20, len(all_games)))
        game_urls_text = "\\nGAME URLs to include:\\n" + "\\n".join("  - " + g for g in sample_games)

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
            text = text.split("\\n", 1)[1] if "\\n" in text else text[3:]
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
    topic_list = "\\n".join([f"- {t}" for t in topic_areas]) if isinstance(topic_areas, list) else str(topic_areas)
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
                    "system": f"You write tweets for @brendanwardai -- a founder who builds AI-powered marketing systems.\\nVoice: {voice_notes}\\nTopics: {topic_list}\\n\\nRules:\\n1. Under 280 chars. Most 150-250.\\n2. Lowercase casual tone.\\n3. Sound human, not AI.\\n4. 1-2 relevant hashtags per tweet.\\n5. Mix hot takes, observations, tips, engagement posts.\\n6. Be direct and opinionated.",
                    "messages": [{"role": "user", "content": f"Generate {posts_per_day} tweets for {date_str}.\\n{num_text} text only, {num_image} with images.\\nReturn ONLY a JSON array: [{{\\"content\\":\\"tweet\\",\\"type\\":\\"text|image\\",\\"image_prompt\\":\\"for images only\\",\\"category\\":\\"topic\\"}}]"}],
                },
                timeout=90,
            )
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"].strip()
            if text.startswith("```"):
                text = text.split("\\n", 1)[1] if "\\n" in text else text[3:]
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
'''

with open("generate_all.py", "w") as f:
    f.write(GENERATE_ALL_CODE)
print("  ✅ generate_all.py updated")


# ── 4. Write post_all.py ────────────────────────────────────────────────────
print("📝 Writing updated post_all.py...")
POST_ALL_CODE = '''#!/usr/bin/env python3
"""
post_all.py — Multi-account Twitter poster
Reads approved posts from Google Sheet tabs and posts them via Upload Post API.
Supports text, image, and thread posts with smart scheduling fallbacks.
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
    data = {"user": profile, "platform[]": "x", "title": content}
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
        data["timezone"] = "America/New_York"
    resp = requests.post(
        f"{UPLOAD_POST_BASE}/upload",
        headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
        data=data, timeout=60,
    )
    if resp.status_code >= 400:
        print(f"    Text post error: {resp.text[:300]}")
    resp.raise_for_status()
    return resp.json()


def post_photo(content, image_url, profile, scheduled_date=None):
    img_resp = requests.get(image_url, timeout=30)
    img_resp.raise_for_status()
    tmp_path = Path(__file__).parent / "tmp_photo.jpg"
    with open(tmp_path, "wb") as f:
        f.write(img_resp.content)

    data = {"user": profile, "platform[]": "x", "title": content}
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
        print(f"    Photo upload error: {resp.text[:300]}")
    resp.raise_for_status()
    return resp.json()


def post_thread(tweets, profile, scheduled_date=None):
    results = []
    for i, tweet in enumerate(tweets):
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
            results.append(result)
            print(f"    Thread {i+1}/{len(tweets)} posted")
            time.sleep(3)
        except Exception as e:
            print(f"    Thread tweet {i+1} failed: {e}")
            results.append(None)
    return results


def generate_image_fresh(prompt, model="seedream-4.5"):
    if not LEONARDO_API_KEY:
        return ""
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}",
    }
    payload = {"model": model, "parameters": {"width": 1024, "height": 1024, "prompt": prompt, "quantity": 1}, "public": False}
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
        print(f"    Fresh image error: {e}")
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
        print(f"  Tab \\'{tab_name}\\' not found, skipping")
        return 0, 0

    records_raw = ws.get_all_values()
    if len(records_raw) < 2:
        print(f"  {tab_name}: No data rows")
        return 0, 0

    headers = records_raw[0]
    records = [dict(zip(headers, r + [\\'\\'] * (len(headers) - len(r)))) for r in records_raw[1:]]

    to_post = []
    thread_tweets = []

    for i, row in enumerate(records):
        row_num = i + 2
        status = str(row.get("Status", "")).strip().lower()
        date = str(row.get("Date", "")).strip()
        post_type = str(row.get("Type", "")).strip().lower()

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

        try:
            if post_type == "image":
                img_url = None
                if image_preview and image_preview.startswith("http"):
                    img_url = image_preview
                elif image_prompt:
                    print(f"    Generating fresh image...")
                    model = "lucid-origin" if tab_name == "EveryFreeTool" else "seedream-4.5"
                    img_url = generate_image_fresh(image_prompt, model=model)

                if img_url:
                    try:
                        result = post_photo(content, img_url, profile, scheduled)
                    except Exception as e:
                        print(f"    Photo scheduled failed: {e}")
                        try:
                            result = post_photo(content, img_url, profile)
                        except Exception as e2:
                            print(f"    Photo immediate failed: {e2}, falling back to text")
                            result = post_text(content, profile, scheduled)
                else:
                    print(f"    No image available, posting as text")
                    result = post_text(content, profile, scheduled)
            else:
                result = post_text(content, profile, scheduled)

            status_col = headers.index("Status") + 1 if "Status" in headers else len(headers)
            ws.update_cell(row_num, status_col, "posted")
            posted += 1
            print(f"    Posted successfully")
        except Exception as e:
            print(f"    Failed: {e}")
            status_col = headers.index("Status") + 1 if "Status" in headers else len(headers)
            ws.update_cell(row_num, status_col, f"failed: {str(e)[:50]}")
            failed += 1
        time.sleep(2)

    if thread_tweets:
        print(f"  Posting thread ({len(thread_tweets)} tweets)...")
        tweets = [t.get("Content", "").strip() for t in thread_tweets if t.get("Content", "").strip()]
        first_time = thread_tweets[0].get("Time", "12:00").strip()
        scheduled = get_scheduled_datetime(today, first_time)
        try:
            results = post_thread(tweets, profile, scheduled)
            status_col = headers.index("Status") + 1 if "Status" in headers else len(headers)
            for t_row in thread_tweets:
                ws.update_cell(t_row["row_num"], status_col, "posted")
            posted += len(thread_tweets)
            print(f"    Thread posted ({len(tweets)} tweets)")
        except Exception as e:
            print(f"    Thread failed: {e}")
            status_col = headers.index("Status") + 1 if "Status" in headers else len(headers)
            for t_row in thread_tweets:
                ws.update_cell(t_row["row_num"], status_col, f"failed: {str(e)[:50]}")
            failed += len(thread_tweets)

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
'''

with open("post_all.py", "w") as f:
    f.write(POST_ALL_CODE)
print("  ✅ post_all.py updated")


# ── 5. Write GitHub Actions workflow ────────────────────────────────────────
print("📝 Writing updated GitHub Actions workflow...")
os.makedirs(".github/workflows", exist_ok=True)
with open(".github/workflows/daily-post.yml", "w") as f:
    f.write("""name: Twitter Autoposter

on:
  schedule:
    # Generate weekly batch — Sunday at 10am ET (14:00 UTC)
    - cron: '0 14 * * 0'
    # Post daily — 8am ET (12:00 UTC)
    - cron: '0 12 * * *'
    # Backup post run — 8:30am ET in case first one misses
    - cron: '30 12 * * *'
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to run'
        required: true
        type: choice
        options:
          - generate
          - post

permissions:
  contents: write

jobs:
  generate:
    if: >-
      (github.event_name == 'schedule' && github.event.schedule == '0 14 * * 0') ||
      (github.event_name == 'workflow_dispatch' && github.event.inputs.action == 'generate')
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests pyyaml gspread

      - name: Generate weekly posts
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          LEONARDO_API_KEY: ${{ secrets.LEONARDO_API_KEY }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
          GOOGLE_SHEETS_CREDS: ${{ secrets.GOOGLE_SHEETS_CREDS }}
          GOOGLE_CREDS_PATH: /tmp/google-creds.json
        run: |
          echo "$GOOGLE_SHEETS_CREDS" > /tmp/google-creds.json
          python generate_all.py

  post:
    if: >-
      (github.event_name == 'schedule' && (github.event.schedule == '0 12 * * *' || github.event.schedule == '30 12 * * *')) ||
      (github.event_name == 'workflow_dispatch' && github.event.inputs.action == 'post')
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests pyyaml gspread

      - name: Post approved content
        env:
          UPLOAD_POST_API_KEY: ${{ secrets.UPLOAD_POST_API_KEY }}
          UPLOAD_POST_USER: ${{ secrets.UPLOAD_POST_USER }}
          LEONARDO_API_KEY: ${{ secrets.LEONARDO_API_KEY }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
          GOOGLE_SHEETS_CREDS: ${{ secrets.GOOGLE_SHEETS_CREDS }}
          GOOGLE_CREDS_PATH: /tmp/google-creds.json
        run: |
          echo "$GOOGLE_SHEETS_CREDS" > /tmp/google-creds.json
          python post_all.py
""")
print("  ✅ daily-post.yml updated")


# ── 6. Git add, commit, push ────────────────────────────────────────────────
print("\n📤 Pushing to GitHub...")
subprocess.run(["git", "add", "-A"], check=True)
result = subprocess.run(
    ["git", "commit", "-m", "MEGA UPDATE: 8 posts/day, Lucid Origin for EFT, threads, better prompts, backup cron"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("  ✅ Committed")
    push_result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if push_result.returncode == 0:
        print("  ✅ Pushed to GitHub")
    else:
        print(f"  ❌ Push failed: {push_result.stderr}")
else:
    print(f"  ⚠️  Nothing to commit or error: {result.stderr}")

print("\n" + "=" * 50)
print("🎉 MEGA UPDATE COMPLETE!")
print("=" * 50)
print("""
What changed:
  ✅ 8 posts/day per site account (up from 5)
  ✅ Lucid Origin model for EveryFreeTool images (unlimited, HD)
  ✅ Seedream 4.5 kept for WhatIfs images
  ✅ Weekly thread generation (Wednesdays)
  ✅ Better content prompts — every post ties back to the site
  ✅ Content mix enforcement (40% spotlights, 30% takes, 20% engagement, 10% images)
  ✅ Backup cron at 8:30am ET in case 8am misses
  ✅ Smart scheduling — missed times get pushed forward

Next steps:
  1. Clear old posts from your Google Sheet tabs (or just delete the EveryFreeTool and WhatIfs tabs)
  2. Go to GitHub → Actions → Twitter Autoposter → Run workflow → generate
  3. Review the new posts in your Sheet — you'll see the upgraded quality
  4. Approve and run post to fire them off
""")
