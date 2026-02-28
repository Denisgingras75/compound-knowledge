# Agent Topology

How multi-agent teams compound knowledge faster than solo sessions.

## The Multiplier Effect

A single session learns linearly. A team of agents learns superlinearly — because independent agents hitting the same problem from different angles provides the **confirmation signal** that the immune system needs to promote observations to patterns.

Solo session: observation → sits in raw log → eventually forgotten
Multi-agent: observation by Agent A + independent confirmation by Agent B → pattern in 1 session instead of 3

## Team Structures

### Hub and Spoke (Current)
```
         Denis (hub)
        /  |   \   \
    crow  hawk  bear  tiger
```

One orchestrator (Denis or a dispatch agent) assigns independent tasks. Agents work in parallel. No direct agent-to-agent coordination.

**Strengths:** Simple. No conflict. Tasks are cleanly separated.
**Weaknesses:** No cross-pollination during execution. Insights only compound at session end.

### Mesh (Future)
```
    crow ←→ hawk
      ↕  ✕   ↕
    bear ←→ tiger
```

Agents communicate directly via the phone system. Schema changes broadcast. Findings propagate mid-session.

**Strengths:** Faster knowledge flow. One agent's discovery immediately helps others.
**Weaknesses:** Noise risk. Coordination overhead. Potential conflicts (two agents editing the same file).

### Layered (Hybrid)
```
    [Orchestrator]
         ↓ directives
    [Worker Agents]
         ↓ findings
    [Reviewer Agent]
         ↓ graduated knowledge
    [Knowledge Base]
```

Workers produce. A dedicated reviewer agent processes their outputs into knowledge. Workers never see each other directly — they interact through the shared knowledge base.

**Strengths:** Clean separation. Reviewer catches patterns workers miss. Knowledge base stays curated.
**Weaknesses:** Reviewer is a bottleneck. Delayed feedback loop.

## Push vs Pull

The team needs both:

| Type | Mechanism | When |
|------|-----------|------|
| Pull | `/start` loads KB files | Session boot. Passive. |
| Push | PostToolUse broadcasts | Schema changes. Active. |
| Push | `agents push <name> "msg"` | Orchestrator wakes idle agent. Active. |
| Pull | Voicemail check | Session boot. Async handoff. |
| Push | `#insights` channel | Cross-session finding. Active. |

The current system is mostly pull (load at start) with some push (PostToolUse hooks, tmux push). The ideal is more push — agents should be notified of relevant findings as they happen, not just at session start.

## Conflict Resolution

When multiple agents touch the same codebase:

1. **File-level separation** — Dispatch assigns non-overlapping files. Best prevention.
2. **Git branches** — Each agent works in a worktree. Merge at end.
3. **Schema-first** — Schema agent goes first. Others start after schema is stable.
4. **Broadcast on write** — PostToolUse hook notifies all agents when key files change.

Current approach: file-level separation (dispatch assigns independent tasks) + schema-first ordering when tasks depend on schema.

## The Scaling Question

Does adding more agents always help?

**Yes, when:**
- Tasks are genuinely independent
- Each agent has enough context to work autonomously
- The knowledge base benefits from more data points

**No, when:**
- Tasks have hidden dependencies (two agents edit the same state)
- Context injection cost exceeds session budget (too many rules to load)
- Orchestration overhead exceeds parallel gains (managing 10 agents costs more than the work)

Sweet spot for the current system: 3-4 agents on independent features. Beyond that, coordination cost grows faster than throughput.

## Discovery: Agent Identity and Specialization

Agents that work on the same domain repeatedly develop implicit specialization through the knowledge base. Agent A works on frontend three times → the frontend KB gets denser → the next frontend agent (even if it's Agent B) starts with Agent A's accumulated knowledge.

The specialization isn't in the agent — it's in the domain tag. Any agent assigned to @frontend inherits all frontend knowledge. This is a feature: agents are interchangeable, but knowledge is cumulative.
