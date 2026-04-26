import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class UserProject:
    project_area: str = ""
    project_description: str = ""
    target_population: str = ""
    research_focus: str = ""


@dataclass
class UserProfile:
    applicant_type: str = ""
    location: str = ""
    budget_needed: Optional[float] = None
    deadline_by: str = ""
    organization_name: str = ""
    institution_type: str = ""
    demographics: str = ""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def split_csv_like(value: Any) -> List[str]:
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
    matches = re.findall(r"\d[\d,]*\.?\d*", text)
    if not matches:
        return None

    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return None


def normalize_user_project(raw: Dict[str, Any]) -> UserProject:
    return UserProject(
        project_area=normalize_text(raw.get("project_area")),
        project_description=normalize_text(raw.get("project_description")),
        target_population=normalize_text(raw.get("target_population")),
        research_focus=normalize_text(raw.get("research_focus")),
    )


def normalize_user_profile(raw: Dict[str, Any]) -> UserProfile:
    return UserProfile(
        applicant_type=normalize_text(raw.get("applicant_type")),
        location=normalize_text(raw.get("location")),
        budget_needed=parse_money(raw.get("budget_needed")),
        deadline_by=normalize_text(raw.get("deadline_by")),
        organization_name=normalize_text(raw.get("organization_name")),
        institution_type=normalize_text(raw.get("institution_type")),
        demographics=normalize_text(raw.get("demographics")),
    )


def normalize_grant_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "grant_title": raw.get("grant_title", "Unknown Grant"),
        "project_area": normalize_text(raw.get("project_area")),
        "summary_text": normalize_text(raw.get("summary_text", "")),
        "demographic_requirements": normalize_text(raw.get("demographic_requirements")),
        "geographic_restrictions": normalize_text(raw.get("geographic_restrictions")),
        "eligible_applicant_type_list": split_csv_like(raw.get("eligible_applicant_type")),
        "funding_amount": parse_money(raw.get("funding_amount")),
        "deadline": normalize_text(raw.get("deadline")),
        "institution_type": normalize_text(raw.get("institution_type")),
        "eligibility_summary": normalize_text(raw.get("eligibility_summary")),
    }