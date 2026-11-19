# VidoGrid video generation integration

This module adds a provider adapter and a sequential clip-job submission workflow.
It does not claim that the mobile app's advertised free daily generations are
available through the API. The official API documentation describes API-key
authentication and VidoGrid credits; check the account endpoint and current
pricing before submitting paid jobs.

## Configuration

Set these values in a local `.env` file (never commit the real key):

```dotenv
VIDOGRID_API_KEY=your_api_key
VIDOGRID_MODEL=veo-3.1-fast
VIDOGRID_ASPECT_RATIO=16:9
VIDOGRID_RESOLUTION=720p
```

The API base URL defaults to `https://api.vidogrid.ai/uapi/v1`.

## Workflow

1. Build a shot list from an approved script/storyboard.
2. Use `build_segments` to create ordered prompts with a shared visual bible
   and continuity instructions.
3. Check account balance with `VidoGridClient.account()`.
4. Submit jobs sequentially with `submit_segments`. A JSON manifest is written
   after every accepted job so accepted UUIDs are not lost if the process stops.
5. Poll each UUID with `VidoGridClient.history(uuid)` until the provider reports
   a terminal state and exposes an output file.
6. Download completed clips, validate their actual duration/format, then join
   them locally with FFmpeg in manifest order.

## Important limits

- A 15-second target in the storyboard is not a provider guarantee. Actual
  duration depends on the selected model and its documented request options.
- This first adapter uses the documented Veo endpoint and fields
  `model`, `prompt`, `aspect_ratio`, and `resolution`. Model-specific
  duration controls, reference-frame chaining, signed webhook verification,
  automatic downloads, and FFmpeg rendering are follow-up work.
- API jobs consume API credits. Do not assume the mobile app's free quota is
  shared with the API.
- No job is submitted unless the user explicitly runs the submit command with
  a configured API key. No YouTube publishing is performed.
