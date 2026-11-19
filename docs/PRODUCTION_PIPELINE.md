# One-minute production pipeline

The initial production target is a standard 60-second 16:9 YouTube video made from
four ordered 15-second VidoGrid clips. It is not a YouTube Short unless the channel
owner separately chooses a vertical format.

## Stages

1. Create a four-beat storyboard and review the prompts.
2. Fill the four `narration_en` and `subtitle_fa` fields in the storyboard with fact-checked English narration and faithful Persian translations.
3. Generate Persian SRT and, if a properly licensed Piper voice model is installed, local English narration WAV. These steps use no paid API credits.
4. Generate the clip prompt manifest locally; this step spends no API credits.
5. Review the VidoGrid account balance, then explicitly approve paid API submission.
6. Poll each accepted job UUID, persist status, and download the completed MP4.
7. Normalize and concatenate the clips with FFmpeg.
8. Mux the narration audio and Persian SRT subtitle track.
9. Review duration, visual continuity, factual accuracy, audio levels, subtitles,
   copyright, and provider watermarks manually before upload.

## Commands

```bash
nextgen-academy storyboard --topic "How quantum computers work"
nextgen-academy video-plan --topic "How quantum computers work" --scene "..." --scene "..." --scene "..." --scene "..."
nextgen-academy subtitles
nextgen-academy voiceover --model models/piper/your-english-voice.onnx
nextgen-academy video-submit --confirm-paid-api
nextgen-academy video-download
nextgen-academy video-render --subtitles output/persian.srt --narration-audio output/narration.wav
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
- This version does not generate verified research or factual scripts. Piper TTS is an optional local engine requiring a downloaded voice model; check each model's license. The pipeline does not automatically choose a voice model. It does not yet generate
  thumbnails, or publish to YouTube. Those are separate modules/integrations.
- YouTube publishing remains deliberately out of scope until OAuth, quota handling,
  resumable uploads, channel confirmation, and a final human approval gate exist.
