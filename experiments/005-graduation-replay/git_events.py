#!/usr/bin/env python3
"""Experiment 005, part B input: turn a repo's git history into pipeline events.

Writes one JSON object per line, in time order:

  {"type": "observation", "ts": ..., "session": ..., "id": ..., "text": ...}
  {"type": "session_end", "ts": ..., "session": ...}

An observation is one finding from a fix commit: each bullet in the commit
body, or the subject (plus first paragraph) when there are no bullets. This
mirrors a raw-log entry, one insight per line. A session is a run of commits
by the same author with no gap longer than --gap-minutes; its last commit is
treated as the SessionEnd that triggers auto-graduate.sh.

    python3 git_events.py --repo ~/code/wgh --out results/events.jsonl
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import gitlog

FIX = re.compile(r"^(fix|hotfix|revert)\b|\bfix(e[sd])?\b|\bbugs?\b|\bcrash|\bbroken\b|\bregression\b", re.I)
BULLET = re.compile(r"^\s*[-*•]\s+(.*)")
TRAILER = re.compile(r"^(Co-Authored-By|Signed-off-by|Claude-Session|🤖|Generated with):?", re.I)
CONTAINER = re.compile(r"\b\d+\s+(?:[\w/-]+\s+){0,3}?(fixes|issues|bugs|cleanups|findings|blockers)\b", re.I)


def ts(date):
    return datetime.fromisoformat(date).timestamp()


def findings(commit):
    """Split a fix commit into one text per finding: the subject with the first
    prose paragraph, plus one per bullet. A subject that only counts its
    bullets ("fix: 32 bug fixes from audit") is left out when bullets exist."""
    lines = [l for l in commit.body.split("\n") if not TRAILER.match(l.strip())]
    bullets, cur = [], None
    for line in lines:
        m = BULLET.match(line)
        if m:
            cur = [m.group(1).strip()]
            bullets.append(cur)
        elif cur is not None and line.startswith(("  ", "\t")) and line.strip():
            cur.append(line.strip())  # wrapped continuation of the bullet above
        else:
            cur = None
    paragraphs = [p.strip() for p in "\n".join(lines).split("\n\n") if p.strip()]
    prose = next((p for p in paragraphs
                  if not BULLET.match(p.split("\n")[0]) and not p.split("\n")[0].rstrip().endswith(":")), "")
    out = []
    if not (bullets and CONTAINER.search(commit.subject)):
        out.append(f"{commit.subject} {prose}".replace("\n", " ").strip())
    return out + [" ".join(b) for b in bullets]


def sessions(all_commits, gap_minutes):
    """Map each commit sha to a session id: same author, no gap longer than gap_minutes.

    Parallel sessions by one author get merged into one, which makes
    'independent confirmation' harder to reach, never easier.
    """
    open_session, session_of, count = {}, {}, 0
    for c in sorted(all_commits, key=lambda c: ts(c.date)):
        cur = open_session.get(c.author)
        if not cur or ts(c.date) - cur["last"] > gap_minutes * 60:
            count += 1
            cur = open_session[c.author] = {"id": f"s{count:04d}"}
        cur["last"] = ts(c.date)
        session_of[c.sha] = cur["id"]
    return session_of


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("results") / "events.jsonl"))
    ap.add_argument("--gap-minutes", type=int, default=120)
    args = ap.parse_args()

    all_commits = list(gitlog.commits(args.repo, with_patch=False))
    session_of = sessions(all_commits, args.gap_minutes)

    events, last_commit = [], {}
    for c in all_commits:
        s = session_of[c.sha]
        last_commit[s] = max(last_commit.get(s, 0), ts(c.date))
        if FIX.search(c.subject):
            for i, text in enumerate(findings(c)):
                events.append({"type": "observation", "ts": ts(c.date), "date": c.date[:10],
                               "session": s, "id": f"{c.sha[:8]}#{i}", "text": text})
    for s, t in last_commit.items():
        events.append({"type": "session_end", "ts": t + 1, "session": s})
    events.sort(key=lambda e: (e["ts"], e["type"] == "session_end"))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        for e in events:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    obs = [e for e in events if e["type"] == "observation"]
    print(f"{len(all_commits)} commits, {len(last_commit)} sessions, "
          f"{len({e['id'].split('#')[0] for e in obs})} fix commits, {len(obs)} observations -> {out}")


if __name__ == "__main__":
    main()
