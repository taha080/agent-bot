# agent-bot

Live demo: https://taha080.github.io/agent-bot/

Your own named AI teammates, running locally and free — inspired by the
public idea of Grok Bot (a named agent with its own computer that keeps
working on multi-step jobs), re-implemented from scratch. No code,
design, or assets from any commercial product are used here.

## What it does

- **Named bots, each with its own computer (workspace):** every bot gets
  its own folder, files, and memory. Create one with
  `python -m agent_bot create-bot helper`.
- **Multi-step jobs:** a bot runs tools — read/write files, run shell
  commands, fetch a URL, calculate — inside its own workspace.
- **Approvals for sensitive actions:** overwriting files, deleting,
  installing software, or network-touching commands pause and ask a
  human first. Nothing sensitive runs silently.
- **Routines (teach by showing):** save a list of steps as a routine
  (`bots/<name>/routines/morning.json`) and replay it any time with
  `python -m agent_bot run --bot helper --routine morning`.
- **Multi-bot chat:** two bots in one session hand a task to each other:
  `python -m agent_bot team --bots helper,scout --task "recall"`.

## Live demo

Open https://taha080.github.io/agent-bot/ to try a bot in the
browser. The demo chat also has a file picker: attach files, preview
text, JSON, and Markdown files (first 300 characters), and type
`files` to list what you attached.

## Quick start

```bash
python -m agent_bot create-bot helper
python -m agent_bot chat --bot helper --message "remember launch day is Monday"
python -m agent_bot chat --bot helper --message "recall"
python -m agent_bot chat --bot helper --message "files"
```

## Routines

A routine file is JSON:

```json
{"steps": [
  {"tool": "write", "path": "notes.txt", "content": "morning check done"},
  {"tool": "calc", "expression": "2 + 3 * 4"}
]}
```

Save it as `bots/helper/routines/morning.json`, then run it. Steps that
need approval print a hint instead of running until you pass `--approve`
or confirm at the prompt.

## Video episodes (same type as a Grok Bot episode)

The Season 2 Day 1 reference clip was made by Grok Bot itself, not by
Flow — so this repo also ships the video side: an episode builder that
takes clips from any video model you already use, then stitches them
into one episode with narration, burned-in subtitles, chapter
overlays, and a "TO BE CONTINUED" end card — the same structure as
that reference episode.

```bash
python -m agent_bot video --script examples/script-day.json \
  --clips-dir ./my-clips --narration ./narration.mp3 --out episode.mp4
```

The script JSON lists one scene per clip: `clip`, `narration`,
`chapter`, `duration`, and optionally `audio` — a per-scene narration
file. Pass its folder with ``--audio-dir``:

```bash
python -m agent_bot video --script examples/script-day.json \
  --clips-dir ./my-clips --audio-dir ./my-audio --out episode.mp4
```

When a scene has `audio`, its clip is looped to exactly that audio's
length, so narration is never cut off and no scene freezes past its
clip. If you give per-scene audio and no single ``--narration`` file,
the per-scene tracks are concatenated into the episode's soundtrack.

Clips are yours — generate them with your

own Grok Bot, Flow, Veo, or another tool you have access to, then drop
them in `--clips-dir`. `agent_bot/providers.py` also defines a clip
provider interface: plug in a video API with your own key from the
environment (`VIDEO_API_KEY`, never committed), or use the local
fallback, which honestly only does slow camera zoom/pan over a still
— not real character motion.

## Optional model

Local mode needs no key and no account. If you later want a real model,
set `GROQ_API_KEY` in your own environment (a free Groq key you paste
yourself) — the key is never stored in this repo.

## Tests

```bash
python -m pytest tests/ -q
```

## License

MIT. Built as an original, free, local alternative — not affiliated
with xAI, Grok, or any other product.
