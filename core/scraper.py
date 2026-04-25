import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import os

def fetch_grant_markdown(url, filename):
    """Fetches a URL, extracts the main text, and saves it as Markdown."""
    print(f"Fetching {url}...")
    try:
        # Standard headers 
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the main content area
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        if not main_content:
            print("Could not find main content.")
            return False

        # Convert the HTML to Markdown
        raw_markdown = md(str(main_content), strip=['a', 'img'])
        
        # Clean up excess whitespace
        clean_markdown = '\n'.join([line.strip() for line in raw_markdown.splitlines() if line.strip()])

        os.makedirs(os.path.join("data", "raw_markdown"), exist_ok=True)

        # Save to data folder
        filepath = os.path.join("data", "raw_markdown", f"{filename}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(clean_markdown)
            
        print(f"Success! Saved to {filepath}")
        return True

    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return False

if __name__ == "__main__":
    urls_to_scrape = {
        "The Catalyst Fund": "https://www.phila.gov/programs/the-catalyst-fund/",
        "NFS Business Assistance Grant": "https://phila-uyims.formstack.com/forms/business_assistance_grant",
        "NFS Beautification Grant": "https://phila-uyims.formstack.com/forms/nfs_beautification_grant",
        "NFS Non-Profit Capital Grant": "https://phila-uyims.formstack.com/forms/nfs_nonprofitcapital_grant",
        "The Community Fund": "https://philacityfund.org/grantmaking/community-fund/",
        "Henrietta Tower Wurts Memorial Grant": "https://www.philafound.org/nonprofits/available-grants/henrietta-tower-wurts/",
        "Black Community Leaders Grants": "http://philafound.org/nonprofits/available-grants/special-initiative-grants/black-community-leaders/",
        "GSK Impact Awards for Greater Philadelphia": "https://www.philafound.org/nonprofits/available-grants/special-initiative-grants/gsk-impact-awards/",
        "District Attorney's Office Forfeiture Fund": "https://www.philafound.org/nonprofits/available-grants/special-initiative-grants/dao/",
        "West Philadelphia Creative Grants": "https://paulrobesonhouse.org/west-philadelphia-creative-grants/",
        "Creative Entrepreneur Accelerator Program": "https://www.philaculture.org/CEA",
        "Art Works": "https://www.philafound.org/nonprofits/available-grants/special-initiative-grants/art-works/",
        "Edna W. Andrade Grants": "https://www.philafound.org/nonprofits/available-grants/special-initiative-grants/edna-w-andrade-grants/",
        "Forman Family Fund Grants": "https://www.philafound.org/nonprofits/available-grants/special-initiative-grants/forman-family-fund-grants/",
        "William Penn Foundation Grants": "https://williampennfoundation.org/program/arts-and-culture",

    }
    
    for name, url in urls_to_scrape.items():
        fetch_grant_markdown(url, name)