#!/usr/bin/env python3
"""
Automated Twitter/X posting system via Zernio API.
Reads approved posts from Google Sheets and publishes via Zernio.
Supports text-only and image posts across 3 accounts.
"""

import os
import sys
import json
import time
import gspread
import requests
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials

# ============================================================
# CONFIGURATION
# ============================================================

ZERNIO_API_KEY = os.environ.get('ZERNIO_API_KEY', 'sk_3281b259c4b4a3810de80d69c7c424c04bb453af6fb5e4bbed659721ac52116e')
ZERNIO_BASE_URL = 'https://zernio.com/api/v1'

SHEET_ID = '14S2PLjzgmOt59oDhmmOWkdoIC6VhpAkGTpM7o8NZAJI'

# Tab name -> Zernio account ID mapping
ACCOUNTS = {
    'Posts': {
        'account_id': '69bb3ea36cb7b8cf4c80c376',
        'username': '@brendanwardai',
        'platform': 'twitter'
    },
    'EveryFreeTool': {
        'account_id': '69bb410c6cb7b8cf4c80c9e7',
        'username': '@EveryFreeTool',
        'platform': 'twitter'
    },
    'WhatIfs': {
        'account_id': '69bb424e6cb7b8cf4c80cd10',
        'username': '@IfsWhat91839',
        'platform': 'twitter'
    }
}

TIMEZONE = 'America/New_York'

# ============================================================
# GOOGLE SHEETS AUTH
# ============================================================

def get_sheet():
    """Authenticate with Google Sheets and return the spreadsheet."""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS', '')
    if not creds_json:
        # Try loading from file (local development)
        creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
        if os.path.exists(creds_file):
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                creds_file,
                ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            )
        else:
            print("ERROR: No Google credentials found. Set GOOGLE_CREDENTIALS env var or provide credentials.json")
            sys.exit(1)
    else:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict,
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )
    
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


# ============================================================
# ZERNIO API
# ============================================================

def zernio_headers():
    return {
        'Authorization': f'Bearer {ZERNIO_API_KEY}',
        'Content-Type': 'application/json'
    }


def post_to_zernio(content, account_id, image_url=None, scheduled_time=None):
    """
    Post content via Zernio API.
    
    Args:
        content: Tweet text
        account_id: Zernio account ID
        image_url: Optional image URL for image posts
        scheduled_time: Optional ISO datetime string for scheduling. If None, publishes now.
    
    Returns:
        (success: bool, response_data: dict, status_text: str)
    """
    payload = {
        'content': content,
        'platforms': [{
            'platform': 'twitter',
            'accountId': account_id
        }]
    }
    
    # Add image if present
    if image_url and image_url.strip():
        payload['mediaItems'] = [{
            'type': 'image',
            'url': image_url.strip()
        }]
    
    # Schedule or publish now
    if scheduled_time:
        payload['scheduledFor'] = scheduled_time
        payload['timezone'] = TIMEZONE
    else:
        payload['publishNow'] = True
    
    try:
        resp = requests.post(
            f'{ZERNIO_BASE_URL}/posts',
            headers=zernio_headers(),
            json=payload,
            timeout=30
        )
        
        data = resp.json() if resp.text else {}
        
        if resp.status_code in (200, 201):
            platform_status = 'unknown'
            platforms = data.get('post', {}).get('platforms', [])
            if platforms:
                platform_status = platforms[0].get('status', 'unknown')
            return True, data, platform_status
        else:
            error_msg = data.get('error', data.get('message', resp.text[:200]))
            return False, data, f'error: {error_msg}'
    
    except requests.exceptions.Timeout:
        return False, {}, 'error: request timed out'
    except requests.exceptions.RequestException as e:
        return False, {}, f'error: {str(e)}'


# ============================================================
# POSTING LOGIC
# ============================================================

def find_column_index(headers, possible_names):
    """Find column index by trying multiple possible header names (case-insensitive)."""
    for i, h in enumerate(headers):
        if h.strip().lower() in [n.lower() for n in possible_names]:
            return i
    return -1


def get_today_str():
    """Get today's date string in the format used in the sheet."""
    from datetime import timezone as tz
    # Use ET (UTC-4 or UTC-5 depending on DST)
    # Approximate with UTC-4 for EDT
    now_utc = datetime.utcnow()
    now_et = now_utc - timedelta(hours=4)
    return now_et.strftime('%Y-%m-%d')


def parse_time_to_iso(date_str, time_str):
    """Convert date + time strings to ISO format for Zernio scheduling."""
    try:
        # Try common time formats
        for fmt in ['%H:%M', '%I:%M %p', '%I:%M%p', '%H:%M:%S']:
            try:
                t = datetime.strptime(time_str.strip(), fmt)
                return f'{date_str}T{t.strftime("%H:%M:%S")}'
            except ValueError:
                continue
        return None
    except Exception:
        return None


def should_publish_now(date_str, time_str):
    """Check if the scheduled time has already passed today."""
    try:
        now_utc = datetime.utcnow()
        now_et = now_utc - timedelta(hours=4)  # Approximate EDT
        
        iso_time = parse_time_to_iso(date_str, time_str)
        if not iso_time:
            return True  # Can't parse time, just publish now
        
        scheduled = datetime.strptime(iso_time, '%Y-%m-%dT%H:%M:%S')
        return now_et > scheduled
    except Exception:
        return True


def post_from_sheet(sheet, tab_name, account_config):
    """Process and post all approved posts from a single sheet tab."""
    
    account_id = account_config['account_id']
    username = account_config['username']
    
    try:
        worksheet = sheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"  WARNING: Tab '{tab_name}' not found, skipping")
        return 0, 0
    
    all_values = worksheet.get_all_values()
    if len(all_values) < 2:
        print(f"  No data in {tab_name}")
        return 0, 0
    
    headers = all_values[0]
    rows = all_values[1:]
    
    # Find column indices (flexible matching)
    date_col = find_column_index(headers, ['date', 'Date', 'DATE'])
    time_col = find_column_index(headers, ['time', 'Time', 'TIME', 'scheduled_time', 'Scheduled Time'])
    content_col = find_column_index(headers, ['content', 'Content', 'CONTENT', 'text', 'Text', 'tweet', 'Tweet'])
    status_col = find_column_index(headers, ['status', 'Status', 'STATUS'])
    image_col = find_column_index(headers, ['image_url', 'Image URL', 'image', 'Image', 'IMAGE_URL', 'media_url', 'Media URL'])
    type_col = find_column_index(headers, ['type', 'Type', 'TYPE', 'post_type', 'Post Type'])
    
    if content_col == -1:
        print(f"  ERROR: Can't find content column in {tab_name}")
        return 0, 0
    if status_col == -1:
        print(f"  ERROR: Can't find status column in {tab_name}")
        return 0, 0
    
    today = get_today_str()
    posted = 0
    failed = 0
    
    for row_idx, row in enumerate(rows):
        # Pad row if needed
        while len(row) <= max(filter(lambda x: x >= 0, [date_col, time_col, content_col, status_col, image_col, type_col])):
            row.append('')
        
        # Check status
        status = row[status_col].strip().lower()
        if status not in ('approved', 'edited'):
            continue
        
        # Check date (if date column exists)
        if date_col >= 0:
            row_date = row[date_col].strip()
            if row_date and row_date != today:
                continue
        
        content = row[content_col].strip()
        if not content:
            continue
        
        # Get image URL if present
        image_url = None
        if image_col >= 0 and row[image_col].strip():
            image_url = row[image_col].strip()
        
        # Get scheduled time
        time_str = row[time_col].strip() if time_col >= 0 else ''
        
        # Mark as "scheduling" BEFORE posting (prevents duplicates)
        sheet_row = row_idx + 2  # +1 for header, +1 for 1-indexed
        worksheet.update_cell(sheet_row, status_col + 1, 'scheduling')
        
        # Determine: publish now or schedule
        scheduled_time = None
        if time_str and date_col >= 0 and row[date_col].strip():
            if should_publish_now(row[date_col].strip(), time_str):
                scheduled_time = None  # Publish immediately
                print(f"  [{username}] Publishing now (time passed): {content[:60]}...")
            else:
                scheduled_time = parse_time_to_iso(row[date_col].strip(), time_str)
                print(f"  [{username}] Scheduling for {scheduled_time}: {content[:60]}...")
        else:
            print(f"  [{username}] Publishing now: {content[:60]}...")
        
        # Post via Zernio
        success, data, status_text = post_to_zernio(
            content=content,
            account_id=account_id,
            image_url=image_url,
            scheduled_time=scheduled_time
        )
        
        if success:
            worksheet.update_cell(sheet_row, status_col + 1, 'posted')
            posted += 1
            print(f"    ✓ {status_text}")
        else:
            worksheet.update_cell(sheet_row, status_col + 1, 'failed')
            failed += 1
            print(f"    ✗ {status_text}")
        
        # Small delay to avoid rate limits
        time.sleep(1)
    
    return posted, failed


def run_post():
    """Main posting function — reads all tabs and posts approved content."""
    print(f"\n{'='*60}")
    print(f"AUTOPOSTER — Zernio Engine")
    print(f"Date: {get_today_str()} ET")
    print(f"{'='*60}\n")
    
    sheet = get_sheet()
    
    total_posted = 0
    total_failed = 0
    
    for tab_name, account_config in ACCOUNTS.items():
        print(f"\n--- {tab_name} ({account_config['username']}) ---")
        posted, failed = post_from_sheet(sheet, tab_name, account_config)
        total_posted += posted
        total_failed += failed
        print(f"  Results: {posted} posted, {failed} failed")
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_posted} posted, {total_failed} failed")
    print(f"{'='*60}\n")
    
    if total_failed > 0:
        sys.exit(1)


# ============================================================
# THREAD POSTING (Wednesday)
# ============================================================

def post_thread_to_zernio(tweets, account_id):
    """
    Post a thread (list of tweet strings) via Zernio.
    Zernio's thread support: post first tweet, then reply chain.
    Falls back to individual posts if thread API isn't available.
    """
    # For now, post as individual tweets with slight delays
    # Zernio may support native threads — check their docs
    results = []
    for i, tweet in enumerate(tweets):
        success, data, status_text = post_to_zernio(
            content=tweet,
            account_id=account_id
        )
        results.append((success, status_text))
        if i < len(tweets) - 1:
            time.sleep(3)  # Delay between thread tweets
    return results


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'post'
    
    if action == 'post':
        run_post()
    elif action == 'test':
        # Quick test: post one test tweet to each account
        print("Running test posts...")
        for tab_name, config in ACCOUNTS.items():
            success, data, status = post_to_zernio(
                content=f"System test from {config['username']} — {datetime.utcnow().isoformat()[:19]}",
                account_id=config['account_id']
            )
            print(f"  {config['username']}: {'✓' if success else '✗'} {status}")
    else:
        print(f"Unknown action: {action}")
        print("Usage: python3 post_all.py [post|test]")
        sys.exit(1)
