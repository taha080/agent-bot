"""Small toolset for a bot. Every tool is sandboxed to the bot's workspace
except read-only web fetch. Sensitive actions raise ApprovalRequired
unless the caller passes approve=True (the CLI asks the human first).
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path


class ApprovalRequired(Exception):
    """Raised when a sensitive action needs a human's explicit approval."""


def _inside(workspace: Path, target: str) -> Path:
    path = (workspace / target).resolve()
    if not str(path).startswith(str(workspace.resolve())):
        raise ValueError(f"Refusing path outside workspace: {target}")
    return path


def read_file(workspace: Path, target: str) -> str:
    return _inside(workspace, target).read_text(encoding="utf-8")


def write_file(workspace: Path, target: str, content: str, approve: bool = False) -> str:
    path = _inside(workspace, target)
    if path.exists() and not approve:
        raise ApprovalRequired(f"Overwriting {target} needs approval.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {target} ({len(content)} chars)."


def delete_file(workspace: Path, target: str, approve: bool = False) -> str:
    if not approve:
        raise ApprovalRequired(f"Deleting {target} needs approval.")
    _inside(workspace, target).unlink(missing_ok=True)
    return f"Deleted {target}."


def list_files(workspace: Path) -> list[str]:
    return sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*") if p.is_file())


def run_command(workspace: Path, command: str, approve: bool = False) -> str:
    """Run a shell command inside the workspace.

    Commands that install software, touch the network, or write outside
    the workspace are sensitive and need approval.
    """
    sensitive = ("pip install", "apt", "curl", "wget", "rm -rf", "sudo", "> /", ">> /")
    if any(word in command for word in sensitive) and not approve:
        raise ApprovalRequired(f"Command needs approval: {command}")
    result = subprocess.run(
        command, shell=True, cwd=workspace, capture_output=True, text=True, timeout=60
    )
    return (result.stdout + result.stderr).strip() or f"(exit {result.returncode})"


def fetch_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError("Only http(s) URLs are allowed.")
    request = urllib.request.Request(url, headers={"User-Agent": "agent-bot/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        text = response.read().decode("utf-8", errors="replace")
    return text[:4000]


def calc(expression: str) -> str:
    allowed = set("0123456789+-*/(). %")
    if not set(expression) <= allowed:
        raise ValueError("Only numbers and + - * / ( ) % are allowed.")
    return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307 - sandboxed charset
