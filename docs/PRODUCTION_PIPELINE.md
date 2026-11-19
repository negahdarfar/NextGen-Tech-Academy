# Cloud-first production pipeline

The target is a standard 60-second, 16:9 YouTube video. Narration is English and subtitles are Persian. The cloud path does not require Ollama or an always-on laptop.

## Automated run

The GitHub Actions workflow .github/workflows/auto-publish.yml can be started manually or on its Tuesday/Friday schedule.

    nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing"
    nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing" --upload

When no topic is supplied, RSS headlines are used to choose a topic. The automated run:

1. Discovers candidate articles and papers from RSS feeds.
2. Uses the configured cloud LLM fallback order to draft four English narration scenes and Persian translations.
3. Carries source URLs and claim-to-source IDs into the storyboard. RSS discovery and model-generated citations are not proof; review source contents.
4. Creates four linked storyboard scenes.
5. Generates English narration using the configured cloud TTS adapter and Persian SRT subtitles.
6. Searches Pexels for suitable landscape stock footage and downloads one clip of at least 15 seconds per scene using the free API.
7. Assembles the footage with FFmpeg, narration and subtitles, then checks that the output is approximately one minute.
8. Creates YouTube metadata and, only when --upload is supplied, uploads through OAuth as private by default.

## Configure cloud providers

Store keys as GitHub Actions Secrets, never in the repository:

- PEXELS_API_KEY — free Pexels developer API key for stock footage.
- At least one of GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY for cloud writing.
- YOUTUBE_TOKEN_JSON for OAuth upload with the youtube.upload scope.

Pexels API use is free subject to its published rate limits and license. It returns existing stock footage; it is not an AI text-to-video generator. If no suitable clip is available, the run stops. No paid provider fallback is configured.

OmniRoute may be used as an ephemeral gateway for LLM requests. It is not a source of free model credits. Check upstream provider quotas and billing.

## Upload and publishing safety

- Upload is private by default.
- Public visibility is blocked unless YOUTUBE_ALLOW_PUBLIC=true is deliberately configured.
- The YouTube OAuth token must be valid before upload begins.
- Review the Pexels license, attribution requirements, source quality and final video before public release.
- GitHub Actions minutes, storage and artifact quotas apply.

## Local development

Ollama remains an optional development tool, not a cloud runtime dependency. The cloud path can be tested locally with Python, FFmpeg and the cloud extra, provided all required credentials are supplied in the environment or a local ignored .env file.
