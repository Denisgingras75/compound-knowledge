# Trust Decay Model

Not all knowledge ages the same. Confidence scoring and decay keep the knowledge base honest.

## The Confidence Scale

```
0 — Expired. Was observed once, never confirmed, aged out.
1 — Observed. First sighting. Might be wrong. Might be situational.
2 — Confirmed. Independent verification. Probably right. Push to relevant sessions.
3 — Locked. Multiple confirmations. Treated as law. Always injected.
```

## Why Decay Matters

Without decay, the knowledge base grows monotonically. Every observation sticks forever. After 100 sessions, you're loading 500 rules — most of which were situational findings that no longer apply because:
- The code was refactored
- The dependency was updated
- The convention was changed
- The bug was fixed at the root

Decay is the garbage collector. It removes knowledge that isn't being re-confirmed.

## Decay Mechanics

Current implementation (in `auto-graduate.sh`):

```
IF observation.age > 30 days
AND observation.last_confirmed < 30 days ago
THEN observation.confidence -= 1
```

When confidence hits 0, the observation becomes a candidate for removal in the next cleanup pass.

Locked rules (confidence 3) are immune to automatic decay. They can only be removed through:
1. Explicit contradiction by a new confidence-2+ finding
2. Manual review and deletion

## The Re-confirmation Signal

Decay resets when:
- A different agent encounters the same finding
- The same pattern appears in a different context
- A PostToolUse hook catches the same antipattern

Each re-confirmation updates `last_confirmed` and potentially bumps confidence.

## Trust Economics

Think of confidence as a currency:
- **Earning trust is expensive** — requires independent confirmation, time, different contexts
- **Losing trust is automatic** — happens through inaction (not being re-confirmed)
- **Regaining trust is cheaper** — a single re-confirmation resets the decay clock

This mirrors how real trust works. You don't trust someone after one interaction. You trust them after consistent, independent evidence. And that trust erodes if they go silent for long enough.

## Edge Cases

### The True But Rare Rule
Some rules are true but only apply in rare situations (e.g., "Safari 15 crashes on toSorted()"). These might not get re-confirmed often because the situation doesn't arise frequently.

Solution: Locked rules (confidence 3) don't decay. Once something has been confirmed enough to reach locked status, it persists until explicitly contradicted. The graduation threshold is high enough that only genuinely persistent truths make it.

### The Context-Dependent Truth
"Always use `style={{}}` for colors" is true in WGH's dual-theme system. It might not be true in a different project.

Solution: Domain tagging. The rule is tagged to `ui/wgh`, not `ui/global`. It only loads when working on WGH frontend.

### The Evolving Convention
Conventions change. "Use `var` for local computed values" might be a Denis preference today and reversed tomorrow.

Solution: Human-gated graduation to permanent rules. Conventions that might change stay at confidence 2 (pushed but not locked). Only conventions confirmed to be permanent get locked.

## What We Don't Have Yet

- **Decay visualization** — No dashboard showing which rules are aging and might drop off
- **Re-confirmation tracking** — No count of how many times a rule has been re-confirmed
- **Domain-specific decay rates** — All rules decay at the same rate. Infrastructure rules might need slower decay than UI rules.
- **Cascading invalidation** — When a root rule is contradicted, derived rules should also be flagged
