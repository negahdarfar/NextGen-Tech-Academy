# Cloud-first documentary production pipeline

The production target is a standard 16:9 YouTube documentary, selectable from 3 to 10 minutes. Narration is English and Persian subtitles are synchronized as a subtitle track. GitHub Actions runs the workflow without Ollama or an always-on laptop.

## Automated run

Open **Actions → Automated YouTube documentary factory → Run workflow** or use the schedule (Tuesday and Friday, 06:17 UTC).

1. Discover a technology topic when no topic is supplied and collect up to 20 RSS research leads.
2. Ask the configured cloud LLM to draft 12-40 ordered scenes, English narration and Persian translations (15 seconds per scene).
3. Retrieve matching landscape footage from Pexels and record creator/source attribution.
4. Generate English narration with Edge TTS, normalizing each scene to 15 seconds.
5. Loop/trim each stock clip to the target scene length, assemble with FFmpeg and mux narration plus Persian subtitles.
6. Validate the rendered duration against the requested 3-10 minute target.
7. Generate YouTube title, description, tags, chapters and thumbnail prompt.
8. Preserve production files as an Actions artifact. Upload is optional for manual runs and private-only by default.

## Required GitHub Actions secrets

- `GEMINI_API_KEY` (or another configured cloud LLM key)
- `PEXELS_API_KEY` (Pexels API key; VidoGrid is not used)
- `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with `youtube.upload` scope, required only for upload)

Optional Actions variables: `LLM_PROVIDER_ORDER` and `OPENROUTER_MODEL`.

## Safeguards and limitations

- Pexels footage is real stock footage, not AI-generated video. It is illustrative B-roll and may not exactly depict each narrated event.
- Pexels API limits, Gemini free-tier quotas and GitHub Actions usage limits apply; this is not unlimited free compute.
- RSS results are discovery leads, not fact-checked primary evidence. Review all claims and source links.
- Manual upload defaults off. When enabled, upload is private. Public publishing remains disabled in the workflow.
- Automated tests do not validate live Pexels availability, TTS, OAuth or an actual YouTube upload. Supervise the first end-to-end run.
