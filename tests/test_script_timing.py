import unittest
from nextgen_tech_academy.script_timing import estimate_duration_seconds

class ScriptTimingTests(unittest.TestCase):
    def test_estimates_one_minute_script(self):
        self.assertEqual(estimate_duration_seconds(" ".join(["word"] * 145)), 60)

    def test_empty_script_is_zero(self):
        self.assertEqual(estimate_duration_seconds(""), 0)

    def test_rejects_invalid_wpm(self):
        with self.assertRaises(ValueError):
            estimate_duration_seconds("hello", 0)

if __name__ == "__main__":
    unittest.main()
