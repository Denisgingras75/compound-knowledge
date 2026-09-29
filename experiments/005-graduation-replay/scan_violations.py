#!/usr/bin/env python3
"""Experiment 005, part A: did rules in CLAUDE.md stop the mistakes they name?

For every non-merge commit, read the CLAUDE.md the session started from (the
commit's parent) and count rule violations in the lines the commit added.
Comparing commits that could see a rule with commits that could not gives a
prevention measure for each rule.

    python3 scan_violations.py --repo ~/code/wgh --rules rules.json --out results
"""

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import gitlog

COMMENT_PREFIXES = ("//", "/*", "*", "--", "#!")


def is_comment(line):
    return line.lstrip().startswith(COMMENT_PREFIXES)


class Rule:
    def __init__(self, spec):
        self.id = spec["id"]
        self.text = spec["rule"]
        self.soft = spec.get("soft")
        self.anchor = re.compile(spec["anchor"])
        self.include = re.compile(spec["include"])
        self.exclude = re.compile(spec["exclude"]) if spec.get("exclude") else None
        self.pattern = re.compile(spec["pattern"])
        self.compliant = re.compile(spec["compliant"]) if spec.get("compliant") else None

    def applies(self, path):
        return bool(self.include.search(path)) and not (self.exclude and self.exclude.search(path))

    def violations(self, lines):
        return [l for l in lines if not is_comment(l) and self.pattern.search(l)]

    def compliant_uses(self, lines):
        if not self.compliant:
            return 0
        return sum(1 for l in lines if not is_comment(l) and self.compliant.search(l))


def new_bucket():
    return {"commits": 0, "lines": 0, "added": 0, "removed": 0, "net_new": 0,
            "commits_introducing": 0, "compliant": 0}


def add_to(bucket, row):
    net = max(0, row["added"] - row["removed"])
    bucket["commits"] += 1
    bucket["lines"] += row["lines"]
    bucket["added"] += row["added"]
    bucket["removed"] += row["removed"]
    bucket["net_new"] += net
    bucket["commits_introducing"] += 1 if net else 0
    bucket["compliant"] += row["compliant"]


def finish(bucket):
    b = dict(bucket)
    b["share_introducing"] = round(b["commits_introducing"] / b["commits"], 4) if b["commits"] else None
    b["net_new_per_1k_lines"] = round(1000 * b["net_new"] / b["lines"], 3) if b["lines"] else None
    uses = b["compliant"] + b["net_new"]
    b["compliance"] = round(b["compliant"] / uses, 4) if uses else None
    return b


def risk_ratio(after, before):
    """Risk ratio of 'commit introduces a violation', exposed vs unexposed, with a 95% CI.

    Uses a 0.5 continuity correction when a cell is zero. Violations cluster
    in a few commits, so treat the interval as a rough guide, not a test.
    """
    a, n1 = after["commits_introducing"], after["commits"]
    b, n2 = before["commits_introducing"], before["commits"]
    if not n1 or not n2:
        return None
    if a == 0 or b == 0:
        a, b, n1, n2 = a + 0.5, b + 0.5, n1 + 0.5, n2 + 0.5
    rr = (a / n1) / (b / n2)
    se = math.sqrt(max(1 / a - 1 / n1 + 1 / b - 1 / n2, 0))
    return {"ratio": round(rr, 3), "low": round(rr * math.exp(-1.96 * se), 3), "high": round(rr * math.exp(1.96 * se), 3)}


def anchor_history(repo, blobs, rules, project_file):
    """Dates when each rule's anchor entered or left the project file."""
    events = defaultdict(list)
    for c in gitlog.commits(repo, paths=[project_file], with_patch=False):
        before = blobs.get(c.parent, project_file)
        after = blobs.get(c.sha, project_file)
        for r in rules:
            had, has = bool(r.anchor.search(before)), bool(r.anchor.search(after))
            if had != has:
                events[r.id].append({"date": c.date[:10], "sha": c.sha[:8], "change": "added" if has else "removed", "subject": c.subject})
    return events


def aggregate(rows, key):
    """Group per-commit rows by key(row) and exposure: {key: {"unexposed": ..., "exposed": ...}}."""
    groups = defaultdict(lambda: {True: new_bucket(), False: new_bucket(), "any": new_bucket()})
    for row in rows:
        for side in (row["exposed"], "any"):
            add_to(groups[key(row)][side], row)
    return {
        k: {"unexposed": finish(v[False]), "exposed": finish(v[True]), "combined": finish(v["any"]),
            "risk_ratio": risk_ratio(v[True], v[False])}
        for k, v in sorted(groups.items())
    }


def windows(history):
    """Date windows between consecutive rule changes, so each rule can be compared
    with rules that had not been added yet (a staggered-adoption check)."""
    cuts = sorted({e["date"] for events in history.values() for e in events})
    edges = ["0000-00-00"] + cuts + ["9999-99-99"]
    return list(zip(edges, edges[1:]))


def window_of(date, spans):
    for lo, hi in spans:
        if lo <= date < hi:
            return f"{lo if lo[0] != '0' else 'start'} → {hi if hi[0] != '9' else 'end'}"


def scan(repo, rules, project_file, skip):
    blobs = gitlog.Blobs(repo)
    history = anchor_history(repo, blobs, rules, project_file)
    spans = windows(history)
    rows, instances = [], []

    for c in gitlog.commits(repo, paths=["src", "supabase", "api"]):
        if any(c.sha.startswith(s) for s in skip):
            continue
        guide = blobs.get(c.parent, project_file)
        for r in rules:
            files = [f for f in c.files if r.applies(f.path)]
            lines = sum(1 for f in files for l in f.added if l.strip())
            if not lines:
                continue
            exposed = bool(r.anchor.search(guide))
            added = removed = compliant = 0
            for f in files:
                hits = r.violations(f.added)
                added += len(hits)
                removed += len(r.violations(f.removed))
                compliant += r.compliant_uses(f.added)
                for h in hits:
                    instances.append([r.id, c.sha[:8], c.date[:10], c.model, "yes" if exposed else "no", f.path, h.strip()[:160]])
            rows.append({"rule": r.id, "sha": c.sha[:8], "date": c.date[:10], "model": c.model, "exposed": exposed,
                         "lines": lines, "added": added, "removed": removed, "compliant": compliant})
    blobs.close()

    report = []
    for r in rules:
        mine = [row for row in rows if row["rule"] == r.id]
        everyone = aggregate(mine, lambda row: "all").get("all")
        claude = aggregate([row for row in mine if row["model"] != "none"], lambda row: "claude").get("claude")
        report.append({
            "id": r.id,
            "rule": r.text,
            "soft": r.soft,
            "has_compliant": r.compliant is not None,
            "anchor_history": history.get(r.id, []),
            **everyone,
            "claude_only": claude,
            "windows": aggregate(mine, lambda row: window_of(row["date"], spans)),
            "monthly": aggregate(mine, lambda row: row["date"][:7]),
            "by_model": aggregate(mine, lambda row: row["model"]),
        })
    return report, instances, spans, rows


def fmt(x, pct=False):
    if x is None:
        return "–"
    return f"{100 * x:.1f}%" if pct else f"{x:g}"


def markdown(report, population=None):
    rows = [
        "| Rule | In CLAUDE.md | Commits without / with rule | Commits adding a violation | Net-new per 1k lines "
        "| Right way / wrong way (with rule) | Risk ratio (95% CI) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in report:
        added = [e["date"] for e in r["anchor_history"] if e["change"] == "added"]
        removed = [e["date"] for e in r["anchor_history"] if e["change"] == "removed"]
        since = (added[0] if added else "–") + (f" → removed {removed[-1]}" if removed else "")
        p = r[population] if population else r
        u, e, rr = p["unexposed"], p["exposed"], p["risk_ratio"]
        ratio = f"{rr['ratio']:.2f} ({rr['low']:.2f}–{rr['high']:.2f})" if rr else "–"
        rows.append(
            f"| `{r['id']}`{' (soft)' if r['soft'] else ''} | {since} | {u['commits']} / {e['commits']} "
            f"| {fmt(u['share_introducing'], True)} → {fmt(e['share_introducing'], True)} "
            f"| {fmt(u['net_new_per_1k_lines'])} → {fmt(e['net_new_per_1k_lines'])} "
            f"| {e['compliant'] if r['has_compliant'] else '–'} / {e['net_new']} | {ratio} |"
        )
    return "\n".join(rows)


def window_markdown(report, spans):
    """Share of commits adding a violation, per window between rule changes.
    Bold cells are windows in which that rule was in CLAUDE.md."""
    labels = [window_of(lo, spans) for lo, _ in spans]
    short = [l.replace("2026-", "") for l in labels]
    rows = ["| Rule | " + " | ".join(short) + " |", "|---|" + "---|" * len(labels)]
    for r in report:
        changes = [(e["date"], e["change"]) for e in r["anchor_history"]]
        cells = []
        for (lo, _), label in zip(spans, labels):
            live = False
            for date, change in changes:
                if date <= lo:
                    live = change == "added"
            b = r["windows"].get(label, {}).get("combined")
            if not b or not b["commits"]:
                cells.append("–")
                continue
            text = f"{fmt(b['share_introducing'], True)} ({b['commits_introducing']}/{b['commits']})"
            cells.append(f"**{text}**" if live else text)
        rows.append(f"| `{r['id']}` | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", required=True, help="path to the project's git repository")
    ap.add_argument("--rules", default=str(Path(__file__).with_name("rules.json")))
    ap.add_argument("--out", default=str(Path(__file__).with_name("results")))
    args = ap.parse_args()

    spec = json.loads(Path(args.rules).read_text())
    rules = [Rule(s) for s in spec["rules"]]
    skip = spec.get("skip_commits", {})
    report, instances, spans, rows = scan(args.repo, rules, spec.get("project_file", "CLAUDE.md"), skip)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "violations.json").write_text(json.dumps(report, indent=2) + "\n")
    with open(out / "violation_instances.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rule", "commit", "date", "model", "rule_in_claude_md", "path", "added_line"])
        w.writerows(instances)
    touching = {}
    for row in rows:
        touching.setdefault(row["rule"], []).append({"sha": row["sha"], "date": row["date"], "exposed": row["exposed"]})
    (out / "rule_commits.json").write_text(json.dumps(touching) + "\n")
    with open(out / "violation_commits.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rule", "commit", "date", "model", "rule_in_claude_md", "added", "removed", "net_new"])
        for row in rows:
            if row["added"]:
                w.writerow([row["rule"], row["sha"], row["date"], row["model"], "yes" if row["exposed"] else "no",
                            row["added"], row["removed"], max(0, row["added"] - row["removed"])])
    table = "\n\n".join([
        "## All commits\n\n" + markdown(report),
        "## Commits co-authored by Claude only\n\n" + markdown(report, "claude_only"),
        "## Share of commits adding a violation, between rule changes\n\n"
        "Bold: the rule was in CLAUDE.md for that whole window.\n\n" + window_markdown(report, spans),
        "## Skipped commits\n\n" + "\n".join(f"- `{sha}`: {why}" for sha, why in skip.items()),
    ])
    (out / "violations.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main()
