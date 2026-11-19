# VidoGrid video generation integration

This module adds a provider adapter and a sequential clip-job submission workflow.
The default endpoint is VidoGrid's Grok Imagine Video 1.5 Lite route, which the
official model listing describes as supporting clips up to 15 seconds. The
mobile app's advertised free daily generations are not assumed to be available
through the API. The API documentation describes API-key authentication and
VidoGrid credits; check the account endpoint and current pricing before
submitting jobs.

## Configuration

Set these values in a local `.env` file (never commit the real key):

```dotenv
VIDOGRID_API_KEY=your_api_key
VIDOGRID_ENDPOINT=/video-gen/grok-imagine-video-1.5-lite
VIDOGRID_MODEL=grok-imagine-video-1.5-lite
VIDOGRID_DURATION_SECONDS=15
VIDOGRID_ASPECT_RATIO=16:9
VIDOGRID_RESOLUTION=720p
```

The API base URL defaults to `https://api.vidogrid.ai/uapi/v1`.

## Workflow

1. Build an ordered shot list from an approved script/storyboard.
2. Use `build_segments` to create prompts with a shared visual bible and
   continuity instructions.
3. Check account balance with `VidoGridClient.account()`.
4. Submit jobs sequentially with `submit_segments`. A JSON manifest is written
   after every accepted job so accepted UUIDs are not lost if the process stops.
5. Poll each UUID with `VidoGridClient.history(uuid)` until the provider reports
   a terminal state and exposes an output file.
6. Download completed clips, validate their actual duration/format, then join
   them locally with FFmpeg in manifest order.

## Important limits

- Grok Imagine Video 1.5 Lite supports up to 15 seconds per generated clip.
  Always inspect the returned clip metadata; a target duration is not proof
  that the provider rendered exactly 15 seconds.
- The Lite model does not provide the same reference-image/last-frame controls
  as the full Grok model. Prompt continuity is implemented now; visual
  reference-frame chaining is a follow-up feature and may require a different
  model and higher credit cost.
- The first adapter uses the documented VidoGrid multipart API shape and
  configurable endpoint. Provider-specific parameter changes must be verified
  against the live API docs before production use.
- API jobs consume API credits. Do not assume the mobile app's free quota is
  shared with the API.
- Signed webhook verification, automatic downloads, FFmpeg rendering, and
  YouTube publishing are not implemented yet.
- No job is submitted unless the user explicitly runs the submit command with
  a configured API key and confirms the operation.
