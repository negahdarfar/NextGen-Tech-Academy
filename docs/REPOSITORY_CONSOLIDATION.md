# Repository consolidation inventory

Canonical destination: `negahdarfar/NextGen-Tech-Academy`.

This inventory records why assets were or were not copied. Source repositories remain unchanged and are not archived by this PR.

| Source repository | Reviewed role | Decision |
|---|---|---|
| `negahdarfar/-ai-shorts-factory` | Agent skills, MoneyPrinterTurbo Shorts workflow, SEO helpers, competitor research, upload/analytics helpers, documentary clip assembler | Port selected general editorial skills and long-form clip assembly only. Do not port vertical/Shorts production workflows or duplicate the existing NextGen engine. |
| `negahdarfar/ai-trend-shorts-factory` | Private daily Shorts generator: Google Trends, optional YouTube popular feed, Gemini script, Pixabay portrait stock, Edge TTS, 1080×1920 render, review-only artifact | Do not merge: its core pipeline is vertical Shorts-only and uses a separate Gemini/Pixabay secret set. Keep intact for later archival after the canonical workflow is accepted. |
| `negahdarfar/nextgen-tech-academy-web` | Separate website shell and Supabase schema | Keep separate: it is the web frontend, not a video-production engine. Do not merge or archive with video factories. |
| `negahdarfar/korosh` | Generic development-container repository | No video-production assets identified in the reviewed tree. |
| `negahdarfar/earnorbit` | Separate application/API project | Not a video-production repository; keep separate. |
| `negahdarfar/NFT-Art-Factory` | Independent generative-art and marketplace workflow | Keep separate; it is an artwork business pipeline, not a YouTube video engine. |

## Explicitly excluded from this integration

- `moneyprinterturbo.yml`, daily Shorts schedules, portrait/9:16 render steps, and batch-specific uploader scripts: these are explicitly configured for four vertical Shorts and should not control the standard 16:9 documentary factory.
- Competitor research script that queries `videoDuration=short`: its data model is Shorts-specific.
- YouTube Analytics script: it requires `yt-analytics.readonly`; the existing upload authorization is not expanded and no new OAuth consent is requested here.
- FreeLLMAPI router/runtime and provider-specific credentials: those components depend on distinct gateway endpoints and secrets. They require a separate compatibility review; no secret values are readable or copied through this integration.
- Provider-specific scripts requiring a different API key set (Gemini/Pixabay) or unknown paid quotas: not enabled in the canonical workflow.

## Secret and archival policy

GitHub Actions secret values cannot be exported by this process. This integration did not read, expose, delete, or modify any secret. If a future canonical workflow needs a secret that currently exists only in a source repository, its owner must add the value directly to the canonical repository's Actions Secrets through GitHub's secure UI.

Do not archive any source repository until:
1. the draft PR has been reviewed and merged into the canonical default branch;
2. the canonical workflows pass CI;
3. a private end-to-end production test succeeds and the actual video output is reviewed;
4. all required secrets are deliberately configured in the canonical repository;
5. the user explicitly confirms the archival step.

Archival is reversible; deletion is not part of this plan.
