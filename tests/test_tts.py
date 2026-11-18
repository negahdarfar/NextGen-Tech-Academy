import tempfile
import unittest
import wave
from pathlib import Path
from nextgen_tech_academy.tts import wav_duration

class TtsTests(unittest.TestCase):
    def test_reads_wav_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "voice.wav"
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(b"\x00\x00" * 32000)
            self.assertAlmostEqual(wav_duration(path), 2.0)

if __name__ == "__main__":
    unittest.main()
