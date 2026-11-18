import unittest
from unittest.mock import patch
from nextgen_tech_academy.pipeline import run_pipeline

class PipelineTests(unittest.TestCase):
    @patch("nextgen_tech_academy.pipeline.render")
    @patch("nextgen_tech_academy.pipeline.synthesize")
    def test_runs_tts_then_render_with_supplied_persian_srt(self, synth, render):
        synth.return_value = 125.0
        render.return_value = {"output":"episode.mp4","duration_seconds":125.0}
        manifest = {"script":"script.txt","piper_model":"voice.onnx","image":"bg.png",
                    "persian_srt":"fa.srt","output":"episode.mp4","build_dir":"build-test"}
        result = run_pipeline(manifest)
        synth.assert_called_once()
        render.assert_called_once()
        self.assertEqual(result["narration_duration_seconds"],125.0)
        self.assertEqual(result["subtitle_mode"],"provided")

if __name__ == "__main__":
    unittest.main()
