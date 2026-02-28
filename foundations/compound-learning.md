# Compound Learning Theory

Knowledge compounds when Session N's learnings automatically improve Session N+1.

This isn't about documentation. Documentation is static — someone writes it, someone reads it, and it rots. Compound learning is a **living system** where knowledge flows through capture, abstraction, and injection without manual intervention.

## The Three Layers

### 1. Capture

Every session produces learnings. Most are lost. The capture layer's job is to extract signal before the session dies.

What to capture:
- **Decisions made** — what was chosen AND what was rejected (dead ends are gold)
- **Files touched** — the breadcrumb trail of what the session actually worked on
- **Blockers hit** — what went wrong, what the error was, how it was resolved
- **Domain tags** — which part of the system was involved (frontend, database, infra, etc.)

What NOT to capture:
- Session-specific ephemera (task IDs, temporary variables, in-progress state)
- Unverified conclusions from reading a single file
- Anything that duplicates existing documentation

The key insight: **capture the WHY, not just the WHAT.** "Changed line 47 of auth.js" is useless to future sessions. "Auth was failing because the trigger fires on INSERT only, not UPDATE" — that's a reusable learning.

### 2. Abstraction

Raw session dumps are too noisy to inject into future sessions. The abstraction layer transforms raw captures into structured, tagged, confidence-scored knowledge.

The pipeline:
1. **Raw observation** — First sighting. Low confidence. Stored but not pushed.
2. **Pattern recognition** — Second sighting in a *different* context (different session, different agent, different task). Confidence bumps.
3. **Confirmed rule** — Third+ sighting. High confidence. Gets actively injected into relevant sessions.
4. **Contradiction detection** — New finding conflicts with existing rule. Both flagged for human review.

The critical principle: **knowledge is stored by root cause, not by who found it.** If Agent A discovers a Safari bug while building a modal, and Agent B hits the same bug while building a list — the rule gets tagged to the *Safari/CSS* domain, not to "modals" or "lists." Future sessions working on ANY UI component get warned.

### 3. Injection

The right knowledge, at the right time, in the right amount.

Injection is task-aware:
- Starting frontend work? Load UI/UX rules + global rules.
- Starting schema work? Load database rules + global rules.
- Starting a code review? Load ALL rules + recent observations.

Injection respects confidence:
- Confidence 3 (locked rules) = treated as law. Always injected.
- Confidence 2 (confirmed patterns) = injected as guidelines.
- Confidence 1 (observations) = available on pull, not pushed.

Injection respects budget:
- Every injected rule costs context tokens.
- High-confidence, domain-relevant rules first.
- Cut low-confidence, cross-domain rules when budget is tight.

## The Immune System Model

Don't try to predict what knowledge will be relevant. Instead, learn from collisions.

The analogy is biological:
1. An agent encounters a problem (pathogen)
2. The system records the encounter (antibody)
3. If a *different* agent independently encounters the same problem — the system recognizes the pattern (immune memory)
4. Future agents are pre-armed against it (vaccination)

This is fundamentally different from documentation, which tries to predict what will be needed. The immune system doesn't predict — it reacts, remembers, and generalizes.

Key properties:
- **No false positives from prediction** — only real problems get recorded
- **Cross-session confirmation** — requires independent verification, not just repetition
- **Automatic generalization** — the tag system routes knowledge to everyone who might need it
- **Decay** — old antibodies that aren't re-triggered eventually fade

## The Communication Hierarchy

Knowledge transmission between sessions evolved through recognizable stages:

| Medium | Analog | Properties |
|--------|--------|------------|
| Memory files | Written word | Persists, single reader at a time, requires pull |
| Agent calls | Phone calls | Real-time, multi-party, dies when call ends |
| Voicemail | Email | Async, domain-routed, persistent, no response needed |
| Push notifications | Text messages | Mid-session interrupts, shoulder taps |
| Shared workspace | FaceTime | Ambient awareness of what others are doing |
| Auto-detection | Nervous system | Pattern recognition from collisions, no manual input |

Each layer adds capability but also cost. The system should use the lightest medium that achieves the goal.

## What Compounds vs What Doesn't

**Compounds:**
- Root-cause analysis of bugs (applies to all similar code)
- Convention discoveries (benefits every future session)
- Dead-end documentation (prevents wasted exploration)
- Cross-domain causal chains (symptom in A, root cause in B)

**Doesn't compound:**
- Session-specific task context
- File paths that change
- Temporary workarounds
- Opinion without evidence

## The Goal

A system where the 100th session is dramatically more productive than the 1st — not because the model is smarter, but because the infrastructure around it has accumulated 99 sessions worth of verified, tagged, confidence-scored knowledge that gets injected exactly when it's relevant.

That's compound learning.
