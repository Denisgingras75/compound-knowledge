# The Immune System Pattern

Don't predict what will go wrong. React, remember, generalize.

## The Pattern

```
Agent A hits problem X while working on Task 1
  → Record observation: "X happened in domain D" [confidence: 1]

Agent B hits problem X while working on Task 2 (independently)
  → System detects: same problem, different context
  → Promote to pattern: "X is a recurring issue in domain D" [confidence: 2]

Agent C starts working in domain D
  → System injects: "Watch out for X" before C ever encounters it
  → C avoids the problem entirely [confidence: 3 after C confirms]
```

## Why It Works

Traditional documentation tries to predict what developers will need to know. This fails because:
- Authors can't anticipate every scenario
- Context changes what's relevant
- Documentation rots as code evolves

The immune system doesn't predict. It:
1. **Reacts** to actual problems (no false positives from guessing)
2. **Remembers** via structured storage (tagged, timestamped, confidence-scored)
3. **Generalizes** via domain tagging (a Safari bug found in modals protects all UI work)
4. **Decays** when findings aren't re-confirmed (stale rules fade after 30 days)

## Confirmation Requires Independence

The key constraint: confidence only increases through **independent** confirmation. The same agent hitting the same bug twice doesn't count — that's repetition, not confirmation.

Why? Because the same agent might be stuck in the same wrong mental model. Independent confirmation from a different agent (different session, different task, different approach) provides genuine signal that the finding is broadly true, not locally coincidental.

## Implementation

### First encounter
```
- [2026-02-28] [Agent-A] [safari] — toSorted() crashes on Safari 15 [confidence: 1]
```
Stored in observations.md. Not pushed to anyone.

### Second encounter (different agent)
```
- [2026-02-28] [Agent-A+Agent-B] [safari] — ES2023 methods crash Safari 15
  — independently confirmed [confidence: 2]
```
Promoted to kb-ui-ux.md. Pushed to future UI sessions.

### Third+ encounter
```
confidence: 3 (locked rule)
```
Added to CLAUDE.md learned rules. Always injected. Treated as law.

## Decay

An observation that was noted once but never re-confirmed in 30 days gets its confidence decremented. Eventually it drops to 0 and is candidates for removal.

This prevents rule accumulation — old findings that were situational (specific to a version, a dependency, a code path that was refactored) don't permanently pollute the knowledge base.

## The Collision Graph

Over time, the immune system builds a graph of which problems tend to co-occur:
- Safari bugs cluster with CSS/flex/gap issues
- Schema bugs cluster with RPC param naming
- Auth bugs cluster with RLS policies

These clusters become **domains** — tags that route knowledge efficiently. The domains aren't pre-defined. They emerge from the collision data.

## What This Replaces

| Before | After |
|--------|-------|
| "Read the docs before starting" | System loads only relevant rules |
| "Don't forget about Safari" | System warns before Safari-risky code |
| "We tried that last week" | Dead end is recorded, never re-explored |
| "Ask Denis about the convention" | Convention is confidence-3 rule, auto-injected |

## Status

Currently implemented via:
- `insight-broadcast.sh` — Captures insights, cross-references against existing knowledge, promotes on independent confirmation
- `auto-graduate.sh` — Clusters raw observations into patterns, promotes high-confirmation patterns
- `observations.md` — Raw findings storage
- `kb-*.md` files — Graduated knowledge base

Working but early. The cross-session confirmation logic is functional. Decay is implemented. Domain routing is basic (tag-based, not graph-based).
