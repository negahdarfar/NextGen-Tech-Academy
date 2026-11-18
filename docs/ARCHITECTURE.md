# Architecture and status

## Pipeline

`research -> verify -> plan -> script -> package -> voice -> assets -> edit -> subtitles -> chapters/SEO -> quality gate -> human approval -> publish adapter`

## Integrated now

- All 11 YouTube Agent skills are linked project-locally as a pinned Git submodule at `.claude/`.
- The upstream submodule includes its six standard-library Python utilities and 21-hook formula data.
- Video policy rejects any primary upload under 60 seconds, non-long-form format, Shorts, non-English narration, or missing Persian subtitles.
- GitHub Actions runs unit tests and validates the example manifest.

## Not implemented yet

- Automated topic research and source verification
- Text-to-speech / voice generation
- Persian subtitle translation and timing
- Licensed media retrieval and FFmpeg rendering
- Thumbnail generation
- YouTube OAuth, upload, scheduling, and analytics ingestion

These are future adapters. The upstream skills themselves do not render or upload videos. Human approval remains mandatory.
