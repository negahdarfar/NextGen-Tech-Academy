# NextGen Tech Academy

Cloud-first YouTube production toolkit for technology and education documentaries. The canonical repository contains two separate production paths: a legacy one-minute episode workflow and a resumable long-form documentary factory.

## Long-form documentary factory

- Landscape 16:9 output, 1920×1080 at 30 fps.
- Documentary durations: 15, 30 or 60 minutes.
- Eight planned chapters, English narration and Persian subtitles.
- Chapter research leads, bilingual scripts, visual-shot plans, narration, stock/generated visuals, FFmpeg assembly and YouTube metadata.
- Resumable chapter/shot checkpoints; completed assets are retained across retry attempts.
- GitHub Actions cloud execution; no always-on laptop or VPS is required.
- The production workflow is manual-dispatch only. It does not upload to YouTube.

The visual plan allocates 78, 153 or 303 shots for 15, 30 or 60 minutes respectively. A long-form run may therefore exceed free API quotas or GitHub runner limits; start with 15 minutes and check provider quotas first.

## Zero-budget provider policy

The default long-form workflow is deliberately conservative:

- **LLM:** FreeLLMAPI cloud gateway pair (`FREELLMAPI_CLOUD_BASE_URL` + `FREELLMAPI_CLOUD_API_KEY`) or OpenRouter with `OPENROUTER_MODEL` explicitly ending in `:free`. Unknown or paid model pricing is rejected. No paid LLM fallback is enabled.
- **Visuals:** Pexels API (`PEXELS_API_KEY`) in `auto`/Pexels mode. Pexels supplies licensed stock footage; it is not generative AI.
- **Narration:** Edge TTS through the cloud optional dependency. Check the provider's current terms, voice usage rights and commercial-use conditions before monetization.
- **Assembly:** FFmpeg on GitHub-hosted runners.
- **Agnes:** Optional separate provider. It may incur charges if a promotion has ended; it is disabled unless explicitly selected and separately acknowledged. Do not treat any promotion as a permanent free tier.

Free quotas, service availability and terms can change. GitHub Actions minutes, runner time, cache and artifact quotas also apply.

## Configure GitHub Actions

Open **Settings → Secrets and variables → Actions** in this repository. Add secrets directly there; never paste credentials into chat, commit them, or place them in source files.

Required for the long-form zero-budget workflow:

1. `FREELLMAPI_CLOUD_BASE_URL` and `FREELLMAPI_CLOUD_API_KEY`, **or** `OPENROUTER_API_KEY` plus repository variable `OPENROUTER_MODEL` ending in `:free`.
2. `PEXELS_API_KEY`.

Optional:

- `AGNES_API_KEY` only if you deliberately choose the potentially chargeable Agnes provider and acknowledge its possible cost.
- `YOUTUBE_TOKEN_JSON` only for the separate, human-approved upload step. It must be OAuth authorized-user JSON with YouTube upload scope; an API key is not a substitute.

### Start a long-form run

1. Open **Actions → Long-form documentary factory → Run workflow**.
2. Enter a documentary topic.
3. Choose 15 minutes for the first end-to-end validation; 30/60 minutes can require many more provider requests.
4. Keep visual provider as `auto` for Pexels-only zero-budget mode.
5. Set `confirm_generation` to true only after checking credentials and quotas.
6. Keep `allow_agnes_potential_cost` false.

The workflow saves a resumable artifact even if a run fails. A retry with the same topic and duration can restore prior assets. The output is a private Actions artifact retained for 14 days; it is not automatically uploaded or published.

## Human review and YouTube upload

The factory stops after rendering `final-documentary.mp4` and creating `youtube-package.json`. Before upload, watch the entire video and verify:

- Claims against original, trustworthy sources (RSS entries are discovery leads, not fact-checking).
- Persian translation and subtitle timing (timings are estimates and need correction).
- Audio quality, factual context, visual continuity and chapter transitions.
- Stock-footage licensing, attribution, AI/TTS provider terms and commercial-use rights.

Mark every chapter `reviewed` only after completing that review. Then upload privately with `documentary-upload --approve-upload`. Public visibility additionally requires `--approve-public`. The production workflow itself never uploads.

## Legacy one-minute workflow

The repository also retains the separate `auto-publish.yml` / `auto-run` workflow for standard one-minute, 16:9 episodes. It has its own provider configuration and publishing safeguards; it is not the long-form factory. See [docs/PRODUCTION_PIPELINE.md](docs/PRODUCTION_PIPELINE.md) for the distinction and detailed commands.

## Repository quality status

The latest verified CI run on commit `e91b40f388912d31b82b35de6a75dc39f8ddde72` completed successfully: 83 Python tests passed and the OmniRoute smoke job passed. This validates the code/test workflow, not a real external-provider documentary run. A real end-to-end production still requires the credentials above and a first 15-minute validation.

## Editorial skills

Selected editorial skills and helper scripts are vendored under `.claude/skills/`. See [docs/AGENT_SKILLS.md](docs/AGENT_SKILLS.md). GitHub Actions does not execute agent skill files automatically.
