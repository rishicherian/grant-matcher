import re
from typing import Any, Dict, List, Optional


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def parse_money(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_text(value)
    if not text or text == "not specified":
        return None

    matches = re.findall(r"\d[\d,]*\.?\d*", text)
    if not matches:
        return None

    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return None


def normalize_location(text: str) -> str:
    text = normalize_text(text)
    replacements = {
        "philly": "philadelphia",
        "pa": "pennsylvania",
        "ny": "new york",
        "nj": "new jersey",
    }
    words = text.replace(",", " ").split()
    words = [replacements.get(word, word) for word in words]
    return " ".join(words)


def fuzzy_overlap(a: str, b: str) -> int:
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0

    a_words = set(a.replace(",", " ").split())
    b_words = set(b.replace(",", " ").split())
    return len(a_words & b_words)


def location_match_score(user_location: str, grant_location: str) -> Dict[str, Any]:
    user_location = normalize_location(user_location)
    grant_location = normalize_location(grant_location)

    if not grant_location or grant_location == "not specified":
        return {"matched": True, "score": 1, "reason": "Grant does not specify geographic restrictions."}

    if user_location in grant_location or grant_location in user_location:
        return {"matched": True, "score": 3, "reason": "Location strongly matches the grant's geography."}

    overlap = fuzzy_overlap(user_location, grant_location)
    if overlap >= 1:
        return {"matched": True, "score": 2, "reason": "Location partially matches the grant's geography."}

    return {"matched": False, "score": 0, "reason": "Location does not match the grant's geographic restrictions."}


def applicant_type_match_score(user_type: str, grant_type: str) -> Dict[str, Any]:
    user_type = normalize_text(user_type)
    grant_type = normalize_text(grant_type)

    if not grant_type or grant_type == "not specified":
        return {"matched": True, "score": 1, "reason": "Grant does not clearly specify applicant type restrictions."}

    if not user_type:
        return {"matched": False, "score": 0, "reason": "User applicant type was not provided."}

    synonym_groups = [
        {"student", "college student", "undergraduate", "graduate student"},
        {"nonprofit", "non-profit", "501c3", "501(c)(3)", "charity"},
        {"individual", "person", "resident", "citizen"},
        {"researcher", "faculty", "scholar", "academic"},
        {"university", "college", "higher education"},
        {"business", "startup", "company", "small business", "entrepreneur"},
    ]

    for group in synonym_groups:
        if user_type in group and any(term in grant_type for term in group):
            return {"matched": True, "score": 3, "reason": "Applicant type matches through an equivalent category."}

    if user_type in grant_type or grant_type in user_type:
        return {"matched": True, "score": 3, "reason": "Applicant type directly matches."}

    overlap = fuzzy_overlap(user_type, grant_type)
    if overlap >= 1:
        return {"matched": True, "score": 2, "reason": "Applicant type partially matches the grant requirements."}

    return {"matched": False, "score": 0, "reason": "Applicant type does not match the grant's eligible applicant type."}


def project_area_match_score(project_area: str, grant_area: str, summary_text: str) -> Dict[str, Any]:
    project_area = normalize_text(project_area)
    grant_area = normalize_text(grant_area)
    summary_text = normalize_text(summary_text)

    combined = f"{grant_area} {summary_text}"

    if not project_area:
        return {"matched": True, "score": 1, "reason": "Project area was not provided, so this was not used as a filter."}

    if project_area in combined:
        return {"matched": True, "score": 3, "reason": "Project area strongly matches the grant."}

    words = [w for w in project_area.split() if len(w) > 3]
    overlap = sum(1 for w in words if w in combined)

    if overlap >= 2:
        return {"matched": True, "score": 2, "reason": "Project area partially matches the grant description."}

    if overlap == 1:
        return {"matched": True, "score": 1, "reason": "Project area has a weak match to the grant description."}

    return {"matched": False, "score": 0, "reason": "Project area does not seem to match this grant well."}


def demographic_match_score(target_population: str, grant_demographics: str) -> Dict[str, Any]:
    target_population = normalize_text(target_population)
    grant_demographics = normalize_text(grant_demographics)

    if not grant_demographics or grant_demographics == "not specified":
        return {"matched": True, "score": 1, "reason": "Grant does not specify demographic restrictions."}

    if not target_population:
        return {"matched": True, "score": 1, "reason": "Target population was not provided, so this was not used strictly."}

    synonym_groups = [
        {"youth", "teens", "young people", "students", "children"},
        {"seniors", "elderly", "older adults"},
        {"women", "girls", "female"},
        {"artists", "artist", "creatives"},
        {"low income", "underserved", "economically disadvantaged"},
    ]

    for group in synonym_groups:
        if target_population in group and any(term in grant_demographics for term in group):
            return {"matched": True, "score": 3, "reason": "Target population matches the grant's demographic focus."}

    if target_population in grant_demographics or grant_demographics in target_population:
        return {"matched": True, "score": 3, "reason": "Target population directly matches demographic requirements."}

    overlap = fuzzy_overlap(target_population, grant_demographics)
    if overlap >= 1:
        return {"matched": True, "score": 2, "reason": "Target population partially matches demographic requirements."}

    return {"matched": False, "score": 0, "reason": "Target population does not match the grant's demographic requirements."}


def budget_match_score(budget_needed: Any, funding_amount: Any) -> Dict[str, Any]:
    user_budget = parse_money(budget_needed)
    grant_budget = parse_money(funding_amount)

    if user_budget is None:
        return {"matched": True, "score": 1, "reason": "Requested budget was not provided."}

    if grant_budget is None:
        return {"matched": True, "score": 1, "reason": "Grant funding amount was not specified."}

    if grant_budget >= user_budget:
        return {"matched": True, "score": 3, "reason": "Grant funding amount covers the requested budget."}

    if grant_budget >= 0.7 * user_budget:
        return {"matched": True, "score": 1, "reason": "Grant funding amount is below the request, but still somewhat close."}

    return {"matched": False, "score": 0, "reason": "Grant funding amount is much lower than the requested budget."}


def evaluate_single_grant(
    grant: Dict[str, Any],
    user_profile: Dict[str, Any],
    project_info: Dict[str, Any],
) -> Dict[str, Any]:
    metadata = grant.get("metadata", {})
    summary_text = grant.get("summary_text", "")

    checks = {
        "project_area": project_area_match_score(
            project_info.get("project_area", ""),
            metadata.get("project_area", ""),
            summary_text,
        ),
        "applicant_type": applicant_type_match_score(
            user_profile.get("applicant_type", ""),
            metadata.get("eligible_applicant_type", ""),
        ),
        "location": location_match_score(
            user_profile.get("location", ""),
            metadata.get("geographic_restrictions", ""),
        ),
        "budget": budget_match_score(
            user_profile.get("budget_needed"),
            metadata.get("funding_amount"),
        ),
        "demographics": demographic_match_score(
            project_info.get("target_population", ""),
            metadata.get("demographic_requirements", ""),
        ),
    }

    total_score = sum(check["score"] for check in checks.values())

    eligible_reasons = [check["reason"] for check in checks.values() if check["matched"]]
    ineligible_reasons = [check["reason"] for check in checks.values() if not check["matched"]]

    # Softer threshold: 6 or more points counts as eligible
    # This allows some imperfect matches through.
    eligible = total_score >= 6

    return {
        "id": grant.get("id", "unknown"),
        "metadata": metadata,
        "summary_text": summary_text,
        "eligible": eligible,
        "match_score": total_score,
        "eligible_reasons": eligible_reasons,
        "ineligible_reasons": ineligible_reasons,
        "match_details": checks,
    }


def filter_grants_by_profile(
    grants: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    project_info: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    evaluated = [
        evaluate_single_grant(grant, user_profile, project_info)
        for grant in grants
    ]

    evaluated.sort(key=lambda g: g["match_score"], reverse=True)

    eligible = [grant for grant in evaluated if grant["eligible"]]
    ineligible = [grant for grant in evaluated if not grant["eligible"]]

    # fallback: if nothing qualifies, still return the top 3 closest matches as eligible-like suggestions
    if not eligible and evaluated:
        fallback = evaluated[:3]
        for grant in fallback:
            grant["eligible"] = True
            grant["eligible_reasons"].append(
                "This grant was included as a closest partial match even though it was not a perfect fit."
            )
        eligible = fallback
        ineligible = evaluated[3:]

    return {
        "eligible": eligible,
        "ineligible": ineligible,
        "all": evaluated,
    }