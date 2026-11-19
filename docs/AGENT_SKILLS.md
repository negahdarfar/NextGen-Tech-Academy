# Specialist agent skills

These are role specifications for a future orchestrator, not claims that autonomous agents are already implemented.

1. **Trend Scout** — proposes technology topics and explains the evidence for audience relevance.
2. **Research Analyst** — gathers primary sources and structured evidence with dates and URLs.
3. **Fact Checker** — checks claims against sources and flags uncertainty or contradictions.
4. **Story Architect** — turns verified research into a coherent narrative outline.
5. **Scriptwriter** — writes clear English narration for the selected audience and duration.
6. **Persian Localization Editor** — translates and adapts narration into natural Persian subtitles.
7. **Visual Director** — maps each script segment to footage, diagrams, or generated imagery.
8. **Asset & Rights Curator** — tracks source, license, attribution, and usage restrictions for every asset.
9. **Voice & Audio Producer** — selects configured text-to-speech voices and checks audio quality.
10. **Video Editor & QA** — assembles the timeline and checks render, captions, audio, and pacing.
11. **YouTube Growth Analyst** — prepares metadata and analyzes performance data when authorized access exists.

## Orchestration rule

Agents must exchange structured artifacts and cite evidence. The orchestrator must stop for human review when evidence is weak, rights are unclear, a provider fails, or a publish action is requested.

## Vendored executable YouTube skills

Selected MIT-licensed skills and their dependency-free helper tools are now vendored under `.claude/skills/`. The upstream copyright and MIT terms are preserved in `.claude/skills/YOUTUBE-AGENT-LICENSE`.

| Skill | Location | Purpose |
|---|---|---|
| Script & hook scoring | `.claude/skills/yt-script/` | Five hook options, scoring, evidence-aware script structure |
| Packaging | `.claude/skills/yt-package/` | Title/thumbnail pairing lint and clarity checks |
| SEO | `.claude/skills/yt-seo/` | Search-intent-led descriptions, tags and query alignment |
| Planning | `.claude/skills/yt-plan/` | Capacity-aware editorial calendar |
| Chapters | `.claude/skills/yt-chapters/` | Transcript-based chapter draft and YouTube rule validation |
| Editing decisions | `.claude/skills/yt-edit/` | Transcript-based edit decision list; does not alter media |
| Retention | `.claude/skills/yt-retention/` | Analysis of exported audience-retention CSV |
| Viral research | `.claude/skills/yt-viral/` | Relative outlier analysis against each channel median |
| Channel audit | `.claude/skills/yt-audit/` | Prioritized channel review |

### Invocation and limits

These are agent-readable skill instructions and local CLI helpers. GitHub Actions does not interpret `SKILL.md` automatically; no claim is made that autonomous agents are running. Use the Python helpers explicitly in an agent or a tested workflow. The skills do not upload, publish, delete, or modify channel content.

Some upstream examples refer to Shorts. For this repository, apply the editorial principles to standard 16:9 videos and long-form documentaries; do not import Shorts-specific production targets or vertical-render settings. Competitor research and analytics require their own authorized data sources. Analytics exports and YouTube Analytics API scopes are not enabled or requested by this integration.

### Local helper commands

```bash
python .claude/skills/yt-script/hookscore.py --hook "A factual opening line with a clear promise."
python .claude/skills/yt-package/title.py --title "A clear documentary title" --thumb "THE EVIDENCE"
python .claude/skills/yt-chapters/chapters.py transcript.srt --target 8
python .claude/skills/yt-edit/deadair.py transcript.srt --json
python .claude/skills/yt-retention/retention.py retention.csv --json
python .claude/skills/yt-viral/swipe.py collected.json --min 2.0 --json
```
