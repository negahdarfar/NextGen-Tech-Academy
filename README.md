# NextGen-Tech-Academy

Cloud-first automated YouTube documentary production. The workflow runs on GitHub-hosted runners: no Ollama and no always-on laptop are required.

## Video format
- Standard 16:9 YouTube documentaries, selectable from 3 to 10 minutes.
- English AI-assisted narration with synchronized Persian subtitle track.
- 15-second stock-footage scenes assembled by FFmpeg; footage is licensed stock B-roll, not AI-generated video.
- Automatically extracts 3, 5 or 8 ranked vertical highlights from the finished documentary using local Whisper, Gemini and FFmpeg/OpenCV.
- Chapters, metadata, research links and footage attribution are generated with the production package.
- YouTube upload is private by default. Public publishing is disabled.

## Cloud and local components
- Gemini (optional Groq/OpenRouter fallback) drafts the bilingual documentary script from RSS research leads.
- Pexels supplies landscape stock footage.
- Edge TTS creates English narration.
- FFmpeg assembles video, narration and Persian subtitles.
- The MIT-licensed AI-Youtube-Shorts-Generator runs locally on the GitHub runner to select and render vertical highlights; it does not call a paid clipping API.
- YouTube Data API uploads the master documentary privately when enabled. Short clips are currently delivered as workflow artifacts, not automatically published.

## GitHub Actions setup
Add repository Actions secrets:
- `GEMINI_API_KEY` (required for script generation and AI highlight ranking; free-tier quotas apply)
- `PEXELS_API_KEY` (Pexels API key for stock footage search/download)
- `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with the `youtube.upload` scope; required only when uploading)

Optional repository variables:
- `LLM_PROVIDER_ORDER` (default `gemini,groq,openrouter`)
- `OPENROUTER_MODEL` (must end in `:free`; paid models are blocked)

Open **Actions → Automated YouTube documentary factory → Run workflow**. Choose a duration from 3 to 10 minutes and the number of vertical highlights (3, 5 or 8). Leave topic blank for automatic topic discovery. The upload checkbox defaults to false; if enabled, the finished master video is uploaded privately. Scheduled runs are Tuesday and Friday at 06:17 UTC; they upload privately only when `YOUTUBE_TOKEN_JSON` is configured, otherwise they still generate the artifact.

## Outputs
The workflow preserves `output/` as a GitHub Actions artifact for 14 days, including the master MP4, storyboard, Persian SRT, narration, footage-source manifest, YouTube metadata package, vertical MP4 clips and highlight report. If highlight extraction fails, the master documentary and its files are still preserved.

## Important notes
Pexels API quotas and license terms apply; this is not unlimited free compute. Gemini free-tier quotas and GitHub Actions usage limits also apply. The workflow records creator/source URLs in the output and description. RSS results are research leads, not verified evidence: fact-check claims, review the complete video and confirm media rights before public release. The first live run should be supervised. Public YouTube publishing remains disabled.
