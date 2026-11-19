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
- At least one LLM route: the optional `FREELLMAPI_CLOUD_BASE_URL` + `FREELLMAPI_CLOUD_API_KEY` pair, or `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY` for cloud writing.
- `YOUTUBE_TOKEN_JSON` for OAuth upload with the `youtube.upload` scope.

At least one of `AGNES_API_KEY` or `PEXELS_API_KEY` is required for visual scenes. Never commit credentials.

OmniRoute may be used as an ephemeral gateway for LLM requests. It is not a source of free model credits.

## Upload and publishing safety

- Upload is private by default.
- Public visibility is blocked unless `YOUTUBE_ALLOW_PUBLIC=true` is deliberately configured.
- Review source contents, factual claims, translations, audio, model terms, stock licenses and final video before public release.
- GitHub Actions minutes, storage and artifact quotas apply.

## Long-form documentary assembly (new utility; not yet an automated factory)

The main cloud workflow above still targets a one-minute 16:9 episode. It has not yet been converted into a fully automated 15–60+ minute documentary pipeline. To safely join already-produced clips into a longer sequence, the repository now includes `scripts/assemble_documentary.py`:

```bash
python scripts/assemble_documentary.py --clips output/documentary-clips.json --output output/documentary.mp4 --subtitles output/subtitles.fa.srt --voiceover output/narration.mp3
```

The JSON manifest is an ordered array of local clip paths; relative paths are resolved from the manifest file. The tool normalizes clips to 1920×1080/30fps, joins them in order, and can add a narration track and a soft Persian subtitle track. Add `--burn-subtitles` only when captions should be permanently burned into the picture. FFmpeg is required. This utility does not create long scripts, generate footage, translate subtitles, or upload/publish. It must be tested with real sample media before it is used in a scheduled workflow.


### Resumable long-form run state

After creating a blueprint, initialize a durable chapter manifest:

```bash
nextgen-academy documentary-plan --topic "How AI is changing scientific research" --minutes 15
nextgen-academy documentary-init --plan output/documentary-plan.json --state output/documentary-run.json
```

Record chapter stages in order as work is completed. Existing chapter outputs are retained when another chapter is retried:

```bash
nextgen-academy documentary-progress --chapter 1 --status researched --output-name research --output-path output/research/chapter-01.json
nextgen-academy documentary-progress --chapter 1 --status scripted --output-name script --output-path output/scripts/chapter-01.md
nextgen-academy documentary-progress --chapter 2 --error "Temporary provider failure"
```

Stages are `planned → researched → scripted → narrated → assembled → reviewed`. Skipping or moving backwards is blocked by default. Re-initialization refuses to overwrite an existing run manifest. Writes use an atomic replace so an interrupted save does not leave a partially-written JSON file. When every chapter is reviewed, the run is marked `ready_for_human_approval`; this is not permission to publish publicly. These commands track state only and do not yet run the chapter research, writing, narration, or media-generation stages automatically.

### Optional FreeLLMAPI cloud route

The LLM provider chain can use `FREELLMAPI_CLOUD_BASE_URL` + `FREELLMAPI_CLOUD_API_KEY` before the existing providers. The adapter calls the gateway model catalogue first and accepts only explicit free markers or machine-readable zero input/output prices. Unknown pricing is not treated as free. This is the cloud endpoint only; it does not connect to the phone/Tailscale gateway. The credentials are optional and must be entered directly as Actions Secrets in this repository if available.


## Long-form production blueprint (planning stage)

Create a structured 15-, 30- or 60-minute production blueprint without starting paid services or uploading anything:

```bash
nextgen-academy documentary-plan --topic "How AI is changing scientific research" --minutes 15 --output output/documentary-plan.json
```

The planner allocates chapter time, narration word-count targets, and a shot list using 12-second (or shorter) visual slots. It produces a blueprint only: it does not claim to have written or fact-checked the full narration, generated clips, or rendered a documentary. At 12 seconds per slot, a 15-minute episode needs 75 slots, a 30-minute episode 150, and a 60-minute episode 300. This keeps provider limits visible before any media-generation request is made.
