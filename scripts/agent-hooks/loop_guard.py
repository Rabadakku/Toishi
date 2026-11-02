#!/usr/bin/env python3
"""PreToolUse hook: stop sub-agents that loop or run away.

Claude Code runs this before every tool call (see .claude/settings.json). It only acts inside
sub-agents (the hook input carries an agent_id there); the main session is never touched.

- The same tool call (same tool, same input) three times in a row is refused with a message
  telling the agent to stop retrying and report.
- After MAX_CALLS tool calls an agent may only run git (to commit) and must send its report.

Exit code 2 refuses the call and shows stderr to the agent. State lives in a temp folder, one
small JSON file per agent.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

REPEAT_LIMIT = 3
MAX_CALLS = int(os.environ.get("TOISHI_AGENT_MAX_CALLS", "400"))
STATE_DIR = Path(
    os.environ.get("TOISHI_AGENT_GUARD_DIR", Path(tempfile.gettempdir()) / "mastery-agent-guard")
)


def decide(event: dict[str, Any], state: dict[str, Any]) -> tuple[int, str]:
    """Update state for one tool call; return (exit code, message)."""
    tool = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    key = hashlib.sha256(
        json.dumps([tool, tool_input], sort_keys=True, default=str).encode()
    ).hexdigest()
    calls = int(state.get("calls", 0)) + 1
    repeat = int(state.get("repeat", 0)) + 1 if key == state.get("last") else 1
    state.update(calls=calls, repeat=repeat, last=key)

    if repeat >= REPEAT_LIMIT:
        return 2, (
            f"Loop guard: this exact {tool} call has been made {repeat} times in a row. "
            "Don't retry it. Write down what you know and finish with your report "
            "(BLOCKED or PARTIAL) explaining the diagnosis."
        )
    if calls > MAX_CALLS:
        command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
        if tool == "Bash" and command.lstrip().startswith("git "):
            return 0, ""
        return 2, (
            f"Loop guard: {calls} tool calls in this agent, over the limit of {MAX_CALLS}. "
            "Wrap up now: commit what works (git is still allowed) and send your final "
            "report listing what's left."
        )
    return 0, ""


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:  # never block on a malformed event (and stay valid on old Pythons)
        return 0
    agent = event.get("agent_id")
    if not agent:
        return 0  # the main session is never limited
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"{hashlib.sha256(str(agent).encode()).hexdigest()[:24]}.json"
    try:
        state = json.loads(path.read_text())
    except Exception:
        state = {}
    code, message = decide(event, state)
    path.write_text(json.dumps(state))
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
