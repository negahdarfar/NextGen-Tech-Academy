# One-minute production pipeline

The initial production target is a standard 60-second 16:9 YouTube video made from
four ordered 15-second VidoGrid clips. It is not a YouTube Short unless the channel
owner separately chooses a vertical format.

## Stages

1. Create a four-beat storyboard and review the prompts.
2. Add fact-checked English narration and its Persian translation to each scene.
3. Generate the clip prompt manifest locally; this step spends no API credits.
4. Review the VidoGrid account balance, then explicitly approve paid API submission.
5. Poll each accepted job UUID, persist status, and download the completed MP4.
6. Normalize and concatenate the clips with FFmpeg.
7. Optionally mux narration audio and a Persian SRT subtitle track.
8. Review duration, visual continuity, factual accuracy, audio levels, subtitles,
   copyright, and provider watermarks manually before upload.

## Commands

```bash
nextgen-academy storyboard --topic "How quantum computers work"
nextgen-academy video-plan --topic "How quantum computers work" --scene "..." --scene "..." --scene "..." --scene "..."
nextgen-academy video-submit --confirm-paid-api
nextgen-academy video-download
nextgen-academy video-render --subtitles output/persian.srt
```

Set the VidoGrid key in a local `.env` file. Never commit it. Install FFmpeg
separately and ensure `ffmpeg` is on PATH. Narration audio is optional; provide
a ready-made audio file with `--narration-audio`.

## Known boundaries

- VidoGrid API history payloads can evolve. The adapter accepts common terminal
  statuses and searches nested result objects for HTTPS MP4/video URLs, but must
  be verified against a real account before production.
- No API requests are made by storyboard, planning, subtitle, or render commands.
- Generation consumes account credits. Each submit command requires explicit
  paid-API acknowledgement and an interactive confirmation.
- This version does not generate verified research, factual scripts, TTS narration,
  thumbnails, or publish to YouTube. Those are separate modules/integrations.
- YouTube publishing remains deliberately out of scope until OAuth, quota handling,
  resumable uploads, channel confirmation, and a final human approval gate exist.
