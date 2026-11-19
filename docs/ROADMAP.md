# Roadmap

## Phase 0 — repository foundation
- [x] Python package skeleton
- [x] Environment configuration template
- [x] Plan-only CLI
- [x] Architecture and specialist-role documentation
- [x] CI workflow and baseline test run (43 tests passed on the integration branch)

## Phase 1 — reliable content artifacts
- [ ] Typed research-source model with URL, publisher, date, and evidence excerpt
- [ ] Topic brief and script schemas
- [ ] English narration script generator behind a provider interface
- [ ] Persian SRT generation and validation
- [ ] Artifact storage and resumable job state

## Phase 2 — media production
- [ ] TTS provider interface and local/free options assessment
- [ ] Visual asset manifest with license/provenance
- [ ] FFmpeg-based rendering adapter
- [ ] Render validation and preview workflow

## Phase 3 — YouTube integration
- [ ] OAuth setup and secure token storage
- [ ] Metadata and thumbnail preparation
- [ ] Upload as private/unlisted first
- [ ] Quota, retries, resumability, and clear upload status
- [ ] Explicit approval gate before public publishing

## Phase 4 — analytics and optimization
- [ ] Authorized YouTube Analytics integration
- [ ] Retention and click-through reporting
- [ ] Evidence-based topic and packaging experiments

## Acceptance criteria

A phase is complete only when it has automated tests, documented configuration, failure handling, and a reproducible local run. A feature is not considered implemented merely because it appears in a roadmap or agent description.


## Integration update — 2026-11-19
- [x] Create a backup branch before consolidation.
- [x] Vendor selected MIT-licensed YouTube editorial skills and CLI helpers (hook scoring, title/thumbnail lint, SEO, planning, chapters, edit decision lists, retention analysis, viral outlier analysis, channel audit).
- [x] Add CI smoke tests for the vendored tools.
- [x] Add a guarded long-form clip-assembly utility with manifest validation.
- [ ] Convert the current one-minute pipeline into a fully sourced, resumable 15–60+ minute documentary workflow.
- [ ] Validate long-form rendering, audio, subtitle sync, asset rights, and upload on a private test before any public release.
- [ ] Review and reconcile remaining useful components from the other video repositories.
