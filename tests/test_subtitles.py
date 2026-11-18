import unittest
from nextgen_tech_academy.subtitles import validate_srt, timestamp_ms

class SubtitleTests(unittest.TestCase):
    def test_valid_two_cue_srt(self):
        srt = "1\n00:00:00,000 --> 00:00:02,000\nسلام\n\n2\n00:00:02,100 --> 00:00:04,000\nدنیا"
        self.assertEqual(validate_srt(srt), [])

    def test_detects_overlap(self):
        srt = "1\n00:00:00,000 --> 00:00:03,000\nاول\n\n2\n00:00:02,000 --> 00:00:04,000\nدوم"
        self.assertTrue(any("overlaps" in e for e in validate_srt(srt)))

    def test_detects_empty_file(self):
        self.assertTrue(validate_srt(""))

    def test_timestamp_conversion(self):
        self.assertEqual(timestamp_ms("00:01:02,003"), 62003)

if __name__ == "__main__":
    unittest.main()
