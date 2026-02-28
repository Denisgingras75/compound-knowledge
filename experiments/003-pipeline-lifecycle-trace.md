# Experiment 003: Pipeline Lifecycle Trace

**Date:** 2026-02-28
**Investigator:** Research agent (Opus 4.6)
**Method:** Read-only trace of all pipeline components, state files, debug logs, and data stores

---

## 1. Pipeline Map

```
SESSION START                           MID-SESSION                         SESSION END
=============                           ===========                         ===========

inject-rules.sh ─── rules.jsonl ───┐    midsession-timer.sh                insight-broadcast.sh
  (weight >= 2, top 20)            │      calls insight-broadcast.sh         reads insight-buffer.jsonl
                                   │                                         AUDN vs CODEX Raw Log
context-loader.sh ─── topics/ ─────┤    insight-detect.sh (PostToolUse)      writes: CODEX Raw Log
  (CWD mapping, NO kb-*.md)        │      7 signals → insight-buffer.jsonl     + #insights channel
                                   │                                         cross-session → observations.md
                                   │                                         clears buffer
                                   ▼
                           AGENT SESSION                                   auto-graduate.sh
                           (tool calls)                                      reads: CODEX Raw Log
                                                                             clusters 3+ → Graduated Patterns
                                                                             cross-session via Supabase
                                                                             writes: kb-{domain}.md
                                                                             decay: observations > 30d

                                                                           sleep-agent.sh
                                                                             reads: CODEX Raw Log
                                                                             haiku call → rules.jsonl
```

### Data Stores (4 tiers)

| Tier | File(s) | Loaded at boot? | Auto-populated? |
|------|---------|-----------------|-----------------|
| T1: Session buffer | .hotline/insight-buffer.jsonl | No | YES (PostToolUse) |
| T2: Raw Log | CODEX.md ## Raw Log | No | YES (insight-broadcast) |
| T3: Observations | observations.md | No | YES (cross-session) |
| T3: KB domain files | kb-{domain}.md (TWO locations) | PARTIAL | YES (auto-graduate) |
| T4: Graduated Patterns | CODEX.md ## Graduated Patterns | No | YES (auto-graduate) |
| T5: Learned Rules | rules.jsonl | YES (inject-rules.sh) | YES (sleep-agent.sh) |
| T6: CLAUDE.md | Global + project CLAUDE.md | YES (auto) | MANUAL only |

---

## 2. What Actually Runs (Evidence from Debug Logs)

### insight-detect.sh (PostToolUse hook)
**Status: RUNNING.** The tool-sequence.log has 26 entries from current session. The insight-buffer.jsonl currently has 1 entry (a "pivot" signal from agent G-p822). The hook fires on every tool call.

### insight-broadcast.sh (SessionEnd + midsession)
**Status: PARTIALLY RUNNING.** Only 2 of 23 total SessionEnd events include `insight-broadcast.sh` in the command chain. The older SessionEnd hooks used a different command string that did NOT include it. The midsession-timer.sh does call it. So broadcast runs mid-session but was missing from most session ends until the hook was recently updated.

### auto-graduate.sh (SessionEnd)
**Status: RUNNING RECENTLY.** 7 of 23 SessionEnd events include `auto-graduate.sh`. Evidence: CODEX.md has 4 auto-generated patterns (General, Infra, Infra Source, Jitter clusters). The script is functional -- it produced real output.

### sleep-agent.sh (SessionEnd)
**Status: RUNNING.** Present in the same 7 recent SessionEnd chains. Produced 23 rules in rules.jsonl, all from 2026-02-28 (the day the pipeline was fully assembled).

### inject-rules.sh (SessionStart)
**Status: RUNNING.** Present in settings.json SessionStart hooks. Outputs "Learned Rules" section with feedback tag instructions. 23 rules loaded at boot, filtered by weight >= 2.

### context-loader.sh (SessionStart)
**Status: RUNNING BUT INCOMPLETE.** Loads topic files (wgh-core.md, schema-data.md, etc.) based on CWD mapping. Does NOT load kb-*.md files. This is the documented gap from compound-learning-v2.md Step 4.

---

## 3. Tracing Real Examples

### Example A: "Hold your position when challenged" rule

**Current location:** rules.jsonl (r009, weight 4), kb-global-rules.md (confidence 2), CODEX.md Raw Log ("Denis correction -- don't be spineless")

**Trace backward:**
1. Denis corrected an agent during a session ("Your opinion is different every five minutes")
2. The /end-session manually wrote this to CODEX Raw Log as entry `### 2026-02-28: Denis correction -- don't be spineless`
3. sleep-agent.sh processed it into rules.jsonl as r009
4. It was also manually written into kb-global-rules.md during a KB seeding session

**Was it ever in observations.md?** NO. It jumped directly from CODEX Raw Log to rules.jsonl via sleep-agent.sh, and was manually placed in kb-global-rules.md.

**Did insight-detect.sh catch it?** Signal 3 (Denis correction) was designed for this, but the detection relies on the text pattern appearing in tool_result output. The correction happened in conversation, not in a tool result. The signal likely did NOT fire automatically.

### Example B: "Safari needs explicit width on flex children with gap"

**Current location:** CODEX Raw Log (`### 2026-02-28: [frontend] Safari needs explicit width on flex children with gap`), rules.jsonl (r011, weight 4)

**Trace backward:**
1. Source line: "tagged by G-p42" -- this was captured by Signal 2 (self-report tag)
2. insight-detect.sh caught the `[INSIGHT]` tag in tool output
3. insight-broadcast.sh processed it from buffer to CODEX Raw Log
4. sleep-agent.sh graduated it to rules.jsonl

**Was it ever in observations.md?** NO. It went buffer -> CODEX Raw Log -> rules.jsonl, skipping the observations/KB tier entirely.

### Example C: "Learning pipeline architecture exists but capture net too narrow"

**Current location:** observations.md (confidence 2, agents bear + unknown cross-confirmation)

**Trace backward:**
1. Agent "bear" (G-p995) wrote the compound-learning-v2.md design doc
2. The observation was placed directly in observations.md with `[confidence: 2]` during an agent audit session
3. It was NOT auto-detected by insight-detect.sh

**Has it graduated?** NO. It sits in observations.md at confidence 2 but has no path to auto-graduate because:
- auto-graduate.sh only processes CODEX Raw Log entries (not observations.md directly)
- The cross-session detection in auto-graduate.sh Phase B only promotes from #insights channel to kb-{domain}.md
- observations.md entries have no automated graduation path to kb files

### Example D: All 7 observations.md entries

All 7 entries in observations.md were placed there on 2026-02-28 by specific named agents (bear, hawk, crow) during coordinated audit sessions. ALL have `[confidence: 2]`. NONE were auto-detected by insight-detect.sh. They were manually written by agents who were specifically tasked with auditing the system.

**Graduation status:** STUCK. None have moved to kb-*.md files through automated means.

---

## 4. Pipeline Breaks

### BREAK 1: observations.md is a dead end (CRITICAL)

**The problem:** observations.md has no automated reader. Nothing processes it into kb-*.md files. The auto-graduate.sh Phase B reads the #insights Supabase channel and cross-references with observations, but only to BUMP confidence -- it doesn't graduate observations into KB files on its own.

**Evidence:** 7 observations sitting at confidence 2 since 2026-02-28. Zero graduated.

**Fix:** auto-graduate.sh Phase B should also scan observations.md and graduate entries with confidence >= 2 to kb-{domain}.md.

### BREAK 2: context-loader.sh does not inject KB files (CRITICAL)

**The problem:** At session start, agents get topic files (wgh-core.md, schema-data.md) but NOT kb-*.md files. The KB files only load if the agent happens to be in a project that has them referenced in CLAUDE.md. There's no automated injection of the learned domain rules.

**However:** inject-rules.sh DOES load rules.jsonl. So the "muscle memory" tier works. But the richer, more detailed kb-*.md tier is orphaned from the boot sequence.

**Evidence:** context-loader.sh source code has zero references to `kb-` anything.

**Impact:** The entire kb-*.md tier (5 files across 2 directories, ~50 rules) is functionally invisible to most sessions.

### BREAK 3: Two KB directories, no unification

**The problem:** KB files exist in TWO locations:
- `/Users/denisgingras/.claude/knowledge_base/` (5 files, loaded by unknown mechanism)
- `/Users/denisgingras/.claude/memory/knowledge_base/` (6 files including observations.md, written to by auto-graduate.sh)

auto-graduate.sh writes to `~/.claude/memory/knowledge_base/kb-{domain}.md`, but the older KB files in `~/.claude/knowledge_base/` are a separate set. They contain overlapping but not identical content. Nothing reconciles them.

**Evidence:** Comparing kb-global-rules.md between the two directories:
- `~/.claude/knowledge_base/kb-global-rules.md`: 12 rules, includes "Fight fakes with economics", "Separate proof from monetization"
- `~/.claude/memory/knowledge_base/kb-global-rules.md`: 10 rules, similar but different format and content

### BREAK 4: insight-broadcast.sh was missing from most SessionEnd hooks (NOW FIXED)

**The problem:** Of 23 SessionEnd events in debug logs, only 2 included insight-broadcast.sh. The rest used older hook chains that skipped it. This means insights captured during sessions were NOT being flushed to CODEX Raw Log at session end.

**Current status:** The latest settings.json has it. This is fixed going forward.

### BREAK 5: CODEX Active Rules section is permanently empty

**The problem:** CODEX.md has an `## Active Rules` section with a comment saying rules get promoted from Graduated Patterns when confirmed 3+ sessions. But:
1. The Jitter pattern has 6 confirmations (flagged as promotion candidate)
2. Nothing automatically writes to Active Rules
3. auto-graduate.sh only flags candidates with a print statement -- it doesn't promote

**Evidence:** CODEX Active Rules section has zero entries despite having a pattern with 6 confirmations.

### BREAK 6: The sleep-agent.sh bypass

**The problem:** sleep-agent.sh reads CODEX Raw Log and uses a haiku API call to generate rules in rules.jsonl. This BYPASSES the entire observations -> KB -> Graduated Patterns hierarchy. Raw log entries jump directly to rules.jsonl.

This is actually functional (it produces rules), but it means:
- The confidence ladder (1 -> 2 -> 3 -> CLAUDE.md) is theoretical
- The actual path is: Raw Log -> haiku -> rules.jsonl (one hop)
- observations.md, kb-*.md, and Graduated Patterns are bypassed entirely

### BREAK 7: The AUDN filter may be too aggressive

**The problem:** insight-broadcast.sh uses Jaccard similarity at threshold 0.5 to deduplicate against CODEX Raw Log. With only 7 raw entries and large stopword list, similar-sounding but different insights may be filtered as duplicates.

**Evidence:** Cannot confirm directly, but the buffer currently has 1 entry, and the CODEX Raw Log has 7 entries -- a ratio that suggests low throughput. With 7+ detection signals now active, this needs monitoring.

### BREAK 8: 30-day decay runs on every auto-graduate execution

**The problem:** Every time auto-graduate.sh runs (at every session end), it decrements confidence on all observations older than 30 days. If 5 sessions end in one day, an observation gets decremented 5 times. No "already decayed today" guard.

**Current impact:** Zero. All observations are from 2026-02-28 (today). But in 30 days, if this isn't fixed, observations will be aggressively decayed to 0 and effectively deleted.

---

## 5. Scoring the System

### Capture Rate: ~5%
- **Denominator:** Agents run 20+ sessions/day with dozens of learnings each
- **Numerator:** 7 CODEX Raw Log entries + 7 observations = 14 captured items
- insight-detect.sh has 7 signal types but most produce nothing. The "pivot" signal produced 1 item in the current buffer. Self-report tags produced 2 entries. The majority of knowledge enters through MANUAL placement by agents during audit sessions.

### Graduation Rate (observations -> KB): 0%
- 7 observations in observations.md. Zero have graduated to kb-*.md through automated means.
- The pipe between observations and KB files does not exist as automated flow.

### Graduation Rate (Raw Log -> Graduated Patterns): ~75%
- 19 of ~26 original Raw Log entries graduated to Graduated Patterns (4 auto-clusters)
- 7 remain in Raw Log
- auto-graduate.sh is the most functional part of the pipeline

### Graduation Rate (Raw Log -> rules.jsonl): 100%
- sleep-agent.sh processes ALL Raw Log entries every session end
- 23 rules in rules.jsonl, all from 2026-02-28
- This is the ONLY path that works end-to-end automatically

### Injection Rate: ~60%
- rules.jsonl: 23 rules, injected at boot via inject-rules.sh (WORKING)
- kb-*.md: 5 files with ~50 rules, NOT injected at boot (BROKEN)
- CODEX Graduated Patterns: 13 patterns, NOT injected at boot (BROKEN)
- topics/: 9 topic files, injected at boot via context-loader.sh (WORKING)

### End-to-End: 1 session (via bypass)
- Discovery -> rules.jsonl -> injection: happens in 1 session cycle (sleep-agent at end, inject-rules at next start)
- Discovery -> observations -> KB -> Graduated Patterns -> Active Rules -> CLAUDE.md: **NEVER COMPLETES.** The full pipeline has never produced an end-to-end graduation.

---

## 6. The Real Pipeline vs. The Designed Pipeline

### What Was Designed (compound-learning-v2.md)
```
insight-detect -> buffer -> insight-broadcast -> CODEX Raw Log -> auto-graduate -> Graduated Patterns
                                              -> observations.md -> reviewer -> kb-*.md -> CLAUDE.md
```

### What Actually Works
```
insight-detect -> buffer -> insight-broadcast -> CODEX Raw Log -> sleep-agent -> rules.jsonl -> inject-rules
                                                               -> auto-graduate -> Graduated Patterns (dead end)
                                              -> observations.md (dead end, manually populated)

Manual placement by agents -> kb-*.md (orphaned, not boot-injected to most sessions)
Manual placement by agents -> CODEX Graduated Patterns (orphaned)
Manual rules -> WGH CLAUDE.md (the REAL source of truth, hand-maintained)
```

### The Functional Shortcut
The system that ACTUALLY works is a 3-node shortcut:
1. **Raw Log capture** (insight-detect + manual entry)
2. **sleep-agent.sh** (haiku synthesizes Raw Log -> rules.jsonl)
3. **inject-rules.sh** (rules.jsonl -> session boot context)

Everything else (observations, kb-*.md, Graduated Patterns, Active Rules, CLAUDE.md promotion) is either broken, orphaned, or manual-only.

---

## 7. Bottleneck Analysis

### Primary Bottleneck: No Reader for observations.md
The observations file is written to but never read by any automated process. It is a write-only append log. This single gap breaks the middle of the pipeline.

### Secondary Bottleneck: KB files not injected at boot
Even if observations graduated to kb-*.md, those files are not loaded by context-loader.sh. The compound-learning-v2.md design doc explicitly calls this out as Step 4 ("Extend context-loader.sh to include kb-*.md files"). Not yet built.

### Tertiary Bottleneck: No reviewer.sh
The design calls for a haiku-powered reviewer that synthesizes session dumps into structured findings. sleep-agent.sh partially fills this role for rules.jsonl, but the reviewer -> observations -> KB path doesn't exist. The reviewer was designed but never built.

---

## 8. Specific Fixes (Ordered by Impact)

### Fix 1: Wire KB files into context-loader.sh (30 min, $0)
Add `kb-global-rules.md` to EVERY session boot. Add domain-specific KB files based on CWD mapping. This immediately makes ~50 existing KB rules visible to agents.

```python
# Add to context-loader.sh
kb_dir = os.path.expanduser('~/.claude/knowledge_base')
# Always load global rules
global_kb = os.path.join(kb_dir, 'kb-global-rules.md')
if os.path.exists(global_kb):
    print(global_kb)
# Domain-specific
kb_mapping = {
    'whats-good-here': ['kb-ui-ux.md', 'kb-database.md', 'kb-backend.md'],
    '.claude/scripts': ['kb-agent-infra.md'],
}
```

### Fix 2: Add observations -> KB graduation to auto-graduate.sh (1 hour, $0)
After Phase C (decay), add Phase D: scan observations.md for entries with confidence >= 2, extract domain tag, write to kb-{domain}.md. Remove graduated entries from observations.md.

### Fix 3: Unify the two KB directories (15 min, $0)
Delete `~/.claude/memory/knowledge_base/kb-*.md` duplicates. Point auto-graduate.sh at `~/.claude/knowledge_base/` as the single source. Or symlink one to the other.

### Fix 4: Add Active Rules promotion to auto-graduate.sh (30 min, $0)
When a Graduated Pattern reaches 6+ confirmations, auto-write it to CODEX Active Rules section. Currently this is only flagged with a print statement.

### Fix 5: Guard 30-day decay with daily debounce (15 min, $0)
Write a `last-decay-date` file. Only run decay if it hasn't run today. Prevents multi-session-same-day over-decay.

### Fix 6: Build reviewer.sh (2 hours, ~$0.005/session)
The missing synthesis brain. Takes session dumps, calls haiku, routes findings to observations.md and contradictions.md. Already fully designed in compound-learning-v2.md.

---

## 9. Summary Verdict

The compound learning system has **working plumbing at the edges** (capture and injection) but a **hollowed-out middle**. The designed pipeline has 6 stages; only 3 actually function. The system works today because of a shortcut (sleep-agent.sh) that bypasses the entire confidence ladder.

| Component | Designed | Built | Running | Producing Output |
|-----------|----------|-------|---------|-----------------|
| insight-detect.sh | YES | YES | YES | YES (1 buffer entry) |
| insight-broadcast.sh | YES | YES | PARTIALLY | YES (7 CODEX entries) |
| observations.md | YES | YES | YES (writes) | NO (never read) |
| reviewer.sh | YES | NO | NO | NO |
| auto-graduate.sh | YES | YES | YES | YES (4 patterns) |
| kb-*.md injection | YES | NO | NO | NO |
| Active Rules promotion | YES | NO | NO | NO |
| CLAUDE.md promotion | YES | NO | NO | NO |
| sleep-agent.sh (bypass) | NO* | YES | YES | YES (23 rules) |
| inject-rules.sh | YES | YES | YES | YES (20 rules at boot) |

*sleep-agent.sh was not part of the original compound-learning-v2 design but is the only path that works end-to-end.

**The system is 50% built, 30% functional, and 0% end-to-end through the designed path.**

The irony: the system built to help agents learn from mistakes has its own learning gap -- the observations that identified these breaks (experiment 001, 002, and the crow/hawk/bear audits) are all sitting in observations.md with no automated path forward.

---

*Experiment conducted 2026-02-28 by research agent. Read-only -- no scripts were executed, no files were modified outside this report.*
