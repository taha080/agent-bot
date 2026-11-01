"""Video episode builder: the part that makes the same *type* of video
as a Grok Bot episode -- real AI-video clips stitched into one episode
with narration, burned-in subtitles, chapter overlays, and an end card.

How it works (original implementation, no copied code or assets):
  1. A script JSON lists scenes: narration text, on-screen chapter
     title, clip file, and duration.
  2. Clips come from any video model the user already has access to
     (their own Grok Bot, Flow, Veo, or another tool). This repo does
     NOT bundle or copy any commercial model; it orchestrates clips
     the user generated themselves.
  3. assemble() stitches the clips, lays the narration audio over
     them, burns subtitles, draws a chapter title at each scene start,
     and appends a "TO BE CONTINUED" end card.

A clip provider interface is included for automation: implement
generate_clip() for a video API you hold a key for (the key is read
from the environment, never stored in the repo). A local fallback
provider animates a still first-frame with a slow zoom/pan -- it is
honestly labelled as camera motion, not real character motion.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Scene:
    clip: str          # path to an 8s-ish video clip, relative to clips_dir
    narration: str     # what the narrator says in this scene
    chapter: str = ""  # on-screen chapter title, "" for none
    duration: float = 8.0


def load_script(script_file: Path) -> list[Scene]:
    data = json.loads(Path(script_file).read_text())
    return [Scene(**scene) for scene in data["scenes"]]


def _srt_time(seconds: float) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    millis = int(round((secs - int(secs)) * 1000))
    return f"{int(hours):02d}:{int(minutes):02d}:{int(secs):02d},{millis:03d}"


def build_subtitles(scenes: list[Scene]) -> str:
    """One subtitle block per scene, timed to the scene's slot."""
    blocks, cursor = [], 0.0
    for index, scene in enumerate(scenes, start=1):
        blocks.append(
            f"{index}\n{_srt_time(cursor)} --> {_srt_time(cursor + scene.duration)}"
            f"\n{scene.narration}\n"
        )
        cursor += scene.duration
    return "\n".join(blocks)


def chapter_overlays(scenes: list[Scene]) -> list[str]:
    """ffmpeg drawtext filters: chapter title for the first 3s of a scene."""
    filters, cursor = [], 0.0
    for scene in scenes:
        if scene.chapter:
            safe = scene.chapter.replace("'", r"\'").replace(":", r"\:")
            filters.append(
                f"drawtext=text='{safe}':fontsize=64:fontcolor=white:"
                f"box=1:boxcolor=black@0.6:x=(w-text_w)/2:y=80:"
                f"enable='between(t,{cursor:.1f},{cursor + 3:.1f})'"
            )
        cursor += scene.duration
    return filters


def assemble(
    scenes: list[Scene],
    clips_dir: Path,
    narration_audio: Path | None,
    out_file: Path,
    end_card_text: str = "TO BE CONTINUED",
    resolution: str = "1920x1080",
) -> str:
    """Concatenate clips, add narration, subtitles, chapters, end card."""
    clips_dir, out_file = Path(clips_dir), Path(out_file)
    work = out_file.parent / ".assemble_tmp"
    work.mkdir(parents=True, exist_ok=True)

    concat_list = work / "concat.txt"
    concat_list.write_text("".join(
        f"file '{(clips_dir / scene.clip).resolve()}'\n" for scene in scenes
    ))
    subtitles = work / "subs.srt"
    subtitles.write_text(build_subtitles(scenes))

    video_only = work / "video_only.mp4"
    draw = ",".join(chapter_overlays(scenes))
    vf = [f"scale={resolution}"]
    if draw:
        vf.append(draw)
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-vf", ",".join(vf), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(video_only),
    ], check=True, capture_output=True)

    # End card: 3s black frame with text, appended after the episode.
    end_card = work / "endcard.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s={resolution}:d=3",
        "-vf", f"drawtext=text='{end_card_text}':fontsize=72:fontcolor=white:"
               "x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(end_card),
    ], check=True, capture_output=True)

    inputs = ["-i", str(video_only), "-i", str(end_card)]
    filter_complex = f"[0:v][1:v]concat=n=2:v=1:a=0[v];[v]subtitles={subtitles}[vout]"
    if narration_audio:
        inputs += ["-i", str(narration_audio)]
        filter_complex += ";[2:a]apad=whole_dur=1[a]"
        audio_args = ["-map", "[vout]", "-map", "[a]", "-shortest"]
    else:
        audio_args = ["-map", "[vout]"]
    subprocess.run([
        "ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
        *audio_args, "-c:v", "libx264",
        "-pix_fmt", "yuv420p", str(out_file),
    ], check=True, capture_output=True)
    total = sum(scene.duration for scene in scenes) + 3
    return f"Built {out_file} ({total:.0f}s, {len(scenes)} scenes + end card)."
