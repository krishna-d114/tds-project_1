import requests
import json
import time
from datetime import datetime
from urllib.parse import urlencode
from datetime import timezone
import sys
sys.stdout.reconfigure(encoding='utf-8')
# STEP 1: Paste your _t cookie here after logging in manually
COOKIE = "_t=kUNYZ%2Fx4P%2BMT%2BZUZ8q2cAAOoywEwJ3JSYm5t4Afn%2BfIOhzQ%2F5sYl5WhNQYS5zDGx0ZPGU%2FiKqTdrlLE%2ByleiMCjGLINv%2FJUUNPAqSeV%2Byu%2B8CvbdFUkXQK34iwNcYO5R2XzxA6P1w8nSVFeSyZoixKqsKhd1hJr8JvHZMNlsUQFT3dDM6xBuCfhDvnVJhNs3Fd%2B1ld6n5cNXyrJS7u1s2bTKSmrAPsXpBKqaRzEv%2B8ScdRz1V7fRyQW5bfW58v177NSzWrYu5LxJFzFsA88MWXHsgTEPPC0%2FhX0F5a6G7%2BEDpM011gc2L11ITXVeSrFz--gBMpF5SR3LrFrp4B--uDs0qfTDYyUhVrZoRRPDnQ%3D%3D"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": COOKIE
}

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"

# DATE RANGE CONFIGURATION
START_DATE = "2025-01-01"  # Format: YYYY-MM-DD
END_DATE = "2025-04-14"    # Format: YYYY-MM-DD

# Files
LINKS_FILE = "data/tds_links.txt"
OUTPUT_FILE = "data/discourse_posts.json"

def parse_date(date_str):
    """Parse ISO date string to datetime object"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return None

def is_within_date_range(post_date_str, start_date, end_date):
    """Check if post date is within the specified range"""
    post_date = parse_date(post_date_str)
    if not post_date:
        return False

    start_dt = datetime.fromisoformat(start_date + "T00:00:00").replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_date + "T23:59:59").replace(tzinfo=timezone.utc)

    return start_dt <= post_date <= end_dt

def get_full_topic(topic_url):
    response = requests.get(topic_url + ".json", headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch topic: {response.status_code} {topic_url}")
        return None
    
    topic_json = response.json()
    topic_title = topic_json.get("title", "")
    topic_slug = topic_json.get("slug", "")
    topic_id = topic_json.get("id", "")
    topic_full_url = f"{BASE_URL}/t/{topic_slug}/{topic_id}"
    
    # Check if topic creation date is within range
    topic_created = topic_json.get("created_at", "")
    if not is_within_date_range(topic_created, START_DATE, END_DATE):
        print(f"Topic created outside date range: {topic_title}")
        return None
    
    posts = []
    for post in topic_json.get("post_stream", {}).get("posts", []):
        post_date = post.get("created_at", "")
        
        # Only include posts within the date range
        if is_within_date_range(post_date, START_DATE, END_DATE):
            posts.append({
                "author": post.get("username", ""),
                "date": post_date,
                "content": post.get("cooked", "").replace('<p>', '').replace('</p>', '').strip()
            })
    
    # Only return topic if it has posts in the date range
    if posts:
        return {
            "title": topic_title,
            "url": topic_full_url,
            "created_at": topic_created,
            "posts": posts
        }
    
    return None

def main():
    print(f"Scraping posts from {START_DATE} to {END_DATE}")
    
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        topic_urls = [line.strip() for line in f if line.strip()]
    
    all_topics = []
    processed = 0
    
    for url in topic_urls:
        if url.startswith("/"):
            full_topic_url = BASE_URL + url
        elif url.startswith("http"):
            full_topic_url = url
        else:
            full_topic_url = BASE_URL + "/" + url
        
        try:
            print(f"Scraping: {full_topic_url}")
            topic_data = get_full_topic(full_topic_url)
            if topic_data:
                all_topics.append(topic_data)
                print(f"Found {len(topic_data['posts'])} posts in date range")
            else:
                print(f"No posts in date range")
                
            processed += 1
            if processed % 10 == 0:
                print(f"Processed {processed}/{len(topic_urls)} topics")
                
        except Exception as e:
            print(f"Error fetching {full_topic_url}: {e}")
        
        # Be polite to the server
        time.sleep(1)
    
    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_topics, f, indent=2, ensure_ascii=False)
    
    print(f"\nCompleted! Found {len(all_topics)} topics with posts in date range.")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()