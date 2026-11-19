# Cloud-first production pipeline

The target is a standard 60-second, 16:9 YouTube video made from four 15-second stock-footage sections. Narration is English and subtitles are Persian. GitHub Actions runs the cloud workflow without Ollama or an always-on laptop.

## Automated run

Run **Actions → Automated YouTube video factory → Run workflow** or use the schedule (Tuesday and Friday, 06:17 UTC).

1. Discover a technology topic and collect RSS research leads.
2. Use Gemini (with optional Groq/OpenRouter fallback) to draft four narration scenes and Persian subtitles.
3. Retrieve matching landscape footage from Pexels and record creator/source attribution.
4. Generate English narration with Edge TTS.
5. Trim four stock clips to 15 seconds each, assemble with FFmpeg, and mux narration and Persian subtitles.
6. Validate final duration (55–70 seconds); upload through YouTube OAuth as private only when requested.

## Required GitHub Actions secrets

- `GEMINI_API_KEY` (or another configured cloud LLM key)
- `PEXELS_API_KEY` (free Pexels API key; VidoGrid is no longer used)
- `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with `youtube.upload` scope)

Optional Actions variables: `LLM_PROVIDER_ORDER` and `OPENROUTER_MODEL`.

## Important limitations and safeguards

- Pexels footage is real stock footage, not AI-generated video. It is illustrative B-roll and may not exactly depict each narrated event.
- Pexels API limits and license terms apply. The workflow stores creator names and source URLs in its output and video description; review attribution before public release.
- The workflow uploads privately by default. Public uploads remain disabled.
- Automated tests do not validate live Pexels availability, TTS, OAuth or actual YouTube upload. Supervise the first run.
