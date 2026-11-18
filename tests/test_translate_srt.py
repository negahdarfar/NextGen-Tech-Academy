import unittest
from nextgen_tech_academy.translate_srt import translate_srt_content

class TranslateSrtTests(unittest.TestCase):
    def test_translates_text_and_preserves_timing(self):
        source = "1\n00:00:00,000 --> 00:00:02,000\nHello world"
        result = translate_srt_content(source, lambda text: "سلام دنیا")
        self.assertIn("00:00:00,000 --> 00:00:02,000", result)
        self.assertTrue(result.endswith("سلام دنیا\n"))

    def test_rejects_empty_translation(self):
        source = "1\n00:00:00,000 --> 00:00:02,000\nHello world"
        with self.assertRaises(ValueError):
            translate_srt_content(source, lambda text: "")

if __name__ == "__main__":
    unittest.main()
