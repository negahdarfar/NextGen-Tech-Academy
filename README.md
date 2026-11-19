# NextGen-Tech-Academy

Cloud-first AI video production and YouTube upload automation. The cloud pipeline does **not** require Ollama, a local computer, or an always-on server.

## Target format

- Standard YouTube 16:9 video, currently 60 seconds.
- English narration and Persian subtitles.
- Research, bilingual script, free stock footage, TTS, FFmpeg assembly, metadata and YouTube upload.
- Cloud execution through GitHub Actions; manual dispatch or scheduled runs.

## Providers and costs

- **Visual footage:** Pexels API free developer tier. It requires a free PEXELS_API_KEY, is subject to API rate limits and Pexels licensing/attribution rules, and retrieves existing stock footage. It does not generate custom AI video.
- **Language models:** Gemini, Groq and OpenRouter through the configured fallback chain. Free-tier access and quotas depend on provider account eligibility. OmniRoute is an optional gateway, not a source of free credits.
- **Narration:** Edge TTS through the cloud optional dependency. This external service may be rate-limited; review its terms and voice usage rights before commercial use.
- **Editing:** FFmpeg on GitHub-hosted runners.

No VidoGrid API, credits, paid video-model rotation, or VidoGrid account is used.

## GitHub Actions setup

Add repository Actions secrets:
1. PEXELS_API_KEY — free key from the Pexels developer dashboard.
2. At least one of GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY.
3. YOUTUBE_TOKEN_JSON — OAuth authorized-user JSON with the youtube.upload scope, only if uploading.

Open Actions → Automated YouTube video factory → Run workflow. Supply a topic or leave it blank for RSS-based topic discovery. The workflow uploads privately by default and stores output artifacts for 14 days.

The schedule is Tuesday and Friday at 06:17 UTC. GitHub-hosted runners execute the process even when the user's laptop is off. GitHub Actions minutes and artifact quotas still apply.

## Stock footage source

The pipeline searches Pexels for relevant landscape stock clips, downloads footage and assembles it with narration and subtitles. Pexels is a stock-footage source, not text-to-video generation. If no suitable clip of the required duration is available, the run stops rather than silently switching to a paid provider.

Register for a free Pexels API key and save it as PEXELS_API_KEY in GitHub Actions Secrets. Review Pexels license and attribution requirements for every published video.

## Local test run (no Ollama)

Requires Python 3.10+ and FFmpeg:

    python -m pip install -e ".[dev,cloud]"
    nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing"

Add credentials to the process environment or a local, ignored .env file. Never commit keys or OAuth tokens.

See docs/YOUTUBE_SETUP.md for one-time channel authorization and secure GitHub secret configuration.

## OmniRoute integration (ephemeral GitHub Actions gateway)

The video factory can start OmniRoute on the GitHub-hosted runner for each job. It installs the pinned omniroute@3.8.54 package, starts the API on loopback, checks readiness, and runs the pipeline. The runner is discarded after the job. No VPS, public gateway URL, always-on laptop, or Ollama installation is required.

OmniRoute is only a model gateway. It does not provide free model quota or API credits. Confirm upstream provider billing and limits before enabling scheduled runs.

## YouTube publishing safeguards

- Upload is private by default.
- Public visibility is blocked unless YOUTUBE_ALLOW_PUBLIC=true is explicitly set.
- Upload uses resumable transfer.
- Research collects RSS titles, summaries and links; it does not independently prove claims.
- Human review of facts, source quality, translation, audio, footage rights, attribution, watermarks and final render is required before public release.

## Important limitations

- The first cloud end-to-end run still needs validation against the Pexels API key, cloud LLM keys, TTS endpoint and YouTube OAuth credentials.
- Free API tiers and model access vary by provider and can change.
- Pexels stock clips may not match every storyboard scene exactly. The pipeline must not claim generated footage when using stock footage.
- No public upload is enabled by default.
