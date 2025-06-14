import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from datetime import timezone
import sys

# Force UTF-8 encoding for stdout on all platforms (Python 3.7+)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    
COOKIE = "_t=I%2B0SgdzTY9QCybEVKgrbSDUdnPMuGm1KULaSccc1ADvmJHskStEN5aRKUTKgDvYMh8BWyQJS4NjfQjOoKCSH5vlw8sOMvx1U35jy1oY5TR9TLrqkORTZ3iHPq%2FiqVJUIolOGcAqSb3aVFYJoJIZea%2BWoctXG4ryPwnRod26Iuq3e4mGH7lfC7AEWb9Hn3qLz4Ibn1qgzQgAFS7%2BuP2y%2FpDdeUib8BtGvNaJKipyDNrFcniEHA1mkSS%2FIRdQHBV8Dwzyqn8krRmmivKOjSlEPv%2FDrv4STAhNh4gJ9i4GW4vWZuGevdg4tnXuKNLkyh4s8--p7cXbwPUewkXjIeK--4K6jS47eNhAmWizkCuZgFQ%3D%3D"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": COOKIE
}

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
TDS_CATEGORY_URL = f"{BASE_URL}/c/courses/tds-kb/34"

# DATE RANGE CONFIGURATION
START_DATE = "2025-01-01"  # Format: YYYY-MM-DD
END_DATE = "2025-04-14"    # Format: YYYY-MM-DD

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

def get_topic_creation_date(topic_url):
    """Get the creation date of a topic by fetching its JSON"""
    try:
        response = requests.get(topic_url + ".json", headers=HEADERS)
        if response.status_code == 200:
            topic_json = response.json()
            return topic_json.get("created_at", "")
    except:
        pass
    return None

def scrape_tds_links():
    print(f"Scraping links for topics created between {START_DATE} and {END_DATE}")
    
    # You might need to scrape multiple pages to get all topics
    page = 0
    all_filtered_links = []
    
    while True:
        # Add page parameter to URL
        page_url = f"{TDS_CATEGORY_URL}?page={page}" if page > 0 else TDS_CATEGORY_URL
        
        response = requests.get(page_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch page {page}")
            break
            
        soup = BeautifulSoup(response.text, "html.parser")
        topics = soup.find_all("a", class_="title raw-link raw-topic-link")
        
        if not topics:
            print(f"No more topics found on page {page}")
            break
        
        print(f"Processing page {page} - found {len(topics)} topics")
        
        page_filtered_links = []
        
        for topic in topics:
            url = topic['href']
            
            # Build full URL
            if url.startswith("/"):
                full_url = BASE_URL + url
            else:
                full_url = url
            
            # Get topic creation date
            creation_date = get_topic_creation_date(full_url)
            
            if creation_date and is_within_date_range(creation_date, START_DATE, END_DATE):
                page_filtered_links.append(url)
                print(f"Added: {topic.get_text().strip()}")
            else:
                print(f"Skipped: {topic.get_text().strip()} (outside date range)")
            
            # Small delay to be respectful
            time.sleep(0.5)
        
        all_filtered_links.extend(page_filtered_links)
        
        # If no links were added from this page, we might be outside our date range
        if not page_filtered_links and page > 0:
            print("No topics in date range found on this page, stopping...")
            break
        
        page += 1
        
        # Safety limit to prevent infinite loops
        if page > 50:
            print("Reached page limit, stopping...")
            break
    
    # Save filtered links
    with open("data/tds_links.txt", "w", encoding="utf-8") as f:
        for url in all_filtered_links:
            f.write(url + "\n")
    
    print(f"\nCompleted! Found {len(all_filtered_links)} topics in the specified date range.")
    print(f"Links saved to data/tds_links.txt")

if __name__ == "__main__":
    scrape_tds_links()