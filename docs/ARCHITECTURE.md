# Architecture and implementation status

## Pipeline

`research -> verify -> plan -> script -> package -> voice -> assets -> edit -> subtitles -> chapters/SEO -> quality gate -> human approval -> publish adapter`

## Implemented in this branch

- All 11 YouTube Agent skills are linked project-locally as a pinned Git submodule at `.claude/`.
- The upstream submodule includes its six standard-library Python utilities and 21-hook formula data.
- Video manifest policy rejects primary uploads under 60 seconds, non-long-form format, Shorts, non-English narration, or non-Persian subtitle metadata.
- Script timing estimator checks approximate spoken duration before recording/TTS (default 145 words per minute; actual duration must be checked after rendering).
- SRT structural validator checks cue numbering, timestamp format/ranges, empty cues, and overlapping timings.
- Research-pack validator requires source URLs, publishers, publication/access dates, distinct domains, and traceable source IDs for each factual claim.
- GitHub Actions runs unit tests and validates the example manifest and sample script.

## Not implemented yet

- Automated topic research and source verification
- Text-to-speech / voice generation
- Persian translation quality checks and subtitle alignment against generated audio
- Licensed media retrieval and FFmpeg rendering
- Thumbnail generation
- YouTube OAuth, upload, scheduling, and analytics ingestion

These require independent adapters and end-to-end tests. The upstream skills themselves do not render or upload videos. Human approval remains mandatory.
