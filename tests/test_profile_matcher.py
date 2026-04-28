import unittest
from core.profile_matcher import (
    evaluate_single_grant, 
    location_match_score, 
    applicant_type_match_score,
    parse_money
)

class TestProfileMatcherEdgeCases(unittest.TestCase):

    def setUp(self):
        self.base_grant = {
            "id": "grant_001",
            "metadata": {
                "grant_title": "Local Philly Arts Fund",
                "project_area": "arts",
                "eligible_applicant_type": "nonprofit",
                "geographic_restrictions": "Philadelphia, PA",
                "funding_amount": "$10,000",
                "demographic_requirements": "youth"
            },
            "summary_text": "Funding for local nonprofits to teach art."
        }

    # --- MISSING DATA EDGE CASES ---
    def test_missing_grant_metadata(self):
        """Ensure the evaluator doesn't crash if the grant is missing data fields."""
        empty_grant = {"id": "grant_empty", "metadata": {}, "summary_text": ""}
        user_profile = {"applicant_type": "student", "location": "NY"}
        project_info = {"project_area": "science"}
        
        result = evaluate_single_grant(empty_grant, user_profile, project_info)
        self.assertIsNotNone(result)
        self.assertTrue(result["match_details"]["location"]["matched"])

    def test_empty_user_inputs(self):
        """If a user skips an optional field, they shouldn't be penalized."""
        result = location_match_score("", "Philadelphia, PA")
        self.assertTrue(result["matched"])
        self.assertEqual(result["score"], 1)

    # --- INTENDED TASKS (LOGIC & NORMALIZATION) ---
    def test_location_normalization(self):
        """Test if the system successfully translates shorthand to full names."""
        result = location_match_score("Philly", "Philadelphia")
        self.assertTrue(result["matched"])
        self.assertEqual(result["score"], 3)

    def test_national_location_override(self):
        """If a grant is nationwide, it should match ANY user location."""
        result = location_match_score("Boston, MA", "United States / Nationwide")
        self.assertTrue(result["matched"])
        self.assertEqual(result["score"], 3)

if __name__ == "__main__":
    unittest.main()