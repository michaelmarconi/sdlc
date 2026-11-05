#!/bin/sh
# Runs status_check.py and then reference_check.py, or, on a computer without Python 3, refuses
# edits to the lifecycle's documents rather than let them through unchecked, as this plugin's
# ADR 0003 requires.
# Claude Code runs this as a PreToolUse hook on Write, Edit and MultiEdit; exit code 2 blocks.

input=$(cat)

if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "$input" | python3 "$(dirname "$0")/status_check.py" || exit $?
    printf '%s\n' "$input" | python3 "$(dirname "$0")/reference_check.py"
    exit $?
fi

if printf '%s\n' "$input" | grep -Eiq '"file_path" *: *"[^"]*docs/((specs|adrs|plans|spikes)/|brief\.md")'; then
    echo "The sdlc plugin needs Python 3 to check the lifecycle's documents. Install Python 3 and try again." >&2
    exit 2
fi
exit 0
