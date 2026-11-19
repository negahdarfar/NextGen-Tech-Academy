# Architecture

## Design principle

Each production stage is an independent component with explicit inputs and outputs. Provider integrations must be replaceable, testable, and disabled unless configured. The initial implementation is deliberately plan-only.

## Proposed pipeline

1. **Topic discovery** — identify candidate subjects and record why they are timely.
2. **Research** — gather primary sources, publication dates, quotes, and source URLs.
3. **Fact review** — flag unsupported claims, conflicts, and uncertainty.
4. **Script** — create an English narration script with a target duration and audience.
5. **Localization** — produce Persian subtitles and validate timing/encoding.
6. **Visual planning** — map narration sections to footage, diagrams, and generated assets.
7. **Asset acquisition** — use licensed/openly usable media or generated visuals; preserve provenance.
8. **Rendering** — assemble audio, visuals, captions, and transitions.
9. **Quality assurance** — inspect duration, audio levels, subtitle sync, factual claims, and rights.
10. **YouTube packaging** — prepare metadata, chapters, thumbnail, and visibility settings.
11. **Publishing** — future module; requires OAuth, explicit channel authorization, quota/error handling, and approval.

## Provider boundaries

- Research provider: returns sourced records, not unsupported prose.
- Language model provider: accepts structured prompts and returns typed content.
- Speech provider: returns audio plus metadata such as duration and voice settings.
- Media provider: returns assets with license/provenance metadata.
- Renderer: consumes a timeline and produces a local video file.
- YouTube publisher: must be isolated and disabled by default.

## Local-first strategy

Use local tools when they meet quality and performance needs. Ollama is an optional local language-model endpoint. The default configuration points to localhost, but the current foundation does not make network calls to it.

## Reliability

- Persist intermediate artifacts so a failed stage can resume.
- Make stages idempotent where possible.
- Record provider, model, prompt version, source URLs, and asset licenses.
- Never publish automatically until a separate approval gate is implemented.
