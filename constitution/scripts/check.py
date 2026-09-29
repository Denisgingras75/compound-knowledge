#!/usr/bin/env python3
"""Monthly check: is each article with a `check:` regex actually preventing its mistake?

For every article that has a check regex, count commits that added a matching
line in the same length of time before and after the article was added, across
the repos you pass. The method is experiment 005's, simplified.

    python3 check.py ~/code/wgh ~/code/nomans ~/code/JITTEr
"""

import argparse
import re
import subprocess
from datetime import date, timedelta
from pathlib import Path

from common import articles, home, meta_field


def commits_with(repo, rx, since, until):
    out = subprocess.run(
        ["git", "-C", repo, "log", "--no-merges", "-p", "--unified=0", "--format=\x1e%H",
         f"--since={since}", f"--until={until}"],
        capture_output=True, text=True, errors="replace",
    ).stdout
    hits = total = 0
    for rec in out.split("\x1e")[1:]:
        total += 1
        if any(l.startswith("+") and not l.startswith("+++") and rx.search(l[1:]) for l in rec.split("\n")):
            hits += 1
    return hits, total


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repos", nargs="+")
    args = ap.parse_args()

    today = date.today()
    print("| Article | Scope | Commits breaking it: before → after | Verdict |")
    print("|---|---|---|---|")
    for a in articles((home() / "RULES.md").read_text()):
        pattern, added = meta_field(a, "check"), meta_field(a, "added")
        if not pattern or not added:
            continue
        start = date.fromisoformat(added)
        window = max((today - start).days, 1)
        before_from = start - timedelta(days=window)
        rx = re.compile(pattern)
        repos = [r for r in args.repos if a["scope"] == "global" or Path(r).name == a["scope"]]
        b = [commits_with(r, rx, before_from, start) for r in repos]
        f = [commits_with(r, rx, start, today + timedelta(days=1)) for r in repos]
        bh, bt = sum(x[0] for x in b), sum(x[1] for x in b)
        fh, ft = sum(x[0] for x in f), sum(x[1] for x in f)
        if ft == 0:
            verdict = "no commits since it was added"
        elif fh == 0:
            verdict = "working" if bh else "no violations either side (can't tell)"
        elif bt and fh / ft >= bh / bt:
            verdict = "NOT WORKING: reword or repeal"
        else:
            verdict = "helping, still broken sometimes"
        print(f"| {a['id']} {a['rule'][:60]} | {a['scope']} | {bh}/{bt} → {fh}/{ft} | {verdict} |")


if __name__ == "__main__":
    main()
