import unittest
from pathlib import Path
from nextgen_tech_academy.render import build_ffmpeg_command

class RenderCommandTests(unittest.TestCase):
    def test_builds_video_with_audio_and_soft_persian_subtitles(self):
        cmd = build_ffmpeg_command(Path("/tmp/bg image.png"), Path("/tmp/voice.wav"),
                                   Path("/tmp/out.mp4"), Path("/tmp/fa.srt"))
        self.assertIn("/tmp/bg image.png", cmd)
        self.assertIn("mov_text", cmd)
        self.assertIn("language=fas", cmd)
        self.assertEqual(cmd[-1], "/tmp/out.mp4")

    def test_builds_without_subtitles(self):
        cmd = build_ffmpeg_command(Path("/tmp/bg.png"), Path("/tmp/voice.wav"),
                                   Path("/tmp/out.mp4"))
        self.assertNotIn("mov_text", cmd)
        self.assertIn("-shortest", cmd)

if __name__ == "__main__":
    unittest.main()
