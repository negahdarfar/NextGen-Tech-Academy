# Architecture

The cloud pipeline is composed of replaceable stages: topic discovery, source collection, Gemini/Groq/OpenRouter script drafting, English narration, Persian subtitle generation, licensed stock-footage retrieval, FFmpeg rendering, quality checks and YouTube upload.

## Media provider
Pexels supplies landscape stock footage through its API. Each selected asset is recorded with its Pexels video ID, creator and source URL. Four 15-second sections are normalized and assembled into a 60-second 16:9 video. This is stock footage and motion editing, not text-to-video generation.

## Runtime
GitHub Actions executes the cloud workflow; Ollama remains optional for local experiments. Pexels API access and YouTube OAuth credentials are stored as GitHub Actions secrets. The uploader defaults to private visibility.
