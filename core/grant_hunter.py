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
    search_queries = [
        # --- PENNSYLVANIA ---
        # Urban & Tech
        "Philadelphia PA tech equity and digital inclusion grants",
        "Pittsburgh PA manufacturing, robotics, and workforce development funding",
        "Philadelphia PA civic tech and smart city initiative grants",
        # Community & Health
        "Allentown PA affordable housing and homelessness initiatives",
        "Reading PA youth literacy and bilingual education funding",
        "Lancaster PA sustainable agriculture and rural farming grants",
        # History & Environment
        "Scranton PA historical preservation and downtown revitalization grants",
        "Erie PA Great Lakes environmental conservation and water quality grants",
        "Bethlehem PA local performing arts and cultural heritage foundation",
        # Academic
        "Pennsylvania scientific research grant opportunities higher education universities",

        # --- NEW YORK ---
        # NYC specific
        "Brooklyn NY affordable housing development and tenant rights grants",
        "Bronx NY food desert, nutrition, and urban agriculture funding",
        "Queens NY immigrant and refugee support services grants",
        # Upstate & Long Island
        "Buffalo NY rust belt economic revitalization and small business grants",
        "Rochester NY photonics, optics, and STEM research grants",
        "Syracuse NY veteran support and reintegration funding",
        "Ithaca NY clean energy, solar, and climate resilience grants",
        "Hudson Valley NY land trust and forest conservation grants",
        "Long Island NY coastal erosion and marine biology grants",

        # --- NEW JERSEY ---
        "Newark NJ civic tech, education reform, and youth empowerment grants",
        "Camden NJ maternal health and infant mortality reduction grants",
        "Trenton NJ criminal justice reform and reentry program funding",
        "Jersey City NJ after-school STEM and arts program grants",
        "Atlantic City NJ hospitality workforce retraining and economic grants",
        "Paterson NJ historic mill preservation and urban renewal funding",
        "Princeton NJ academic fellowships and humanities research foundation",

        # --- MASSACHUSETTS ---
        "Boston MA life sciences, biotech, and medical research startup grants",
        "Worcester MA opioid addiction recovery and public health prevention funding",
        "Springfield MA early childhood education and childcare grants",
        "Cambridge MA AI for social good and tech ethics funding",
        "New Bedford MA offshore wind and maritime innovation grants",
        "Lowell MA textile arts, history, and cultural heritage grants",

        # --- CONNECTICUT ---
        "New Haven CT biotech research and medical innovation foundation grants",
        "Hartford CT public transportation and urban mobility funding",
        "Bridgeport CT brownfield remediation and environmental cleanup grants",
        "Stamford CT corporate social responsibility community grants",
        "Waterbury CT senior care, aging in place, and elderly support grants",

        # --- RHODE ISLAND ---
        "Providence RI culinary arts and food entrepreneurship grants",
        "Newport RI maritime history and youth sailing program funding",
        "Pawtucket RI arts district infrastructure and creative economy grants",
        "Cranston RI disability advocacy and accessible infrastructure grants",

        # --- NORTHERN NEW ENGLAND (VT, NH, ME) ---
        "Burlington VT sustainable forestry and renewable energy grants",
        "Portland ME aquaculture and sustainable fisheries funding",
        "Manchester NH rural broadband access and telehealth community grants",
        "Bangor ME indigenous and tribal community support grants",
        "Brattleboro VT local food systems and farmers market funding",
        "Augusta ME rural healthcare clinic and nursing grants",

        # --- MARYLAND & DELAWARE ---
        "Baltimore MD youth violence prevention and mentorship program grants",
        "Wilmington DE financial literacy and minority-owned business grants",
        "Annapolis MD Chesapeake Bay water quality and ecosystem restoration grants",
        "Dover DE special education and neurodiversity advocacy funding",
        "Bethesda MD independent biomedical research foundation funding"
    ]
    
    urls = hunt_for_grants(search_queries, max_results_per_query=7)
        
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