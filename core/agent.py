from core.tools import search_grant_database
from core.eligibility import safe_check_eligibility
from core.profile_builder import extract_user_profile, find_missing_fields


class SimpleMemory:
    def __init__(self):
        self.user_profile = {}
        self.search_query = ""
        self.retrieved_grants = []
        self.evaluated_grants = []

    def store_user_profile(self, profile):
        self.user_profile = profile

    def store_search_query(self, query):
        self.search_query = query

    def store_retrieved_grants(self, grants):
        self.retrieved_grants = grants

    def store_evaluated_grants(self, grants):
        self.evaluated_grants = grants


def build_search_query(raw_user_input, user_profile):
    parts = [
        raw_user_input,
        user_profile.get("project_area", ""),
        user_profile.get("target_population", ""),
        user_profile.get("location", ""),
        user_profile.get("applicant_type", ""),
        f"${user_profile.get('budget_needed')}" if user_profile.get("budget_needed") else "",
        user_profile.get("research_focus", ""),
        user_profile.get("institution_type", ""),
    ]

    return " ".join(str(part) for part in parts if part).strip()


def score_grant(user_profile, grant_metadata, eligibility_result):
    score = 0

    final_status = eligibility_result.get("final_status", "uncertain")

    if final_status == "eligible":
        score += 50
    elif final_status == "uncertain":
        score += 15

    user_project_area = str(user_profile.get("project_area", "")).lower()
    grant_project_area = str(grant_metadata.get("project_area", "")).lower()
    if user_project_area and user_project_area in grant_project_area:
        score += 20

    user_target = str(user_profile.get("target_population", "")).lower()
    grant_demo = str(grant_metadata.get("demographic_requirements", "")).lower()
    if user_target and user_target in grant_demo:
        score += 15

    user_location = str(user_profile.get("location", "")).lower()
    grant_geo = str(grant_metadata.get("geographic_restrictions", "")).lower()
    if user_location and any(word in grant_geo for word in user_location.split()):
        score += 10

    budget_needed = user_profile.get("budget_needed")
    funding_amount = grant_metadata.get("funding_amount")

    try:
        if budget_needed is not None and funding_amount not in [None, "", "Not specified"]:
            grant_amount_num = float(str(funding_amount).replace("$", "").replace(",", ""))
            if grant_amount_num >= float(budget_needed):
                score += 10
    except Exception:
        pass

    return score


def rank_grants(user_profile, evaluated_grants):
    for grant in evaluated_grants:
        grant["score"] = score_grant(
            user_profile,
            grant["metadata"],
            grant["eligibility"]
        )

    return sorted(evaluated_grants, key=lambda x: x["score"], reverse=True)


def run_agent(
    raw_user_input=None,
    profile=None,
    n_results=5,
    use_llm_for_ambiguous=False,
    use_llm_for_profile_extraction=True
):
    if profile is None and raw_user_input is None:
        raise ValueError("Either raw_user_input or profile must be provided")
    
    memory = SimpleMemory()

    if profile is not None:
        user_profile = profile
    else:
        user_profile = extract_user_profile(
            raw_user_input,
            use_llm_for_profile_extraction=use_llm_for_profile_extraction
        )
    memory.store_user_profile(user_profile)

    missing_required = find_missing_fields(user_profile)
    if missing_required:
        return {
            "success": False,
            "needs_clarification": True,
            "missing_fields": missing_required,
            "message": f"Missing fields: {', '.join(missing_required)}",
            "user_profile": user_profile,
            "memory": memory.__dict__
        }

    query = build_search_query(raw_user_input, user_profile)
    memory.store_search_query(query)

    retrieved_grants = search_grant_database(query, n_results=n_results)
    memory.store_retrieved_grants(retrieved_grants)

    if not retrieved_grants:
        return {
            "success": False,
            "error": "No grants were retrieved from the database.",
            "query": query,
            "user_profile": user_profile,
            "memory": memory.__dict__
        }

    evaluated_grants = []

    for grant in retrieved_grants:
        metadata = grant.get("metadata", {})

        eligibility = safe_check_eligibility(
            user_profile=user_profile,
            grant_metadata=metadata,
            use_llm_for_ambiguous=use_llm_for_ambiguous
        )

        evaluated_grants.append({
            "id": grant.get("id", "unknown"),
            "metadata": metadata,
            "summary_text": grant.get("summary_text", ""),
            "eligibility": eligibility
        })

    memory.store_evaluated_grants(evaluated_grants)

    ranked_grants = rank_grants(user_profile, evaluated_grants)

    eligible = [g for g in ranked_grants if g["eligibility"]["final_status"] == "eligible"]
    uncertain = [g for g in ranked_grants if g["eligibility"]["final_status"] == "uncertain"]
    ineligible = [g for g in ranked_grants if g["eligibility"]["final_status"] == "ineligible"]

    return {
        "success": True,
        "user_profile": user_profile,
        "query": query,
        "eligible": eligible,
        "uncertain": uncertain,
        "ineligible": ineligible,
        "results": ranked_grants,
        "memory": memory.__dict__
    }


def print_agent_results(results):
    if not results.get("success"):
        print("\nAGENT FAILED")

        if results.get("error"):
            print("Error:", results["error"])
        elif results.get("message"):
            print("Message:", results["message"])
        else:
            print("Message: Unknown failure")

        if results.get("missing_fields"):
            print("Missing fields:", ", ".join(results["missing_fields"]))

        if results.get("user_profile"):
            print("Extracted profile:", results["user_profile"])

        if results.get("query"):
            print("Query:", results["query"])

        return

    print("\nSEARCH QUERY:")
    print(results.get("query", ""))

    print("\nEXTRACTED USER PROFILE:")
    print(results.get("user_profile", {}))

    print("\nELIGIBLE GRANTS:")
    if results.get("eligible"):
        for grant in results["eligible"]:
            title = grant["metadata"].get("grant_title", "Unknown Title")
            print(f"- {title} | Score: {grant['score']}")
            print(f"  Explanation: {grant['eligibility']['final_explanation']}")
    else:
        print("None")

    print("\nUNCERTAIN GRANTS:")
    if results.get("uncertain"):
        for grant in results["uncertain"]:
            title = grant["metadata"].get("grant_title", "Unknown Title")
            print(f"- {title} | Score: {grant['score']}")
            print(f"  Explanation: {grant['eligibility']['final_explanation']}")
    else:
        print("None")

    print("\nINELIGIBLE GRANTS:")
    if results.get("ineligible"):
        for grant in results["ineligible"]:
            title = grant["metadata"].get("grant_title", "Unknown Title")
            print(f"- {title} | Score: {grant['score']}")
            print(f"  Explanation: {grant['eligibility']['final_explanation']}")
    else:
        print("None")


if __name__ == "__main__":
    sample_user_input = (
        "I am a college student in philly and I need a 5,000 grant "
        "for a mental health research project focused on teens. What can I apply for?"
    )

    results = run_agent(
        raw_user_input=sample_user_input,
        n_results=10,
        use_llm_for_ambiguous=False,
        use_llm_for_profile_extraction=True
    )

    print_agent_results(results)