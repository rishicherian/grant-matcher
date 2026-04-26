from typing import Any, Dict, List

from core.tools import search_grant_database


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def build_project_query(project_info: Dict[str, Any]) -> str:
    parts = [
        project_info.get("project_area", ""),
        project_info.get("project_description", ""),
        project_info.get("target_population", ""),
        project_info.get("research_focus", ""),
    ]
    return " ".join(str(part) for part in parts if part).strip()


def grant_text_blob(grant: Dict[str, Any]) -> str:
    metadata = grant.get("metadata", {})
    summary_text = grant.get("summary_text", "")

    parts = [
        metadata.get("grant_title", ""),
        metadata.get("project_area", ""),
        metadata.get("eligibility_summary", ""),
        metadata.get("demographic_requirements", ""),
        summary_text,
    ]
    return normalize_text(" ".join(str(part) for part in parts if part))


def project_relevance_score(project_info: Dict[str, Any], grant: Dict[str, Any]) -> int:
    text = grant_text_blob(grant)

    project_area = normalize_text(project_info.get("project_area"))
    project_description = normalize_text(project_info.get("project_description"))
    target_population = normalize_text(project_info.get("target_population"))
    research_focus = normalize_text(project_info.get("research_focus"))

    score = 0

    if project_area and project_area in text:
        score += 5

    if target_population and target_population in text:
        score += 3

    if research_focus and research_focus in text:
        score += 3

    if project_description:
        words = [w for w in project_description.split() if len(w) > 3]
        overlap = sum(1 for w in words if w in text)
        score += min(overlap, 5)

    return score


def find_project_matches(project_info: Dict[str, Any], n_results: int = 10) -> List[Dict[str, Any]]:
    query = build_project_query(project_info)
    if not query:
        return []

    raw_results = search_grant_database(query, n_results=max(n_results, 15))
    if not raw_results:
        return []

    ranked = sorted(
        raw_results,
        key=lambda grant: project_relevance_score(project_info, grant),
        reverse=True,
    )

    cleaned = []
    for grant in ranked[:10]:
        cleaned.append({
            "id": grant.get("id", "unknown"),
            "metadata": grant.get("metadata", {}),
            "summary_text": grant.get("summary_text", ""),
        })

    return cleaned


if __name__ == "__main__":
    sample_project_info = {
        "project_area": "mental health research",
        "project_description": "Research on mental health outcomes for teens in Philadelphia",
        "target_population": "teens",
        "research_focus": "youth mental health",
    }

    results = find_project_matches(sample_project_info)
    print(f"Found {len(results)} project matches:")
    for i, grant in enumerate(results, start=1):
        print(f"{i}. {grant.get('metadata', {}).get('grant_title', 'Unknown Title')}")