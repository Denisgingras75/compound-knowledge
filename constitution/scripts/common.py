"""Shared paths and parsing for the constitution plugin."""

import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "RULES.md"
ARTICLE = re.compile(r"^### (A\d+) · (global|project:\s*(\S+))\s*$")


def home():
    d = Path(os.environ.get("CONSTITUTION_DIR", Path.home() / ".claude" / "constitution")).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    rules = d / "RULES.md"
    if not rules.exists():
        shutil.copy(TEMPLATE, rules)
    for name in ("PENDING.md", "AMENDMENTS.md"):
        (d / name).touch()
    return d


def articles(text):
    """Yield dicts for each article: id, scope ('global' or a project name), rule, meta lines."""
    body = text.split("## Articles", 1)[-1]
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    cur = None
    for line in body.split("\n"):
        m = ARTICLE.match(line.strip())
        if m:
            if cur:
                yield cur
            cur = {"id": m.group(1), "scope": m.group(3) or "global", "rule": "", "meta": []}
        elif cur is not None and line.strip():
            if line.strip().startswith("- "):
                cur["meta"].append(line.strip()[2:])
            elif not cur["rule"]:
                cur["rule"] = line.strip()
    if cur:
        yield cur


def meta_field(article, key):
    for m in article["meta"]:
        for part in m.split(" · "):
            k, _, v = part.partition(":")
            if k.strip() == key:
                return v.strip().strip("`")
    return None
