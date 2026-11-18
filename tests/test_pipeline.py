import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nextgen_tech_academy.pipeline import run_pipeline

class PipelineTests(unittest.TestCase):
    @patch("nextgen_tech_academy.pipeline.render")
    @patch("nextgen_tech_academy.pipeline.synthesize")
    def test_runs_tts_then_render_with_supplied_persian_srt(self, synth, render):
        synth.return_value = 125.0
        render.return_value = {"output":"episode.mp4","duration_seconds":125.0}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subtitles = root / "fa.srt"
            subtitles.write_text("1\\n00:00:00,000 --> 00:00:02,000\\nسلام", encoding="utf-8")
            manifest = {"script":str(root/"script.txt"),"piper_model":str(root/"voice.onnx"),
                        "image":str(root/"bg.png"),"persian_srt":str(subtitles),
                        "output":"episode.mp4","build_dir":str(root/"build")}
            result = run_pipeline(manifest)
        synth.assert_called_once()
        render.assert_called_once()
        self.assertEqual(result["narration_duration_seconds"],125.0)
        self.assertEqual(result["subtitle_mode"],"provided")

if __name__ == "__main__":
    unittest.main()
