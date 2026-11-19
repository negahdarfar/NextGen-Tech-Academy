# OmniRoute on ephemeral GitHub-hosted runners

## Architecture

NextGen starts OmniRoute inside the same GitHub Actions job that runs the video factory. The runner installs Node.js 22 and the pinned OmniRoute package, starts the gateway on loopback, checks its local model endpoint, and then runs the existing Python production pipeline. The runner is discarded after the job. No always-on VPS, public gateway URL, laptop, or Ollama installation is required.

The gateway is deliberately bound to `127.0.0.1`; it is not exposed to the public internet. The workflow keeps API-key enforcement disabled for this temporary process and the adapter sends no bearer token. This is safe only because the listener is bound to loopback on an isolated GitHub-hosted runner; never expose this setup to a public network.

## Provider credentials

The existing GitHub Actions secret `GEMINI_API_KEY` is passed to the runner and OmniRoute as a provider credential. No additional OmniRoute secret is required for this mode. The default routed model is `gemini/gemini-2.5-flash`; change it with the optional Actions variable `OMNIROUTE_MODEL` only after verifying the model and its billing tier in the provider account.

A Gemini API key does not guarantee free use. Google's free-tier eligibility, limits, model availability, and billing settings control actual charges. Confirm the Google AI Studio / Cloud project has the intended billing configuration before enabling scheduled production.

## Workflow behavior

1. GitHub Actions checks out the repository.
2. Node.js 22.22.2 is installed.
3. If `GEMINI_API_KEY` exists, the workflow installs `omniroute@3.8.54`, generates temporary instance secrets, starts it on loopback, and polls `/v1/models` for the configured Gemini model.
4. Python and FFmpeg are installed.
5. NextGen runs its existing credit-guarded production pipeline. The LLM adapter tries OmniRoute first, then the existing configured Gemini/Groq/OpenRouter adapters according to `LLM_PROVIDER_ORDER`.
6. The existing private-by-default YouTube upload behavior and artifact retention remain unchanged.
7. GitHub discards the runner after the job.

The current workflow does not need `OMNIROUTE_BASE_URL` or `OMNIROUTE_API_KEY` repository secrets. It sets the base URL locally for the current runner only and intentionally omits client authentication on the loopback-only listener. If Gemini is not configured, the OmniRoute startup step is skipped and the existing provider chain remains available.

## Cost and safety

OmniRoute is a routing gateway, not a source of free credits. This implementation uses the explicit Gemini model by default rather than assuming an undocumented `auto/subscription` route. A free-tier API key may still be rate-limited or unavailable, and a project with billing enabled may incur charges. Check the provider's current console and terms.

The workflow retains the existing VidoGrid free-credit guard and private YouTube upload default. LLM provider fallback is configurable; if strict zero-cost behavior is required, configure only providers/models whose no-charge status and hard-stop behavior have been verified. Never assume a provider will stop instead of billing after a quota is exhausted.

## Manual verification

After the pull request is merged, open Actions → Automated YouTube video factory and run it with a topic. Check the log for “OmniRoute is ready on the GitHub-hosted runner.” The first full run still requires valid VidoGrid credentials and separately verified free-credit cost settings, Edge TTS network availability, and YouTube OAuth JSON if upload is enabled.

No credentials are written to the repository, and no live provider request or video generation is performed by the code change itself.
