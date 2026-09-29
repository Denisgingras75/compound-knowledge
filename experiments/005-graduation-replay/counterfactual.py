#!/usr/bin/env python3
"""Experiment 005, part D: what would decay cost in repeat mistakes? (a model)

History only shows one world: the rules humans wrote into CLAUDE.md. To ask
what a pipeline-managed rule would have done, this replays the real commit
stream for each rule (the real commits that touched the rule's files, in the
real sessions, with a pipeline run at every real SessionEnd) and draws each
commit's violation at random:

  rule not injected  -> probability measured before the rule existed
  rule injected      -> probability measured once the rule was in CLAUDE.md
                        (confidence 2+ counts as injected)

Every drawn violation is a sighting a PostToolUse hook would catch. The
confidence ladder and decay are the same code as replay.py. Scenarios:
no rule, the human rule (on from its real date), and the pipeline under each
decay policy. Numbers are averages over --runs seeded simulations.

    python3 counterfactual.py --repo ~/code/wgh --results results
"""

import argparse
import json
import random
import statistics
from pathlib import Path

import git_events
import gitlog
import replay

POLICIES = ("per-run", "window", "none")


def merge(stream, ends):
    return sorted([("commit", c) for c in stream] + [("end", e) for e in ends],
                  key=lambda x: (x[1]["ts"], x[0] == "end"))


def simulate(events, n_commits, p_off, p_on, decay, seed):
    """One run: returns (violating commits, share of commits with the rule injected, drops)."""
    rng = random.Random(seed)
    pipe = replay.Pipeline(min_shared=3, decay=decay)
    violations = injected_commits = 0
    for kind, e in events:
        if kind == "end":
            pipe.run(e["ts"])
            continue
        live = next((f for f in pipe.findings if f.alive), None)
        on = live is not None and live.confidence >= 2
        injected_commits += on
        if rng.random() < (p_on if on else p_off):
            violations += 1
            pipe.observe({"ts": e["ts"], "date": e["date"], "session": e["session"],
                          "id": e["sha"], "text": "rule", "key": "rule"})
    drops = sum(1 for f in pipe.findings if not f.alive and any(
        h["event"].startswith("independent confirmation (2)") for h in f.history))
    return violations, injected_commits / n_commits, drops


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--results", default=str(Path(__file__).with_name("results")))
    ap.add_argument("--runs", type=int, default=500)
    ap.add_argument("--gap-minutes", type=int, default=120)
    args = ap.parse_args()
    res = Path(args.results)

    commits = list(gitlog.commits(args.repo, with_patch=False))
    session_of = {sha[:8]: s for sha, s in git_events.sessions(commits, args.gap_minutes).items()}
    when = {c.sha[:8]: git_events.ts(c.date) for c in commits}
    ends = [e for e in map(json.loads, open(res / "events.jsonl")) if e["type"] == "session_end"]
    rules = {r["id"]: r for r in json.loads((res / "violations.json").read_text())}
    touching = json.loads((res / "rule_commits.json").read_text())

    report = []
    for rule_id, rows in touching.items():
        r = rules[rule_id]
        before, after = r["unexposed"], r["exposed"]
        if not before["commits_introducing"]:
            continue  # never violated before the rule: nothing to learn from
        p_off = before["commits_introducing"] / before["commits"]
        # a rule with no violations after it landed still gets a small chance, not zero
        p_on = max(after["commits_introducing"], 0.5) / after["commits"]
        stream = [{"sha": x["sha"], "date": x["date"], "ts": when[x["sha"]], "session": session_of[x["sha"]],
                   "exposed": x["exposed"]} for x in rows]
        human = sum(p_on if x["exposed"] else p_off for x in stream)
        entry = {
            "id": rule_id, "commits": len(stream), "p_without_rule": round(p_off, 4), "p_with_rule": round(p_on, 4),
            "expected_violations": {"no rule": round(p_off * len(stream), 1), "human rule": round(human, 1)},
            "rule_injected_share": {"human rule": round(sum(x["exposed"] for x in stream) / len(stream), 3)},
            "pipeline_drops": {},
        }
        events = merge(stream, ends)
        for pol in POLICIES:
            sims = [simulate(events, len(stream), p_off, p_on, pol, seed) for seed in range(args.runs)]
            entry["expected_violations"][f"pipeline ({pol})"] = round(statistics.mean(s[0] for s in sims), 1)
            entry["rule_injected_share"][f"pipeline ({pol})"] = round(statistics.mean(s[1] for s in sims), 3)
            entry["pipeline_drops"][pol] = round(statistics.mean(s[2] for s in sims), 2)
        report.append(entry)

    (res / "counterfactual.json").write_text(json.dumps(report, indent=2) + "\n")
    cols = ["no rule", "human rule"] + [f"pipeline ({p})" for p in POLICIES]
    rows = ["| Rule | Commits | " + " | ".join(cols) + " | Times the pipeline deleted a promoted rule (as built / window) |",
            "|---|---|" + "---|" * len(cols) + "---|"]
    for e in report:
        cells = [f"{e['expected_violations'][c]:g}" for c in cols]
        rows.append(f"| `{e['id']}` | {e['commits']} | " + " | ".join(cells)
                    + f" | {e['pipeline_drops']['per-run']:g} / {e['pipeline_drops']['window']:g} |")
    table = ("Expected commits that add a violation, over the whole history "
             f"(mean of {args.runs} simulations)\n\n" + "\n".join(rows))
    (res / "counterfactual.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main()
