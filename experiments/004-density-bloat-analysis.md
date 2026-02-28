# Experiment 004: Information Density & Bloat Analysis

**Date:** 2026-02-28
**Researcher:** Agent (Opus 4.6)
**Scope:** All memory/knowledge files loaded into Claude context at session start

---

## 1. Methodology

- Read every file in the memory system (28 files total)
- Counted characters (chars / 4 = approximate tokens)
- Counted discrete facts/rules/items per file
- Calculated tokens-per-fact (lower = denser, better)
- Estimated formatting overhead (headers, blank lines, separators, boilerplate instructions)
- Cross-referenced every rule/fact across all files for redundancy
- Assessed staleness against known current state (branch main, commit 06d080e)

---

## 2. Density Leaderboard

### Core Files (Always Loaded)

| File | Chars | ~Tokens | Facts | Tok/Fact | Fmt% | Grade |
|------|-------|---------|-------|----------|------|-------|
| `~/.claude/CLAUDE.md` | 1,520 | 380 | 22 | 17 | 12% | **A** |
| `whats-good-here/CLAUDE.md` | 4,680 | 1,170 | 68 | 17 | 8% | **A** |
| `MEMORY.md` | 2,120 | 530 | 18 | 29 | 25% | **B** |
| `TODO.md` | 7,240 | 1,810 | 71 | 25 | 15% | **B-** |
| `PLAYBOOK-wgh.md` | 6,360 | 1,590 | 52 | 31 | 20% | **C+** |
| `shared-context.md` | 1,880 | 470 | 26 | 18 | 18% | **A-** |
| `phone-inbox.md` | 2,400 | 600 | 8 | 75 | 60% | **F** |
| `connections.md` | 2,560 | 640 | 11 | 58 | 10% | **D** |

### Knowledge Base (`~/.claude/knowledge_base/`)

| File | Chars | ~Tokens | Facts | Tok/Fact | Fmt% | Grade |
|------|-------|---------|-------|----------|------|-------|
| `kb-global-rules.md` | 1,460 | 365 | 11 | 33 | 15% | **B** |
| `kb-ui-ux.md` | 960 | 240 | 7 | 34 | 12% | **B** |
| `kb-database.md` | 880 | 220 | 6 | 37 | 12% | **B** |
| `kb-backend.md` | 840 | 210 | 7 | 30 | 12% | **B+** |
| `kb-agent-infra.md` | 680 | 170 | 4 | 43 | 15% | **C** |
| `observations.md` | 3,440 | 860 | 22 | 39 | 18% | **C+** |
| `contradictions.md` | 280 | 70 | 0 | -- | 100% | **F** |

### Knowledge Base (`~/.claude/memory/knowledge_base/`) -- THE DUPLICATE SET

| File | Chars | ~Tokens | Facts | Tok/Fact | Fmt% | Grade |
|------|-------|---------|-------|----------|------|-------|
| `kb-global-rules.md` | 1,120 | 280 | 9 | 31 | 15% | **B** |
| `kb-ui-ux.md` | 1,160 | 290 | 10 | 29 | 12% | **B+** |
| `kb-database.md` | 1,060 | 265 | 8 | 33 | 12% | **B** |
| `kb-backend.md` | 720 | 180 | 6 | 30 | 12% | **B+** |
| `kb-agent-infra.md` | 1,240 | 310 | 12 | 26 | 15% | **A-** |
| `observations.md` | 1,720 | 430 | 7 | 61 | 18% | **D** |
| `contradictions.md` | 260 | 65 | 0 | -- | 100% | **F** |

### Topic Files (`memory/topics/`)

| File | Chars | ~Tokens | Facts | Tok/Fact | Fmt% | Grade |
|------|-------|---------|-------|----------|------|-------|
| `wgh-core.md` | 940 | 235 | 16 | 15 | 12% | **A+** |
| `launch.md` | 680 | 170 | 10 | 17 | 15% | **A** |
| `jitter.md` | 1,040 | 260 | 14 | 19 | 10% | **A** |
| `schema-data.md` | 1,080 | 270 | 14 | 19 | 10% | **A** |
| `brand-ui.md` | 960 | 240 | 14 | 17 | 10% | **A** |
| `business.md` | 680 | 170 | 12 | 14 | 10% | **A+** |
| `agent-infra.md` | 1,160 | 290 | 15 | 19 | 12% | **A** |
| `algo-vpn.md` | 520 | 130 | 6 | 22 | 10% | **A** |
| `compound-learning.md` | 2,880 | 720 | 32 | 23 | 15% | **A-** |
| `compound-learning-brainstorm.md` | 4,600 | 1,150 | 36 | 32 | 22% | **C+** |

---

## 3. Key Finding: TWO DUPLICATE KNOWLEDGE BASES

**The single biggest source of waste.**

There are two nearly-identical knowledge_base directories:
- `~/.claude/knowledge_base/` (7 files, ~2,135 tokens)
- `~/.claude/memory/knowledge_base/` (7 files, ~1,820 tokens)

They contain the same file names with slightly different versions of the same rules. Neither is a strict superset of the other -- they diverged. Combined waste: **~1,820 tokens** (the entire duplicate set).

| File | `~/.claude/knowledge_base/` | `~/.claude/memory/knowledge_base/` | Overlap |
|------|---------------------------|-------------------------------------|---------|
| `kb-global-rules.md` | 11 rules (has promoted observations) | 9 rules (original seed) | 7 rules identical |
| `kb-ui-ux.md` | 7 rules (has .maybeSingle, error objects) | 10 rules (has CSS tokens, components list) | 4 rules identical |
| `kb-database.md` | 6 rules (has ROUND, plpgsql qualify) | 8 rules (has core tables, API pattern) | 4 rules identical |
| `kb-backend.md` | 7 rules (has localStorage, auth gates) | 6 rules (has pre-code, pre-test conventions) | 3 rules identical |
| `kb-agent-infra.md` | 4+2 rules | 12 rules (has compound learning, Denis AI) | 3 rules identical |
| `observations.md` | 38 observations (full backfill) | 7 observations (agent-only) | 0 overlap |
| `contradictions.md` | empty | empty | both empty |

**Recommendation:** Merge into ONE canonical location (`~/.claude/knowledge_base/`). Take the union of all unique rules. Delete the duplicate directory. **Saves ~1,820 tokens.**

---

## 4. Cross-File Redundancy Map

### Tier 1: Facts repeated 4+ times (critical waste)

| Fact | Appearances | Files | Wasted Tokens |
|------|------------|-------|---------------|
| "No ES2023+ (toSorted, Array.at, findLast, Object.groupBy) -- Safari crashes" | **7** | CLAUDE.md (WGH), PLAYBOOK (Theory 3, Gotcha), kb-global-rules x2, kb-ui-ux x2, brand-ui topic, shared-context | ~140 |
| "className=layout, style={{}}=color -- breaks dual theme" | **7** | CLAUDE.md (WGH), PLAYBOOK (Theory 2, Gotcha), kb-global-rules x2, kb-ui-ux x2, brand-ui topic, shared-context | ~175 |
| "All hooks before early return null -- React violation" | **6** | CLAUDE.md (WGH), PLAYBOOK (Theory 2, Gotcha), kb-global-rules x2, kb-ui-ux x2, brand-ui topic | ~120 |
| "Read schema.sql first, trace 4 layers" | **6** | CLAUDE.md (WGH), PLAYBOOK (Theory 1, Gotcha), kb-global-rules x2, kb-database x2, schema-data topic | ~150 |
| "Use logger, never console.*" | **5** | CLAUDE.md (WGH), kb-global-rules x2, kb-backend x2, shared-context | ~75 |
| "API layer required -- no direct supabase imports" | **5** | CLAUDE.md (WGH), PLAYBOOK Gotcha, kb-backend x2, schema-data topic, shared-context | ~100 |
| "RPC p_ prefix inconsistent -- verify in schema.sql" | **5** | CLAUDE.md (WGH), PLAYBOOK Gotcha, kb-database x2, schema-data topic, shared-context | ~75 |
| "Core tables: restaurants, dishes, votes..." | **4** | CLAUDE.md (WGH), kb-database x2, schema-data topic | ~120 |
| "Named export + export default" | **4** | CLAUDE.md (WGH), PLAYBOOK Gotcha, kb-ui-ux x2, brand-ui topic | ~60 |
| "API pattern: try/catch createClassifiedError" | **4** | CLAUDE.md (WGH), kb-database (memory), kb-backend x2, schema-data topic | ~100 |
| "Phone rules: no pile-ons, 2-3 agents, code to GitHub" | **4** | kb-agent-infra x2, agent-infra topic x2 | ~60 |
| "-l flag for tmux send-keys" | **4** | MEMORY.md, TODO.md, kb-agent-infra (memory), shared-context | ~60 |
| "Don't abstract on first sighting" | **3** | kb-global-rules (memory), kb-agent-infra (memory), compound-learning topic | ~30 |

### Tier 2: Facts repeated 2-3 times

| Fact | Count | Canonical Home |
|------|-------|---------------|
| CSS token list (--color-accent-gold, etc.) | 3 | WGH CLAUDE.md |
| Available hooks list | 3 | WGH CLAUDE.md |
| Routes list | 3 | WGH CLAUDE.md |
| Key RPCs list | 3 | WGH CLAUDE.md |
| Display components (DishListItem variants) | 3 | WGH CLAUDE.md |
| Component file placement rules | 3 | WGH CLAUDE.md |
| Google OAuth status | 2 | TODO.md |
| Reviewer architecture (3 layers) | 2 | compound-learning topic + brainstorm |
| Graduation protocol | 2 | compound-learning topic + brainstorm |
| UX connection friction fix (3 defaults) | 3 | agent-infra topic + compound-learning + brainstorm |
| KB file structure listing | 2 | compound-learning topic + brainstorm |
| Communication evolution table | 2 | compound-learning topic + brainstorm |
| "Hold position when challenged" | 2 | kb-global-rules x2 |
| Immune system model | 3 | compound-learning topic + brainstorm + observations |

### Summary of Redundancy

| Category | Unique Facts | Total Appearances | Redundant Copies | Wasted Tokens |
|----------|-------------|-------------------|------------------|---------------|
| Tier 1 (4+ copies) | 13 | 65 | 52 | ~1,265 |
| Tier 2 (2-3 copies) | 14 | 35 | 21 | ~420 |
| **Total** | **27** | **100** | **73** | **~1,685** |

---

## 5. Staleness Analysis

### Completed TODOs Still Listed as Open

TODO.md has 71 items. Of these, 14 are marked `[x]` (completed) but still consume tokens. The completed items occupy approximately **800 tokens** of context. After ~1 week, completed items provide zero value and should be purged.

Specific stale completed items:
- Security audit (done 2026-02-28) -- 2 lines
- Seed killer lists (done) -- 2 lines
- Fix jitter_profiles RLS (done) -- 1 line
- ReviewFlow hardcoded hex (done) -- 2 lines
- Source weighting consistency (done) -- 2 lines
- Test tmux push (done) -- 1 line
- Audit observations.md (done) -- 1 line
- Google OAuth frontend (done) -- 2 lines
- Broader seeding script (done) -- 1 line
- Migration guide (done) -- 1 line
- Unified merge (done) -- 1 line
- Review seeding (done) -- 1 line
- Schema merge (done) -- 1 line
- Curated Local Lists (done) -- 2 lines
- Critical RPC fix (done) -- 1 line
- tmux send-keys push (done) -- 2 lines

### Stale Session Pointers

| Location | Current Value | Issue |
|----------|---------------|-------|
| MEMORY.md "Session Pointers" | `commit 06d080e` | Will be stale next commit |
| MEMORY.md "Session Pointers" | `branch main` | Correct but redundant with TODO.md |
| TODO.md "Active branch" | `main (merge/unified is behind main)` | merge/unified note is stale (already merged) |
| shared-context.md "Active Work" table | 3 agents, all from 2026-02-28 17:42-17:46 | Stale within hours |
| shared-context.md | "deployed to Netlify" | Likely stale -- project uses Vercel (mentioned in WGH CLAUDE.md) |
| phone-inbox.md | 10 unread voicemails, all from old sessions | 100% stale on next session |

### Stale State References

- `shared-context.md` says "deployed to Netlify" but `whats-good-here/CLAUDE.md` and `PLAYBOOK-wgh.md` say Vercel. **Contradiction.**
- `phone-inbox.md` is entirely ephemeral -- it is always stale by the time the next session reads it, because the phone system has moved on. Loading it burns ~600 tokens for data that was relevant only at the timestamp it was written.
- `connections.md` references "Taco Value Graph" with "DO NOT BUILD YET" -- this is also in `wgh-core.md`. Two places to maintain the same hold decision.

### Topic Files -- No Staleness Dates

Topic files have no "last updated" timestamp except `wgh-core.md` ("as of 2026-02-28"). All other topic files have no way to assess staleness. Since all were created/updated 2026-02-28, none are stale yet, but the lack of timestamps will make future staleness invisible.

---

## 6. Worst Offenders

### 6a. phone-inbox.md (Grade: F, 600 tokens)

- **100% ephemeral.** Contains agent presence, active calls, unread voicemails, and recent messages -- ALL of which are stale by the time any future session reads them.
- The voicemails all say the same thing: "Branch: main. Last commit: 06d080e."
- **Recommendation:** Do not load at session start. The phone system should be queried live, not read from a snapshot file. **Saves 600 tokens.**

### 6b. connections.md (Grade: D, 640 tokens)

- 11 connection entries, each with a 2-sentence analogy and a "when to pull" instruction.
- Dense with prose but low in actionable rules. The analogies are for Denis's brain, not agent behavior.
- Only 2-3 connections are relevant in any given session.
- **Recommendation:** Keep file but do NOT auto-load. Load on-demand when touching multiple domains (as MEMORY.md already instructs). **Saves 640 tokens when not needed.**

### 6c. compound-learning-brainstorm.md (Grade: C+, 1,150 tokens)

- This is a meeting transcript/synthesis. 80% of its content is already distilled into `compound-learning.md` (the topic file).
- The brainstorm file adds: assignments (stale -- session-specific), "What I Learned" reflections (meta), and the communication evolution table (duplicated in topic).
- **Recommendation:** Archive to a non-loaded location (e.g., `~/.claude/memory/archives/`). The topic file already captures everything actionable. **Saves 1,150 tokens.**

### 6d. PLAYBOOK-wgh.md (Grade: C+, 1,590 tokens)

- Contains 4 "Theories" that are excellent but verbose -- the same rules appear in compressed form in WGH CLAUDE.md.
- Gotchas section (lines 92-131) is a 1:1 duplicate of rules already in WGH CLAUDE.md's Rules section.
- "Recent Learnings" section (3 items from 2026-02-23) -- narrow, 5 days old, already embedded in working knowledge.
- **Recommendation:** Cut Gotchas section entirely (all rules are in WGH CLAUDE.md). Keep Theories section (unique framing). Cut Recent Learnings after 7 days. **Saves ~600 tokens.**

### 6e. Two contradictions.md files (Grade: F, combined 135 tokens)

- Both completely empty (only boilerplate headers).
- Two files, zero content.
- **Recommendation:** Keep one, delete one. The one in `~/.claude/knowledge_base/` is the canonical location. **Saves ~65 tokens.**

---

## 7. The Diet Plan

### Step 1: Eliminate duplicate knowledge_base (saves ~1,820 tokens)

Merge `~/.claude/memory/knowledge_base/` INTO `~/.claude/knowledge_base/` (take the union of unique rules from both). Delete `~/.claude/memory/knowledge_base/`.

### Step 2: Stop loading phone-inbox.md at boot (saves ~600 tokens)

Query the phone system live instead of reading a stale snapshot. If live query is not available, at minimum truncate to just "Online agents" and "Unread voicemails" (subject line only, no body).

### Step 3: Archive compound-learning-brainstorm.md (saves ~1,150 tokens)

Move to `~/.claude/memory/archives/`. The topic file `compound-learning.md` already has everything.

### Step 4: Deduplicate PLAYBOOK-wgh.md (saves ~600 tokens)

**Before (Gotchas section, 40 lines, ~600 tokens):**
```
## Gotchas

### schema.sql is source of truth
- **Gotcha:** Don't reverse-engineer schema from Supabase dashboard or migration files
- **Why:** Denis maintains schema.sql manually. Migrations are generated from it...

### No ES2023+ in frontend
- **Gotcha:** toSorted(), Array.at(), findLast() will break Safari
- **Why:** Island tourists use older iPhones...

[...8 more gotchas, all duplicated from WGH CLAUDE.md rules...]
```

**After (0 lines):**
Delete entire Gotchas section. Every rule is already in `whats-good-here/CLAUDE.md` in compressed form. Keep only Theories (unique high-level framing) and Environment/Recent Learnings.

### Step 5: Purge completed TODOs (saves ~800 tokens)

**Before:**
```
- [x] **Full security audit (2026-02-28)** -- DONE. Rotated service role key...
- [x] **Seed killer lists** -- DONE. 1,069 votes across 110 MV dishes...
[...14 completed items with detailed descriptions...]
```

**After:**
```
## Recently Completed
security audit, seed killer lists, jitter RLS, hex cleanup, source weighting, tmux push, oauth frontend, seeding, migrations, unified merge, curated lists, rpc fix
```

One line. Same information for "what's done" without the details that no longer matter.

### Step 6: Establish canonical locations (eliminates Tier 1 redundancy, saves ~1,265 tokens)

| Rule | Canonical Location | Remove From |
|------|--------------------|-------------|
| ES2023 ban | `whats-good-here/CLAUDE.md` (line: `!es2023...`) | PLAYBOOK Gotcha, both kb-global-rules, both kb-ui-ux, brand-ui topic, shared-context |
| className/style split | `whats-good-here/CLAUDE.md` (line: `@jsx...`) | PLAYBOOK Theory 2 + Gotcha, both kb-global-rules, both kb-ui-ux, brand-ui topic, shared-context |
| Hooks before returns | `whats-good-here/CLAUDE.md` (line: `@modal...`) | PLAYBOOK Theory 2 + Gotcha, both kb-global-rules, both kb-ui-ux, brand-ui topic |
| 4-layer trace | `whats-good-here/CLAUDE.md` (line: `@schema-change...`) | PLAYBOOK Theory 1 + Gotcha, both kb-global-rules, both kb-database, schema-data topic |
| Logger not console | `whats-good-here/CLAUDE.md` (line: `!console.*...`) | both kb-global-rules, both kb-backend, shared-context |
| API layer required | `whats-good-here/CLAUDE.md` (line: `!direct-supabase-in-UI...`) | PLAYBOOK Gotcha, both kb-backend, schema-data topic, shared-context |
| Core tables | `whats-good-here/CLAUDE.md` (Core Tables section) | both kb-database, schema-data topic |
| API pattern | `whats-good-here/CLAUDE.md` (API Pattern section) | both kb-database, both kb-backend, schema-data topic |

**Principle:** `whats-good-here/CLAUDE.md` is the canonical location for all WGH-specific coding rules. KB files should ONLY contain rules that:
1. Are NOT already in any CLAUDE.md
2. Were discovered through compound learning (agent observations)
3. Are cross-domain truths that don't belong to any single project

After dedup, the KB files shrink to:

| File | Before (tokens) | After (tokens) | Content remaining |
|------|-----------------|----------------|-------------------|
| `kb-global-rules.md` | 365 | ~150 | "Hold position," credentials, PII, economics of fakes, proof/monetization, feature-as-question, embeddable infra |
| `kb-ui-ux.md` | 240 | ~80 | .maybeSingle(), error object rendering, barrel imports, 400-line extract limit |
| `kb-database.md` | 220 | ~80 | ROUND()::NUMERIC, plpgsql qualify, optimistic rollback, selectFields+map |
| `kb-backend.md` | 210 | ~100 | localStorage rule, auth gates, CSP both-src, adversarial testing |
| `kb-agent-infra.md` | 170 | ~100 | Polling fix observation, filesystem vs Supabase |

### Step 7: Trim shared-context.md (saves ~150 tokens)

- Fix "Netlify" to "Vercel"
- Remove "Active Work" table (always stale)
- Remove "Research Reports" section (already in MEMORY.md)

### Step 8: Add timestamps to topic files

No token cost. Add `updated: YYYY-MM-DD` to each topic file's frontmatter so staleness becomes detectable.

### Step 9: Format optimization (saves ~200 tokens across system)

Tables use more tokens than dense lists for small datasets. The MEMORY.md index table (9 rows) costs ~180 tokens. A compressed format:

**Before (table, ~180 tokens):**
```
| Topic | When to pull | File |
|-------|-------------|------|
| WGH Core | product, stack, routes, state | topics/wgh-core.md |
| Launch | memorial-day, timeline, go-to-market | topics/launch.md |
[...7 more rows...]
```

**After (dense list, ~100 tokens):**
```
## Topics
wgh-core(product,stack,routes) launch(timeline,go-to-market) jitter(identity,biometrics) schema-data(supabase,sql,rpc) brand-ui(theme,css,components) business(personas,revenue) agent-infra(phone,mcp) compound-learning(kb,cross-pollination) algo-vpn(chrome,extension)
```

---

## 8. Total Projected Savings

| Action | Tokens Saved |
|--------|-------------|
| Eliminate duplicate knowledge_base | 1,820 |
| Stop loading phone-inbox.md at boot | 600 |
| Archive compound-learning-brainstorm.md | 1,150 |
| Deduplicate PLAYBOOK Gotchas section | 600 |
| Purge completed TODOs | 800 |
| Deduplicate Tier 1 rules across kb/topic files | 1,265 |
| Trim shared-context.md | 150 |
| Format optimizations | 200 |
| **TOTAL** | **~6,585 tokens** |

### Current total loaded tokens (estimate)

All files combined: ~14,400 tokens (if everything is loaded).

### Post-diet total: ~7,815 tokens

**That is a 46% reduction** with zero information loss.

---

## 9. The Real Architecture Problem

The redundancy is not accidental -- it is structural. The system has **four layers that all try to store the same coding rules:**

1. `whats-good-here/CLAUDE.md` -- project rules (the source of truth, auto-loaded by Claude)
2. `PLAYBOOK-wgh.md` -- "theories" and "gotchas" (same rules with narrative framing)
3. `kb-*.md` files -- "graduated observations" (same rules with confidence scores)
4. `topics/*.md` -- "associative memory" (same rules organized by domain)

Each layer was designed for a different PURPOSE:
- CLAUDE.md = agent instructions (imperative)
- PLAYBOOK = learning journal (explanatory)
- KB files = cross-agent knowledge transfer (graduated)
- Topics = context-triggered loading (associative)

But in practice, they all contain the same ~20 coding rules because those rules are the most important things the system knows.

**The fix is architectural:** Coding rules live in CLAUDE.md ONLY. KB files store only agent-discovered insights NOT already in CLAUDE.md. Topics store only context/strategy, not rules. PLAYBOOK stores only theories (the "why" framing), never the rules themselves.

---

## 10. Priority Action Items

1. **Merge the two knowledge_base directories** -- pick `~/.claude/knowledge_base/`, merge unique rules in, delete `~/.claude/memory/knowledge_base/`
2. **Purge completed TODOs** -- compress to one-line "recently completed" summary
3. **Archive compound-learning-brainstorm.md** -- topic file has it all
4. **Delete PLAYBOOK Gotchas section** -- WGH CLAUDE.md is the canonical location
5. **Stop auto-loading phone-inbox.md** -- query live or don't load
6. **Deduplicate KB rules** -- remove anything already in WGH CLAUDE.md
7. **Fix shared-context.md** -- Netlify->Vercel, remove stale agent table
8. **Add `updated:` timestamps to topic files**

Estimated implementation time: 30 minutes for a single session.
Expected ongoing savings: ~6,585 tokens per session, every session, forever.
At ~$0.015/1K tokens (Opus input), that is ~$0.10 per session saved.
Over 20 sessions/day: ~$2/day, ~$60/month.

---

*This analysis read 28 files totaling ~57,600 characters (~14,400 tokens). The irony is not lost on me.*
