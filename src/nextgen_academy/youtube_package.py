"""Build an editable YouTube publishing package without inventing sources."""
from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any

def _stamp(seconds: int) -> str:
    hours,rem=divmod(seconds,3600); minutes,secs=divmod(rem,60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"

def build_youtube_package(storyboard_path: str | Path, output_path: str | Path) -> Path:
    payload=json.loads(Path(storyboard_path).read_text(encoding="utf-8"))
    topic=str(payload.get("topic","")).strip(); scenes=payload.get("scenes",[])
    if not topic or len(scenes)<12: raise ValueError("A topic and at least 12 scenes (3 minutes) are required.")
    titles=[f"{topic}: The Technology Explained",f"How {topic} Could Change the Future",f"What You Need to Know About {topic}"]
    duration=int(payload.get("clip_duration_seconds",15))
    chapters=[{"time":_stamp(i*duration),"title":str(scene.get("title",f"Chapter {i+1}"))} for i,scene in enumerate(scenes)]
    words=re.findall(r"[A-Za-z0-9]+",topic.lower())
    tags=list(dict.fromkeys(words+["technology","innovation","science","future","explained","documentary"]))
    package:dict[str,Any]={"topic":topic,"title_options":titles,"recommended_title":titles[0],
      "description_template":f"Explore {topic} in this technology documentary.\n\nResearch sources:\n[ADD VERIFIED PRIMARY SOURCES]\n\nSubscribe for more explainers.",
      "tags":tags[:25],"hashtags":["#Technology","#Innovation","#Science"],"chapters":chapters,
      "thumbnail_prompt":f"Create a clean, high-contrast 16:9 documentary thumbnail about {topic}; one central subject, cinematic lighting, readable English title, no misleading claims.",
      "pinned_comment":f"What is the most interesting question you have about {topic}?",
      "publication_checks":["Verify all factual claims against primary sources.","Review the complete exported video and Persian subtitles.","Check commercial-use rights for narration, footage, music and images.","Confirm title, thumbnail and chapters accurately represent the video."],
      "note":"Metadata is an editable draft; it is not a guarantee of search ranking."}
    target=Path(output_path); target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding="utf-8")
    return target
