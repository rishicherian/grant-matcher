import os
import re
import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# llm clinet, If env vars are missing, LLM review just won't run.
LLM_BASE_URL = os.environ.get("MISTRAL_BASE_URL")
LLM_API_KEY = os.environ.get("MISTRAL_API_KEY")
LLM_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

llm_client = None
if LLM_BASE_URL and LLM_API_KEY:
    llm_client = OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY
    )


# User profile structure
@dataclass
class UserProfile:
    """
    Normalized user profile used by the eligibility checker.
    Keep this strict and predictable so the checker never depends on raw user text.
    """
    applicant_type: str = ""
    location: str = ""
    project_area: str = ""
    target_population: str = ""
    budget_needed: Optional[float] = None
    organization_name: str = ""
    project_description: str = ""

    # Optional extra fields that help future expansion
    state: str = ""
    city: str = ""
    zip_code: str = ""
    is_rural: Optional[bool] = None
    notes: str = ""


# Keyword normalization layer
APPLICANT_TYPE_SYNONYMS = {
    "nonprofit": {
        "nonprofit", "non-profit", "501c3", "501(c)(3)", "charity", "non profit"
    },
    "individual": {
        "individual", "person", "resident", "applicant", "citizen"
    },
    "artist": {
        "artist", "individual artist", "creative", "creator", "creative entrepreneur"
    },
    "school": {
        "school", "public school", "private school", "k-12 school", "teacher",
        "educator", "classroom", "student group"
    },
    "business": {
        "business", "small business", "for-profit", "for profit", "company",
        "startup", "entrepreneur"
    },
    "researcher": {
        "researcher", "faculty", "academic", "scholar", "university researcher"
    },
    "university": {
        "university", "college", "higher education", "institution of higher education"
    },
    "government": {
        "government", "municipal", "city agency", "public agency"
    }
}

LOCATION_SYNONYMS = {
    "philadelphia": {"philadelphia", "philly"},
    "west philadelphia": {"west philadelphia", "west philly"},
    "pennsylvania": {"pennsylvania", "pa"},
    "new york": {"new york", "ny"},
    "new jersey": {"new jersey", "nj"},
    "rural": {"rural"},
    "urban": {"urban"}
}

PROJECT_AREA_SYNONYMS = {
    "arts": {"arts", "art", "creative", "culture", "cultural"},
    "education": {"education", "teaching", "learning", "school", "academic"},
    "health": {"health", "medical", "wellness", "public health"},
    "environment": {"environment", "climate", "sustainability", "green", "ecology"},
    "community": {"community", "neighborhood", "civic", "community development"},
    "youth": {"youth", "children", "teens", "young people"},
    "business": {"business", "entrepreneurship", "economic development", "small business"}
}

DEMOGRAPHIC_SYNONYMS = {
    "youth": {"youth", "children", "teens", "young people", "students"},
    "seniors": {"seniors", "elderly", "older adults"},
    "women": {"women", "girls", "female"},
    "black communities": {"black", "african american", "black communities"},
    "latino communities": {"latino", "latina", "latinx", "hispanic"},
    "artists": {"artists", "artist", "creatives"},
    "low income": {"low income", "underserved", "economically disadvantaged"}
}



# Utility helpers
def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def split_csv_like(value: Any) -> List[str]:
    """
    Your build_db.py turns list metadata into comma-joined strings.
    This reverses that for fields like eligible_applicant_type. :contentReference[oaicite:5]{index=5}
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_text(v) for v in value if normalize_text(v)]

    text = normalize_text(value)
    if not text or text == "not specified":
        return []

    parts = re.split(r",|/|;|\n", text)
    return [p.strip() for p in parts if p.strip()]


def parse_money(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_text(value)
    if not text or text == "not specified":
        return None

    # Handles "$10,000", "10000", "Up to $25,000"
    matches = re.findall(r"\d[\d,]*\.?\d*", text)
    if not matches: # hi 
        return None

    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return None


def bool_from_text(text: str, positive_terms: List[str], negative_terms: List[str]) -> Optional[bool]:
    text = normalize_text(text)
    if any(term in text for term in positive_terms):
        return True
    if any(term in text for term in negative_terms):
        return False
    return None


def canonicalize_with_map(text: str, mapping: Dict[str, set]) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    matched = []
    for canonical, variants in mapping.items():
        if canonical in text or any(variant in text for variant in variants):
            matched.append(canonical)

    # Fallback: if nothing matched, preserve original text
    return matched if matched else [text]


def is_missing(value: Any) -> bool:
    text = normalize_text(value)
    return value is None or text == "" or text == "not specified" or text == "null"


def contains_exclusionary_language(text: str) -> bool:
    """
    Detect whether project_area or demographic fields look like hard constraints
    versus just topical descriptions.
    """
    text = normalize_text(text)
    hard_markers = [
        "only", "must", "restricted to", "limited to", "eligible applicants include",
        "applicants must", "open only to", "available only to", "requires"
    ]
    return any(marker in text for marker in hard_markers)


def text_overlap(a: str, b: str) -> bool:
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return False
    return a in b or b in a


def get_location_tokens(text: str) -> List[str]:
    return canonicalize_with_map(text, LOCATION_SYNONYMS)


def get_applicant_tokens(text: str) -> List[str]:
    return canonicalize_with_map(text, APPLICANT_TYPE_SYNONYMS)


def get_project_area_tokens(text: str) -> List[str]:
    return canonicalize_with_map(text, PROJECT_AREA_SYNONYMS)


def get_demographic_tokens(text: str) -> List[str]:
    return canonicalize_with_map(text, DEMOGRAPHIC_SYNONYMS)


# Normalization entrypoints
def normalize_user_profile(raw_profile: Dict[str, Any]) -> UserProfile:
    """
    Use this right after collecting user info in your agent.
    """
    budget = raw_profile.get("budget_needed")
    budget_value = None
    if budget is not None:
        budget_value = parse_money(budget)

    location = normalize_text(raw_profile.get("location"))
    city = normalize_text(raw_profile.get("city"))
    state = normalize_text(raw_profile.get("state"))

    # Basic fallback extraction from location string
    if not city and "philadelphia" in location:
        city = "philadelphia"
    if not state and ("pennsylvania" in location or re.search(r"\bpa\b", location)):
        state = "pennsylvania"

    is_rural = raw_profile.get("is_rural")
    if isinstance(is_rural, str):
        is_rural = bool_from_text(is_rural, ["yes", "true", "rural"], ["no", "false", "urban"])

    return UserProfile(
        applicant_type=normalize_text(raw_profile.get("applicant_type")),
        location=location,
        project_area=normalize_text(raw_profile.get("project_area")),
        target_population=normalize_text(raw_profile.get("target_population")),
        budget_needed=budget_value,
        organization_name=normalize_text(raw_profile.get("organization_name")),
        project_description=normalize_text(raw_profile.get("project_description")),
        state=state,
        city=city,
        zip_code=normalize_text(raw_profile.get("zip_code")),
        is_rural=is_rural,
        notes=normalize_text(raw_profile.get("notes")),
    )


def normalize_grant_metadata(raw_grant: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Chroma metadata or JSON grant record into a consistent structure.
    """
    return {
        "grant_title": raw_grant.get("grant_title", "Unknown Grant"),
        "funding_amount_raw": raw_grant.get("funding_amount"),
        "funding_amount": parse_money(raw_grant.get("funding_amount")),
        "deadline": raw_grant.get("deadline", "Not specified"),
        "eligible_applicant_type_raw": raw_grant.get("eligible_applicant_type", "Not specified"),
        "eligible_applicant_type_list": split_csv_like(raw_grant.get("eligible_applicant_type")),
        "geographic_restrictions": normalize_text(raw_grant.get("geographic_restrictions")),
        "project_area": normalize_text(raw_grant.get("project_area")),
        "demographic_requirements": normalize_text(raw_grant.get("demographic_requirements")),
        "eligibility_summary": normalize_text(raw_grant.get("eligibility_summary")),
    }


# Constraint result format
def make_constraint_result(constraint: str, result: str, reason: str) -> Dict[str, str]:
    return {
        "constraint": constraint,
        "result": result,   # pass / fail / uncertain
        "reason": reason
    }


# Individual hard-constraint checks
def check_applicant_type(user: UserProfile, grant: Dict[str, Any]) -> Dict[str, str]:
    eligible_types = grant["eligible_applicant_type_list"]
    user_type = user.applicant_type

    if not user_type:
        return make_constraint_result(
            "applicant_type",
            "uncertain",
            "User applicant type is missing."
        )

    if not eligible_types:
        return make_constraint_result(
            "applicant_type",
            "uncertain",
            "Grant applicant type is not specified."
        )

    user_tokens = set(get_applicant_tokens(user_type))
    grant_tokens = set()
    for item in eligible_types:
        grant_tokens.update(get_applicant_tokens(item))

    if user_tokens & grant_tokens:
        return make_constraint_result(
            "applicant_type",
            "pass",
            f"User applicant type '{user_type}' matches grant applicant types {sorted(grant_tokens)}."
        )

    return make_constraint_result(
        "applicant_type",
        "fail",
        f"User applicant type '{user_type}' does not match grant applicant types {eligible_types}."
    )


def check_geography(user: UserProfile, grant: Dict[str, Any]) -> Dict[str, str]:
    geo = grant["geographic_restrictions"]
    user_location = user.location

    if not user_location:
        return make_constraint_result(
            "geography",
            "uncertain",
            "User location is missing."
        )

    if is_missing(geo):
        return make_constraint_result(
            "geography",
            "pass",
            "Grant does not specify geographic restrictions."
        )

    if "pennsylvania" in geo or re.search(r"\bpa\b", geo):
        if "pennsylvania" in user_location or re.search(r"\bpa\b", user_location):
            return make_constraint_result(
                "geography",
                "pass",
                "User is in Pennsylvania, which is considered nearby."
            )

    if text_overlap(user_location, geo):
        return make_constraint_result(
            "geography",
            "pass",
            f"User location '{user_location}' matches grant geography '{geo}'."
        )

    return make_constraint_result(
        "geography",
        "uncertain",
        f"Grant geography '{geo}' does not clearly match user location '{user_location}', but nearby locations are allowed."
    )


def check_budget(user: UserProfile, grant: Dict[str, Any]) -> Dict[str, str]:
    needed = user.budget_needed
    grant_amount = grant["funding_amount"]

    if needed is None:
        return make_constraint_result(
            "budget",
            "uncertain",
            "User budget needed is missing."
        )

    if grant_amount is None:
        return make_constraint_result(
            "budget",
            "uncertain",
            "Grant funding amount is missing or unparseable."
        )

    if grant_amount >= needed:
        return make_constraint_result(
            "budget",
            "pass",
            f"Grant amount {grant_amount} is at least the requested budget {needed}."
        )

    return make_constraint_result(
        "budget",
        "fail",
        f"Grant amount {grant_amount} is below requested budget {needed}."
    )


def check_project_area(user: UserProfile, grant: Dict[str, Any]) -> Dict[str, str]:
    user_area = user.project_area
    grant_area = grant["project_area"]

    if not user_area:
        return make_constraint_result(
            "project_area",
            "uncertain",
            "User project area is missing."
        )

    if is_missing(grant_area):
        return make_constraint_result(
            "project_area",
            "uncertain",
            "Grant project area is not specified."
        )

    user_tokens = set(get_project_area_tokens(user_area))
    grant_tokens = set(get_project_area_tokens(grant_area))

    if user_tokens & grant_tokens or text_overlap(user_area, grant_area):
        return make_constraint_result(
            "project_area",
            "pass",
            f"User project area '{user_area}' matches grant topic '{grant_area}'."
        )

    return make_constraint_result(
        "project_area",
        "uncertain",
        f"Grant topic '{grant_area}' does not clearly match user mission '{user_area}'."
    )


def check_demographics(user: UserProfile, grant: Dict[str, Any]) -> Dict[str, str]:
    target = user.target_population
    demo = grant["demographic_requirements"]
    eligibility_summary = grant["eligibility_summary"]

    if not target:
        return make_constraint_result(
            "demographics",
            "uncertain",
            "User target population is missing."
        )

    if is_missing(demo):
        return make_constraint_result(
            "demographics",
            "uncertain",
            "Grant demographic requirements are not specified."
        )

    user_tokens = set(get_demographic_tokens(target))
    grant_tokens = set(get_demographic_tokens(demo))
    overlap = user_tokens & grant_tokens

    if overlap:
        return make_constraint_result(
            "demographics",
            "pass",
            f"User target population '{target}' matches grant demographic requirements '{demo}'."
        )

    combined_text = f"{demo} {eligibility_summary}"
    if contains_exclusionary_language(combined_text):
        return make_constraint_result(
            "demographics",
            "fail",
            f"Grant demographic requirements '{demo}' appear restrictive and do not match target population '{target}'."
        )

    return make_constraint_result(
        "demographics",
        "uncertain",
        f"Could not confidently verify demographic match: user='{target}', grant='{demo}'."
    )


# Core aggregation logic
def aggregate_eligibility(checks: List[Dict[str, str]]) -> Dict[str, Any]:
    failed = [c for c in checks if c["result"] == "fail"]
    uncertain = [c for c in checks if c["result"] == "uncertain"]
    passed = [c for c in checks if c["result"] == "pass"]

    if failed:
        status = "ineligible"
    elif uncertain:
        status = "uncertain"
    else:
        status = "eligible"

    return {
        "status": status,
        "reasons": [c["reason"] for c in checks],
        "failed_constraints": [c["constraint"] for c in failed],
        "warnings": [c["reason"] for c in uncertain],
        "matched_constraints": [c["constraint"] for c in passed],
        "raw_checks": checks
    }


def check_eligibility_rule_based(user_profile: Dict[str, Any], grant_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified eligibility checker.
    """
    user = normalize_user_profile(user_profile)
    grant = normalize_grant_metadata(grant_metadata)

    checks = [
        check_project_area(user, grant),
        check_geography(user, grant),
    ]

    result = aggregate_eligibility(checks)
    result["normalized_user_profile"] = asdict(user)
    result["normalized_grant"] = grant
    return result


# Second-stage LLM review for ambiguous cases only
def llm_review_ambiguous_case(
    normalized_user_profile: Dict[str, Any],
    normalized_grant: Dict[str, Any],
    rule_based_result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Only called when rule-based result is uncertain.
    The LLM must use parsed fields only.
    It does NOT override hard failures.
    """
    if llm_client is None:
        return None

    if rule_based_result.get("status") != "uncertain":
        return None

    prompt = f"""
You are reviewing an ambiguous grant eligibility decision.

Your job:
1. Use ONLY the structured fields provided below.
2. Do NOT invent any facts.
3. If the evidence is incomplete or ambiguous, return "uncertain".
4. Never override a clear hard failure. This case is only for ambiguity review.

Return strict JSON with keys:
- status: one of ["eligible", "ineligible", "uncertain"]
- explanation: short string
- evidence_used: list of strings
- confidence: one of ["low", "medium", "high"]

Normalized user profile:
{json.dumps(normalized_user_profile, indent=2)}

Normalized grant:
{json.dumps(normalized_grant, indent=2)}

Rule-based result:
{json.dumps(rule_based_result, indent=2)}
"""

    try:
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cautious eligibility reviewer. Output valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        # Basic validation
        if parsed.get("status") not in {"eligible", "ineligible", "uncertain"}:
            return None

        if parsed.get("confidence") not in {"low", "medium", "high"}:
            parsed["confidence"] = "low"

        return parsed

    except Exception as e:
        return {
            "status": "uncertain",
            "explanation": f"LLM review failed: {str(e)}",
            "evidence_used": [],
            "confidence": "low"
        }


def merge_rule_and_llm_result(rule_result: Dict[str, Any], llm_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Safe merge policy:
    - If rule result is eligible or ineligible, keep it.
    - If rule result is uncertain and LLM exists:
        - accept LLM eligible/ineligible only when confidence is medium/high
        - otherwise remain uncertain
    """
    final_result = dict(rule_result)
    final_result["llm_review"] = llm_result

    if rule_result["status"] in {"eligible", "ineligible"}:
        final_result["final_status"] = rule_result["status"]
        final_result["final_explanation"] = "Final status based on deterministic rule-based checks."
        return final_result

    if not llm_result:
        final_result["final_status"] = "uncertain"
        final_result["final_explanation"] = "Rule-based result was uncertain and no LLM review was available."
        return final_result

    if llm_result["status"] in {"eligible", "ineligible"} and llm_result.get("confidence") in {"medium", "high"}:
        final_result["final_status"] = llm_result["status"]
        final_result["final_explanation"] = llm_result.get("explanation", "LLM reviewed an ambiguous case.")
        return final_result

    final_result["final_status"] = "uncertain"
    final_result["final_explanation"] = "Ambiguous case remained uncertain after LLM review."
    return final_result


def check_eligibility(
    user_profile: Dict[str, Any],
    grant_metadata: Dict[str, Any],
    use_llm_for_ambiguous: bool = True
) -> Dict[str, Any]:
    """
    Public entrypoint for your agent.
    """
    rule_result = check_eligibility_rule_based(user_profile, grant_metadata)

    llm_result = None
    if use_llm_for_ambiguous and rule_result["status"] == "uncertain":
        llm_result = llm_review_ambiguous_case(
            rule_result["normalized_user_profile"],
            rule_result["normalized_grant"],
            rule_result
        )

    return merge_rule_and_llm_result(rule_result, llm_result)


# =========================
# Safe wrapper / guardrails
# =========================
def safe_check_eligibility(
    user_profile: Dict[str, Any],
    grant_metadata: Dict[str, Any],
    use_llm_for_ambiguous: bool = True
) -> Dict[str, Any]:
    if not isinstance(user_profile, dict):
        return {
            "status": "uncertain",
            "final_status": "uncertain",
            "reasons": ["Invalid user profile format."],
            "failed_constraints": [],
            "warnings": ["User profile must be a dictionary."],
            "matched_constraints": [],
            "raw_checks": [],
            "llm_review": None,
            "final_explanation": "Eligibility check could not run because the user profile format was invalid."
        }

    if not isinstance(grant_metadata, dict):
        return {
            "status": "uncertain",
            "final_status": "uncertain",
            "reasons": ["Invalid grant metadata format."],
            "failed_constraints": [],
            "warnings": ["Grant metadata must be a dictionary."],
            "matched_constraints": [],
            "raw_checks": [],
            "llm_review": None,
            "final_explanation": "Eligibility check could not run because the grant metadata format was invalid."
        }

    try:
        return check_eligibility(
            user_profile=user_profile,
            grant_metadata=grant_metadata,
            use_llm_for_ambiguous=use_llm_for_ambiguous
        )
    except Exception as e:
        return {
            "status": "uncertain",
            "final_status": "uncertain",
            "reasons": [f"Eligibility check failed: {str(e)}"],
            "failed_constraints": [],
            "warnings": ["Internal eligibility checker exception."],
            "matched_constraints": [],
            "raw_checks": [],
            "llm_review": None,
            "final_explanation": "Eligibility checker raised an exception and defaulted to uncertain."
        }


# =========================
# Example usage
# =========================
if __name__ == "__main__":
    user_profile = {
        "applicant_type": "nonprofit",
        "location": "Philadelphia, PA",
        "project_area": "arts education",
        "target_population": "youth",
        "budget_needed": 12000,
        "organization_name": "Example Org",
        "project_description": "After-school arts programming for teens",
        "is_rural": False
    }

    grant_metadata = {
        "grant_title": "Example Arts Grant",
        "funding_amount": "$15,000",
        "deadline": "2026-06-01",
        "eligible_applicant_type": "nonprofit, school",
        "geographic_restrictions": "Philadelphia",
        "project_area": "arts, education",
        "demographic_requirements": "youth",
        "eligibility_summary": "Open only to Philadelphia nonprofits and schools serving youth."
    }

    result = safe_check_eligibility(user_profile, grant_metadata, use_llm_for_ambiguous=True)
    print(json.dumps(result, indent=2))