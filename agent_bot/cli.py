"""Command line for agent-bot. Everything runs locally and free.

Usage:
  python -m agent_bot create-bot helper
  python -m agent_bot chat --bot helper
  python -m agent_bot run --bot helper --routine morning [--approve]
  python -m agent_bot team --bots helper,scout --task "recall"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bot import Bot, hand_off

BOTS_ROOT = Path(__file__).resolve().parent.parent / "bots"


def _confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N] ").strip().lower() == "y"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-bot")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-bot")
    create.add_argument("name")

    chat = sub.add_parser("chat")
    chat.add_argument("--bot", required=True)
    chat.add_argument("--message", default=None)

    run = sub.add_parser("run")
    run.add_argument("--bot", required=True)
    run.add_argument("--routine", required=True)
    run.add_argument("--approve", action="store_true")

    team = sub.add_parser("team")
    team.add_argument("--bots", required=True, help="comma-separated, first hands off to second")
    team.add_argument("--task", required=True)

    video = sub.add_parser("video", help="assemble an episode from clips + narration")
    video.add_argument("--script", required=True, help="script JSON (see examples/script-day.json)")
    video.add_argument("--clips-dir", required=True)
    video.add_argument("--narration", default=None, help="narration audio file (optional)")
    video.add_argument("--audio-dir", default=None, help="folder for per-scene audio files named in the script")
    video.add_argument("--out", required=True)
    video.add_argument("--end-card", default="TO BE CONTINUED")

    args = parser.parse_args(argv)

    if args.command == "create-bot":
        Bot(args.name, BOTS_ROOT)
        print(f"Bot '{args.name}' created. Workspace: {BOTS_ROOT / args.name / 'workspace'}")
        return 0

    if args.command == "chat":
        bot = Bot(args.bot, BOTS_ROOT)
        if args.message:
            print(bot.chat(args.message))
            return 0
        print(f"Chatting with {args.bot} (type 'quit' to exit).")
        while True:
            try:
                message = input("you> ")
            except EOFError:
                break
            if message.strip() == "quit":
                break
            print(f"{args.bot}> {bot.chat(message)}")
        return 0

    if args.command == "run":
        bot = Bot(args.bot, BOTS_ROOT)
        approve = args.approve or _confirm("Allow sensitive steps in this routine?")
        for line in bot.run_routine(args.routine, approve=approve):
            print("-", line)
        return 0

    if args.command == "video":
        from .video import assemble, load_script

        scenes = load_script(Path(args.script))
        print(assemble(
            scenes, Path(args.clips_dir),
            Path(args.narration) if args.narration else None,
            Path(args.out), end_card_text=args.end_card,
            audio_dir=Path(args.audio_dir) if args.audio_dir else None,
        ))
        return 0

    if args.command == "team":
        names = [n.strip() for n in args.bots.split(",")]
        bots = [Bot(name, BOTS_ROOT) for name in names]
        result = args.task
        for first, second in zip(bots, bots[1:]):
            result = hand_off(first, second, result)
        print(result)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
