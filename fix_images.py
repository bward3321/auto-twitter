#!/usr/bin/env python3
"""Quick fix: Switch EveryFreeTool images back to Seedream 4.5 and improve image prompts"""
import subprocess, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.run(["git", "pull", "origin", "main"], check=False)

# Fix sites_config.yaml — change lucid-origin to seedream-4.5
with open("sites_config.yaml", "r") as f:
    content = f.read()

content = content.replace('image_model: "lucid-origin"', 'image_model: "seedream-4.5"')
content = content.replace("image_model: lucid-origin", "image_model: seedream-4.5")

with open("sites_config.yaml", "w") as f:
    f.write(content)
print("✅ sites_config.yaml: Switched EveryFreeTool to Seedream 4.5")

# Fix post_all.py — change lucid-origin fallback to seedream-4.5
with open("post_all.py", "r") as f:
    content = f.read()

content = content.replace('"lucid-origin" if tab_name == "EveryFreeTool"', '"seedream-4.5" if tab_name == "EveryFreeTool"')

with open("post_all.py", "w") as f:
    f.write(content)
print("✅ post_all.py: Switched image model fallback to Seedream 4.5")

# Fix generate_all.py — update image prompt instructions to avoid text-heavy graphics
with open("generate_all.py", "r") as f:
    content = f.read()

old_prompt = "Image prompts should describe vibrant, eye-catching visuals"
new_prompt = """Image prompts should describe vibrant, eye-catching visuals — think bold colors, clean abstract designs, metaphorical illustrations.
IMPORTANT FOR IMAGE PROMPTS: Do NOT describe infographics, charts, screenshots, or anything with text/numbers/data in it. AI image generators cannot render readable text. Instead describe:
- Abstract metaphorical scenes (e.g. 'a chain breaking free from a subscription price tag, vibrant colors, minimal style')
- Tool-related objects in creative compositions (e.g. 'a glowing PDF icon floating above a desk, neon style, dark background')
- Conceptual illustrations (e.g. 'a person smashing a piggy bank labeled SaaS, coins flying, pop art style')
- Bold graphic designs with shapes and colors, NO text or numbers"""

content = content.replace(old_prompt, new_prompt)

with open("generate_all.py", "w") as f:
    f.write(content)
print("✅ generate_all.py: Updated image prompts to avoid text-heavy graphics")

# Push
subprocess.run(["git", "add", "-A"], check=True)
result = subprocess.run(
    ["git", "commit", "-m", "fix: switch EFT to Seedream 4.5, fix image prompts to avoid text"],
    capture_output=True, text=True
)
if result.returncode == 0:
    push = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if push.returncode == 0:
        print("✅ Pushed to GitHub")
    else:
        print(f"❌ Push failed: {push.stderr}")
else:
    print(f"⚠️  {result.stderr}")

print("\n🎉 Done! Now clear the EveryFreeTool tab in your Sheet and re-run generate from GitHub Actions.")
