# Cloud-first production pipeline

The target is a standard 60-second, 16:9 YouTube video. Narration is English and subtitles are Persian. The cloud path does not require Ollama or an always-on laptop.

## Visual providers

1. Agnes AI Video 2.5 Flash is the preferred generated-video provider. Its published model reference currently shows a limited-time $0/second promotion, 720P output, 4–12 second clips, and a restricted free/default request rate. Treat it as a testable promotion, not a guaranteed permanent free tier.
2. Pexels is the free stock-video fallback. It retrieves existing clips and is not an AI video generator.
3. Each scene tries Agnes first when `AGNES_API_KEY` is configured. On a provider error, the scene falls back to Pexels if `PEXELS_API_KEY` is configured. Provider provenance is stored in `output/video-jobs.json`.
4. Agnes clips are looped by FFmpeg to fill the 15-second scene timeline; four scenes form the one-minute episode.

## Automated run

The GitHub Actions workflow `.github/workflows/auto-publish.yml` can be started manually or on its Tuesday/Friday schedule.

    nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing"
    nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing" --upload

When no topic is supplied, RSS headlines are used to choose a topic. The automated run:
1. Discovers candidate articles and papers from RSS feeds.
2. Uses the configured cloud LLM fallback order to draft four English narration scenes and Persian translations.
3. Creates four linked storyboard scenes.
4. Generates English narration using the configured cloud TTS adapter and Persian SRT subtitles.
5. Generates a 12-second 720p video per scene with Agnes when available; otherwise retrieves Pexels stock footage.
6. Assembles the scenes with FFmpeg, narration and subtitles, then checks that the output is approximately one minute.
7. Creates YouTube metadata and, only when `--upload` is supplied, uploads through OAuth as private by default.

## Configure GitHub Actions Secrets

- `AGNES_API_KEY` — optional AI video key. Free 720p promotion is limited-time and may change.
- `PEXELS_API_KEY` — optional free stock fallback. Recommended alongside Agnes.
- At least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY` for cloud writing.
- `YOUTUBE_TOKEN_JSON` for OAuth upload with the `youtube.upload` scope.

At least one of `AGNES_API_KEY` or `PEXELS_API_KEY` is required for visual scenes. Never commit credentials.

OmniRoute may be used as an ephemeral gateway for LLM requests. It is not a source of free model credits.

## Upload and publishing safety

- Upload is private by default.
- Public visibility is blocked unless `YOUTUBE_ALLOW_PUBLIC=true` is deliberately configured.
- Review source contents, factual claims, translations, audio, model terms, stock licenses and final video before public release.
- GitHub Actions minutes, storage and artifact quotas apply.
