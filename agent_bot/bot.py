"""A Bot: named teammate with workspace, memory, routines, and a chat loop.

Routines are "teach by showing": a routine is a JSON list of steps
(file writes, commands, fetches) saved under the bot's folder. Running
one replays the steps, pausing for approval wherever a step is
sensitive. Multi-bot chat is just two Bots handing a task to each other
in one session (see cli.py).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import tools

SENSITIVE_HINT = " (needs approval -- rerun with --approve to allow it)"


class Bot:
    def __init__(self, name: str, root: Path):
        self.name = name
        self.root = Path(root) / name
        self.workspace = self.root / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.root / "memory.json"
        if not self.memory_file.exists():
            self.memory_file.write_text(json.dumps({"facts": []}, indent=2))

    def remember(self, fact: str) -> None:
        data = json.loads(self.memory_file.read_text())
        if fact not in data["facts"]:
            data["facts"].append(fact)
        self.memory_file.write_text(json.dumps(data, indent=2))

    def recall(self) -> list[str]:
        return json.loads(self.memory_file.read_text())["facts"]

    def run_routine(self, routine_name: str, approve: bool = False) -> list[str]:
        """Replay a saved routine. Returns one result line per step."""
        routine_file = self.root / "routines" / f"{routine_name}.json"
        steps = json.loads(routine_file.read_text())["steps"]
        results = []
        for step in steps:
            kind = step["tool"]
            try:
                if kind == "write":
                    results.append(tools.write_file(self.workspace, step["path"], step["content"], approve))
                elif kind == "command":
                    results.append(tools.run_command(self.workspace, step["command"], approve))
                elif kind == "fetch":
                    results.append(tools.fetch_url(step["url"])[:200] + "...")
                elif kind == "calc":
                    results.append(tools.calc(step["expression"]))
                else:
                    results.append(f"Unknown step: {kind}")
            except tools.ApprovalRequired as exc:
                results.append(str(exc) + SENSITIVE_HINT)
        return results

    def save_routine(self, routine_name: str, steps: list[dict]) -> str:
        folder = self.root / "routines"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{routine_name}.json").write_text(json.dumps({"steps": steps}, indent=2))
        return f"Routine '{routine_name}' saved with {len(steps)} steps."

    def chat(self, message: str) -> str:
        """Local mode: no model key needed. Understands a few commands and
        otherwise records the message. With GROQ_API_KEY set, a future
        version can plug a free model in here; the key is never stored
        in the repo, only read from the environment.
        """
        text = message.strip()
        if text.startswith("remember "):
            self.remember(text[len("remember "):])
            return f"Noted, {self.name} will remember that."
        if text == "recall":
            facts = self.recall()
            return "I remember:\n- " + "\n- ".join(facts) if facts else "Nothing remembered yet."
        if text == "files":
            files = tools.list_files(self.workspace)
            return "Workspace files:\n- " + "\n- ".join(files) if files else "Workspace is empty."
        return (
            f"{self.name} heard: {text!r}. Try 'remember <fact>', 'recall', "
            "'files', or run a routine with: agent-bot run --bot "
            f"{self.name} --routine <name>"
        )


def hand_off(from_bot: Bot, to_bot: Bot, task: str) -> str:
    """Multi-bot chat: one bot passes a task to another in the same session."""
    return f"{from_bot.name} -> {to_bot.name}: {to_bot.chat(task)}"
