import os
import chromadb

def search_grant_database(query, n_results=3):
    print(f"Searching database for: '{query}'...\n")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    base_dir = os.path.dirname(current_dir)
    db_path = os.path.join(base_dir, "data", "chroma_db")
    
    client = chromadb.PersistentClient(path=db_path)
    
    try:
        collection = client.get_collection(name="grant_opportunities")
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                grant = {
                    "id": results['ids'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "summary_text": results['documents'][0][i]
                }
                formatted_results.append(grant)
                
        return formatted_results
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        return []

if __name__ == "__main__":
    test_query = "funding for public art projects or murals in Philadelphia"
    matches = search_grant_database(test_query)
    
    if matches:
        for match in matches:
            title = match['metadata'].get('grant_title', 'Unknown Title')
            amount = match['metadata'].get('funding_amount', 'Unknown Amount')
            print(f"Found Match: {title} - {amount}")
    else:
        print("No matches found.")