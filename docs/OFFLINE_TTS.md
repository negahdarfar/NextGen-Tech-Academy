# Offline English narration with Piper

The project includes an adapter for the Piper command-line TTS engine. It does
not call a cloud API and does not require an API key.

## Requirements

1. Install a Piper CLI build appropriate for your operating system.
2. Download an English Piper voice model (`.onnx`) and its matching config
   file from a trusted Piper voice-model source.
3. Keep the model files locally; do not commit large voice models to Git.

## Generate narration

```bash
PYTHONPATH=src python -m nextgen_tech_academy.tts examples/sample_script.txt \
  --model /path/to/en_US-lessac-medium.onnx \
  --output build/narration-en.wav
```

The adapter sends the script to the local Piper process, writes WAV audio, and
checks its actual duration. It deletes and rejects audio shorter than 60 seconds.

Voice quality, pronunciation of technical terms, pacing, and pronunciation
dictionaries still require listening and review. Piper model licenses vary;
check the selected voice's license before commercial use.
