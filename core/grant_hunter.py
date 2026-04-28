import time
import uuid
import os
from ddgs import DDGS
from scraper import fetch_grant_markdown

def hunt_for_grants(queries, max_results_per_query=10):
    print("--- Starting the Automated Grant Hunt ---\n")
    discovered_urls = []
    
    tracker_file = "data/seen_urls.txt"
    os.makedirs("data", exist_ok=True)
    
    previously_seen = set()
    if os.path.exists(tracker_file):
        with open(tracker_file, "r") as f:
            previously_seen = set(f.read().splitlines())

    with DDGS() as ddgs:
        for query in queries:
            print(f"Searching for: '{query}'...")
            try:
                results = ddgs.text(query, max_results=max_results_per_query)
                for result in results:
                    url = result.get('href')

                    blacklist = ['/news', '/blog', 'article', 'press', 'wikipedia.org', 'medium.com', 'yahoo.com', 'forbes.com', 'bloomberg.com', 'patch.com']
                    if url and any(bad_word in url.lower() for bad_word in blacklist):
                        print(f"  -> Bypassing Blacklisted URL: {url}")
                        continue
                    
                    if url and url not in discovered_urls and url not in previously_seen:
                        discovered_urls.append(url)
                        print(f"  -> NEW Grant Found: {url}")
                        
                        with open(tracker_file, "a") as f:
                            f.write(url + "\n")
                            
                    elif url in previously_seen:
                        print(f"  -> Skipped (Already in database): {url}")
                        
                time.sleep(2)
            except Exception as e:
                print(f"Error searching for '{query}': {e}")

    return discovered_urls

if __name__ == "__main__":
    dork_suffix = 'grant (apply OR application OR guidelines OR deadline OR "request for proposals" OR rfp) -news -press -site:wikipedia.org'

    industries = [
        "arts and culture",
        "education and youth development",
        "health and wellness",
        "community development and affordable housing",
        "environmental conservation and sustainability",
        "small business and economic development",
        "scientific and medical research",
        "food security and agriculture",
        "social services and nonprofit",
        "technology and digital inclusion"
    ]

    locations = [
        # Pennsylvania
        '"Pennsylvania"', '"Philadelphia" "Pennsylvania"', '"Pittsburgh" "Pennsylvania"', '"Harrisburg" "Pennsylvania"',
        # New York
        '"New York State"', '"New York City"', '"Buffalo" "New York"', '"Rochester" "New York"',
        # New Jersey
        '"New Jersey"', '"Newark" "New Jersey"', '"Camden" "New Jersey"',
        # Massachusetts
        '"Massachusetts"', '"Boston" "Massachusetts"', '"Worcester" "Massachusetts"',
        # Connecticut & Rhode Island
        '"Connecticut"', '"New Haven" "Connecticut"', '"Hartford" "Connecticut"',
        '"Rhode Island"', '"Providence" "Rhode Island"',
        # Northern New England
        '"Vermont"', '"Burlington" "Vermont"',
        '"New Hampshire"', '"Manchester" "New Hampshire"',
        '"Maine"', '"Portland" "Maine"',
        # Maryland & Delaware
        '"Maryland"', '"Baltimore" "Maryland"',
        '"Delaware"', '"Wilmington" "Delaware"'
    ]

    search_queries = []
    for loc in locations:
        for ind in industries:
            search_queries.append(f"{loc} {ind} {dork_suffix}")
    
    print(f"Generated {len(search_queries)} total universal queries. Starting hunt...")
    
    urls = hunt_for_grants(search_queries, max_results_per_query=5)
    
    print("\n" + "="*50)
    print(f"Total unique grant URLs discovered: {len(urls)}")
    print("="*50)
    
    print("\nBeginning data ingestion...")
    for url in urls:
        unique_id = uuid.uuid4().hex[:8]
        filename = f"grant_{unique_id}" 
        
        try:
            success = fetch_grant_markdown(url, filename)
            if success:
                time.sleep(2) 
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")