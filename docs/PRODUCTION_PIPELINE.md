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

## Legacy standalone long-form assembly utility

The main `auto-publish.yml` workflow remains the separate one-minute pipeline. The standalone utility below is retained for custom local manifests; the connected 15–60-minute factory is documented in the later “Fully connected long-form stages” section and uses `documentary-produce`:

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

Stages are `planned → researched → scripted → narrated → assembled → reviewed`. Skipping or moving backwards is blocked by default. Re-initialization refuses to overwrite an existing run manifest. Writes use an atomic replace so an interrupted save does not leave a partially-written JSON file. When every chapter is reviewed, the run is marked `ready_for_human_approval`; this is not permission to publish publicly. These low-level commands remain available for manual recovery and inspection. The `documentary-produce` orchestrator below now runs the research, writing, narration, visual-generation and assembly stages in order, resuming from saved checkpoints.

### Chapter-by-chapter research and bilingual script drafting

Configure at least one supported cloud LLM route and then run a single chapter:

```bash
nextgen-academy documentary-chapter --state output/documentary-run.json --chapter 1 --output-dir output/documentary
```

This command discovers RSS source leads for the documentary topic and chapter, saves the source list, drafts English narration plus a faithful Persian translation, validates the requested narration length and source IDs attached to claims, then records the script path in the run manifest. If drafting fails after research, the chapter remains at the researched stage and can be retried without repeating research. A chapter with a saved script is skipped on subsequent runs unless `--force` is deliberately supplied.

The chapter script includes the narration, translation, claim ledger and visual-shot prompts. The `documentary-voice`, `documentary-visuals` and `documentary-assemble` commands connect the remaining production stages. RSS items are discovery leads, not fact-checked sources; human source verification and editorial review remain mandatory. The automated long-form runner also creates `youtube-package.json` with measured chapter timecodes, source links, stock-footage credits, tags and a thumbnail brief. It does not upload the video.

### Optional FreeLLMAPI cloud route

The LLM provider chain can use `FREELLMAPI_CLOUD_BASE_URL` + `FREELLMAPI_CLOUD_API_KEY` before the existing providers. The adapter calls the gateway model catalogue first and accepts only explicit free markers or machine-readable zero input/output prices. Unknown pricing is not treated as free. This is the cloud endpoint only; it does not connect to the phone/Tailscale gateway. The credentials are optional and must be entered directly as Actions Secrets in this repository if available.


## Long-form production blueprint (planning stage)

Create a structured 15-, 30- or 60-minute production blueprint without starting paid services or uploading anything:

```bash
nextgen-academy documentary-plan --topic "How AI is changing scientific research" --minutes 15 --output output/documentary-plan.json
```

The planner allocates chapter time, narration word-count targets, and a shot list using 12-second (or shorter) visual slots. It produces a blueprint only: it does not claim to have written or fact-checked the full narration, generated clips, or rendered a documentary. Because each chapter has its own visual continuity and clip sequence, the exact 12-second per-chapter allocation is 78 slots for 15 minutes, 153 for 30 minutes, and 303 for 60 minutes. This keeps provider limits visible before any media-generation request is made.


## Chapter narration and Persian subtitle timing

After a chapter reaches `scripted`, run:

```bash
nextgen-academy documentary-voice --state output/documentary-run.json --chapter 1 --script output/documentary/chapter-01-script.json
```

This optional stage uses the existing `cloud` extra (`edge-tts`) to create one English MP3 per chapter and a Persian SRT. Subtitle cue times are estimated by Persian sentence length across the measured audio duration; they are **not word-aligned** and must be checked and corrected by a human before assembly. The chapter advances to `narrated` only after both files are written and the audio duration is validated. No video clips are generated or uploaded by this command.


## Fully connected long-form stages (chapter workflow)

The chapter pipeline now creates a visual-shot list with each bilingual script. For each chapter, complete the steps in order:

```bash
nextgen-academy documentary-chapter --state output/documentary-run.json --chapter 1 --output-dir output/documentary
nextgen-academy documentary-voice --state output/documentary-run.json --chapter 1 --script output/documentary/chapter-01-script.json
nextgen-academy documentary-visuals --state output/documentary-run.json --chapter 1 --script output/documentary/chapter-01-script.json
```

The visual stage resumes from its per-chapter asset manifest and records provider, model/source URL, photographer where applicable, clip path and generation status after each shot. Zero-budget `auto` mode uses Pexels only; Agnes is a separate opt-in because its temporary promotion may end and become chargeable. Agnes requires both an explicit provider selection and `--allow-agnes-potential-cost`. Agnes clips are 720p and limited to 4–12 seconds. Pexels is stock footage, not generated video. Provider quotas and terms may change.

After every chapter has narration and every visual shot has a valid local clip, assemble:

```bash
nextgen-academy documentary-assemble --state output/documentary-run.json --output output/documentary/final-documentary.mp4
```

The assembler synchronizes the visual timeline to measured chapter narration durations, concatenates English audio, offsets Persian subtitle cues, exports 1920×1080/30fps, checks the rendered duration and stream metadata against technical gates, and only then atomically promotes the final MP4. The runner also creates an editable `youtube-package.json` with measured chapter timecodes and recorded source/stock-footage credits. This is a technical assembly gate, not factual, translation, copyright, or editorial approval. A human must watch the complete video and review the source/rights ledger before marking chapters reviewed or uploading. The long-form CLI is manually invoked; the one-minute scheduled workflow is not silently repurposed for 15–60-minute jobs.


### One-command resumable factory and GitHub Actions

For a fully automated run, use the explicit confirmation gate:

```bash
nextgen-academy documentary-produce --topic "How AI is changing scientific research" --minutes 15 --state output/documentary-run.json --output-dir output/documentary --provider auto --confirm-provider-requests
```

The command initializes a blueprint only when the state file does not exist, then resumes chapter-by-chapter at the last saved stage. It stops on a failed chapter without discarding completed work. It does not upload to YouTube. The `longform-documentary.yml` workflow offers the same path from Actions → Long-form documentary factory; generation must be explicitly confirmed, and output is retained as a private workflow artifact. A topic-and-duration-scoped GitHub Actions cache restores the previous run state and generated media on retry, so completed chapters and clips are reused when a job is interrupted. Its zero-budget mode requires FreeLLMAPI with explicit free-model catalogue entries or an OpenRouter model ending in `:free`, plus Pexels for visuals. Agnes requires a separate potential-cost acknowledgement. A 60-minute run can require hundreds of video-provider requests and may exceed free quotas or runner time; use staged/resumable runs and verify the current provider quota before starting.
