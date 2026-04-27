import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.environ.get("MISTRAL_BASE_URL")
LLM_API_KEY = os.environ.get("MISTRAL_API_KEY")
LLM_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

mistral_client = None
if LLM_BASE_URL and LLM_API_KEY:
    mistral_client = OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY
    )


def fallback_rank(eligible_grants):
    ranked = []
    for i, grant in enumerate(eligible_grants, start=1):
        title = grant.get("metadata", {}).get("grant_title", f"Grant {i}")
        summary = grant.get("summary_text", "")
        short_summary = summary[:180] + "..." if len(summary) > 180 else summary

        ranked.append({
            "grant_title": title,
            "rank": i,
            "explanation": (
                "This grant was kept as an eligible match based on your project and profile. "
                f"Summary: {short_summary}"
            )
        })
    return ranked


def rank_and_explain(user_query, eligible_grants):
    """
    Takes a list of eligible grants and uses Mistral to rank them by relevance
    and provide a 2-3 sentence explanation for why they are a good match.
    Falls back to the current order if the API call fails.
    """
    if not eligible_grants:
        return []

    print("Ranking eligible grants and generating explanations...\n")

    if mistral_client is None:
        print("Mistral client is not configured. Using fallback ranking.")
        return fallback_rank(eligible_grants)

    grants_context = ""
    for i, grant in enumerate(eligible_grants):
        title = grant.get("metadata", {}).get("grant_title", f"Grant {i+1}")
        summary = grant.get("summary_text", "")
        grants_context += f"--- Grant {i+1}: {title} ---\n{summary}\n\n"

    system_prompt = """
    You are an expert grant-matching advisor speaking directly to an applicant. You will be provided with their project proposal and a list of eligible grants.

    Your task:
    1. Evaluate how well each grant aligns with the specific project goals.
    2. Rank the grants from best match to worst match.
    3. Write a concise 2-3 sentence evaluation for EACH grant, detailing its specific strengths and weaknesses relative to the proposal.
    4. TONE REQUIREMENT: Speak directly to the applicant using "you" and "your". NEVER refer to them in the third person as "the user" or "the applicant". 

    Return valid JSON in this exact shape:
    {
    "ranked_grants": [
        {
        "grant_title": "string",
        "rank": 1,
        "explanation": "string"
        }
    ]
    }
    """

    user_prompt = f"User Project Proposal:\n{user_query}\n\nEligible Grants:\n{grants_context}"

    try:
        response = mistral_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result_text = response.choices[0].message.content
        parsed_result = json.loads(result_text)

        ranked = parsed_result.get("ranked_grants", [])
        
        valid_titles = [g.get("metadata", {}).get("grant_title", "").lower() for g in eligible_grants]
        
        verified_ranked = []
        for r_grant in ranked:
            title = r_grant.get("grant_title", "")
            if title.lower() in valid_titles:
                verified_ranked.append(r_grant)
            else:
                print(f"GUARDRAIL TRIGGERED: Removed hallucinated grant -> '{title}'")
                
        if isinstance(verified_ranked, list) and verified_ranked:
            return verified_ranked

        print("Ranking response failed verification. Using fallback ranking.")
        return fallback_rank(eligible_grants)

    except Exception as e:
        print(f"Error during ranking: {e}")
        return fallback_rank(eligible_grants)