# NextGen Tech Academy

An AI-assisted production workspace for evidence-led technology education videos.

## Channel rules

- **YouTube format:** standard videos (long-form), not Shorts.
- **Minimum duration:** 60 seconds; the automated manifest gate rejects shorter videos.
- **Language:** English narration with Persian subtitles.
- **Topics:** AI and agents, robotics, chips and computing, biotech and medical technology, space, EVs and batteries, AR/VR, and emerging inventions.
- **Publishing:** human approval is required.

## The 11 YouTube Agent skills

The complete upstream MIT-licensed skill pack is connected as a Git submodule at `.claude/`. It provides:
`yt-script`, `yt-package`, `yt-edit`, `yt-comment`, `yt-plan`, `yt-viral`, `yt-retention`, `yt-shorts`, `yt-seo`, `yt-chapters`, and `yt-audit`, plus six dependency-free Python utilities.

`yt-shorts` is retained only for optional repurposing research. It must not create or publish primary channel uploads.

## Setup

Clone with skills included:

```bash
git clone --recurse-submodules https://github.com/negahdarfar/NextGen-Tech-Academy.git
cd NextGen-Tech-Academy
```

If already cloned without submodules:

```bash
git submodule update --init --recursive
```

Python 3.10+ is required. The initial policy toolkit uses only the standard library:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m nextgen_tech_academy.video_policy examples/video_metadata.json
```

## Pipeline roadmap

Research and source verification → topic planning → script and hook scoring → title/thumbnail package → voiceover and asset plan → editing/rendering → English audio + Persian subtitles → chapters and SEO → quality gate → human approval → optional YouTube upload adapter.

The upstream skills write and analyze; they do **not** render video or publish to YouTube. Rendering, subtitle generation, and YouTube API publishing will be separate adapters and will not be marked complete until implemented and tested. No paid API is required by this scaffold.

## License and attribution

Project-specific code is MIT licensed. The upstream skill pack remains under its original MIT license in the `.claude` submodule.
