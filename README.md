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

2. Open `output/storyboard.json` and fill all four `narration_en` and `subtitle_fa` fields. The English narration must be fact-checked and the Persian text must be its faithful translation. The code does not invent or fact-check documentary claims.

3. Create four linked visual prompts (no API charge). The command reads your edited storyboard, including narration and subtitle fields:

```bash
nextgen-academy video-plan --topic "How humanoid robots are changing manufacturing"
```

You can replace the visual scene descriptions with four `--scene "..." ` arguments.

5. Generate the Persian subtitle file:

```bash
nextgen-academy subtitles
```

6. If Piper is installed and a properly licensed English voice model is downloaded, generate narration locally:

```bash
nextgen-academy voiceover --model models/piper/your-english-voice.onnx
```

The model and its matching `.onnx.json` file are both required. Review the model card and commercial-use terms before publishing.

7. Submit only after checking the VidoGrid balance:

```bash
nextgen-academy video-submit --confirm-paid-api
```

This asks for a second interactive confirmation. Generation may consume credits.

8. Wait for jobs and download the MP4 clips:

```bash
nextgen-academy video-download
```

9. Generate an editable YouTube metadata package (title options, description template, chapters, tags and thumbnail prompt):

```bash
nextgen-academy youtube-package
```

10. Assemble the video with the Persian subtitle track and narration audio:

```bash
nextgen-academy video-render --subtitles output/persian.srt --narration-audio output/narration.wav
```

## What is not automated yet

- Automated research source collection, fact-checking and script drafting (still manual at present).
- Automatic voiceover generation is now wired to optional local Piper; a voice model must be installed and its license checked.
- Background music and sound design.
- Thumbnail image generation and analytics feedback loop. An editable SEO/publishing metadata draft is generated; it is not keyword research or a ranking guarantee.
- YouTube OAuth and publishing (intentionally disabled until secure channel authorization and approval controls are built).

The storyboard defaults are structural scene suggestions, not factual scripts. A human must verify claims, subtitles, licensing and final video before publishing.

See [the full production guide](docs/PRODUCTION_PIPELINE.md) and [VidoGrid notes](docs/VIDOGRID_INTEGRATION.md).
