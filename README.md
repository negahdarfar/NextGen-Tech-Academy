# NextGen-Tech-Academy

Cloud-first AI video production and YouTube upload automation. The cloud pipeline does **not** require Ollama, a local computer, or an always-on server.

## Target format

- Standard YouTube 16:9 video, currently 60 seconds (not Shorts).
- English narration and Persian subtitles.
- Research, bilingual script, AI-generated scenes where free quota is available, stock-footage fallback, TTS, FFmpeg assembly, metadata and YouTube upload.
- Cloud execution through GitHub Actions; manual dispatch or scheduled runs.

## Visual generation strategy

1. **Primary: Agnes AI Video 2.5 Flash.** The provider currently documents a limited-time $0/second promotion for 720p output. It supports 4–12 second clips and a low free/default request rate. This promotion and quota can change or end; it is not a permanent free-production guarantee.
2. **Fallback: Pexels stock footage.** Free API access to existing stock videos. It is not generative AI. The adapter uses it when Agnes is unavailable or no Agnes key is configured.
3. The renderer loops short generated clips to fit the 15-second storyboard segment, then combines four scenes into the one-minute video. The manifest records which provider supplied every scene.

Agnes requires a free account and an API key stored as `AGNES_API_KEY` in GitHub Actions Secrets. Pexels requires `PEXELS_API_KEY`. Configure at least one visual provider; configure both for fallback resilience.

## Other providers and costs

- **Language models:** Gemini, Groq and OpenRouter through the configured fallback chain. Free-tier access and quotas depend on provider account eligibility. OmniRoute is an optional gateway, not a source of free credits.
- **Narration:** Edge TTS through the cloud optional dependency. This external service may be rate-limited; review its terms and voice usage rights before commercial use.
- **Editing:** FFmpeg on GitHub-hosted runners. Standard runners are CPU-based; video generation is performed by the external API, not locally on GitHub.

No VidoGrid or LTX dependency is used.

## GitHub Actions setup

Add repository Actions secrets:

1. `AGNES_API_KEY` — preferred AI video provider (limited-time free promotion; check the provider console).
2. `PEXELS_API_KEY` — free stock fallback (recommended).
3. At least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`.
4. `YOUTUBE_TOKEN_JSON` — OAuth authorized-user JSON with the `youtube.upload` scope, only if uploading.

Open Actions → Automated YouTube video factory → Run workflow. Supply a topic or leave it blank for RSS-based topic discovery. The workflow uploads privately by default and stores output artifacts for 14 days.

The schedule is Tuesday and Friday at 06:17 UTC. GitHub-hosted runners execute the process even when the user's laptop is off. GitHub Actions minutes and artifact quotas still apply.

## Attribution and licensing

- Agnes free-promotion access is not a promise of perpetual free use. Check the current account quota and terms before each production run.
- Pexels content is existing stock footage. Follow Pexels API requirements and credit photographers where possible.
- Review all model/provider terms for commercial use before monetizing output.

## YouTube publishing safeguards

- Upload is private by default.
- Public visibility is blocked unless `YOUTUBE_ALLOW_PUBLIC=true` is explicitly set.
- Upload uses resumable transfer.
- Research collects RSS titles, summaries and links; it does not independently prove claims.
- Human review of facts, source quality, translation, audio, footage rights, attribution, watermarks and final render is required before public release.

## Important limitations

- The first cloud end-to-end run still needs validation against the Agnes/Pexels API key, cloud LLM keys, TTS endpoint and YouTube OAuth credentials.
- Free API tiers and promotions vary by provider and can change.
- Agnes Flash output is 720p and at most 12 seconds per generated clip; short clips are looped to match the storyboard timeline.
- No public upload is enabled by default.


## Editorial skills and long-form tooling

Selected MIT-licensed YouTube editorial skills and their helper scripts are vendored under `.claude/skills/`; see [docs/AGENT_SKILLS.md](docs/AGENT_SKILLS.md) for their purpose, commands, license, and execution limits. GitHub Actions does not execute agent skill files automatically.

The current automated production workflow remains a one-minute 16:9 episode. A separate [documentary clip assembler](scripts/assemble_documentary.py) can join existing clips with optional narration and Persian subtitles, but it is only an assembly utility—not yet an end-to-end long-form documentary generator. See [docs/PRODUCTION_PIPELINE.md](docs/PRODUCTION_PIPELINE.md).


### Optional free-model gateway

The LLM fallback chain can optionally use a cloud FreeLLMAPI-compatible endpoint through `FREELLMAPI_CLOUD_BASE_URL` and `FREELLMAPI_CLOUD_API_KEY`. It first inspects `GET /models` and calls only models explicitly marked free by their ID or structured catalogue pricing; unknown-price and paid models are skipped. This path does not use the Android phone or Tailscale. Secret values are not copied between repositories; configure the pair directly in the canonical repository's Actions Secrets if you want this optional route.
