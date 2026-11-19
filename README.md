# NextGen-Tech-Academy

An open-source foundation for an AI-assisted YouTube education production workflow focused on emerging technology, AI, robotics, space, biotechnology, and future innovations.

## Current status

This repository is being built incrementally. The initial foundation provides project documentation, a configuration layer, and a **plan-only** command. It does not yet generate finished videos, upload to YouTube, or run unattended.

## Goals

- Research and validate timely technology topics.
- Draft English narration and create Persian subtitle files.
- Plan standard long-form YouTube videos (not Shorts by default).
- Keep research, scripting, media generation, editing, and publishing as separate stages.
- Prefer free/open-source and local tools where practical, with optional paid providers.
- Require explicit configuration and approval before external publishing.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -e ".[dev]"
nextgen-academy plan --topic "How humanoid robots are changing manufacturing"
```

The current command only prints a production plan. It does not call external APIs or create/publish a video.

## Configuration

Copy `.env.example` to `.env` and fill in only the providers you choose. Never commit API keys or OAuth tokens. YouTube publishing is not implemented in this foundation.

## Project status

See [docs/ROADMAP.md](docs/ROADMAP.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/AGENT_SKILLS.md](docs/AGENT_SKILLS.md).

## Safety and reliability

- No secrets are stored in source control.
- External research must be sourced and fact-checked.
- Generated claims should be reviewed before publication.
- Publishing must remain disabled until OAuth, channel ownership, quota handling, and user approval are implemented and tested.
