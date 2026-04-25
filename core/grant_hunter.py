import time
import uuid
import os
from ddgs import DDGS
from scraper import fetch_grant_markdown

def hunt_for_grants(queries, max_results_per_query=10):
    print("--- Starting the Automated Grant Hunt ---\n")
    discovered_urls = []
    
    # 1. Establish the memory file
    tracker_file = "data/seen_urls.txt"
    os.makedirs("data", exist_ok=True)
    
    # 2. Load the history of URLs we've already scraped
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
                    
                    # 3. Check if the URL is completely new
                    if url and url not in discovered_urls and url not in previously_seen:
                        discovered_urls.append(url)
                        print(f"  -> NEW Grant Found: {url}")
                        
                        # Save it to permanent memory immediately
                        with open(tracker_file, "a") as f:
                            f.write(url + "\n")
                            
                    elif url in previously_seen:
                        print(f"  -> Skipped (Already in database): {url}")
                        
                time.sleep(2)
            except Exception as e:
                print(f"Error searching for '{query}': {e}")

    return discovered_urls

if __name__ == "__main__":
    search_queries = [
        # Pennsylvania
        "Philadelphia PA local community and non-profit grants"
        "Pittsburgh PA local community development grants",
        "Erie Pennsylvania non-profit youth funding",
        "Allentown PA arts and culture grant application",
        "Harrisburg PA local environmental funding",
        "PA scientific research grant opportunities for Univeristy of Pennsylvania, Temple University, Drexel University, Carnegie Mellon Univeristy, The Pennsylvania State University, University of Pittsburgh, Lehigh University, University of Delaware, Villanova University, Bucknell University, Lafayette College, Swarthmore College, Bryn Mawr College, Haverford College, Franklin & Marshall College, Gettysburg College, Dickinson College, Juniata College, Susquehanna University, Albright College, Elizabethtown College, Messiah University, Arcadia University, etc.",
        
        # New York
        "New York City NY local community foundation grants",
        "Albany NY public health initiative grants",
        "Binghamton New York education non-profit funding",
        "Long Island NY community wellness grant",
        "Westchester County NY local arts grants",
        
        # New Jersey
        "Newark NJ community development funding opportunities",
        "Jersey City NJ after-school program grants",
        "Camden New Jersey urban development funding",
        "Hoboken NJ environmental conservation application",
        
        # Massachusetts
        "Boston MA local community foundation grants",
        "Springfield MA STEM education grant guidelines",
        "Cambridge Massachusetts local arts foundation",
        "Lowell MA community youth program funding",
        
        # Connecticut
        "Hartford CT public health non-profit funding",
        "New Haven Connecticut arts and culture grants",
        "Bridgeport CT environmental project funding",
        
        # Rhode Island
        "Newport RI local community foundation grants",
        "Warwick Rhode Island youth education funding",
        
        # Maryland & Delaware
        "Annapolis MD local conservation grants",
        "Frederick Maryland STEM education application",
        "Dover Delaware community arts funding",
        
        # Northern New England
        "Augusta Maine rural development grant",
        "Manchester NH public health funding opportunities",
        "Montpelier Vermont sustainability grant guidelines"
    ]
    
    # Bump the results per query up to 7
    urls = hunt_for_grants(search_queries, max_results_per_query=7)
    
    urls = hunt_for_grants(search_queries, max_results_per_query=5)
    
    print("\n" + "="*50)
    print(f"Total unique grant URLs discovered: {len(urls)}")
    print("="*50)
    
    # --- UPDATED HANDOFF ---
    print("\nBeginning data ingestion...")
    for url in urls: # Removed the enumerate(urls)
        
        # Generate a random 8-character ID for a truly unique filename
        unique_id = uuid.uuid4().hex[:8]
        filename = f"grant_{unique_id}" 
        
        try:
            success = fetch_grant_markdown(url, filename)
            if success:
                time.sleep(2) 
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")