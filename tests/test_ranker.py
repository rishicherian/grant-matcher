import unittest
from core.ranker import fallback_rank

class TestRanker(unittest.TestCase):
    def setUp(self):
        self.grants = [
            {
                "metadata": {"grant_title": "City-Wide Arts Initiative"},
                "summary_text": "General funding for arts programs."
            },
            {
                "metadata": {"grant_title": "West Philly Creative Grant"},
                "summary_text": "Funding for local artists."
            }
        ]

    def test_fallback_rank_structure(self):
        """Ensure the fallback ranking successfully formats data for the frontend."""
        ranked = fallback_rank(self.grants)
        
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[0]["grant_title"], "City-Wide Arts Initiative")
        self.assertIn("Summary:", ranked[0]["explanation"])

if __name__ == "__main__":
    unittest.main()