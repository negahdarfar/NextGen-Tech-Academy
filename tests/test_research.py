import unittest
from nextgen_tech_academy.research import validate_research_pack

class ResearchPackTests(unittest.TestCase):
    def valid_pack(self):
        return {
            "sources": [
                {"id":"s1","url":"https://example.com/a","publisher":"Example A","published_at":"2026-01-01","accessed_at":"2026-11-18"},
                {"id":"s2","url":"https://example.org/b","publisher":"Example B","published_at":"2026-01-02","accessed_at":"2026-11-18"}
            ],
            "claims": [{"text":"A factual claim to verify","source_ids":["s1","s2"]}]
        }

    def test_accepts_grounded_pack(self):
        self.assertEqual(validate_research_pack(self.valid_pack()), [])

    def test_rejects_claim_without_evidence(self):
        pack=self.valid_pack()
        pack["claims"][0]["source_ids"]=[]
        self.assertTrue(any("at least one source_id" in e for e in validate_research_pack(pack)))

    def test_rejects_duplicate_domain(self):
        pack=self.valid_pack()
        pack["sources"][1]["url"]="https://example.com/other"
        self.assertTrue(any("distinct source domains" in e for e in validate_research_pack(pack)))

    def test_rejects_unknown_source_reference(self):
        pack=self.valid_pack()
        pack["claims"][0]["source_ids"]=["missing"]
        self.assertTrue(any("unknown source ids" in e for e in validate_research_pack(pack)))

if __name__ == "__main__":
    unittest.main()
