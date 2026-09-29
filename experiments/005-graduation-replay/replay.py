#!/usr/bin/env python3
"""Experiment 005, part B: replay the graduation pipeline over real events.

auto-graduate.sh lives on Denis's machine, not in any repository, so this is a
reimplementation of the rules as this repo documents them
(patterns/graduation-pipeline.md, patterns/immune-system.md,
models/trust-decay.md, experiments/003):

  keywords   lowercase words of 4+ characters that are not stopwords
  related    two entries share >= 3 keywords (--min-shared)
  clustering an observation joins the live finding holding the member it
             shares the most keywords with (greedy single linkage)
  1          first sighting
  2          seen in 2+ independent sessions (same session again = repetition)
  3 locked   seen in 3+ independent sessions and alive for 30+ days
  CLAUDE.md  candidate at 6+ independent sessions
  decay      at every SessionEnd (one auto-graduate.sh run), an unlocked finding
             not re-confirmed for 30+ days loses 1 confidence; at 0 it is dropped

--decay picks how often the decrement can fire:
  per-run  every run, as built (experiment 003, break 8)
  daily    at most once per calendar day (the debounce fix proposed in 003)
  window   once per 30 days of silence (the reading closest to trust-decay.md)
  none     never

    python3 replay.py --events results/events.jsonl --classes classes.json --out results
"""

import argparse
import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set

DAY = 86400
WINDOW = 30 * DAY

STOPWORDS = set("""
about above after again against also always another anything around because been before being
below between both came cannot could does doing done down during each else even every from have
having here itself just like made make many more most much must need never only other ours over
same should since some still such than that their them then there these they this those through
under until upon very want were what when where which while will with within without would your
into onto first last next back well once
""".split())


def keywords(text):
    return {w for w in re.findall(r"[a-z0-9_]+", text.lower()) if len(w) >= 4 and w not in STOPWORDS}


def day(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


@dataclass
class Finding:
    id: int
    members: List[dict] = field(default_factory=list)
    member_keywords: List[Set[str]] = field(default_factory=list)
    sessions: Set[str] = field(default_factory=set)
    first_ts: float = 0
    last_confirmed: float = 0
    last_decay: float = 0
    confidence: int = 1
    alive: bool = True
    candidate: bool = False
    key: Optional[str] = None       # exact class key, when events carry one
    dropped_ts: Optional[float] = None
    relearns: Optional[int] = None  # id of a dropped finding this one re-learns
    history: List[dict] = field(default_factory=list)

    def log(self, ts, what):
        self.history.append({"date": day(ts), "event": what})

    def shared(self, kw):
        return max((len(kw & m) for m in self.member_keywords), default=0)


class Pipeline:
    def __init__(self, min_shared=3, decay="per-run"):
        self.min_shared = min_shared
        self.decay = decay
        self.findings: List[Finding] = []
        self.runs = 0

    def best_match(self, kw, alive):
        best, score = None, 0
        for f in self.findings:
            if f.alive == alive:
                s = f.shared(kw)
                if s > score:
                    best, score = f, s
        return (best, score) if score >= self.min_shared else (None, score)

    def match(self, e, kw, alive):
        """Events with a "key" (e.g. a rule id caught by a PostToolUse hook) match exactly;
        free-text events use keyword overlap."""
        if "key" in e:
            return next((f for f in reversed(self.findings) if f.alive == alive and f.key == e["key"]), None)
        return self.best_match(kw, alive)[0]

    def observe(self, e):
        kw = keywords(e["text"])
        f = self.match(e, kw, alive=True)
        if f is None:
            f = Finding(id=len(self.findings), first_ts=e["ts"], last_confirmed=e["ts"], key=e.get("key"))
            dead = self.match(e, kw, alive=False)
            if dead is not None:
                f.relearns = dead.id
                f.log(e["ts"], f"re-learned dropped finding {dead.id}")
            f.log(e["ts"], "observed (1)")
            self.findings.append(f)
        elif e["session"] not in f.sessions:
            f.last_confirmed = e["ts"]
            if f.confidence < 2:
                f.confidence += 1
                f.log(e["ts"], f"independent confirmation ({f.confidence})")
        f.members.append(e)
        f.member_keywords.append(kw)
        f.sessions.add(e["session"])

    def run(self, ts):
        """One auto-graduate.sh run at a SessionEnd: promote, then decay."""
        self.runs += 1
        for f in self.findings:
            if not f.alive:
                continue
            if f.confidence == 2 and len(f.sessions) >= 3 and ts - f.first_ts >= WINDOW:
                f.confidence = 3
                f.log(ts, "locked (3)")
            if f.confidence == 3 and len(f.sessions) >= 6 and not f.candidate:
                f.candidate = True
                f.log(ts, "CLAUDE.md candidate (6+ sessions)")
            if f.confidence >= 3 or self.decay == "none" or ts - f.last_confirmed <= WINDOW:
                continue
            if self.decay == "daily" and day(ts) == day(f.last_decay or 0):
                continue
            if self.decay == "window" and ts - max(f.last_confirmed, f.last_decay) <= WINDOW:
                continue
            f.confidence -= 1
            f.last_decay = ts
            f.log(ts, f"decayed ({f.confidence})")
            if f.confidence == 0:
                f.alive = False
                f.dropped_ts = ts
                f.log(ts, "dropped")


def first(f, prefix):
    return next((h["date"] for h in f.history if h["event"].startswith(prefix)), None)


def summarize(p, events):
    obs = [e for e in events if e["type"] == "observation"]
    fs = p.findings

    def days_to(prefix):
        out = []
        for f in fs:
            d = first(f, prefix)
            if d:
                out.append((datetime.fromisoformat(d) - datetime.fromisoformat(day(f.first_ts))).days)
        return statistics.median(out) if out else None

    return {
        "decay": p.decay,
        "min_shared": p.min_shared,
        "observations": len(obs),
        "pipeline_runs": p.runs,
        "findings": len(fs),
        "singletons": sum(1 for f in fs if len(f.members) == 1),
        "reached_2": sum(1 for f in fs if first(f, "independent confirmation (2)")),
        "reached_3_locked": sum(1 for f in fs if first(f, "locked")),
        "claude_md_candidates": sum(1 for f in fs if f.candidate),
        "dropped": sum(1 for f in fs if not f.alive),
        "dropped_after_reaching_2": sum(1 for f in fs if not f.alive and first(f, "independent confirmation (2)")),
        "relearned": sum(1 for f in fs if f.relearns is not None),
        "alive_at_end": {c: sum(1 for f in fs if f.alive and f.confidence == c) for c in (1, 2, 3)},
        "median_days_to_2": days_to("independent confirmation (2)"),
        "median_days_to_lock": days_to("locked"),
        "median_days_silent_before_drop": median(
            (f.dropped_ts - f.last_confirmed) / DAY for f in fs
            if f.dropped_ts and first(f, "independent confirmation (2)")),
    }


def median(values):
    values = list(values)
    return round(statistics.median(values), 1) if values else None


STAGES = {"reached_2": "independent confirmation (2)", "locked": "locked",
          "candidate": "CLAUDE.md candidate", "dropped": "dropped"}


def label_report(p, labels):
    """Tally hand labels (coherence_labels.json) by how far each finding got."""
    by_stage = {s: {} for s in STAGES}
    findings, unlabeled = {}, 0
    for f in p.findings:
        key = f.members[0]["id"]
        reached = {s: first(f, prefix) for s, prefix in STAGES.items()}
        lab = labels.get(key)
        if not lab:
            unlabeled += 1 if reached["reached_2"] else 0
            continue
        for s, d in reached.items():
            if d:
                by_stage[s][lab["label"]] = by_stage[s].get(lab["label"], 0) + 1
        findings[key] = {**lab, **reached, "sessions": len(f.sessions)}
    return {"by_stage": by_stage, "promoted_but_unlabeled": unlabeled, "findings": findings}


def class_report(p, classes):
    """For each human-labelled mistake class: where its observations landed and when
    the replay would have promoted it, next to the date a human wrote the rule."""
    out = []
    for c in classes:
        rx = re.compile(c["match"], re.I)
        hits = [(f, m) for f in p.findings for m in f.members if rx.search(m["text"])]
        if not hits:
            out.append({**c, "observations": 0})
            continue
        by_finding = {}
        for f, m in hits:
            by_finding.setdefault(f.id, []).append(m)
        main_id = max(by_finding, key=lambda k: len(by_finding[k]))
        f = p.findings[main_id]
        dates = sorted(m["date"] for _, m in hits)
        out.append({
            **c,
            "observations": len(hits),
            "sessions": len({m["session"] for _, m in hits}),
            "first_seen": dates[0],
            "before_rule": sum(1 for d in dates if c.get("rule_date") and d < c["rule_date"]),
            "rule_day": sum(1 for d in dates if c.get("rule_date") and d == c["rule_date"]),
            "after_rule": sum(1 for d in dates if c.get("rule_date") and d > c["rule_date"]),
            "sessions_before_rule": len({m["session"] for _, m in hits
                                         if c.get("rule_date") and m["date"] <= c["rule_date"]}),
            "spread_over_findings": len(by_finding),
            "main_finding": main_id,
            "main_finding_size": len(f.members),
            "main_finding_class_share": round(len(by_finding[main_id]) / len(f.members), 2),
            "replay_reached_2": first(f, "independent confirmation (2)"),
            "replay_locked": first(f, "locked"),
            "replay_candidate": first(f, "CLAUDE.md candidate"),
            "replay_dropped": first(f, "dropped"),
            "relearned": sum(1 for fid in by_finding if p.findings[fid].relearns is not None),
        })
    return out


def with_ticks(events, runs_per_day):
    """Add evenly spaced extra pipeline runs, e.g. to model 20+ sessions a day."""
    if not runs_per_day:
        return events
    t0, t1, step = events[0]["ts"], events[-1]["ts"], DAY / runs_per_day
    ticks = [{"type": "session_end", "ts": t0 + i * step, "session": "tick"}
             for i in range(int((t1 - t0) / step) + 1)]
    return sorted(events + ticks, key=lambda e: (e["ts"], e["type"] == "session_end"))


def replay(events, min_shared, decay):
    p = Pipeline(min_shared=min_shared, decay=decay)
    for e in events:
        if e["type"] == "observation":
            p.observe(e)
        else:
            p.run(e["ts"])
    return p


def load(path):
    """Optional JSON input; 'none', a missing file or an empty file means nothing."""
    p = Path(path)
    if path == "none" or not p.is_file() or not p.read_text().strip():
        return None
    return json.loads(p.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--events", required=True)
    ap.add_argument("--classes", default=str(Path(__file__).with_name("classes.json")),
                    help="mistake classes to track, or 'none'")
    ap.add_argument("--out", default=str(Path(__file__).with_name("results")))
    ap.add_argument("--labels", default=str(Path(__file__).with_name("coherence_labels.json")),
                    help="hand labels of findings, or 'none'")
    ap.add_argument("--min-shared", type=int, default=3)
    ap.add_argument("--runs-per-day", type=int, default=0,
                    help="extra pipeline runs per day on top of one per SessionEnd")
    ap.add_argument("--tag", default="", help="suffix for output file names")
    args = ap.parse_args()

    events = with_ticks([json.loads(l) for l in open(args.events)], args.runs_per_day)
    classes = load(args.classes) or []
    labels = (load(args.labels) or {}).get("labels", {})
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    summaries, per_class, per_label = [], {}, {}
    for decay in ("per-run", "daily", "window", "none"):
        p = replay(events, args.min_shared, decay)
        summaries.append(summarize(p, events))
        per_class[decay] = class_report(p, classes)
        per_label[decay] = label_report(p, labels)
        if decay == "window" and not args.tag:
            dump = [
                {"id": f.id, "size": len(f.members), "sessions": len(f.sessions), "confidence": f.confidence,
                 "alive": f.alive, "relearns": f.relearns, "history": f.history,
                 "members": [{"date": m["date"], "session": m["session"], "id": m["id"], "text": m["text"][:200]}
                             for m in f.members]}
                for f in sorted(p.findings, key=lambda f: -len(f.members))
            ]
            (out / "replay_findings.json").write_text(json.dumps(dump, indent=1, ensure_ascii=False) + "\n")

    (out / f"replay_summary{args.tag}.json").write_text(json.dumps(
        {"runs_per_day": args.runs_per_day, "policies": summaries, "classes": per_class, "labels": per_label},
        indent=2, ensure_ascii=False) + "\n")
    keys = [k for k in summaries[0] if k not in ("decay", "min_shared", "alive_at_end")]
    lines = ["| Metric | " + " | ".join(s["decay"] for s in summaries) + " |",
             "|---|" + "---|" * len(summaries)]
    lines += [f"| {k} | " + " | ".join(str(s[k]) for s in summaries) + " |" for k in keys]
    lines.append("| alive at end (1 / 2 / 3) | " + " | ".join(
        " / ".join(str(s["alive_at_end"][c]) for c in (1, 2, 3)) for s in summaries) + " |")
    if labels:
        lines += ["", "Hand labels of promoted findings (" + ", ".join(summaries[i]["decay"] for i in range(len(summaries))) + ")", ""]
        lines.append("| Stage | " + " | ".join(s["decay"] for s in summaries) + " |")
        lines.append("|---|" + "---|" * len(summaries))
        for stage in STAGES:
            cells = []
            for s in summaries:
                t = per_label[s["decay"]]["by_stage"][stage]
                cells.append(", ".join(f"{t[k]} {k}" for k in ("lesson", "situational", "hotspot", "noise") if t.get(k)) or "–")
            lines.append(f"| {stage} | " + " | ".join(cells) + " |")
    table = "\n".join(lines)
    (out / f"replay_summary{args.tag}.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main()
