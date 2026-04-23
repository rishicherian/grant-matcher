import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the client for Mistral
mistral_client = OpenAI(
    base_url=os.environ.get("MISTRAL_BASE_URL"),
    api_key=os.environ.get("MISTRAL_API_KEY")
)

def rank_and_explain(user_query, eligible_grants):
    """
    Takes a list of eligible grants and uses Mistral to rank them by relevance
    and provide a 2-3 sentence explanation for why they are a good match.
    """
    if not eligible_grants:
        return []

    print("Ranking eligible grants and generating explanations...\n")

    # Format the grants into a readable string for Mistral
    grants_context = ""
    for i, grant in enumerate(eligible_grants):
        title = grant.get("metadata", {}).get("grant_title", f"Grant {i+1}")
        summary = grant.get("summary_text", "")
        grants_context += f"--- Grant {i+1}: {title} ---\n{summary}\n\n"

    system_prompt = """
    You are an expert grant-matching advisor. You will be provided with a user's project proposal and a list of eligible grants.
    
    Your task:
    1. Evaluate how well each grant aligns with the user's specific project goals.
    2. Rank the grants from best match to worst match.
    3. Write a concise, 2-3 sentence explanation for EACH grant detailing exactly why it is a strong match for the user's project.
    
    Return the results strictly as a JSON array of objects. Each object must have:
    - "grant_title" (string)
    - "rank" (integer)
    - "explanation" (string)
    """

    user_prompt = f"User Project Proposal:\n{user_query}\n\nEligible Grants:\n{grants_context}"

    try:
        response = mistral_client.chat.completions.create(
            model="mistral-small-latest", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3 
        )
        
        # Parse the JSON response
        result_text = response.choices[0].message.content
        
        # Sometimes the model wraps the array in a root object like {"ranked_grants": [...]}, so this handles both
        parsed_result = json.loads(result_text)
        
        if isinstance(parsed_result, dict):
            # Extract the list from the dictionary regardless of the key name
            for key, value in parsed_result.items():
                if isinstance(value, list):
                    return value
            return [parsed_result]
        
        return parsed_result

    except Exception as e:
        print(f"Error during ranking: {e}")
        return []