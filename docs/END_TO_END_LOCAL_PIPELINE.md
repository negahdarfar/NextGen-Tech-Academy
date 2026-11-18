# End-to-end local video pipeline

The local orchestrator connects the offline components in sequence:

1. Piper converts the English script to WAV narration.
2. The script's actual generated audio duration must be at least 60 seconds.
3. If an English SRT is supplied, Argos Translate converts cue text to Persian
   while preserving timestamps; alternatively, provide a reviewed Persian SRT.
4. FFmpeg combines the background image, narration, and optional Persian
   subtitle track into a standard MP4.
5. FFprobe checks the final MP4 duration; outputs under 60 seconds are rejected.

## Manifest

Copy `examples/pipeline_manifest.example.json` and update paths to local files.
For offline translation, install Argos Translate and its English-to-Persian
language model, and set `english_srt`. If you already have a reviewed Persian
SRT, replace that field with `persian_srt`. Do not set both.

## Run

```bash
PYTHONPATH=src python -m nextgen_tech_academy.pipeline path/to/manifest.json
```

This first end-to-end route uses one still image as the visual background.
It does not create scenes, animate graphics, transcribe audio, generate a
thumbnail, or upload to YouTube. All assets must be supplied locally, and the
result must be reviewed before publication.
