import unittest
from core.project_matcher import project_relevance_score, build_project_query

class TestProjectMatcherTasks(unittest.TestCase):
    def setUp(self):
        self.grant = {
            "metadata": {
                "grant_title": "Mental Health Innovation Grant",
                "project_area": "mental health, psychology",
                "demographic_requirements": "teens, adolescents"
            },
            "summary_text": "Supporting clinical research focused on youth mental health outcomes."
        }

    # --- INTENDED TASKS ---
    def test_high_relevance_scoring(self):
        """Test that exact keyword matches generate the highest score."""
        project_info = {
            "project_area": "mental health",
            "target_population": "teens",
            "project_description": "clinical research for youth"
        }
        score = project_relevance_score(project_info, self.grant)
        self.assertGreaterEqual(score, 8) 

    def test_low_relevance_scoring(self):
        """Test that completely unrelated projects score zero."""
        project_info = {
            "project_area": "robotics",
            "target_population": "seniors",
            "project_description": "building drones for aerial photography"
        }
        score = project_relevance_score(project_info, self.grant)
        self.assertEqual(score, 0)

    # --- EDGE CASES ---
    def test_partial_word_overlap(self):
        """Test if the system correctly attributes points for partial description overlap."""
        project_info = {
            "project_area": "general medicine",
            "target_population": "adults",
            "project_description": "We are conducting clinical research on outcomes."
        }
        score = project_relevance_score(project_info, self.grant)
        self.assertGreater(score, 0)
        self.assertLess(score, 8)

    def test_empty_query_builder(self):
        """If all project info is empty, it should return an empty string safely."""
        project_info = {"project_area": "", "project_description": "", "target_population": ""}
        query = build_project_query(project_info)
        self.assertEqual(query, "")

if __name__ == "__main__":
    unittest.main()