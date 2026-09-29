"""Read a git repository's history as plain Python objects.

Standard library only, so the scripts in this folder run anywhere Python 3.9+
and git are installed.
"""

import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

REC = "\x1e"   # record separator between commits
UNIT = "\x1f"  # field separator inside a commit header
TRAILER_SEP = "\x1d"

LOG_FORMAT = UNIT.join([
    REC + "%H",
    "%P",
    "%aI",
    "%an",
    "%(trailers:key=Co-Authored-By,valueonly,separator=%x1d)",
    "%s",
    "%b",
]) + UNIT


@dataclass
class FileDiff:
    path: str
    status: str = "M"  # A added, M modified, D deleted, R renamed
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)


@dataclass
class Commit:
    sha: str
    parent: Optional[str]
    date: str      # ISO 8601 author date
    author: str
    model: str     # normalized Co-Authored-By model, or "none"
    subject: str
    body: str
    files: List[FileDiff]


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, check=True, errors="replace",
    ).stdout


def normalize_model(trailers):
    """'Claude Opus 4.6 (1M context) <noreply@anthropic.com>' -> 'Opus 4.6 (1M)'."""
    models = []
    for raw in trailers.split(TRAILER_SEP):
        m = re.search(r"Claude\s+(Opus|Sonnet|Haiku)\s+([\d.]+)(\s*\(1M[^)]*\))?", raw)
        if m:
            models.append(f"{m.group(1)} {m.group(2)}" + (" (1M)" if m.group(3) else ""))
    return " + ".join(sorted(set(models))) if models else "none"


def _parse_patch(text):
    files, cur, in_hunk = [], None, False
    for line in text.split("\n"):
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*) b/(.*)$", line)
            cur = FileDiff(path=m.group(2) if m else line[11:])
            files.append(cur)
            in_hunk = False
        elif cur is None:
            continue
        elif not in_hunk:
            if line.startswith("new file mode"):
                cur.status = "A"
            elif line.startswith("deleted file mode"):
                cur.status = "D"
            elif line.startswith("rename to "):
                cur.status, cur.path = "R", line[len("rename to "):]
            elif line.startswith("@@"):
                in_hunk = True
        elif line.startswith("@@"):
            continue
        elif line.startswith("+"):
            cur.added.append(line[1:])
        elif line.startswith("-"):
            cur.removed.append(line[1:])
    return files


def commits(repo, paths=(), with_patch=True):
    """Yield every non-merge commit, oldest first."""
    args = ["log", "--no-merges", "--reverse", "--no-color", f"--format={LOG_FORMAT}"]
    if with_patch:
        args += ["-p", "-M", "--unified=0"]
    if paths:
        # --full-history: never prune side-branch commits during path limiting
        args += ["--full-history", "--", *paths]
    out = git(repo, *args)
    for record in out.split(REC)[1:]:
        parts = record.split(UNIT)
        sha, parents, date, author, trailers, subject, body = parts[:7]
        patch = UNIT.join(parts[7:])
        parent_list = parents.split()
        yield Commit(
            sha=sha,
            parent=parent_list[0] if parent_list else None,
            date=date,
            author=author,
            model=normalize_model(trailers),
            subject=subject,
            body=body.strip(),
            files=_parse_patch(patch) if with_patch else [],
        )


class Blobs:
    """Cached `git show REV:PATH` for many revisions (one long-lived git process)."""

    def __init__(self, repo):
        self.proc = subprocess.Popen(
            ["git", "-C", repo, "cat-file", "--batch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        )
        self.cache = {}

    def get(self, rev, path):
        if rev is None:
            return ""
        key = f"{rev}:{path}"
        if key not in self.cache:
            self.proc.stdin.write((key + "\n").encode())
            self.proc.stdin.flush()
            header = self.proc.stdout.readline().decode()
            if header.endswith("missing\n"):
                self.cache[key] = ""
            else:
                size = int(header.split()[2])
                data = self.proc.stdout.read(size)
                self.proc.stdout.read(1)  # trailing newline
                self.cache[key] = data.decode("utf-8", errors="replace")
        return self.cache[key]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()
