# NextGen-Tech-Academy

An open-source foundation for an AI-assisted YouTube education production workflow focused on emerging technology, AI, robotics, space, biotechnology, and future innovations.

## Current status

The project now includes a first VidoGrid integration layer for planning ordered 15-second-target clip prompts and submitting jobs sequentially through the official API. It is not yet a complete unattended video factory: automatic result downloads, reference-frame continuity, FFmpeg assembly, final QA, and YouTube publishing remain future work.

## Goals

- Research and validate timely technology topics.
- Draft English narration and create Persian subtitle files.
- Plan standard long-form YouTube videos (not Shorts by default).
- Generate short visual clips from a continuous storyboard and assemble them into long-form videos.
- Prefer free/open-source and local tools where practical, with optional paid providers.
- Require explicit configuration and approval before external publishing.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -e ".[dev]"
nextgen-academy plan --topic "How humanoid robots are changing manufacturing"
```

## VidoGrid clip workflow

Create an ordered prompt manifest without making network requests:

```bash
nextgen-academy video-plan \
  --topic "How humanoid robots are changing manufacturing" \
  --scene "Wide establishing shot of a modern robotics factory at dawn" \
  --scene "A humanoid robot carefully moves a component along the production line" \
  --scene "Close-up of robotic hands inspecting the component"
```

Review `output/video-plan.json`, then configure `VIDOGRID_API_KEY` in a local `.env` file. API submission is an explicit, credit-consuming action and requires both an acknowledgement flag and an interactive confirmation:

```bash
nextgen-academy video-submit --confirm-paid-api
```

See [docs/VIDOGRID_INTEGRATION.md](docs/VIDOGRID_INTEGRATION.md) for details.

**Important:** VidoGrid's mobile app may advertise free daily generations, but that must not be assumed to apply to API calls. The API documentation describes API-key authentication and VidoGrid credits. Check the account balance and current API pricing before submitting jobs.

## Safety and reliability

- No secrets are stored in source control.
- External research must be sourced and fact-checked.
- Generated claims should be reviewed before publication.
- API generation is never started by the planning command.
- Publishing must remain disabled until OAuth, channel ownership, quota handling, and user approval are implemented and tested.
