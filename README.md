# 🤖 Twitter/X Autoposter

Automated content generation and posting system for X/Twitter.

## How It Works

1. **Weekly (Sunday):** Claude generates 28 posts → writes to Google Sheet
2. **You review:** Open the Sheet, change status to "approved" (or edit content)
3. **Daily (every morning):** Script reads today's approved posts → posts via Upload Post API

## Stack
- **Claude API** → generates all tweet content
- **Leonardo.ai** → generates images for image posts  
- **Upload Post API** → posts/schedules to X/Twitter
- **Google Sheets** → review & approval layer
- **GitHub Actions** → runs the crons

## Setup

### 1. Google Sheets API (5 min)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable **Google Sheets API** (APIs & Services → Library → search "Google Sheets API" → Enable)
4. Create Service Account (APIs & Services → Credentials → Create Credentials → Service Account)
5. Create a key for the service account (JSON format) → downloads a `.json` file
6. Create a new Google Sheet → copy the Sheet ID from the URL (`docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`)
7. Share the Sheet with the service account email (it looks like `name@project.iam.gserviceaccount.com`)

### 2. GitHub Repo
```bash
cd twitter-autoposter
git init
git add .
git commit -m "initial commit"
gh repo create bward3321/twitter-autoposter --private --source=. --push
```

### 3. GitHub Secrets
Settings → Secrets → Actions → add these:

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `UPLOAD_POST_API_KEY` | Your Upload Post key |
| `UPLOAD_POST_USER` | `@brendanwardai` |
| `GOOGLE_SHEET_ID` | Sheet ID from URL |
| `GOOGLE_SHEETS_CREDS` | Entire contents of the service account JSON file |
| `LEONARDO_API_KEY` | Leonardo.ai API key (optional) |

### 4. Local Testing
```bash
pip install -r requirements.txt

# Generate posts to sheet
ANTHROPIC_API_KEY=xxx GOOGLE_SHEET_ID=xxx python generate_to_sheet.py

# Post approved content
UPLOAD_POST_API_KEY=xxx UPLOAD_POST_USER=@brendanwardai GOOGLE_SHEET_ID=xxx python post_from_sheet.py
```

## Files
- `generate_to_sheet.py` - Weekly: generate posts → Google Sheet
- `post_from_sheet.py` - Daily: approved posts → X/Twitter
- `topics.yaml` - What to post about + voice guidelines
- `config.yaml` - Schedule settings
- `autoposter.py` - Original direct-post mode (no sheet review)
- `test_post.py` - Quick test script
