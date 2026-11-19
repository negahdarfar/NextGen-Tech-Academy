# One-minute production pipeline

The current target is a standard 60-second 16:9 YouTube video made from four ordered
15-second VidoGrid clips. It is not a Short unless the channel owner separately chooses
a vertical format.

## Stages

1. Draft a bilingual four-scene script with local Ollama, or create an empty storyboard template.
2. Add and manually verify at least two HTTPS sources, then map every factual claim to source IDs.
3. Run the script structure/source-reference gate. It checks completeness, not factual truth.
4. Generate four linked VidoGrid prompts from the reviewed storyboard. English narration and Persian subtitles are carried into the clip manifest.
5. Generate Persian SRT and, optionally, local English narration with Piper.
6. Review VidoGrid credits and explicitly approve paid API submission.
7. Poll each accepted job UUID, persist status and download completed MP4 files.
8. Join clips with FFmpeg and mux narration/subtitles.
9. Generate an editable YouTube metadata package.
10. Watch the exported video and review duration, continuity, factual accuracy, audio, translation, copyright and watermarks.

## Commands

```bash
ollama pull qwen2.5:3b
nextgen-academy draft-script --topic "How quantum computers work"
nextgen-academy script-check
nextgen-academy video-plan --topic "How quantum computers work"
nextgen-academy subtitles
nextgen-academy youtube-package
nextgen-academy voiceover --model models/piper/your-english-voice.onnx
nextgen-academy video-submit --confirm-paid-api
nextgen-academy video-download
nextgen-academy video-render --subtitles output/persian.srt --narration-audio output/narration.wav
```

Ollama must be running locally. The default model is `qwen2.5:3b`; it can be overridden
with `--model` and `--ollama-url`. Piper voice synthesis is optional and requires the
`voice` extra, a downloaded ONNX voice and its JSON config. Review the voice license.

## Known boundaries

- Ollama produces a draft only. It does not browse for sources or verify claims.
- The script review gate validates fields, HTTPS URLs and claim-to-source IDs. A person
  must open every source and decide whether it supports the claim.
- VidoGrid history payloads can evolve. The adapter must be checked against a live account
  before relying on it in production.
- VidoGrid generation consumes account credits. Submission requires both a command-line
  acknowledgement and an interactive confirmation.
- Piper voice quality, model availability and license depend on the selected model.
- The SEO package is a template, not live keyword research or a ranking guarantee.
- Automated research, competitor analysis, thumbnail image generation, music/sound design,
  YouTube OAuth/upload/scheduling and analytics feedback are not implemented yet.
- Human review of the complete export remains mandatory.
