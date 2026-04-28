import os
import json
import chromadb

def build_vector_db():
    print("Initializing ChromaDB...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    
    db_path = os.path.join(base_dir, "data", "chroma_db")
    json_dir = os.path.join(base_dir, "data", "processed_json")
    
    client = chromadb.PersistentClient(path=db_path)
    collection_name = "grant_opportunities"
    
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
        
    collection = client.create_collection(name=collection_name)
    
    documents = []
    metadatas = []
    ids = []
    
    print(f"Reading processed JSON files from {json_dir}...")
    
    if not os.path.exists(json_dir):
        print(f"Error: Could not find the directory {json_dir}")
        return
        
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(json_dir, filename)
            
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    grant_data = json.load(f)
                    
                    if isinstance(grant_data, list):
                        if len(grant_data) > 0:
                            grant_data = grant_data[0]
                        else:
                            print(f"Skipping {filename}: Empty list")
                            continue
                            
                except json.JSONDecodeError:
                    print(f"Skipping {filename}: Invalid JSON")
                    continue
                
            grant_id = filename.replace(".json", "")
            
            title = grant_data.get('grant_title', '')

            if not title or str(title).lower() in ["not specified", "null", "none", ""]:
                # Generate fallback title
                fallback_parts = []

                project_area = grant_data.get("project_area")
                if project_area and project_area != "Not specified":
                    fallback_parts.append(project_area.title())

                demographic = grant_data.get("demographic_requirements")
                if demographic and demographic != "Not specified":
                    fallback_parts.append(demographic.title())

                organization = grant_data.get("organization_name")
                if organization and organization != "Not specified":
                    fallback_parts.append(organization)

                if fallback_parts:
                    title = " / ".join(fallback_parts) + " Grant"
                else:
                    title = f"Grant Opportunity ({grant_id})"

                print(f"Generated fallback title for {filename}: {title}")
            
            searchable_text = f"Title: {title}\n"
            searchable_text += f"Project Area: {grant_data.get('project_area', '')}\n"
            searchable_text += f"Demographics: {grant_data.get('demographic_requirements', '')}\n"
            searchable_text += f"Eligibility: {grant_data.get('eligibility_summary', '')}"
            
            clean_metadata = {}
            for key, value in grant_data.items():
                if key == "grant_title":
                    clean_metadata[key] = title  # <-- force correct title
                    continue

                if value is None or value == "":
                    clean_metadata[key] = "Not specified"
                elif isinstance(value, list):
                    clean_metadata[key] = ", ".join(value)
                else:
                    clean_metadata[key] = str(value)
            
            documents.append(searchable_text)
            metadatas.append(clean_metadata)
            ids.append(grant_id)
            
    if documents:
        print(f"Embedding and storing {len(documents)} grants in the database...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print("Success! Database built successfully.")
    else:
        print("No valid JSON files found to process.")

if __name__ == "__main__":
    build_vector_db()