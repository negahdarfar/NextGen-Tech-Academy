import unittest
from nextgen_tech_academy.video_policy import validate_video

class VideoPolicyTests(unittest.TestCase):
    def valid(self):
        return {"duration_seconds":60,"format":"long_form","is_short":False,
                "narration_language":"en","subtitle_language":"fa"}

    def test_accepts_exactly_one_minute(self):
        self.assertEqual(validate_video(self.valid()), [])

    def test_rejects_under_one_minute(self):
        data=self.valid(); data["duration_seconds"]=59
        self.assertTrue(any("at least 60 seconds" in e for e in validate_video(data)))

    def test_rejects_shorts(self):
        data=self.valid(); data["format"]="shorts"; data["is_short"]=True
        errors=validate_video(data)
        self.assertTrue(any("long_form" in e for e in errors))
        self.assertTrue(any("Shorts are disabled" in e for e in errors))

    def test_requires_english_audio_and_persian_subtitles(self):
        data=self.valid(); data["narration_language"]="fa"; data["subtitle_language"]="en"
        self.assertEqual(len(validate_video(data)), 2)

if __name__ == "__main__":
    unittest.main()
