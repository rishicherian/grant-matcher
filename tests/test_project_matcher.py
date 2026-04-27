import unittest
from core.project_matcher import project_relevance_score

class TestProjectMatcher(unittest.TestCase):
    def setUp(self):
        self.grant = {
            "metadata": {
                "grant_title": "Mental Health Innovation Grant",
                "project_area": "mental health, psychology",
                "demographic_requirements": "teens, adolescents"
            },
            "summary_text": "Supporting clinical research focused on youth mental health outcomes."
        }

    def test_high_relevance_scoring(self):
        """Test that matching keywords generate a high relevance score."""
        project_info = {
            "project_area": "mental health",
            "target_population": "teens",
            "project_description": "clinical research for youth"
        }
        score = project_relevance_score(project_info, self.grant)
        self.assertGreaterEqual(score, 8) # 5 for area + 3 for demographic

    def test_low_relevance_scoring(self):
        """Test that unrelated projects score zero."""
        project_info = {
            "project_area": "robotics",
            "target_population": "seniors",
            "project_description": "building drones for aerial photography"
        }
        score = project_relevance_score(project_info, self.grant)
        self.assertEqual(score, 0)

if __name__ == "__main__":
    unittest.main()