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
- Offline Piper TTS adapter generates English WAV narration from a local voice model and rejects audio under 60 seconds.
- Optional Argos Translate adapter translates English SRT cue text into Persian offline while preserving timestamps; requires a separately installed `en -> fa` model and human language review.
- First local FFmpeg renderer creates MP4 from a background image, narration audio, and optional Persian SRT soft-subtitle track; FFprobe verifies the actual duration and rejects output under 60 seconds.
- GitHub Actions runs unit tests and validates the example manifest and sample script.

## Not implemented yet

- Automated topic research and source verification
- Text-to-speech / voice generation
- Persian translation quality checks and subtitle alignment against generated audio
- Multi-scene editing, transitions, animated visuals, and licensed media retrieval (basic still-image + audio FFmpeg render is implemented)
- Thumbnail generation
- YouTube OAuth, upload, scheduling, and analytics ingestion

These require independent adapters and end-to-end tests. The upstream skills themselves do not render or upload videos. Human approval remains mandatory.
