import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_bot.video import Scene, build_subtitles, chapter_overlays  # noqa: E402


def test_subtitles_and_chapters():
    scenes = [
        Scene(clip="s1.mp4", narration="Hello.", chapter="DAY 1", duration=8.0),
        Scene(clip="s2.mp4", narration="World.", chapter="", duration=8.0),
    ]
    srt = build_subtitles(scenes)
    assert "00:00:00,000 --> 00:00:08,000" in srt
    assert "00:00:08,000 --> 00:00:16,000" in srt
    overlays = chapter_overlays(scenes)
    assert len(overlays) == 1 and "DAY 1" in overlays[0]
    assert "between(t,0.0,3.0)" in overlays[0]
