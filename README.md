# NextGen-Tech-Academy

Cloud-first automated YouTube documentary production. The workflow runs on GitHub-hosted runners: no Ollama and no always-on laptop are required.

## Video format
- Standard 16:9 YouTube documentaries, selectable from 3 to 10 minutes.
- English AI-assisted narration with synchronized Persian subtitle track.
- Hybrid 15-second scenes: optional LTX-2.5 generated shots plus Pexels stock B-roll, assembled by FFmpeg. Pexels remains the automatic fallback.
- Automatically extracts 3, 5 or 8 ranked vertical highlights from the finished documentary using local Whisper, Gemini and FFmpeg/OpenCV.
- Chapters, metadata, research links and footage attribution are generated with the production package.
- YouTube upload is private by default. Public publishing is disabled.

## Cloud and local components
- Gemini (optional Groq/OpenRouter fallback) drafts the bilingual documentary script from RSS research leads and fetched source-page extracts.
- A source-audit step records HTTPS page reachability, page title/description, a bounded text extract and a content hash.
- A claim evidence report records cited source IDs and lexical overlap. This is a triage aid only, **not fact verification**; a human must open sources and verify claims.
- LTX-2.5 Fast can generate a small number of cinematic 8-second 720p shots through the official async API; Pexels supplies all remaining scenes and is the automatic fallback.
- Edge TTS creates English narration.
- FFmpeg assembles video, narration and Persian subtitles.
- The MIT-licensed AI-Youtube-Shorts-Generator runs locally on the GitHub runner to select and render vertical highlights; it does not call a paid clipping API.
- YouTube Data API uploads the master documentary privately when enabled. Short clips are currently delivered as workflow artifacts, not automatically published.

## GitHub Actions setup
Add repository Actions secrets:
- `GEMINI_API_KEY` (required for script generation and AI highlight ranking; free-tier quotas apply)
- `PEXELS_API_KEY` (Pexels API key for stock footage search/download)
- `LTX_API_KEY` (optional; only needed to enable LTX-2.5 API generation; paid API)
- `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with the `youtube.upload` scope; required only when uploading)

Optional repository variables:
- `LLM_PROVIDER_ORDER` (default `gemini,groq,openrouter`)
- `LTX_MAX_SPEND_USD` (default `0`: LTX disabled; set a positive per-run request budget only after reviewing API prices)
- `LTX_MAX_SCENES` (default `2`); `LTX_MODEL` (default `ltx-2-5-fast`); `LTX_RESOLUTION` (default `1280x720`); `LTX_CLIP_SECONDS` (default `8`)
- `OPENROUTER_MODEL` (must end in `:free`; paid models are blocked)

Open **Actions → Automated YouTube documentary factory → Run workflow**. Choose a duration from 3 to 10 minutes and the number of vertical highlights (3, 5 or 8). Leave topic blank for automatic topic discovery. The upload checkbox defaults to false; if enabled, the finished master video is uploaded privately. Scheduled runs are Tuesday and Friday at 06:17 UTC; they upload privately only when `YOUTUBE_TOKEN_JSON` is configured, otherwise they still generate the artifact.

## LTX-2.5 cost and safety
LTX generation is disabled by default. It requires both the optional `LTX_API_KEY` secret and a positive `LTX_MAX_SPEND_USD` Actions variable. At the documented LTX-2.5 Fast 720p rate ($0.09/output second), one 8-second shot is approximately $0.72; at 1080p ($0.13/second), approximately $1.04. The local budget limits the number of requests submitted by this workflow but is not a provider-side hard billing cap. Review the LTX console balance, disable automatic top-up if desired, and never add the key unless you accept API charges. With no key or a zero budget, the workflow uses Pexels only. API errors fall back to the already-downloaded Pexels scene.

## Outputs
The workflow preserves `output/` as a GitHub Actions artifact for 14 days, including the master MP4, storyboard, Persian SRT, narration, source audit, claim evidence audit, footage-source manifest, YouTube metadata package, vertical MP4 clips and highlight report. If highlight extraction fails, the master documentary and its files are still preserved.

## Important notes
Pexels API quotas and license terms apply; this is not unlimited free compute. Gemini free-tier quotas and GitHub Actions usage limits also apply. The workflow records creator/source URLs in the output and description. RSS feeds and fetched pages are research inputs, not guaranteed reliable evidence. A reachable page or keyword overlap does not prove a claim. Human fact-checking, complete-video review and media-rights review are mandatory before public release. The first live run should be supervised. Public YouTube publishing remains disabled.
