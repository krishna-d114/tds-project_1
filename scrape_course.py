from playwright.sync_api import sync_playwright
import requests
from urllib.parse import urljoin
import os
import time

BASE_URL = "https://tds.s-anand.net/#/2025-01/"
MD_BASE_URL = "https://tds.s-anand.net/"
OUTPUT_DIR = "data/course_markdown"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_md_links_with_playwright():
    md_links = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(5)  # Ensure content fully loads

        links = page.query_selector_all("aside.sidebar a[href^='#/']")
        for link in links:
            href = link.get_attribute("href")
            if href:
                md_filename = href[2:] + ".md"  # Remove "#/" and add ".md"
                if md_filename not in md_links:
                    md_links.append(md_filename)

        browser.close()
    return md_links

def download_md_file(md_filename):
    md_url = urljoin(MD_BASE_URL, md_filename)
    response = requests.get(md_url)
    if response.status_code == 200:
        # FORCE save to OUTPUT_DIR
        filename_only = os.path.basename(md_filename)
        file_path = os.path.join(OUTPUT_DIR, filename_only)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Downloaded: {md_url} → {file_path}")
    else:
        print(f"Failed to download: {md_url} | Status code: {response.status_code}")

if __name__ == "__main__":
    print("Extracting .md links from Docsify sidebar using Playwright...")
    md_files = extract_md_links_with_playwright()
    print(f"Found {len(md_files)} Markdown files.")

    for md_file in md_files:
        download_md_file(md_file)

    print(f"✅ All Markdown files downloaded to: {OUTPUT_DIR}")
