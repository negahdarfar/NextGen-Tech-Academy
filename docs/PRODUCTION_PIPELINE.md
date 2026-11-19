# Cloud-first production pipeline

The target is a standard 60-second, 16:9 YouTube video made from four ordered 15-second clips. Narration is English and subtitles are Persian. The cloud path does not require Ollama or an always-on laptop.

## Automated run

The GitHub Actions workflow `.github/workflows/auto-publish.yml` can be started manually or on its Tuesday/Friday schedule.

```bash
nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing"
nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing" --upload
```

When no topic is supplied, RSS headlines are used to choose a topic. The automated run:

1. Discovers candidate articles and papers from RSS feeds.
2. Uses the configured cloud LLM fallback order (Gemini, Groq, OpenRouter) to draft four English narration scenes and Persian translations.
3. Carries source URLs and claim-to-source IDs into the storyboard. RSS discovery and model-generated citations are not proof; review source contents.
4. Creates four linked video prompts.
5. Generates English narration using the configured cloud TTS adapter and Persian SRT subtitles.
6. Checks VidoGrid account data and refuses to submit unless a separately reported free/trial balance and model-specific cost estimates cover the complete rotation.
7. Rotates selected models across clips, saves each accepted job UUID, polls job history and downloads completed clips.
8. Assembles the clips with FFmpeg and checks that the output is approximately one minute.
9. Creates YouTube metadata and, only when `--upload` is supplied, uploads through OAuth as **private** by default.

## Configure cloud providers

Store keys as GitHub Actions Secrets, never in the repository:

- `VIDOGRID_API_KEY`
- At least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`
- `YOUTUBE_TOKEN_JSON` for OAuth upload with the `youtube.upload` scope

Configure these Actions Variables:

- `LLM_PROVIDER_ORDER`, e.g. `gemini,groq,openrouter`
- `VIDOGRID_MODEL_ROTATION`, e.g. `grok-imagine-video-1.5-lite,veo-3.1-fast,omni-1.2-flash`
- `VIDOGRID_MODEL_CREDIT_COSTS`, JSON object with a checked current credit estimate for every selected model

The credit costs are account-specific and must be taken from the current VidoGrid account/pricing interface. Do not copy example values as if they were real prices. If the API only reports a combined balance rather than a separate free/trial balance, the workflow stops before generating any clip.

## Upload and publishing safety

- Upload is private by default.
- Public visibility is blocked unless `YOUTUBE_ALLOW_PUBLIC=true` is deliberately configured.
- The YouTube OAuth token must be refreshed and valid before VidoGrid generation begins.
- Public publishing should remain disabled until the first private upload and a complete human quality review succeed.
- GitHub Actions minutes, storage and artifact quotas apply.

## Local development

Ollama remains an optional development tool, not a cloud runtime dependency. The cloud path can be tested locally with Python, FFmpeg and the `cloud` extra, provided all required credentials are supplied in the environment or a local ignored `.env` file.

## Not yet proven in a live account

Automated tests mock external providers. They do not validate the user's VidoGrid account balance schema, live model entitlements, real job history response, TTS availability, YouTube OAuth or actual video quality. The first run must be supervised and private.
