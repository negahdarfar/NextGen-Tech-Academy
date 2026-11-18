# NextGen Tech Academy

An AI-assisted production workspace for evidence-led technology education videos.

## Channel rules

- **YouTube format:** standard videos (long-form), not Shorts.
- **Minimum duration:** 60 seconds; the automated manifest gate rejects shorter videos.
- **Language:** English narration with Persian subtitles.
- **Topics:** AI and agents, robotics, chips and computing, biotech and medical technology, space, EVs and batteries, AR/VR, and emerging inventions.
- **Publishing:** human approval is required.

## The 11 YouTube Agent skills

The complete upstream MIT-licensed skill pack is connected as a Git submodule at `.claude/`. It provides: `yt-script`, `yt-package`, `yt-edit`, `yt-comment`, `yt-plan`, `yt-viral`, `yt-retention`, `yt-shorts`, `yt-seo`, `yt-chapters`, and `yt-audit`, plus six dependency-free Python utilities.

`yt-shorts` is retained only for optional repurposing research. It must not create or publish primary channel uploads.

## Setup

```bash
git clone --recurse-submodules https://github.com/negahdarfar/NextGen-Tech-Academy.git
cd NextGen-Tech-Academy
```

If already cloned without submodules: `git submodule update --init --recursive`.

Python 3.10+; no Python runtime dependencies are needed for the included validators:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m nextgen_tech_academy.video_policy examples/video_metadata.json
PYTHONPATH=src python -m nextgen_tech_academy.script_timing examples/sample_script.txt
```

The SRT validator is available as `nextgen_tech_academy.subtitles.validate_srt` and checks cue structure, timestamps, sequence, and overlap. The offline Piper adapter (`nextgen_tech_academy.tts`) can generate English WAV narration without a cloud API when a local Piper voice model is installed. The local FFmpeg renderer (`nextgen_tech_academy.render`) muxes a still-image background, narration audio, and optional Persian soft subtitles into MP4, then probes and rejects outputs under 60 seconds. The optional Argos Translate adapter can translate English SRT cue text to Persian offline while preserving timestamps (requires an installed `en -> fa` model). See `docs/OFFLINE_TTS.md`, `docs/OFFLINE_SUBTITLES.md`, and `docs/LOCAL_RENDERING.md`. See `docs/LOCAL_RENDERING.md`. It does not judge translation quality or synchronization against audio. The research-pack validator (`nextgen_tech_academy.research.validate_research_pack`) requires traceable claims, dated sources, and at least two distinct domains; see `docs/RESEARCH_STANDARD.md`.

## Pipeline roadmap

Research and source verification → topic planning → script and hook scoring → title/thumbnail package → voiceover and asset plan → editing/rendering → English audio + Persian subtitles → chapters and SEO → quality gate → human approval → optional YouTube upload adapter.

The upstream skills write and analyze; they do **not** render video or publish to YouTube. Automated research, TTS, Persian subtitle translation/alignment, licensed media retrieval, FFmpeg rendering, thumbnail generation, YouTube OAuth/upload, scheduling, and analytics are separate adapters still to be implemented and tested. No paid API is required by this scaffold.
