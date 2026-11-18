# Local MP4 rendering (first renderer)

The initial renderer creates a standard MP4 from one still image, one narration
audio file, and an optional Persian SRT subtitle track. It is deliberately
small and local-first; it does not yet assemble multi-scene timelines, animate
visuals, generate narration, or source images.

## Install

- Python 3.10+
- FFmpeg including `ffmpeg` and `ffprobe` on PATH

Examples:
- Ubuntu/Debian: `sudo apt install ffmpeg`
- macOS with Homebrew: `brew install ffmpeg`
- Windows: install an FFmpeg build and add its `bin` directory to PATH.

## Prepare inputs

Create an image, English narration audio, and Persian SRT. Keep rights/attribution
records for all visual and audio assets. The renderer does not download media.

Copy `examples/render_manifest.example.json` to a working manifest and update
its paths. Then run:

```bash
PYTHONPATH=src python -m nextgen_tech_academy.render path/to/render-manifest.json
```

The renderer muxes Persian subtitles as a soft subtitle track (not burned into
the image), probes the actual output duration, and deletes/rejects any render
shorter than 60 seconds. A separate review is still needed for audio/video
quality, factual accuracy, subtitle synchronization, aspect ratio, and rights.

## Known limitation

This is a proof-of-pipeline renderer, not the finished documentary editor.
Multi-scene timelines, transitions, captions burned into the picture, generated
visuals, and automated TTS are planned adapters.
