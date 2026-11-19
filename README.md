# NextGen-Tech-Academy

Cloud-first AI video production and YouTube upload automation. The cloud pipeline does **not** require Ollama or an always-on laptop.

## Target format

- Standard YouTube 16:9 video, currently 60 seconds (four connected 15-second clips).
- English narration and Persian subtitles.
- Research leads, bilingual script, video generation, TTS, FFmpeg assembly, metadata and YouTube upload.
- Cloud execution through GitHub Actions; manual dispatch or scheduled runs.

## Cloud providers

The script writer uses a configurable fallback chain: Gemini, Groq and OpenRouter. Configure one or more API keys as GitHub Actions Secrets. Free-tier availability and model names can change; the app tries configured providers in order and reports a failure if all are unavailable.

VidoGrid video models can be rotated using `VIDOGRID_MODEL_ROTATION`. The default rotation includes Grok Imagine Video 1.5 Lite, Veo 3.1 Fast and Omni 1.2 Flash. These models are routed through their documented VidoGrid endpoints. VidoGrid API requests consume VidoGrid credits. The automation deliberately fails closed unless the account response exposes a separate free/trial credit balance and `VIDOGRID_MODEL_CREDIT_COSTS` contains a cost for every selected model. The application will not guess that app-level free generations are available to the API.

Cloud narration uses Edge TTS through the `cloud` optional dependency. It is an external service and may be rate-limited or change; review its terms and voice usage rights before commercial use.

## GitHub Actions setup

1. Add repository **Actions secrets**:
   - `VIDOGRID_API_KEY`
   - At least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` (OpenRouter only runs a model ending in `:free` unless `ALLOW_PAID_LLM=true` is explicitly set)
   - `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with the `youtube.upload` scope)
2. Add repository **Actions variables** if needed:
   - `LLM_PROVIDER_ORDER` (default `gemini,groq,openrouter`)
   - `VIDOGRID_MODEL_ROTATION` (default `grok-imagine-video-1.5-lite,veo-3.1-fast,omni-1.2-flash`)
   - `VIDOGRID_MODEL_CREDIT_COSTS` (required JSON cost per model; exact account pricing)
   - `VIDOGRID_TOTAL_BALANCE_IS_FREE` (keep `false` unless you have confirmed that the entire VidoGrid `/account` balance consists only of free credits)
3. Confirm VidoGrid API pricing and the account's separately identified free/trial credit balance. Set `VIDOGRID_MODEL_CREDIT_COSTS` as a JSON object (for example, `{"grok-imagine-video-1.5-lite": 1, "veo-3.1-fast": 2, "omni-1.2-flash": 2}`) only after checking the exact current credit cost shown in your VidoGrid account. The numbers in this example are placeholders, not actual prices.
4. Open **Actions → Automated YouTube video factory → Run workflow**. Supply a topic or leave it blank for RSS-based topic discovery.
5. The workflow uploads privately by default and stores output artifacts for 14 days.

The schedule is Tuesday and Friday at 06:17 UTC. GitHub-hosted runners execute the process even when the user's laptop is off. GitHub Actions minutes and artifact quotas still apply.

## Inspect VidoGrid credits without generating

Before the first production run, set `VIDOGRID_API_KEY` locally or as a GitHub Actions Secret and inspect the exact account response with `nextgen-academy vidogrid-account`. This command does not submit video jobs or spend generation credits. The production runner performs the same check before using any cloud LLM or TTS quota.

## Local test run (no Ollama)

Requires Python 3.10+ and FFmpeg:

```bash
python -m pip install -e ".[dev,cloud]"
nextgen-academy auto-run --topic "How humanoid robots are changing manufacturing"
```

Add credentials to the process environment or a local, ignored `.env` file. Never commit keys or OAuth tokens.

See [YouTube OAuth setup](docs/YOUTUBE_SETUP.md) for one-time channel authorization and secure GitHub secret configuration.

## OmniRoute integration (optional AI gateway)

The LLM adapter can route script-generation requests through a self-hosted OmniRoute instance. This keeps the existing Gemini/Groq/OpenRouter adapters available as fallbacks and does not change the video-generation or YouTube-upload stages.

Add these GitHub Actions **Secrets** (never commit them):
- `OMNIROUTE_BASE_URL` — public HTTPS base URL reachable from the GitHub-hosted runner, ending in `/v1` (for example, `https://ai-gateway.example.com/v1`). `localhost` and `127.0.0.1` will not work from GitHub-hosted runners.
- `OMNIROUTE_API_KEY` — an API key created in OmniRoute Dashboard → Endpoints.

Optional GitHub Actions **Variables**:
- `OMNIROUTE_MODEL` — defaults to `auto/subscription` (subscription-quota-only routing; it should fail closed rather than silently falling back to billable providers).
- `LLM_PROVIDER_ORDER` — defaults to `omniroute,gemini,groq,openrouter`. Put or remove providers to change fallback order.

Connect at least one eligible provider in OmniRoute Dashboard → Providers, then create an endpoint key in Dashboard → Endpoints. For the no-surprise-cost default, use `auto/subscription` and confirm the connected provider's terms and quota. Do not use `auto`, `auto/cheap`, or a paid model unless you intentionally accept possible charges. OmniRoute does not grant free credits; provider free tiers, eligibility, regional access, and limits are controlled by each provider.

See [OmniRoute setup and security notes](docs/OMNIROUTE_SETUP.md). If OmniRoute is unavailable, the existing LLM fallback chain continues to Gemini, Groq, and OpenRouter according to `LLM_PROVIDER_ORDER`.

## YouTube publishing safeguards

- OAuth refresh-token credentials are required; an API key alone cannot upload to a personal channel.
- Default visibility is **private**. Public publishing is blocked unless `YOUTUBE_ALLOW_PUBLIC=true` is explicitly set.
- Upload uses resumable transfer.
- Automated research collects RSS titles, summaries and links. It does not independently prove claims or guarantee source reliability.
- Human review of facts, source quality, translation, audio, rights, watermarks and the final render is required before public release.

## Important limitations

- The first cloud end-to-end run has not yet been validated against the user's live VidoGrid account, cloud LLM keys, TTS endpoint or YouTube OAuth credentials.
- Free API tiers and model access vary by provider and can change without notice.
- The credit guard blocks generation unless a separate free/trial balance is visible and a per-clip estimate is configured. If VidoGrid only reports a combined balance, the safe behavior is to stop. An explicit `VIDOGRID_TOTAL_BALANCE_IS_FREE=true` opt-in is available only if you have verified that no paid credits are included.
- No public upload is enabled by default.
- VidoGrid may return model-specific durations or output schemas; inspect the first live run before enabling recurring automation.
