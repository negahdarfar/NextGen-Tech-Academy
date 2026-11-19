"""Assemble licensed stock clips, English narration and Persian subtitles."""
from __future__ import annotations
import json, shutil, subprocess
from pathlib import Path
from typing import Any

class PipelineError(RuntimeError):
    pass

def render_video(jobs_manifest: str | Path, output_file: str | Path,
                 subtitles: str | Path | None = None,
                 narration_audio: str | Path | None = None) -> Path:
    manifest=json.loads(Path(jobs_manifest).read_text(encoding="utf-8"))
    jobs=sorted(manifest.get("jobs",[]),key=lambda item:int(item["index"]))
    if len(jobs)!=4: raise PipelineError("The one-minute preset requires exactly four stock clips.")
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg: raise PipelineError("FFmpeg was not found.")
    output=Path(output_file); output.parent.mkdir(parents=True,exist_ok=True)
    work=output.parent/(output.stem+"_normalized"); work.mkdir(parents=True,exist_ok=True)
    normalized=[]
    for job in jobs:
        source=Path(job.get("local_path",""))
        if not source.is_file(): raise PipelineError(f"Missing stock clip: {source}")
        target=work/f"clip_{int(job['index']):03d}.mp4"
        _run([ffmpeg,"-y","-i",str(source),"-t","15","-an","-vf",
              "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
              "-c:v","libx264","-preset","veryfast","-crf","21","-movflags","+faststart",str(target)])
        normalized.append(target)
    concat=work/"concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in normalized),encoding="utf-8")
    joined=work/"joined.mp4"
    _run([ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(joined)])
    inputs=["-i",str(joined)]
    audio_idx=None; sub_idx=None
    if narration_audio:
        audio=Path(narration_audio)
        if not audio.is_file(): raise PipelineError(f"Narration audio not found: {audio}")
        audio_idx=1; inputs += ["-i",str(audio)]
    if subtitles:
        sub=Path(subtitles)
        if not sub.is_file(): raise PipelineError(f"Subtitle file not found: {sub}")
        sub_idx=1+int(bool(narration_audio)); inputs += ["-i",str(sub)]
    cmd=[ffmpeg,"-y",*inputs,"-map","0:v:0"]
    if audio_idx is not None: cmd += ["-map",f"{audio_idx}:a:0","-c:a","aac","-shortest"]
    else: cmd += ["-map","0:a?","-c:a","copy"]
    if sub_idx is not None: cmd += ["-map",f"{sub_idx}:s:0","-c:s","mov_text"]
    cmd += ["-c:v","copy","-movflags","+faststart",str(output)]
    _run(cmd)
    return output

def validate_render_duration(video_path: str | Path, minimum_seconds: float=55.0, maximum_seconds: float=70.0) -> float:
    ffprobe=shutil.which("ffprobe")
    if not ffprobe: raise PipelineError("ffprobe was not found.")
    result=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(video_path)],capture_output=True,text=True)
    if result.returncode: raise PipelineError(f"Could not inspect final video: {result.stderr[-1200:]}")
    try: duration=float(result.stdout.strip())
    except ValueError as exc: raise PipelineError("ffprobe returned an invalid duration.") from exc
    if not minimum_seconds<=duration<=maximum_seconds: raise PipelineError(f"Final render is {duration:.2f}s; expected {minimum_seconds:.0f}-{maximum_seconds:.0f}s. Upload blocked.")
    return duration

def write_srt(segments: list[dict[str,Any]], target: str | Path) -> Path:
    cursor=0.0; rows=[]
    for item in segments:
        duration=float(item.get("duration_seconds",15))
        caption=str(item.get("subtitle") or item.get("narration","")).strip()
        if caption: rows.append(f"{len(rows)+1}\n{_stamp(cursor)} --> {_stamp(cursor+duration)}\n{caption}\n")
        cursor+=duration
    path=Path(target); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("\n".join(rows),encoding="utf-8-sig")
    return path

def _stamp(seconds: float) -> str:
    ms=int(round(seconds*1000)); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _run(command: list[str]) -> None:
    result=subprocess.run(command,capture_output=True,text=True)
    if result.returncode: raise PipelineError(f"Media command failed: {result.stderr[-2500:]}")
