"""Command-line entry point for cloud and local production workflows."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .config import load_dotenv
from .ollama_writer import draft_storyboard
from .planning import build_plan, plan_as_dict
from .script import default_storyboard, save_script_package
from .video_segments import build_segments, segments_as_dicts

def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="nextgen-academy",description="Produce bilingual YouTube technology documentaries.")
    sub=parser.add_subparsers(dest="command",required=True)
    plan=sub.add_parser("plan",help="create a research/production plan"); plan.add_argument("--topic",required=True); plan.add_argument("--audience",default="curious general audience")
    storyboard=sub.add_parser("storyboard",help="create a starter storyboard"); storyboard.add_argument("--topic",required=True); storyboard.add_argument("--output",default="output/storyboard.json")
    draft=sub.add_parser("draft-script",help="draft a script using local Ollama"); draft.add_argument("--topic",required=True); draft.add_argument("--output",default="output/storyboard.json"); draft.add_argument("--ollama-url",default="http://127.0.0.1:11434"); draft.add_argument("--model",default="qwen2.5:3b"); draft.add_argument("--timeout",type=int,default=180)
    clips=sub.add_parser("video-plan",help="create linked documentary clip prompts"); clips.add_argument("--topic",required=True); clips.add_argument("--scene",action="append"); clips.add_argument("--storyboard",default="output/storyboard.json"); clips.add_argument("--style",default="cinematic documentary, realistic detail, natural motion"); clips.add_argument("--output",default="output/video-plan.json")
    auto=sub.add_parser("auto-run",help="run cloud documentary production without Ollama")
    auto.add_argument("--topic",default=""); auto.add_argument("--output-dir",default="output"); auto.add_argument("--duration-minutes",type=int,choices=range(3,11),default=5)
    auto.add_argument("--upload",action="store_true",help="upload privately to YouTube after rendering")
    return parser

def main() -> int:
    args=build_parser().parse_args(); load_dotenv()
    if args.command=="plan":
        print(json.dumps(plan_as_dict(build_plan(args.topic,args.audience)),ensure_ascii=False,indent=2)); return 0
    if args.command=="storyboard":
        path=save_script_package(args.topic,default_storyboard(args.topic),args.output); print(f"Created starter storyboard: {path}"); return 0
    if args.command=="draft-script":
        path=draft_storyboard(args.topic,args.output,args.ollama_url,args.model,args.timeout); print(f"Created bilingual AI draft (not fact-checked): {path}"); return 0
    if args.command=="video-plan":
        storyboard_scenes=None
        if args.scene: scenes=args.scene
        else:
            p=Path(args.storyboard)
            if p.is_file():
                data=json.loads(p.read_text(encoding="utf-8"))
                if data.get("topic")!=args.topic: raise SystemExit("Storyboard topic does not match --topic.")
                storyboard_scenes=data.get("scenes",[]); scenes=[item["scene"] for item in storyboard_scenes]
            else: scenes=[item["scene"] for item in default_storyboard(args.topic)]
        if not scenes: raise SystemExit("At least one scene is required.")
        segments=segments_as_dicts(build_segments(args.topic,scenes,args.style,duration_seconds=15))
        if storyboard_scenes:
            for i,scene in enumerate(storyboard_scenes):
                segments[i]["narration"]=scene.get("narration_en",""); segments[i]["subtitle"]=scene.get("subtitle_fa","")
        payload={"topic":args.topic,"target_duration_seconds":len(segments)*15,"clip_duration_target_seconds":15,"aspect_ratio":"16:9","visual_style":args.style,"segments":segments}
        target=Path(args.output); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        print(f"Created {len(segments)} linked scenes ({len(segments)*15} seconds): {target}"); return 0
    if args.command=="auto-run":
        from .automation import run_automated
        result=run_automated(args.topic,args.output_dir,publish=args.upload,duration_minutes=args.duration_minutes)
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    return 2

if __name__=="__main__": raise SystemExit(main())
