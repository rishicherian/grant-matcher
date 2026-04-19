import os
import re
import json
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

load_dotenv()

LLM_BASE_URL = os.environ.get("MISTRAL_BASE_URL")
LLM_API_KEY = os.environ.get("MISTRAL_API_KEY")
LLM_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

llm_client = None
if OpenAI is not None and LLM_BASE_URL and LLM_API_KEY:
    llm_client = OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY
    )


APPLICANT_TYPE_RULES = {
    "nonprofit": ["nonprofit", "non-profit", "501c3", "501(c)(3)", "charity"],
    "student": ["student", "college student", "undergraduate", "graduate student", "phd student"],
    "researcher": ["researcher", "faculty", "professor", "lab", "research team", "academic"],
    "teacher": ["teacher", "educator", "classroom", "school teacher"],
    "school": ["school", "public school", "high school", "university", "college"],
    "individual": ["individual", "artist", "person", "resident"],
    "business": ["business", "small business", "startup", "entrepreneur", "company"],
}

PROJECT_AREA_RULES = {
    "arts": ["arts", "art", "music", "dance", "theater", "theatre", "creative", "mural"],
    "education": ["education", "teaching", "learning", "school", "curriculum", "literacy"],
    "health": ["health", "medical", "wellness", "public health"],
    "mental health": ["mental health", "depression", "anxiety", "therapy", "behavioral health"],
    "research": ["research", "study", "clinical trial", "data collection", "investigation"],
    "mental health research": ["mental health research", "behavioral health research", "psychology research"],
    "environment": ["environment", "climate", "sustainability", "green", "ecology"],
    "community development": ["community", "neighborhood", "community development", "civic"],
    "youth programming": ["after-school", "afterschool", "youth program", "teen program", "out-of-school time"],
    "business development": ["entrepreneurship", "business development", "economic development"],
}

TARGET_POPULATION_RULES = {
    "youth": ["youth", "teen", "teens", "children", "kids", "adolescents", "students"],
    "college students": ["college students", "undergraduates", "graduate students"],
    "seniors": ["seniors", "elderly", "older adults"],
    "women": ["women", "girls", "female"],
    "artists": ["artists", "creatives"],
    "low-income communities": ["low income", "underserved", "economically disadvantaged"],
}

LOCATION_RULES = {
    "Philadelphia, PA": ["philadelphia", "philly"],
    "Pennsylvania": ["pennsylvania", " pa "],
    "New York, NY": ["new york", "nyc", "brooklyn", "manhattan"],
    "New Jersey": ["new jersey", " nj "],
}


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def extract_budget(raw_user_input):
    matches = re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)", raw_user_input)
    if not matches:
        return None
    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return None


def rule_match(raw_text, rules_dict):
    raw_lower = raw_text.lower()
    matches = []

    for canonical_value, keywords in rules_dict.items():
        for keyword in keywords:
            if keyword.lower() in raw_lower:
                matches.append(canonical_value)
                break

    return matches


def choose_best_project_area(matches):
    if not matches:
        return ""

    priority = [
        "mental health research",
        "mental health",
        "research",
        "arts",
        "education",
        "health",
        "environment",
        "community development",
        "youth programming",
        "business development",
    ]

    for item in priority:
        if item in matches:
            return item

    return matches[0]


def choose_best_applicant_type(matches):
    if not matches:
        return ""

    priority = [
        "nonprofit",
        "student",
        "researcher",
        "teacher",
        "school",
        "business",
        "individual",
    ]

    for item in priority:
        if item in matches:
            return item

    return matches[0]


def choose_best_target_population(matches):
    if not matches:
        return ""

    priority = ["youth", "college students", "seniors", "women", "artists", "low-income communities"]

    for item in priority:
        if item in matches:
            return item

    return matches[0]


def choose_best_location(matches):
    if not matches:
        return ""
    return matches[0]


def extract_user_profile_rule_based(raw_user_input):
    applicant_type_matches = rule_match(raw_user_input, APPLICANT_TYPE_RULES)
    project_area_matches = rule_match(raw_user_input, PROJECT_AREA_RULES)
    target_population_matches = rule_match(raw_user_input, TARGET_POPULATION_RULES)
    location_matches = rule_match(raw_user_input, LOCATION_RULES)

    profile = {
        "applicant_type": choose_best_applicant_type(applicant_type_matches),
        "location": choose_best_location(location_matches),
        "project_area": choose_best_project_area(project_area_matches),
        "target_population": choose_best_target_population(target_population_matches),
        "budget_needed": extract_budget(raw_user_input),
        "organization_name": "",
        "project_description": raw_user_input,
        "research_focus": "",
        "institution_type": "",
        "career_stage": ""
    }

    raw_lower = raw_user_input.lower()

    if "college student" in raw_lower or "university student" in raw_lower:
        profile["institution_type"] = "college"
        profile["career_stage"] = "student"
        if not profile["applicant_type"]:
            profile["applicant_type"] = "student"

    if "research" in raw_lower and not profile["research_focus"]:
        if "mental health" in raw_lower:
            profile["research_focus"] = "mental health"
        else:
            profile["research_focus"] = "research"

    return profile


def sanitize_llm_profile(profile):
    allowed_keys = {
        "applicant_type",
        "location",
        "project_area",
        "target_population",
        "budget_needed",
        "organization_name",
        "project_description",
        "research_focus",
        "institution_type",
        "career_stage"
    }

    clean = {key: "" for key in allowed_keys}
    clean["budget_needed"] = None

    if not isinstance(profile, dict):
        return clean

    for key in allowed_keys:
        value = profile.get(key)

        if key == "budget_needed":
            if value in [None, "", "null"]:
                clean[key] = None
            else:
                try:
                    if isinstance(value, str):
                        digits = re.sub(r"[^\d.]", "", value)
                        clean[key] = float(digits) if digits else None
                    else:
                        clean[key] = float(value)
                except Exception:
                    clean[key] = None
        else:
            clean[key] = normalize_text(value)

    return clean


def llm_extract_user_profile(raw_user_input):
    if llm_client is None:
        return {}

    system_prompt = """
You extract structured grant-seeking profiles from user requests.

Return ONLY valid JSON with exactly these keys:
- applicant_type
- location
- project_area
- target_population
- budget_needed
- organization_name
- project_description
- research_focus
- institution_type
- career_stage

Rules:
- Use empty string "" when unknown
- Use null for budget_needed when unknown
- Do not invent facts that are not supported by the user input
- You may infer reasonable labels when strongly supported
- Keep project_area concise but specific
- Keep applicant_type concise
- Return JSON only
"""

    user_prompt = f"Extract a grant-seeking profile from this request:\n\n{raw_user_input}"

    try:
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)
        return sanitize_llm_profile(parsed)

    except Exception as e:
        print(f"LLM profile extraction failed: {e}")
        return {}


def merge_profiles(rule_profile, llm_profile):
    merged = dict(rule_profile)

    for key, llm_value in llm_profile.items():
        current_value = merged.get(key)

        if key == "budget_needed":
            if current_value is None and llm_value is not None:
                merged[key] = llm_value
        else:
            if not current_value and llm_value:
                merged[key] = llm_value

    if not merged.get("project_description"):
        merged["project_description"] = rule_profile.get("project_description", "")

    return merged


def find_missing_fields(user_profile):
    required_fields = ["location", "project_area"]
    return [field for field in required_fields if not user_profile.get(field)]


def find_high_value_missing_fields(user_profile):
    important_fields = ["applicant_type", "target_population"]
    return [field for field in important_fields if not user_profile.get(field)]


def extract_user_profile(raw_user_input, use_llm_for_profile_extraction=True):
    rule_profile = extract_user_profile_rule_based(raw_user_input)

    missing_required = find_missing_fields(rule_profile)
    missing_high_value = find_high_value_missing_fields(rule_profile)

    should_call_llm = use_llm_for_profile_extraction and (
        missing_required or missing_high_value
    )

    if not should_call_llm:
        return rule_profile

    llm_profile = llm_extract_user_profile(raw_user_input)
    merged_profile = merge_profiles(rule_profile, llm_profile)

    return merged_profile


if __name__ == "__main__":
    sample_input = (
        "I am a college student in philly and I need a 5,000 grant "
        "for a mental health research project focused on teens."
    )

    profile = extract_user_profile(
        sample_input,
        use_llm_for_profile_extraction=True
    )

    print(json.dumps(profile, indent=2))