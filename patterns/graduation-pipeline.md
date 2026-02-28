# The Graduation Pipeline

How raw observations become trusted rules.

## The Lifecycle

```
RAW OBSERVATION          CONFIRMED PATTERN          LOCKED RULE
(confidence: 1)          (confidence: 2)            (confidence: 3)

First sighting.    →     Independent confirmation.  →  Multiple confirmations.
Stored, not pushed.      Pushed to relevant sessions.   Injected always.
May be wrong.            Probably right.                Treated as law.

observations.md          kb-{domain}.md                CLAUDE.md learned rules
```

## Entry Points

Knowledge enters the pipeline from:

1. **Session end dumps** — `/end-session` extracts decisions, blockers, files touched, domain tags
2. **Midsession checkpoints** — Periodic dumps during long sessions (before compression loses the insight)
3. **Agent broadcasts** — The `#insights` channel where agents publish findings
4. **PostToolUse hooks** — Automated detection of known antipatterns (hex in JSX, console.log, ES2023+)
5. **Manual codex entries** — Denis's sharp observations captured in the codex

## Graduation Criteria

### Observation → Pattern (1 → 2)
- Same finding observed by **different agents** (different PIDs)
- OR same finding in **different contexts** (different task types)
- Keyword overlap ≥ 50% between findings
- Not a duplicate of existing KB entry

### Pattern → Rule (2 → 3)
- 3+ independent confirmations
- No contradicting observations in the same timeframe
- Survives 30-day decay window (keeps getting re-confirmed)

### Rule → Learned Rule (3 → CLAUDE.md)
- 6+ confirmations (auto-graduate.sh promotion threshold)
- Human review (Denis resolves any ambiguity)
- Formatted as: `When [trigger] → Do [action] — [consequence if violated]`

## Contradiction Handling

When a new observation contradicts an existing rule:

1. Both get flagged in `contradictions.md`
2. Existing rule gets a `⚠️ contested` tag
3. Neither is deleted — both persist until human resolution
4. The system presents both sides: "Rule says X, but observation says Y"

This prevents the system from silently flipping positions. Contradictions are valuable data — they often indicate context-dependent truths (works in one domain, fails in another).

## The Clustering Algorithm

`auto-graduate.sh` clusters raw observations using keyword overlap:

1. Extract meaningful keywords (4+ chars, non-stopword) from each entry
2. Two entries are "related" if they share 3+ keywords
3. Greedy clustering: build groups of 3+ related entries
4. Each cluster graduates into a named pattern
5. Graduated entries are removed from raw log

The algorithm is intentionally simple. Sophisticated NLP would be overkill — the keyword overlap heuristic catches the patterns that matter (same error, same file, same concept) without false positives.

## Token Cost of Rules

Every graduated rule that gets injected into sessions costs tokens. The pipeline implicitly manages this:

- Confidence 1: 0 injection cost (pull-only)
- Confidence 2: Injected to task-matched sessions only
- Confidence 3: Injected to all sessions

As rules accumulate, injection cost grows. The decay mechanism counters this — rules that stop being relevant eventually drop off. The steady state is a compact, high-confidence knowledge base.

## Metrics (Aspirational)

What we'd measure if we had instrumentation:
- **Time to graduation:** How many sessions between first observation and locked rule?
- **Prevention rate:** How often does an injected rule prevent a mistake?
- **False positive rate:** How often does the system warn about something that isn't actually a problem?
- **Coverage:** What percentage of mistakes were already known but not loaded?

## Current State

The pipeline is operational:
- `insight-broadcast.sh` handles capture + cross-session detection
- `auto-graduate.sh` handles clustering + graduation
- `observations.md` stores raw findings
- `kb-*.md` files store graduated patterns
- CLAUDE.md learned rules section stores locked rules
- Decay runs during graduation (30-day window)

Gaps:
- No instrumentation for prevention rate
- Contradiction detection is manual
- Domain routing is tag-based, not learned from collision data
- Graduation from kb to CLAUDE.md requires manual review
