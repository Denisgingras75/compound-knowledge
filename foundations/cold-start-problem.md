# The Cold Start Problem

Every Claude session begins knowing nothing about you.

It doesn't know your codebase. It doesn't know your stack. It doesn't know that Safari 15 breaks on `toSorted()`, or that your Supabase schema uses inconsistent `p_` prefixes on RPC params, or that the last three sessions tried and failed to fix the same auth bug.

This is the cold start problem. And it's the single biggest bottleneck to productive AI-assisted development.

## Why It Exists

LLMs are stateless by design. Each API call is independent. There is no "memory" between sessions — only what you explicitly inject into the context window at the start. The model's weights contain general knowledge, but nothing about *your* specific world.

This means every session has a ramp-up cost:
- Reading project files to understand structure
- Re-discovering conventions and patterns
- Repeating context that was established yesterday
- Re-learning personal preferences and workflow

On a complex project, this ramp-up can consume 20-40% of a session's useful context window before any real work begins.

## Why Bigger Context Isn't The Answer

The naive solution: "just give it more context." Feed in every file, every doc, every previous conversation. But:

1. **Noise drowns signal.** A 200K context window stuffed with everything is worse than a 50K window with exactly the right things. The model attends to everything equally — it can't tell which of those 200K tokens actually matter for *this* task.

2. **Context is expensive.** Every token costs money and latency. Loading 100K tokens of "just in case" context at $15/M input tokens adds up fast when you're running 50 sessions a day.

3. **Compression is lossy.** When conversations get long, the system compresses earlier messages. Nuance disappears. The insight from turn 3 that would have prevented the mistake at turn 40 — gone.

## What Actually Works

The solution isn't more context. It's **better context selection** — loading exactly what's relevant for *this* task, *this* session, *this* moment.

This requires:
1. **Structured memory** — Not a flat file of everything. Organized by domain, tagged by relevance, ranked by confidence.
2. **Task-aware loading** — Frontend work loads UI rules. Schema work loads database rules. No wasted tokens on irrelevant context.
3. **Graduated confidence** — Not all knowledge is equal. A rule confirmed across 5 sessions is more trustworthy than a one-time observation. The system should know the difference.
4. **Decay and contradiction** — Old rules that haven't been re-confirmed should fade. Rules that conflict should be flagged, not silently coexist.

## The Cost of Getting It Wrong

When the cold start isn't solved:
- Agents repeat known mistakes (debugging time: 10-30 min each)
- Conventions drift (one session uses `logger`, the next uses `console.log`)
- Decisions are reversed without context (Session 5 undoes what Session 3 decided, because Session 5 doesn't know why Session 3 chose that)
- Dead ends are re-explored (3 sessions in a row try the same approach that doesn't work)

When it *is* solved:
- Session 1 hits a wall, records the finding
- Session 2 starts with that finding already loaded
- Session 3 confirms it independently, confidence increases
- Session 4 never even encounters the problem — it's warned before it gets there

That's compounding.

## See Also

- [Compound Learning Theory](./compound-learning.md) — How knowledge grows across sessions
- [Context Architecture](./context-architecture.md) — How context flows into sessions
