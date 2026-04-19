import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("MISTRAL_BASE_URL"),
    api_key=os.environ.get("MISTRAL_API_KEY")
)

def clean_json_string(raw_string):
    """Removes markdown code blocks if the model accidentally includes them."""
    cleaned = re.sub(r'^```json\s*', '', raw_string, flags=re.IGNORECASE)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned.strip()

def extract_grant_data(markdown_text):
    system_prompt = """
    You are a precise data extraction assistant. Extract the following fields from the grant text:
    - grant_title (string)
    - funding_amount (number or null)
    - deadline (string or null)
    - eligible_applicant_type (list of strings)
    - geographic_restrictions (string)
    - project_area (string)
    - demographic_requirements (string)
    - eligibility_summary (string)
    
    Return ONLY valid JSON matching these exact keys. Do not include any other text.
    """
    
    try:
        response = client.chat.completions.create(
            # IMPORTANT: Check your API documentation to ensure this exact string is correct!
            model="mistral-small-latest", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this grant data:\n\n{markdown_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_output = response.choices[0].message.content
        clean_output = clean_json_string(raw_output)
        return json.loads(clean_output)
        
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        print(f"Raw Model Output was:\n{raw_output}")
        return None
    except Exception as e:
        print(f"API Error during extraction: {e}")
        return None

def process_all_markdown_files():
    input_dir = "data/raw_markdown"
    output_dir = "data/processed_json"
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")
            
            with open(filepath, "r", encoding="utf-8") as f:
                markdown_text = f.read()
                
            extracted_json = extract_grant_data(markdown_text)
            
            if extracted_json:
                output_filename = filename.replace(".md", ".json")
                output_filepath = os.path.join(output_dir, output_filename)
                
                with open(output_filepath, "w", encoding="utf-8") as out_f:
                    json.dump(extracted_json, out_f, indent=4)
                print(f"Successfully saved {output_filename}\n")
            else:
                print(f"Failed to extract data for {filename}\n")

if __name__ == "__main__":
    process_all_markdown_files()