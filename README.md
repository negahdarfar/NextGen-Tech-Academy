# NextGen-Tech-Academy

An AI-assisted production workflow for English-language technology documentaries with Persian subtitles.

## Current preset

**One minute, standard 16:9 YouTube video, four linked 15-second clips.** The project prepares prompts, submits them to VidoGrid only after explicit confirmation, polls and downloads results, and assembles a final MP4 with FFmpeg. This is a working code path, not yet verified against a live VidoGrid account.

## Setup

Requires Python 3.10+ and FFmpeg on PATH.

```bash
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and add your VidoGrid API key locally. Never commit the key.

## One-minute workflow

1. Create a four-scene storyboard:

```bash
nextgen-academy storyboard --topic "How humanoid robots are changing manufacturing"
```

2. Create four linked visual prompts (no API charge):

```bash
nextgen-academy video-plan --topic "How humanoid robots are changing manufacturing"
```

You can replace the default scene descriptions with four `--scene "..." ` arguments.

3. Add reviewed English narration and Persian translations to the scene entries in `output/video-plan.json`. The code does not invent or fact-check documentary claims.

4. Submit only after checking the VidoGrid balance:

```bash
nextgen-academy video-submit --confirm-paid-api
```

This asks for a second interactive confirmation. Generation may consume credits.

5. Wait for jobs and download the MP4 clips:

```bash
nextgen-academy video-download
```

6. Create a Persian subtitle track and assemble the video:

```bash
nextgen-academy subtitles
nextgen-academy video-render --subtitles output/persian.srt
```

If narration audio is ready, add `--narration-audio path/to/narration.mp3` to the render command.

## What is not automated yet

- Research source collection and fact-check approval.
- High-quality English script writing and Persian translation.
- Text-to-speech generation, background music and sound design.
- Thumbnail generation, chapter/SEO package, analytics feedback loop.
- YouTube OAuth and publishing (intentionally disabled until secure channel authorization and approval controls are built).

The storyboard defaults are structural scene suggestions, not factual scripts. A human must verify claims, subtitles, licensing and final video before publishing.

See [the full production guide](docs/PRODUCTION_PIPELINE.md) and [VidoGrid notes](docs/VIDOGRID_INTEGRATION.md).
