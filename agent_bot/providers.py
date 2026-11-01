"""Clip providers: how a scene's video clip is produced.

Only the interface lives here. A provider that calls a commercial
video API must be configured with the user's own key from the
environment (never committed), and the provider must be one the user
already has lawful access to. The local provider needs no key at all
but only animates a still image -- it is camera motion, not the real
character motion a video model produces, and it is labelled as such.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class ClipProvider:
    def generate_clip(self, scene: dict, reference_images: list[Path], out: Path) -> str:
        raise NotImplementedError


class LocalMotionProvider(ClipProvider):
    """Fallback: slow zoom/pan over a first-frame image (camera motion only)."""

    def generate_clip(self, scene: dict, reference_images: list[Path], out: Path) -> str:
        if not reference_images:
            raise ValueError("LocalMotionProvider needs a first-frame image.")
        image = reference_images[0]
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(image),
            "-vf", "scale=1920:1080,zoompan=z='min(zoom+0.0008,1.15)':d=200:"
                   "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080",
            "-t", "8", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
        ], check=True, capture_output=True)
        return f"Local-motion clip (camera motion only): {out}"


class ApiVideoProvider(ClipProvider):
    """Template for a video-model API the user holds a key for.

    Set VIDEO_API_KEY and VIDEO_API_URL in the environment, and adapt
    _call_api() to that provider's documented request format. This
    template deliberately ships no provider-specific code or key.
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("VIDEO_API_KEY", "")
        self.api_url = os.environ.get("VIDEO_API_URL", "")

    def generate_clip(self, scene: dict, reference_images: list[Path], out: Path) -> str:
        if not self.api_key or not self.api_url:
            raise RuntimeError(
                "Set VIDEO_API_KEY and VIDEO_API_URL in your environment first; "
                "no key is stored in this repo."
            )
        raise NotImplementedError(
            "Adapt _call_api() to your video provider's documented API, then "
            "save its returned clip to `out`."
        )
