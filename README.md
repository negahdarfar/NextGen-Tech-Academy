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


## Free AI clipping workflow

A separate GitHub Actions workflow converts a long YouTube video into ranked vertical clips without a paid clipping API:
- Open **Actions → Free AI video clipper → Run workflow**.
- Enter a YouTube URL for a video you own or are authorized to edit.
- Choose 3, 5, or 8 clips and the source speech language.
- The workflow uses the MIT-licensed [AI YouTube Shorts Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) in its local mode, pinned to commit `1142a747b0056da5551970e88ca9f1ec85deafc5`.
- Faster-Whisper transcribes on the GitHub Actions runner; Gemini ranks highlight moments; FFmpeg/OpenCV renders 9:16 MP4 clips.
- Download the MP4 files and `clip-report.json` from the run's Artifacts section.

This clipping workflow needs the existing `GEMINI_API_KEY` Actions secret; it does not need MuAPI, Ollama, VidoGrid, OpusClip, Vizard, Klap, or Pexels. The clipper software and media-processing tools are free/open source. Gemini free-tier quotas and GitHub Actions usage limits still apply. Processing speed depends on video length and runner load. This workflow currently creates downloadable artifacts; it does not publish the extracted clips automatically.

Only process videos you own or have permission to use. A public YouTube URL does not itself grant reuse rights.
