# NextGen-Tech-Academy

Cloud-first automated YouTube documentary production. The workflow runs on GitHub-hosted runners: no Ollama and no always-on laptop are required.

## Video format
- Standard 16:9 YouTube documentaries, selectable from 3 to 10 minutes.
- English AI-assisted narration with synchronized Persian subtitle track.
- 15-second stock-footage scenes assembled by FFmpeg; footage is licensed stock B-roll, not AI-generated video.
- Chapters, metadata, research links and footage attribution are generated with the production package.
- YouTube upload is private by default. Public publishing is disabled.

## Cloud providers
- Gemini (optional Groq/OpenRouter fallback) drafts the bilingual documentary script from RSS research leads.
- Pexels supplies landscape stock footage.
- Edge TTS creates English narration.
- FFmpeg assembles video, narration and Persian subtitles.
- YouTube Data API uploads privately when the workflow input is enabled.

## GitHub Actions setup
Add repository Actions secrets:
- `GEMINI_API_KEY` (or another configured cloud LLM provider key)
- `PEXELS_API_KEY` (Pexels API key for stock footage search/download)
- `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with the `youtube.upload` scope)

Optional repository variables:
- `LLM_PROVIDER_ORDER` (default `gemini,groq,openrouter`)
- `OPENROUTER_MODEL` (must end in `:free`; paid models are blocked)

Open **Actions → Automated YouTube documentary factory → Run workflow**. Choose a duration from 3 to 10 minutes. Leave topic blank for automatic topic discovery. The upload checkbox defaults to false; if enabled, the finished video is uploaded privately. Scheduled runs are Tuesday and Friday at 06:17 UTC and upload privately.

## Outputs
The workflow preserves `output/` as a GitHub Actions artifact for 14 days, including the MP4, storyboard, Persian SRT, narration, footage-source manifest and YouTube metadata package.

## Important notes
Pexels API quotas and license terms apply; this is not unlimited free compute. Gemini free-tier quotas and GitHub Actions usage limits also apply. The workflow records creator/source URLs in the output and description. RSS results are research leads, not verified evidence: fact-check claims, review the complete video and confirm media rights before public release. The first live run should be supervised.
