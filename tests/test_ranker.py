import unittest
from core.ranker import fallback_rank

class TestRankerFailures(unittest.TestCase):
    def setUp(self):
        self.grants = [
            {
                "id": "grant_1",
                "metadata": {"grant_title": "City-Wide Arts Initiative"},
                "summary_text": "General funding for arts programs."
            },
            {
                "id": "grant_2",
                "metadata": {"grant_title": "West Philly Creative Grant"},
                "summary_text": "Funding for local artists."
            }
        ]

    # --- FAILURE RECOVERY ---
    def test_fallback_rank_structure(self):
        """If the LLM API times out, the fallback must perfectly mimic the expected JSON structure."""
        ranked = fallback_rank(self.grants)
        
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[0]["grant_title"], "City-Wide Arts Initiative")
        self.assertIn("Summary:", ranked[0]["explanation"])

    def test_empty_grants_handling(self):
        """If an empty list is passed to the ranker, it should safely return an empty list."""
        ranked = fallback_rank([])
        self.assertEqual(len(ranked), 0)
        self.assertEqual(ranked, [])

    def test_missing_title_fallback(self):
        """If a grant is missing its title metadata, the fallback should generate a placeholder instead of crashing."""
        broken_grant = [{"metadata": {}, "summary_text": "Some text"}]
        ranked = fallback_rank(broken_grant)
        self.assertEqual(ranked[0]["grant_title"], "Grant 1")

if __name__ == "__main__":
    unittest.main()