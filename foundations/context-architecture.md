# Context Architecture

How knowledge flows from storage into a live session.

## The Funnel

Every session has a fixed context budget. The architecture's job is to fill that budget with maximum signal, minimum noise.

```
                    TOTAL CONTEXT BUDGET
                    ┌──────────────────┐
                    │  System prompt    │  ← Fixed cost. Rules of engagement.
                    │  CLAUDE.md        │  ← Project rules. Always loaded.
                    │  MEMORY.md        │  ← Cross-session brain. Always loaded.
                    ├──────────────────┤
                    │  Task-matched     │  ← KB files selected by task type.
                    │  knowledge base   │     Frontend → kb-ui-ux.md
                    │                   │     Backend → kb-backend.md
                    │                   │     Schema → kb-database.md
                    ├──────────────────┤
                    │  Observations     │  ← Low-confidence findings. Optional.
                    │  Voicemails       │  ← Async messages from other sessions.
                    │  Recent git state │  ← What just happened in the codebase.
                    ├──────────────────┤
                    │                   │
                    │  WORKING SPACE    │  ← The actual conversation. Files read,
                    │                   │     code written, decisions made.
                    │                   │
                    └──────────────────┘
```

The top layers are cheap (small, high-signal). The bottom is where real work happens. The goal: minimize the top layers' token cost while maximizing their information density.

## Loading Strategy

### Always-on (every session)
- **CLAUDE.md** — Project rules, conventions, do/don't lists. ~1-2K tokens. Non-negotiable.
- **MEMORY.md** — Cross-session state. Current branch, last commit, active priorities. ~1K tokens. Kept concise by design (200-line cap).

### Task-matched (selective)
- **Knowledge base files** — Loaded based on what the session is about to do. A frontend session loads UI rules; a schema session loads database rules. This is the key insight: *don't load what you don't need.*

| Task | Load | Skip |
|------|------|------|
| Frontend/UI | kb-ui-ux.md, kb-global-rules.md | kb-database.md, kb-backend.md |
| Database/schema | kb-database.md, kb-global-rules.md | kb-ui-ux.md |
| Full-stack | All KB files | Nothing |
| Code review | All KB + observations.md | Nothing |

### On-demand (pull when needed)
- **Observations** — Low-confidence findings. Not injected automatically. Available if the session hits something relevant.
- **Voicemails** — Async handoffs from previous sessions. Checked at start, not continuously loaded.
- **Topic files** — Deep dives on specific domains (jitter, agent infra, business strategy). Pulled by keyword match against current task.

## The Compression Problem

Long sessions hit context limits. When they do, the system compresses earlier messages. This is lossy — insights from early in the conversation disappear.

Mitigations:
1. **Midsession checkpoints** — Dump current learnings to persistent storage *during* the session, not just at the end. If the session compresses, the learnings survive.
2. **Short, focused sessions** — A session that does one thing well is more productive than a session that tries to do everything and loses context halfway through.
3. **External state** — Keep TODO lists, decisions, and blockers in files, not in conversation memory. Files don't compress.

## Token Economics

At $15/M input tokens (Opus):
- Loading 10K tokens of context at session start = $0.15
- Running 50 sessions/day = $7.50/day just on context loading
- Loading 50K tokens of "everything" = $0.75/session = $37.50/day

The task-matched loading approach cuts context cost by 60-70% compared to loading everything. More importantly, it improves quality — less noise means better attention.

## The Startup Sequence

What actually happens when a session boots:

```
1. Read MEMORY.md              → cross-session state, pointers
2. Check phone inbox           → voicemails, active calls, agent roster
3. Read shared context         → what other agents are doing
4. Ask: "What are we doing?"   → human provides task direction
5. Load task-matched KB        → inject relevant rules
6. Read project CLAUDE.md      → project-specific conventions
7. Begin work                  → maximum context available for the actual task
```

Steps 1-3 are automatic. Step 4 is the human handshake — the system needs to know what kind of work to prepare for. Steps 5-6 are selective based on step 4. Step 7 starts with a clean, well-informed context.

## Multi-Session Context

When multiple sessions run in parallel (agent teams), context needs to flow *between* sessions, not just *into* them.

Mechanisms:
- **Broadcast hooks** — Schema changes auto-notify all agents via PostToolUse hooks
- **Agent phone** — Real-time messaging between sessions (Supabase-backed)
- **Shared files** — `shared-context.md` updated by any session, read by all
- **Voicemail** — Structured async handoffs with context dumps

The challenge: broadcasting everything creates noise. The solution: domain-tagged routing. A schema change broadcasts to sessions tagged @backend and @schema. A CSS fix doesn't.

## Open Questions

- How do you measure context quality? Token count is easy; information density is hard.
- What's the optimal session length before compression losses outweigh continuation benefits?
- Can you pre-compute which KB rules are most likely to be relevant based on the files about to be edited?
- Is there a way to detect when a session is about to hit a known failure mode, and inject the relevant rule *just in time*?
