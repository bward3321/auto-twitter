#!/usr/bin/env python3
"""
Quick fix: Switch to Nano Banana 2, fix upload_text endpoint, push to GitHub.
Run from inside your auto-twitter repo folder.
"""
import subprocess, os

REPO = os.path.expanduser("~/Downloads/twitter-autoposter")
if os.path.exists(REPO):
    os.chdir(REPO)
else:
    print("Trying current directory...")

subprocess.run(["git", "pull", "origin", "main"], check=False)

# --- Fix post_all.py: use /api/upload_text for text posts ---
with open("post_all.py", "r") as f:
    content = f.read()

# Fix the text post endpoint
content = content.replace('/api/upload"', '/api/upload_text"')
content = content.replace("UPLOAD_POST_BASE}/upload\"", "UPLOAD_POST_BASE}/upload_text\"")

# Also change seedream references to nano-banana-2
content = content.replace('"seedream-4.5"', '"nano-banana-2"')

with open("post_all.py", "w") as f:
    f.write(content)
print("✅ post_all.py: Fixed text endpoint + Nano Banana 2")

# --- Fix generate_all.py: switch all image models to nano-banana-2 ---
with open("generate_all.py", "r") as f:
    content = f.read()

content = content.replace('"seedream-4.5"', '"nano-banana-2"')

with open("generate_all.py", "w") as f:
    f.write(content)
print("✅ generate_all.py: Switched to Nano Banana 2")

# --- Fix sites_config.yaml ---
with open("sites_config.yaml", "r") as f:
    content = f.read()

content = content.replace('image_model: "seedream-4.5"', 'image_model: "nano-banana-2"')
content = content.replace("image_model: seedream-4.5", "image_model: nano-banana-2")

with open("sites_config.yaml", "w") as f:
    f.write(content)
print("✅ sites_config.yaml: Switched to Nano Banana 2")

# --- Push ---
subprocess.run(["git", "add", "-A"], check=True)
result = subprocess.run(
    ["git", "commit", "-m", "fix: use upload_text endpoint, switch to Nano Banana 2"],
    capture_output=True, text=True
)
if result.returncode == 0:
    push = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if push.returncode == 0:
        print("✅ Pushed to GitHub")
    else:
        print(f"❌ Push failed: {push.stderr}")
else:
    print(f"⚠️ {result.stderr}")

print("\n🎉 Done! Now:")
print("1. Change all 'failed' rows back to 'approved' in your Sheet")
print("2. Go to GitHub → Actions → Run workflow → post → run it")
