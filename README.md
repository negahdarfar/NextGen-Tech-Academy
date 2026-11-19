# NextGen-Tech-Academy

Cloud-first automated YouTube documentary production. The cloud workflow does not require Ollama or an always-on laptop.

## Video format
- Standard 16:9 YouTube video, 60 seconds (four 15-second stock-footage scenes).
- English narration, Persian subtitles, FFmpeg assembly and metadata.
- Private YouTube upload by default; public publishing is disabled.

## Cloud providers
- Gemini (with optional Groq/OpenRouter fallback) writes the bilingual storyboard.
- Pexels API supplies royalty-free stock video footage. This is real stock footage, not AI-generated video.
- Edge TTS creates English narration.
- FFmpeg trims and joins four 15-second segments, adds Persian subtitles and narration.
- YouTube Data API uploads the finished video privately.

## GitHub Actions setup
Add repository Actions secrets:
- `GEMINI_API_KEY` (or another configured LLM provider)
- `PEXELS_API_KEY` (free Pexels API key; required for stock footage search/download)
- `YOUTUBE_TOKEN_JSON` (OAuth authorized-user JSON with the `youtube.upload` scope)

Optional repository variables:
- `LLM_PROVIDER_ORDER` (default `gemini,groq,openrouter`)
- `OPENROUTER_MODEL` (must end in `:free` unless paid use is explicitly enabled; production sets paid use off)

Open Actions → Automated YouTube video factory → Run workflow. Leave topic blank for automatic topic discovery. Upload is private by default. Scheduled runs are Tuesday and Friday at 06:17 UTC.

## Important notes
Pexels API access is subject to its current API limits and license terms. The workflow records creator/source URLs in `stock-footage-sources.json` and the YouTube description. Review attribution and usage terms before public release. Stock footage may not exactly depict every narrated claim; it is illustrative B-roll, not generated footage. The script's research leads still require human fact-checking.
