import json
from core.ranker import rank_and_explain

def run_tests():
    print("--- Running Ranker Tool Tests ---\n")

    # Test Case 1: The Mural Project
    print("Test 1: West Philly Mural Project")
    query_1 = "We want to paint a large mural in West Philadelphia celebrating local history."
    grants_1 = [
        {
            "metadata": {"grant_title": "City-Wide Arts Initiative"},
            "summary_text": "General funding for arts programs across the entire city of Philadelphia."
        },
        {
            "metadata": {"grant_title": "West Philadelphia Creative Grants"},
            "summary_text": "Funding for local artists in West Philadelphia to create community-centric public art."
        }
    ]
    
    result_1 = rank_and_explain(query_1, grants_1)
    print(json.dumps(result_1, indent=2))
    print("\n" + "="*60 + "\n")

    # Test Case 2: A STEM and Education project
    print("Test 2: After-School Tech Program")
    query_2 = "An after-school program focused on teaching robotics and coding to high school students."
    grants_2 = [
        {
            "metadata": {"grant_title": "Local Sports & Health Initiative"},
            "summary_text": "Grants for community youth sports leagues and physical health equipment."
        },
        {
            "metadata": {"grant_title": "Philadelphia Tech for Tomorrow Grant"},
            "summary_text": "Provides resources and funding for STEM education and coding programs in local schools."
        },
        {
            "metadata": {"grant_title": "Forman Family Fund Grants"},
            "summary_text": "Supports out-of-school-time programs addressing photography, architectural drawing, or written arts."
        }
    ]

    result_2 = rank_and_explain(query_2, grants_2)
    print(json.dumps(result_2, indent=2))
    print("\n--- Tests Complete ---")

if __name__ == "__main__":
    run_tests()