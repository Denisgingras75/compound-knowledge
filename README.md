# Compound Knowledge

**The theory of how to make AI sessions smarter over time.**

Every Claude session starts cold. No memory of yesterday. No awareness of what was tried and failed. No accumulated intuition. This repo is about solving that — not with bigger context windows or better prompts, but with **systems that make knowledge compound**.

## The Problem

LLM sessions have three fundamental constraints:

1. **Cold start** — Every session begins at zero. The model knows nothing about your project, your preferences, your past mistakes, or what was tried yesterday.
2. **Context ceiling** — Even within a session, there's a hard limit on what fits in the window. Long sessions compress and lose nuance. The model forgets what it learned 30 minutes ago.
3. **Lossy handoff** — When a session ends, learnings die with it. The next session may repeat the same mistakes, explore the same dead ends, or contradict decisions that were already made.

These aren't bugs. They're physics. And like physics, you don't fight them — you build systems that work *with* them.

## The Thesis

**Knowledge compounds when it's stored by root cause, not by who found it. Tagged by where it matters, not where it was discovered.**

A single session can learn something. But that learning dies when the session ends. The goal is to build infrastructure where:

- Session N's mistake becomes Session N+1's guardrail
- Observations from one domain inform rules in another
- Confidence grows through independent confirmation, not repetition
- Dead ends are recorded so they're never explored twice
- The system gets smarter even when individual sessions are short

## Structure

```
foundations/     Core theory — the problems, the model, the principles
patterns/        Confirmed patterns — things we've proven work
experiments/     What we tried, what worked, what didn't
models/          Frameworks and mental models for the system
```

## Origin

Built from real experience running multi-agent Claude Code sessions on a production app (WGH — dish-level food discovery). Not hypothetical. Every theory here was discovered by hitting the wall, finding a workaround, and then asking *why* the workaround worked.

---

*Started 2026-02-28. Denis Gingras.*
