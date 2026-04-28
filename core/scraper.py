import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import os

def fetch_grant_markdown(url, filename):
    """Fetches a URL, extracts the main text, and saves it as Markdown."""
    print(f"Fetching {url}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        if not main_content:
            print("Could not find main content.")
            return False

        raw_markdown = md(str(main_content), strip=['a', 'img'])
        
        clean_markdown = '\n'.join([line.strip() for line in raw_markdown.splitlines() if line.strip()])

        os.makedirs(os.path.join("data", "raw_markdown"), exist_ok=True)

        filepath = os.path.join("data", "raw_markdown", f"{filename}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(clean_markdown)
            
        print(f"Success! Saved to {filepath}")
        return True

    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return False