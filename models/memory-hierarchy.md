# The Memory Hierarchy

A layered model of how AI session memory works, from volatile to persistent.

## The Layers

```
FASTEST / MOST VOLATILE
┌────────────────────────────────┐
│  Working Memory                │  The conversation itself.
│  (context window)              │  Dies on session end.
│                                │  Subject to compression.
│  ~200K tokens, ~$3/session     │
├────────────────────────────────┤
│  Session Memory                │  Files written during session.
│  (local filesystem)            │  Persists on disk but not in context.
│                                │  Must be explicitly re-read.
│  Unlimited size, $0            │
├────────────────────────────────┤
│  Project Memory                │  CLAUDE.md, SPEC.md, TASKS.md.
│  (project files)               │  Auto-loaded at session start.
│                                │  Shared across all sessions on this project.
│  ~5-10K tokens, $0.15/session  │
├────────────────────────────────┤
│  Cross-Session Memory          │  MEMORY.md, knowledge base files.
│  (memory directory)            │  Selective loading based on task.
│                                │  Shared across all projects.
│  ~10-30K tokens, $0.30/session │
├────────────────────────────────┤
│  Collective Memory             │  Observations, graduated patterns.
│  (knowledge base)              │  Built from multiple agents and sessions.
│                                │  Confidence-scored. Decays over time.
│  Variable, loaded on demand    │
├────────────────────────────────┤
│  Permanent Memory              │  Learned rules in CLAUDE.md.
│  (locked rules)                │  Never expires. Always loaded.
│                                │  Only added through graduation pipeline.
│  ~1-2K tokens, always loaded   │
└────────────────────────────────┘
SLOWEST / MOST PERSISTENT
```

## Properties

| Layer | Volatility | Load Cost | Write Cost | Who Writes |
|-------|-----------|-----------|------------|------------|
| Working | Dies on session end | Free (it IS the session) | Free | The conversation |
| Session | Persists on disk | Must re-read files | File writes | The session |
| Project | Persists in repo | Auto-loaded (~0.15) | Manual edit | Human + AI |
| Cross-Session | Persists in memory dir | Selective (~0.30) | /end-session | AI pipeline |
| Collective | Persists in KB | On-demand | Graduation pipeline | Multi-agent |
| Permanent | Persists forever | Always loaded (~0.02) | Human approval | Human |

## The Key Insight

Each layer up is **more persistent but more expensive to update.** Working memory is free to modify but dies instantly. Permanent memory lasts forever but requires multiple independent confirmations + human review to add a single line.

This is intentional. The graduation cost prevents noise from reaching the upper layers. Only knowledge that has been tested, confirmed, and refined makes it to the top.

## Failure Modes

### Over-caching (too much in upper layers)
- Symptoms: Every session starts slow. Context budget consumed by rules. No room for actual work.
- Fix: Aggressive decay. Task-based selective loading. Ruthless pruning.

### Under-caching (too little persisted)
- Symptoms: Same mistakes repeated. Decisions reversed. Dead ends re-explored.
- Fix: Better end-session capture. Midsession checkpoints. PostToolUse detection hooks.

### Stale cache (outdated knowledge persisted)
- Symptoms: Rules that were true but code has changed. Conventions from old architecture.
- Fix: Confidence decay (30-day window). Contradiction detection. Periodic review.

### Cross-contamination (wrong knowledge loaded)
- Symptoms: Database rules injected into a UI session. Irrelevant warnings.
- Fix: Better domain tagging. Task-matched loading. Don't load everything.

## Analogy to Computer Memory

| AI Memory | Computer Memory | Why |
|-----------|----------------|-----|
| Working memory | CPU registers | Fastest, smallest, most volatile |
| Session memory | L1/L2 cache | Fast access, session-scoped |
| Project memory | L3 cache | Shared across sessions in project |
| Cross-session | RAM | Larger, selective access |
| Collective | SSD | Persistent, slower to write |
| Permanent | ROM/firmware | Never changes without deliberate update |

The computer analogy breaks down in one important way: in computer architecture, lower layers are automatically populated by hardware. In AI memory, the pipeline from working → permanent is a *designed system* that requires intentional engineering. There's no automatic cache-fill — every promotion is earned.
