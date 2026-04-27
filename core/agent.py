from typing import Any, Dict, List

from core.project_matcher import find_project_matches
from core.profile_matcher import filter_grants_by_profile
from core.ranker import rank_and_explain


def run_project_stage(project_info: Dict[str, Any]) -> Dict[str, Any]:
    project_matches = find_project_matches(project_info, n_results=5)

    return {
        "success": True,
        "project_info": project_info,
        "project_matches": project_matches,
    }


def run_profile_stage(
    project_info: Dict[str, Any],
    user_profile: Dict[str, Any],
    project_matches: List[Dict[str, Any]],
) -> Dict[str, Any]:
    filtered = filter_grants_by_profile(
        grants=project_matches,
        user_profile=user_profile,
        project_info=project_info,
    )

    return {
        "success": True,
        "project_info": project_info,
        "user_profile": user_profile,
        "project_matches": project_matches,
        "eligible_grants": filtered.get("eligible", []),
        "ineligible_grants": filtered.get("ineligible", []),
        "all_evaluated_grants": filtered.get("all", []),
    }


def run_ranking_stage(
    project_info: Dict[str, Any],
    user_profile: Dict[str, Any],
    eligible_grants: List[Dict[str, Any]],
) -> Dict[str, Any]:
    user_query = "\n".join([
        f"Project area: {project_info.get('project_area', '')}",
        f"Project description: {project_info.get('project_description', '')}",
        f"Target population: {project_info.get('target_population', '')}",
        f"Research focus: {project_info.get('research_focus', '')}",
        f"Applicant type: {user_profile.get('applicant_type', '')}",
        f"Location: {user_profile.get('location', '')}",
        f"Budget needed: {user_profile.get('budget_needed', '')}",
    ])

    ranked_results = rank_and_explain(user_query, eligible_grants)

    return {
        "success": True,
        "ranked_results": ranked_results,
    }