#!/usr/bin/env python3
"""PreCompact hook: before this session's raw transcript is summarized away, remind
Claude to write down anything from it that belongs in memory but hasn't been saved
yet - this is the actual loss moment memory exists to guard against, and it fires
only when context is about to be compacted, not on every turn.
"""
import json

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreCompact",
                "additionalContext": (
                    "Context is about to be compacted. Before it is: check this conversation for "
                    "user corrections, confirmed non-obvious decisions, or new conventions that "
                    "haven't been saved to memory yet (per the auto-memory system prompt), and "
                    "write them now if so. If nothing qualifies, proceed - this is not a "
                    "requirement to find something."
                ),
            }
        }
    )
)
