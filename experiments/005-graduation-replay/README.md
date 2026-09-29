# Experiment 005 code

Scripts behind [`../005-graduation-replay.md`](../005-graduation-replay.md). Python 3.9+ and git, no packages.

```bash
./run.sh ~/code/wgh            # every part, results in ./results (about 15 seconds)
```

| Script | Part | What it does |
|---|---|---|
| `scan_violations.py` | A | For every commit, checks the CLAUDE.md in its parent commit for each rule in `rules.json`, and counts violations in the lines the commit added |
| `git_events.py` | B | Turns fix commits into observations (one per bullet, plus the subject) and commit runs into sessions |
| `replay.py` | B | The graduation pipeline as documented: keyword clustering, the 1/2/3 ladder, CLAUDE.md candidates, and four decay policies |
| `rule_lifecycle.py` | C | Feeds every real violation to the same pipeline, as a PostToolUse hook would catch it |
| `counterfactual.py` | D | A model: redraws each commit's violation from measured rates, so a hook-fed pipeline can be compared with the human rules |
| `pipeline_events.py` | – | Adapter for the real pipeline's `observations.md` and CODEX.md raw log |
| `gitlog.py` | – | Shared git history reader |

Inputs you can edit:

- `rules.json`: rules a regex can check.
  - `anchor` is text whose presence in CLAUDE.md means the rule is in force.
  - `pattern` is a violation in an added line.
  - `compliant` is the right way to do the same thing.
  - `skip_commits` lists bulk copies to leave out, with a reason for each.
- `classes.json`: mistake classes tracked through the replay, with the date a human wrote each rule.
- `coherence_labels.json`: hand labels for every finding the WGH replay promoted, keyed by first observation id.

## Event format

`replay.py` reads JSON lines in time order:

```json
{"type": "observation", "ts": 1769300000, "date": "2026-01-24", "session": "s0027", "id": "5ab4263#1", "text": "Replace toSorted() with slice().sort()"}
{"type": "session_end", "ts": 1769303600, "session": "s0027"}
```

- `session` decides independence: the same session twice is repetition, not confirmation.
- Each `session_end` is one auto-graduate run.
- An observation with a `"key"` field matches other observations with the same key exactly, instead of by keywords.

## On the real pipeline files

```bash
python3 pipeline_events.py ~/.claude/memory/knowledge_base/observations.md path/to/CODEX.md \
    --out results/pipeline_events.jsonl
python3 replay.py --events results/pipeline_events.jsonl --out results/pipeline --classes none --labels none
```

The adapter reads the formats documented in `patterns/immune-system.md` and experiment 003. It hasn't been run on the real files, so check its first lines of output against the source.

## Results

| File | Contents |
|---|---|
| `violations.md` / `.json` | Part A tables: all commits, Claude-only, windows between rule changes, per model |
| `violation_instances.csv` | Every matched line, for checking the regexes by eye |
| `violation_commits.csv`, `rule_commits.json` | Per-commit counts, used by parts C and D |
| `events.jsonl` | The observations and session ends replayed in part B |
| `replay_summary.md` / `.json` | Part B counts and label tallies per decay policy. `_20perday` is the same run with 20 pipeline runs a day |
| `replay_findings.json` | Every finding from the 30-day-window replay, with members and history |
| `rule_lifecycle.md` / `.json` | Part C |
| `counterfactual.md` / `.json` | Part D |
