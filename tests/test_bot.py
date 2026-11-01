import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_bot.bot import Bot, hand_off  # noqa: E402
from agent_bot import tools  # noqa: E402


def test_workspace_sandbox(tmp_path):
    bot = Bot("tester", tmp_path)
    tools.write_file(bot.workspace, "hello.txt", "hi", approve=True)
    assert tools.read_file(bot.workspace, "hello.txt") == "hi"
    try:
        tools.read_file(bot.workspace, "../escape.txt")
    except ValueError:
        pass
    else:
        raise AssertionError("Path escape was not blocked")


def test_approval_gate(tmp_path):
    bot = Bot("tester", tmp_path)
    tools.write_file(bot.workspace, "a.txt", "x", approve=True)
    try:
        tools.write_file(bot.workspace, "a.txt", "y", approve=False)
    except tools.ApprovalRequired:
        pass
    else:
        raise AssertionError("Overwrite without approval was not blocked")


def test_routine_and_handoff(tmp_path):
    bot = Bot("tester", tmp_path)
    bot.save_routine("demo", [{"tool": "calc", "expression": "2 + 3 * 4"}])
    assert bot.run_routine("demo") == ["14"]
    other = Bot("scout", tmp_path)
    assert "tester -> scout" in hand_off(bot, other, "recall")
