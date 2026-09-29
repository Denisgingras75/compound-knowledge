#!/usr/bin/env python3
"""SessionStart hook: print the articles that apply here, so they enter the session's context."""

import json
import os
import sys
from pathlib import Path

from common import articles, home


def main():
    if os.environ.get("CONSTITUTION_CURATOR"):
        return
    try:
        cwd = json.load(sys.stdin).get("cwd") or os.getcwd()
    except (ValueError, OSError):
        cwd = os.getcwd()
    project = Path(cwd).name
    d = home()
    live = [a for a in articles((d / "RULES.md").read_text()) if a["scope"] in ("global", project)]
    pending = (d / "PENDING.md").read_text().count("\n### P")

    if live:
        print("# Denis's standing rules (from ~/.claude/constitution)")
        print("These come from past sessions and Denis approved each one. Follow them.")
        for a in live:
            print(f"- {a['id']}: {a['rule']}")
    if pending:
        print(f"\n({pending} proposed rule(s) are waiting for review. "
              "Mention once, briefly, that Denis can run /constitution:review-rules.)")


if __name__ == "__main__":
    main()
