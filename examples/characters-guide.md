# Character reference images

Video clips stay on-character when the clip generator is given reference
images. This repo never bundles anyone else's art: put **your own**
character sheets in a folder (for example `characters/`) and pass them
to a clip provider:

```python
from pathlib import Path
from agent_bot.providers import LocalMotionProvider

provider = LocalMotionProvider()
provider.generate_clip(
    {"prompt": "hero on a rooftop at sunset"},
    [Path("characters/hero-new-design.jpg")],
    Path("clips/scene1.mp4"),
)
```

Rules that matter for a series:

- One hero design across every scene and thumbnail. If the design
  changes (for example a new cap and hoodie), the new sheet replaces
  the old one everywhere — never mix old and new designs in one video.
- Keep a fixed colour list per character (cap, hoodie, jeans, shoes)
  and reuse it word-for-word in every clip prompt, so the model cannot
  drift the design between scenes.
- A video-model API provider (see `providers.py`) takes the same
  reference list; only the generation step differs, the assembly step
  (`agent_bot video`) is identical.

Per-scene audio: add an `audio` field to a scene in your script JSON
and pass `--audio-dir`. The builder loops that scene's clip to exactly
the narration length, so voices are never cut off and scenes never
freeze past their clip.
