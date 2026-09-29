#!/usr/bin/env bash
# SessionEnd hook: hand the finished transcript to the curator in the background,
# so closing the session never waits on it.
[ -n "${CONSTITUTION_CURATOR:-}" ] && exit 0   # the curator's own session must not curate itself
DIR="${CONSTITUTION_DIR:-$HOME/.claude/constitution}"
mkdir -p "$DIR"
INPUT="$(mktemp "${TMPDIR:-/tmp}/constitution-XXXXXX")"
cat > "$INPUT"
nohup python3 "$(dirname "$0")/curate.py" --hook-input "$INPUT" >> "$DIR/curator.log" 2>&1 &
disown 2>/dev/null || true
exit 0
