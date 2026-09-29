#!/usr/bin/env python3
"""The curator: read one finished session and propose at most a few rules.

Runs in the background from the SessionEnd hook. It condenses the transcript
(what Denis said, what Claude said, tool errors), asks a headless Claude with
no tools for proposals, and appends them to PENDING.md. Nothing reaches
RULES.md until Denis approves it with /constitution:review-rules.

    python3 curate.py --transcript ~/.claude/projects/<project>/<session>.jsonl --cwd ~/code/wgh
    python3 curate.py --transcript ... --dry-run     # print the proposals, write nothing
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from common import home

MAX_CHARS = 80_000     # transcript digest sent to the curator (the tail is kept)
MIN_PROMPTS = 2        # shorter sessions are skipped
TAGS = re.compile(r"<(system-reminder|command-[\w-]+|local-command-[\w-]+)>.*?</\1>", re.S)

PROMPT = """You are the curator of Denis's constitution: a short file of rules loaded into every Claude Code session he runs, across all his projects.

Read the session below and propose AT MOST 3 new rules. Follow the amendment clause:

{clause}

Only propose a rule when the session shows evidence: Denis corrected Claude, Claude made a mistake that had to be fixed or reverted, or Denis stated a lasting preference. Do not propose rules for one-off task details, general programming knowledge Claude already follows, or anything already covered by the existing rules or pending proposals below. Proposing nothing is the normal outcome.

Existing rules:
{rules}

Pending proposals:
{pending}

Project folder: {project}

Reply with one JSON object per line and nothing else, or the single word NONE. Each object:
{{"rule": "When X → do Y — because Z", "scope": "global" or "project", "evidence": "short quote or description from the session", "check": "optional regex matching a violation in added code, or empty"}}

Session:
{digest}
"""


def text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if b.get("type") == "text":
            parts.append(b.get("text", ""))
        elif b.get("type") == "tool_result" and b.get("is_error"):
            c = b.get("content")
            parts.append("[tool error] " + (text_of(c) if isinstance(c, list) else str(c))[:400])
    return "\n".join(parts)


def digest(transcript):
    lines, prompts = [], 0
    for raw in open(transcript, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if e.get("type") not in ("user", "assistant") or e.get("isSidechain") or e.get("isMeta"):
            continue
        content = e.get("message", {}).get("content")
        text = TAGS.sub("", text_of(content)).strip()
        if not text:
            continue
        if e["type"] == "user":
            if isinstance(content, str) or any(b.get("type") == "text" for b in content or []):
                prompts += 1
                lines.append(f"DENIS: {text[:3000]}")
            else:
                lines.append(text[:400])
        else:
            lines.append(f"CLAUDE: {text[:2000]}")
    return "\n\n".join(lines)[-MAX_CHARS:], prompts


def clause(rules_text):
    m = re.search(r"## Amendment clause\n(.*?)\n## Articles", rules_text, re.S)
    return m.group(1).strip() if m else ""


def ask(prompt, model):
    env = {**os.environ, "CONSTITUTION_CURATOR": "1"}
    out = subprocess.run(
        ["claude", "-p", "--model", model, "--tools", "", "--no-session-persistence"],
        input=prompt, capture_output=True, text=True, env=env, timeout=600,
    )
    if out.returncode:
        raise RuntimeError(out.stderr.strip()[:500])
    return out.stdout


def parse(reply):
    props = []
    for line in reply.splitlines():
        line = line.strip().strip("`")
        if not line.startswith("{"):
            continue
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("rule"):
            props.append(p)
    return props[:3]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--hook-input", help="file holding the SessionEnd hook's JSON")
    ap.add_argument("--transcript")
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--model", default=os.environ.get("CONSTITUTION_MODEL", "sonnet"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    session = ""
    if args.hook_input:
        hook = json.loads(Path(args.hook_input).read_text() or "{}")
        Path(args.hook_input).unlink(missing_ok=True)
        args.transcript = hook.get("transcript_path")
        args.cwd = hook.get("cwd") or args.cwd
        session = hook.get("session_id", "")
    if not args.transcript or not Path(args.transcript).exists():
        return print(f"{date.today()} skip: no transcript")

    d = home()
    done = d / "curated.txt"
    key = session or Path(args.transcript).stem
    if not args.dry_run and done.exists() and key in done.read_text().split():
        return print(f"{date.today()} skip: {key} already curated")

    text, prompts = digest(args.transcript)
    if prompts < MIN_PROMPTS:
        return print(f"{date.today()} skip: {key} has {prompts} prompt(s)")

    rules = (d / "RULES.md").read_text()
    pending = (d / "PENDING.md").read_text().strip() or "(none)"
    project = Path(args.cwd).name
    reply = ask(PROMPT.format(clause=clause(rules), rules=rules.split("## Articles", 1)[-1].strip() or "(none)",
                              pending=pending, project=project, digest=text), args.model)
    props = parse(reply)

    if args.dry_run:
        print(json.dumps(props, indent=2, ensure_ascii=False) if props else "NONE")
        return
    with open(d / "PENDING.md", "a") as fh:
        for i, p in enumerate(props, 1):
            scope = "global" if p.get("scope") != "project" else f"project: {project}"
            fh.write(f"\n### P-{date.today()}-{key[:8]}-{i} · {scope}\n{p['rule']}\n"
                     f"- evidence: {p.get('evidence', '').strip()}\n"
                     f"- from: {project} · session: {key} · check: `{p.get('check') or ''}`\n")
    with open(done, "a") as fh:
        fh.write(key + "\n")
    print(f"{date.today()} {key}: {len(props)} proposal(s) from {project}")


if __name__ == "__main__":
    sys.exit(main())
