#!/usr/bin/env python3
"""Experiment 005, part C: would the pipeline have written, and kept, the rules that worked?

Every commit that added a violation of a CLAUDE.md rule becomes a sighting, as
if a PostToolUse hook had caught it (graduation-pipeline.md, entry point 4).
Sightings replay through the same ladder and decay as replay.py, matched
exactly by rule, with one pipeline run per SessionEnd from events.jsonl.

Run scan_violations.py and git_events.py first.

    python3 rule_lifecycle.py --repo ~/code/wgh --results results
"""

import argparse
import csv
import json
from pathlib import Path

import git_events
import gitlog
import replay

POLICIES = ("per-run", "window", "none")


def dates(f, prefix):
    return [h["date"] for h in f.history if h["event"].startswith(prefix)]


def lifecycle(rule_id, pipeline):
    fs = [f for f in pipeline.findings if f.key == rule_id]
    if not fs:
        return {"reached_2": None, "locked": None, "dropped": [], "alive_at_end": None}
    reached = sorted(d for f in fs for d in dates(f, "independent confirmation (2)"))
    locked = sorted(d for f in fs for d in dates(f, "locked"))
    return {
        "reached_2": reached[0] if reached else None,
        "locked": locked[0] if locked else None,
        "dropped": sorted(d for f in fs for d in dates(f, "dropped")),
        "alive_at_end": fs[-1].confidence if fs[-1].alive else 0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--results", default=str(Path(__file__).with_name("results")))
    ap.add_argument("--gap-minutes", type=int, default=120)
    args = ap.parse_args()
    res = Path(args.results)

    commits = list(gitlog.commits(args.repo, with_patch=False))
    session_of = {sha[:8]: s for sha, s in git_events.sessions(commits, args.gap_minutes).items()}
    when = {c.sha[:8]: git_events.ts(c.date) for c in commits}
    ends = [e for e in map(json.loads, open(res / "events.jsonl")) if e["type"] == "session_end"]
    rules = json.loads((res / "violations.json").read_text())
    sightings = [r for r in csv.DictReader(open(res / "violation_commits.csv")) if int(r["net_new"]) > 0]

    obs = [{"type": "observation", "ts": when[r["commit"]], "date": r["date"], "session": session_of[r["commit"]],
            "id": f"{r['rule']}@{r['commit']}", "text": r["rule"], "key": r["rule"]} for r in sightings]
    events = sorted(obs + ends, key=lambda e: (e["ts"], e["type"] == "session_end"))
    runs = {pol: replay.replay(events, 3, pol) for pol in POLICIES}

    report = []
    for rule in rules:
        mine = [r for r in sightings if r["rule"] == rule["id"]]
        before = [r for r in mine if r["rule_in_claude_md"] == "no"]
        after = [r for r in mine if r["rule_in_claude_md"] == "yes"]
        added = [e["date"] for e in rule["anchor_history"] if e["change"] == "added"]
        report.append({
            "id": rule["id"],
            "human_rule_date": added[0] if added else None,
            "sessions_before_rule": len({session_of[r["commit"]] for r in before}),
            "commits_before_rule": len(before),
            "commits_after_rule": len(after),
            "last_violation": max((r["date"] for r in mine), default=None),
            "pipeline": {pol: lifecycle(rule["id"], runs[pol]) for pol in POLICIES},
        })

    (res / "rule_lifecycle.json").write_text(json.dumps(report, indent=2) + "\n")
    rows = [
        "| Rule | Human rule | Sessions that broke it before the rule | Commits breaking it after | "
        "Pipeline reached 2 | Pipeline locked | Dropped (as built) | Dropped (30-day window) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in report:
        pr, pw = r["pipeline"]["per-run"], r["pipeline"]["window"]
        rows.append(
            f"| `{r['id']}` | {r['human_rule_date'] or '–'} | {r['sessions_before_rule']} | {r['commits_after_rule']} "
            f"| {pw['reached_2'] or 'never'} | {pw['locked'] or 'never'} "
            f"| {', '.join(pr['dropped']) or '–'} | {', '.join(pw['dropped']) or '–'} |"
        )
    table = "\n".join(rows)
    (res / "rule_lifecycle.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main()
