#!/usr/bin/env python3
"""Turn the real pipeline's files into events for replay.py.

Reads the two raw formats documented in this repo and writes events.jsonl:

  observations.md (patterns/immune-system.md)
    - [2026-02-28] [Agent-A] [safari] — toSorted() crashes on Safari 15 [confidence: 1]
    - [2026-02-28] [Agent-A+Agent-B] [safari] — ES2023 methods crash Safari 15

  CODEX.md raw log (experiments/003)
    ### 2026-02-28: [frontend] Safari needs explicit width on flex children with gap
    Source: tagged by G-p42

An agent name (or G-p PID) is one independent source: the same name twice is
repetition, not confirmation. Pass --per-day if names are reused by separate
processes, so each agent-day counts as its own session. Each agent-day ends
with a SessionEnd, since that is when auto-graduate.sh ran. Written against
the documented formats only: if your files differ, adjust the two patterns.

    python3 pipeline_events.py ~/.claude/memory/knowledge_base/observations.md ~/CODEX.md \\
        --out results/pipeline_events.jsonl
    python3 replay.py --events results/pipeline_events.jsonl --out results/pipeline \\
        --classes none --labels none
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OBSERVATION = re.compile(r"^\s*-\s*\[(\d{4}-\d{2}-\d{2})\]\s*\[([^\]]+)\]\s*(?:\[([^\]]+)\]\s*)?[—–-]+\s*(.+)$")
RAW_LOG = re.compile(r"^###\s*(\d{4}-\d{2}-\d{2}):\s*(?:\[([^\]]+)\]\s*)?(.+)$")
AGENT = re.compile(r"tagged by\s+([\w-]+)|\b(G-p\d+)\b")
CONFIDENCE = re.compile(r"\s*\[confidence:\s*\d\]\s*$")


def noon(date, offset=0):
    return datetime.fromisoformat(date).replace(hour=12, tzinfo=timezone.utc).timestamp() + offset


def parse(path):
    lines = Path(path).read_text().split("\n")
    out, i = [], 0
    while i < len(lines):
        m = OBSERVATION.match(lines[i])
        h = RAW_LOG.match(lines[i])
        if m:
            date, agents, domain, text = m.groups()
            for agent in agents.split("+"):
                out.append((date, agent.strip(), domain, CONFIDENCE.sub("", text)))
        elif h:
            date, domain, text = h.groups()
            body = []
            while i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                i += 1
                body.append(lines[i])
            who = AGENT.search("\n".join(body) + " " + text)
            out.append((date, (who.group(1) or who.group(2)) if who else "unknown", domain, text))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default=str(Path(__file__).with_name("results") / "pipeline_events.jsonl"))
    ap.add_argument("--per-day", action="store_true", help="count each agent-day as a separate session")
    args = ap.parse_args()

    rows = [r for f in args.files for r in parse(f)]
    events, ends = [], {}
    for n, (date, agent, domain, text) in enumerate(sorted(rows, key=lambda r: r[0])):
        session = f"{agent}@{date}" if args.per_day else agent
        events.append({"type": "observation", "ts": noon(date, n), "date": date, "session": session,
                       "id": f"p{n:05d}", "text": f"[{domain}] {text}" if domain else text})
        ends[f"{agent}@{date}"] = noon(date, 11 * 3600)
    events += [{"type": "session_end", "ts": t, "session": s} for s, t in ends.items()]
    events.sort(key=lambda e: (e["ts"], e["type"] == "session_end"))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events))
    print(f"{len(rows)} observations from {len(args.files)} file(s), {len(ends)} agent-days -> {out}")


if __name__ == "__main__":
    main()
