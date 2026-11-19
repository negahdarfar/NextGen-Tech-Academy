# OmniRoute integration and deployment

## What this integration changes

The existing `nextgen_academy.llm.generate_json()` function can use OmniRoute as an optional OpenAI-compatible gateway for structured script-generation requests. The video pipeline, VidoGrid adapter, Edge TTS, FFmpeg renderer, and YouTube publisher are unchanged.

Default provider order is now:

`omniroute,gemini,groq,openrouter`

A provider is skipped when its required secret is absent. A request failure is recorded and the next configured provider is attempted.

## Required configuration

Set these as GitHub Actions repository **Secrets**:

- `OMNIROUTE_BASE_URL`: HTTPS URL reachable from the GitHub-hosted runner, normally ending in `/v1`.
- `OMNIROUTE_API_KEY`: endpoint key created in OmniRoute Dashboard → Endpoints.

Optional GitHub Actions **Variables**:

- `OMNIROUTE_MODEL`: defaults to `auto/subscription`.
- `LLM_PROVIDER_ORDER`: defaults to `omniroute,gemini,groq,openrouter`.

Example values (not credentials):

```text
OMNIROUTE_BASE_URL=https://ai-gateway.example.com/v1
OMNIROUTE_MODEL=auto/subscription
LLM_PROVIDER_ORDER=omniroute,gemini,groq,openrouter
```

Do not put API keys in repository files, frontend JavaScript, issue comments, workflow logs, or commit history.

## Important: GitHub-hosted runner networking

The NextGen production pipeline runs on GitHub-hosted runners. Therefore `http://127.0.0.1:20128/v1` only works for a local test where OmniRoute and NextGen run on the same machine. It is not reachable from GitHub Actions.

For cloud automation, OmniRoute must be running on a server reachable over HTTPS. Deploy it behind a TLS reverse proxy or a private access gateway. Do not expose the OmniRoute dashboard or an unauthenticated API to the public internet. Restrict inbound access where possible, use a strong dedicated endpoint key, rotate it if exposed, and keep provider credentials inside OmniRoute's encrypted credential store.

If you do not have a secure, always-reachable host, leave `OMNIROUTE_API_KEY` unset; NextGen will continue using the existing Gemini/Groq/OpenRouter fallback providers. Do not create a public tunnel to an unprotected local dashboard as a shortcut.

## Provider and cost setup

1. Install and start OmniRoute using its official instructions: https://github.com/cheaper-inference/OmniRoute
2. Open its dashboard and connect a provider whose terms permit your intended use.
3. Create a dedicated endpoint key in Dashboard → Endpoints.
4. Configure NextGen's two GitHub Actions secrets.
5. Set `OMNIROUTE_MODEL=auto/subscription` for subscription-quota-only routing.
6. Run a manual workflow and inspect its logs/artifacts before relying on the scheduled run.

OmniRoute is a gateway, not a source of free credits. Provider free tiers can have eligibility, regional, rate, and usage restrictions. The `auto/subscription` route is intended to fail closed rather than silently select a billable fallback. Avoid `auto`, `auto/cheap`, or explicitly paid model IDs unless you have deliberately accepted their billing behavior.

## Local smoke test

Run OmniRoute locally, create an endpoint key, then set:

```bash
export OMNIROUTE_BASE_URL="http://127.0.0.1:20128/v1"
export OMNIROUTE_API_KEY="YOUR_ENDPOINT_KEY"
export OMNIROUTE_MODEL="auto/subscription"
export LLM_PROVIDER_ORDER="omniroute"
```

The gateway API can be checked independently:

```bash
curl "$OMNIROUTE_BASE_URL/models" \
  -H "Authorization: Bearer $OMNIROUTE_API_KEY"
```

Then run the existing NextGen test suite and a non-publishing local workflow. The first successful HTTP response only verifies gateway connectivity; validate JSON schema, model eligibility, cost/quota behavior, and the complete production stages separately.

## Known boundaries

- OmniRoute integration currently covers the language-model JSON generation adapter only.
- It does not route VidoGrid video generation, Edge TTS, FFmpeg, Supabase, or YouTube uploads.
- A live end-to-end check still requires the user's server URL, endpoint key, provider connection, and GitHub Actions secrets. None of these secrets are stored in this repository.
- This repository change does not change the default private-upload safeguard or enable public publishing.
