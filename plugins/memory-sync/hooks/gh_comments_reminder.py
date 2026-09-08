#!/usr/bin/env python3
"""PostToolUse(Bash) hook: after a `gh` call that reads PR/issue feedback, remind
Claude to check whether anything in it is worth saving to memory once addressed.

Fires narrowly - only on commands that plausibly fetched review comments or
discussion - not on every `gh` call, so a `gh pr create` or `gh pr merge` stays silent.
"""
import json
import re
import sys

TRIGGER = re.compile(
    r"\bgh\s+(api\s+\S*/(comments|reviews|issues)\b|pr\s+(view|diff)\b|issue\s+view\b)"
)


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError):
        return

    command = payload.get("tool_input", {}).get("command", "")
    if not TRIGGER.search(command):
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        "This command read PR/issue feedback. Once you've addressed it, check "
                        "whether any of it is a correction, a confirmed non-obvious decision, or "
                        "a new convention worth saving to memory (per the auto-memory system "
                        "prompt) - not just the comments' content, but how this human reviews and "
                        "what they push back on."
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
