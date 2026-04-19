import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.eligibility import safe_check_eligibility


def run_test(name, user, grant, expected):
    result = safe_check_eligibility(user, grant, use_llm_for_ambiguous=False)
    actual = result["final_status"]

    print(f"\n{name}")
    print("Expected:", expected)
    print("Actual:", actual)

    if actual == expected:
        print("PASS")
    else:
        print("FAIL")
        print(result)


# ------------------------
# TEST CASES
# ------------------------

# 1. Happy path
run_test(
    "Happy Path",
    user={
        "applicant_type": "nonprofit",
        "location": "Philadelphia, PA",
        "project_area": "arts",
        "target_population": "youth",
        "budget_needed": 5000,
        "is_rural": False
    },
    grant={
        "grant_title": "Arts Youth Grant",
        "funding_amount": "$10,000",
        "eligible_applicant_type": "nonprofit",
        "geographic_restrictions": "Philadelphia",
        "project_area": "arts",
        "demographic_requirements": "youth",
        "eligibility_summary": "Open only to Philadelphia nonprofits serving youth."
    },
    expected="eligible"
)

# 2. Wrong geography
run_test(
    "Wrong Geography",
    user={
        "applicant_type": "nonprofit",
        "location": "New York, NY",
        "project_area": "arts",
        "target_population": "youth",
        "budget_needed": 5000,
        "is_rural": False
    },
    grant={
        "grant_title": "Arts Youth Grant",
        "funding_amount": "$10,000",
        "eligible_applicant_type": "nonprofit",
        "geographic_restrictions": "Philadelphia",
        "project_area": "arts",
        "demographic_requirements": "youth",
        "eligibility_summary": "Open only to Philadelphia nonprofits serving youth."
    },
    expected="ineligible"
)

# 3. Missing geo → uncertain
run_test(
    "Missing Geography",
    user={
        "applicant_type": "nonprofit",
        "location": "Philadelphia, PA",
        "project_area": "arts",
        "target_population": "youth",
        "budget_needed": 5000
    },
    grant={
        "grant_title": "Arts Youth Grant",
        "funding_amount": "$10,000",
        "eligible_applicant_type": "nonprofit",
        "geographic_restrictions": "Not specified",
        "project_area": "arts",
        "demographic_requirements": "youth",
        "eligibility_summary": "Supports youth arts work."
    },
    expected="uncertain"
)

# 4. Wrong applicant type
run_test(
    "Wrong Applicant Type",
    user={
        "applicant_type": "individual",
        "location": "Philadelphia, PA",
        "project_area": "arts",
        "target_population": "youth",
        "budget_needed": 5000
    },
    grant={
        "grant_title": "Nonprofit Youth Grant",
        "funding_amount": "$10,000",
        "eligible_applicant_type": "nonprofit only",
        "geographic_restrictions": "Philadelphia",
        "project_area": "arts",
        "demographic_requirements": "youth",
        "eligibility_summary": "Open only to Philadelphia nonprofits serving youth."
    },
    expected="ineligible"
)