# NextGen-Tech-Academy

An AI-assisted production workflow for English-language technology explainers and documentaries with Persian subtitles.

## Current preset

**60 seconds, standard 16:9 YouTube video, four linked 15-second clips.** The workflow drafts a bilingual script locally with Ollama, checks source references, prepares VidoGrid prompts, optionally creates local narration with Piper, downloads completed clips and assembles an MP4 with FFmpeg.

This is an evolving codebase. A successful unit-test run does not prove compatibility with a live VidoGrid account, a particular Piper voice model, or every local FFmpeg build.

## Setup

Requires Python 3.10+ and FFmpeg/ffprobe on PATH.

```bash
python -m pip install -e ".[dev]"
```

Optional local voice synthesis:

```bash
python -m pip install -e ".[voice]"
```

Install Ollama separately and pull the small local model:

```bash
ollama pull qwen2.5:3b
```

Copy `.env.example` to `.env` and add your VidoGrid API key locally. Never commit the key.

## One-minute workflow

1. Draft the English narration and Persian subtitles locally:

```bash
nextgen-academy draft-script --topic "How humanoid robots are changing manufacturing"
```

This uses the local Ollama service at `http://127.0.0.1:11434` and model `qwen2.5:3b` by default. It does not browse the web or verify factual claims. If Ollama is unavailable, create an empty template with:

```bash
nextgen-academy storyboard --topic "How humanoid robots are changing manufacturing"
```

2. Manually add at least two verified HTTPS sources to `output/storyboard.json`, each with `id`, `url`, `publisher`, and `checked: true`. Add a `claims` list; each factual claim must contain `text` and `source_ids` referencing supporting source IDs. Open and verify the sources yourself.

3. Run the editorial structure and source-reference gate:

```bash
nextgen-academy script-check
```

This catches missing fields and broken source references. It cannot establish whether a source truly supports a claim.

4. Create four linked 15-second video prompts from the storyboard:

```bash
nextgen-academy video-plan --topic "How humanoid robots are changing manufacturing"
```

This reads the scene descriptions, English narration and Persian subtitles from the storyboard. You can override the scene descriptions with four repeated `--scene "..." ` arguments.

5. Generate the Persian SRT subtitle track:

```bash
nextgen-academy subtitles
```

6. Optionally create English narration locally with Piper. Download a voice model and its matching `.onnx.json` configuration, and review its commercial-use license:

```bash
nextgen-academy voiceover --model models/piper/your-english-voice.onnx
```

7. Review the VidoGrid account balance and explicitly approve generation. This can consume credits:

```bash
nextgen-academy video-submit --confirm-paid-api
```

The command asks for a second interactive confirmation. No VidoGrid generation request is sent before that confirmation.

8. Poll the jobs and download completed clips:

```bash
nextgen-academy video-download
```

9. Create an editable YouTube metadata draft (title options, description template, chapters, tags and thumbnail prompt):

```bash
nextgen-academy youtube-package
```

10. Assemble the final MP4:

```bash
nextgen-academy video-render --subtitles output/persian.srt --narration-audio output/narration.wav
```

Omit `--narration-audio` if no narration track is available.

## Still to build

- Automated web research, primary-source discovery and evidence extraction.
- Automated fact verification beyond structural source-reference checks.
- Higher-quality script editing and human approval UI.
- Music, sound design, thumbnail image generation and visual QA.
- YouTube OAuth, channel authorization, upload, scheduling and analytics feedback.
- Automated competitor research and search-volume-based SEO.

YouTube publishing is intentionally not enabled. Human review of factual claims, translations, licensing, provider watermarks and the final exported video remains mandatory.

See [production pipeline](docs/PRODUCTION_PIPELINE.md) and [VidoGrid integration notes](docs/VIDEOGRID_INTEGRATION.md).
