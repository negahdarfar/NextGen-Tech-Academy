# Architecture

## Design principle

Each production stage is an independent component with explicit inputs and outputs. Provider integrations must be replaceable, testable, and disabled unless configured.

## Proposed pipeline

1. **Topic discovery** — identify candidate subjects and record why they are timely.
2. **Research** — gather primary sources, publication dates, quotes, and source URLs.
3. **Fact review** — flag unsupported claims, conflicts, and uncertainty.
4. **Script** — create an English narration script with a target duration and audience.
5. **Localization** — produce Persian subtitles and validate timing/encoding.
6. **Visual planning** — map narration sections to a storyboard and ordered shots.
7. **Prompt continuity** — apply a shared visual bible and carry scene, subject, lighting, and camera continuity between clips.
8. **Pexels stock footage** — search for suitable landscape clips, download licensed stock footage, and persist a local manifest for rendering.
9. **Asset retrieval and rendering** — retrieve completed clips, validate actual duration, and assemble in storyboard order with FFmpeg.
10. **Quality assurance** — inspect duration, audio levels, subtitle sync, factual claims, and rights.
11. **YouTube packaging** — prepare metadata, chapters, thumbnail, and visibility settings.
12. **Publishing** — future module; requires OAuth, explicit channel authorization, quota/error handling, and approval.

## Provider boundaries

- Research provider: returns sourced records, not unsupported prose.
- Language model provider: accepts structured prompts and returns typed content.
- Speech provider: returns audio plus metadata such as duration and voice settings.
- Media provider: returns assets with license/provenance metadata.
- Pexels adapter: uses the free developer API to search and download existing stock footage; no video-generation credits are purchased.
- Renderer: consumes a local timeline and produces a video file.
- YouTube publisher: must be isolated and disabled by default.

## Local-first strategy

Use local tools when they meet quality and performance needs. Ollama is an optional local language-model endpoint. Pexels is an optional remote stock-footage source; its free API is rate-limited and is not a generative video model.

## Reliability

- Persist intermediate artifacts so a failed stage can resume.
- Make stages idempotent where possible.
- Record provider, model, prompt version, source URLs, and asset licenses.
- Do not assume mobile-app free quotas apply to API usage.
- Never publish automatically until a separate approval gate is implemented.
