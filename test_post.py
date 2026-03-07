#!/usr/bin/env python3
"""
Quick test script - sends a single post to X via Upload Post API.
Run this to verify your Upload Post setup works before going fully automated.

Usage:
  python test_post.py YOUR_UPLOAD_POST_API_KEY YOUR_USER_PROFILE "Your tweet text here"

Example:
  python test_post.py eyJhbGci...DBZpCeq4 test "first automated post. the robots are here. 🤖"
"""

import sys
import requests
import json


def main():
    if len(sys.argv) < 3:
        print("Usage: python test_post.py <API_KEY> <USER_PROFILE> [TWEET_TEXT]")
        print("\nAPI_KEY = your Upload Post API key")
        print("USER_PROFILE = your Upload Post profile username (check dashboard)")
        print("TWEET_TEXT = optional custom tweet text")
        sys.exit(1)
    
    api_key = sys.argv[1]
    user = sys.argv[2]
    
    if len(sys.argv) > 3:
        text = " ".join(sys.argv[3:])
    else:
        text = "first automated post from the command line. the machines are learning. 🤖"
    
    print(f"\n📤 Posting to X via Upload Post API...")
    print(f"   User profile: {user}")
    print(f"   Tweet: {text}")
    print(f"   Length: {len(text)} chars\n")
    
    resp = requests.post(
        "https://api.upload-post.com/api/upload_text",
        headers={"Authorization": f"Apikey {api_key}"},
        data={
            "user": user,
            "platform[]": "x",
            "title": text,
        },
        timeout=30,
    )
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    
    if resp.status_code == 200:
        print("\n🎉 Post sent successfully! Check your X profile.")
    else:
        print(f"\n❌ Something went wrong. Check the response above.")
        print("\nCommon issues:")
        print("  - Wrong API key")
        print("  - Wrong user profile name")
        print("  - X/Twitter account not connected in Upload Post dashboard")
        print("  - Free tier limit reached (10/month)")


if __name__ == "__main__":
    main()
