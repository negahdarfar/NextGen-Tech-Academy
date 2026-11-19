"""Edge neural TTS adapter for cloud runners."""
from __future__ import annotations
import json, shutil, subprocess
from pathlib import Path

class CloudTTSError(RuntimeError):
    pass

def synthesize_cloud_narration(storyboard_path: str | Path, output_wav: str | Path,
                               voice: str = "en-US-AriaNeural", scene_duration: int = 15) -> Path:
    payload=json.loads(Path(storyboard_path).read_text(encoding="utf-8"))
    scenes=payload.get("scenes", [])
    if not scenes: raise CloudTTSError("The storyboard contains no scenes.")
    if scene_duration < 5 or scene_duration > 60: raise CloudTTSError("Scene duration must be 5-60 seconds.")
    if not shutil.which("ffmpeg"): raise CloudTTSError("FFmpeg is required.")
    edge_tts=shutil.which("edge-tts")
    if not edge_tts: raise CloudTTSError("edge-tts executable not found; install the cloud extra.")
    root=Path(output_wav).parent/"voice_parts"; root.mkdir(parents=True,exist_ok=True)
    tracks=[]
    for index,scene in enumerate(scenes,1):
        text=str(scene.get("narration_en","")).strip()
        if not text: raise CloudTTSError(f"Scene {index} has no English narration.")
        mp3=root/f"scene_{index:03d}.mp3"; wav=root/f"scene_{index:03d}.wav"
        result=subprocess.run([edge_tts,"--voice",voice,"--text",text,"--write-media",str(mp3)],capture_output=True,text=True)
        if result.returncode or not mp3.is_file(): raise CloudTTSError(f"Edge TTS failed on scene {index}: {result.stderr[-1000:]}")
        result=subprocess.run(["ffmpeg","-y","-i",str(mp3),"-af",f"apad=whole_dur={scene_duration},atrim=duration={scene_duration}",
                               "-ar","44100","-ac","2",str(wav)],capture_output=True,text=True)
        if result.returncode: raise CloudTTSError(f"Audio normalization failed on scene {index}: {result.stderr[-1000:]}")
        tracks.append(wav)
    concat=root/"concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in tracks),encoding="utf-8")
    output=Path(output_wav); output.parent.mkdir(parents=True,exist_ok=True)
    result=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c:a","pcm_s16le",str(output)],capture_output=True,text=True)
    if result.returncode: raise CloudTTSError(f"Could not join narration: {result.stderr[-1500:]}")
    return output
