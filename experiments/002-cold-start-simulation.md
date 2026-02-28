# Experiment 002: Cold Start Simulation

**Date:** 2026-02-28
**Agent:** Research agent (Opus 4.6)
**Objective:** Measure how effectively the compound knowledge system overcomes Claude's cold start problem.

---

## Methodology

### What was measured
1. **All files loaded at session startup** -- counted by character, converted to approximate tokens (1 token ~ 4 chars)
2. **Three real task scenarios** simulated against the startup context to measure coverage gaps
3. **Cross-file redundancy** tracked by identifying rules/facts that appear in multiple files
4. **Token efficiency** calculated as (useful tokens for a given task) / (total tokens loaded)

### File inventory
Every file was read in full. Files were categorized into four tiers:

| Tier | Description | Files |
|------|-------------|-------|
| T1 | Auto-loaded by Claude (CLAUDE.md + MEMORY.md) | 3 files |
| T2 | Instructed to read on startup (phone, shared-context, TODO) | 4 files |
| T3 | Knowledge base files (two duplicate directories) | 7 + 7 files |
| T4 | Conditional reads (PLAYBOOK, commons, topic index) | 4+ files |

---

## Data: Token Budget

### Character and Token Estimates

Estimates derived from line counts and content density of each file read during this experiment.

| File | ~Chars | ~Tokens | Tier |
|------|--------|---------|------|
| **~/.claude/CLAUDE.md** | 1,520 | 380 | T1-auto |
| **MEMORY.md** (project-scoped) | 1,340 | 335 | T1-auto |
| **whats-good-here/CLAUDE.md** | 4,480 | 1,120 | T1-auto |
| **phone-inbox.md** | 2,080 | 520 | T2-startup |
| **shared-context.md** | 1,800 | 450 | T2-startup |
| **TODO.md** (project-scoped) | 6,200 | 1,550 | T2-startup |
| **TODO.md** (global) | 780 | 195 | T2-startup |
| **kb-global-rules.md** (memory/) | 920 | 230 | T3-KB |
| **kb-ui-ux.md** (memory/) | 960 | 240 | T3-KB |
| **kb-database.md** (memory/) | 880 | 220 | T3-KB |
| **kb-backend.md** (memory/) | 720 | 180 | T3-KB |
| **kb-agent-infra.md** (memory/) | 1,240 | 310 | T3-KB |
| **contradictions.md** (memory/) | 280 | 70 | T3-KB |
| **observations.md** (memory/) | 3,600 | 900 | T3-KB |
| **kb-global-rules.md** (root/) | 1,080 | 270 | T3b-DUPE |
| **kb-ui-ux.md** (root/) | 680 | 170 | T3b-DUPE |
| **kb-database.md** (root/) | 640 | 160 | T3b-DUPE |
| **kb-backend.md** (root/) | 640 | 160 | T3b-DUPE |
| **kb-agent-infra.md** (root/) | 600 | 150 | T3b-DUPE |
| **contradictions.md** (root/) | 220 | 55 | T3b-DUPE |
| **observations.md** (root/) | 3,600 | 900 | T3b-DUPE |
| **PLAYBOOK-wgh.md** | 6,120 | 1,530 | T4-conditional |
| **active-work.md** | 440 | 110 | T4-conditional |
| **decisions.md** | 960 | 240 | T4-conditional |
| **kb-audit.md** | 5,520 | 1,380 | T4-conditional |

### Totals by Tier

| Tier | ~Tokens | % of Total | What it contains |
|------|---------|------------|------------------|
| T1 (auto-loaded) | 1,835 | 15% | Rules, structure, project identity |
| T2 (startup reads) | 2,715 | 22% | Phone inbox, shared state, TODO backlog |
| T3 (knowledge base) | 2,150 | 18% | Curated rules with confidence levels |
| T3b (duplicate KB) | 1,865 | 15% | EXACT DUPLICATES of T3 in second directory |
| T4 (conditional) | 3,260 | 27% | Playbook, audit, decisions |
| **GRAND TOTAL** | **~12,200** | 100% | |
| **De-duplicated total** | **~10,335** | 85% | Removing T3b duplicates |

### Category Breakdown (de-duplicated)

| Category | Tokens | % |
|----------|--------|---|
| Project rules + conventions | ~3,900 | 38% |
| Task backlog / TODO | ~1,745 | 17% |
| Knowledge base (curated rules) | ~2,150 | 21% |
| Session state (phone, agents, active work) | ~1,080 | 10% |
| Playbook (theories + gotchas) | ~1,530 | 15% |

---

## Finding 1: Redundancy Analysis

### Exact duplications found

**Between the two KB directories:**
The entire knowledge base exists in two locations:
- `~/.claude/memory/knowledge_base/` (7 files)
- `~/.claude/knowledge_base/` (7 files)

These are near-identical copies with minor formatting differences. This wastes ~1,865 tokens (15% of total budget).

**Within the KB + CLAUDE.md + PLAYBOOK:**
The following rules appear 3+ times across files:

| Rule | Appearances | Files |
|------|-------------|-------|
| ES2023+ ban (toSorted, .at, findLast) | 6 | CLAUDE.md, kb-global-rules x2, kb-ui-ux x2, PLAYBOOK |
| Hooks before early return | 5 | CLAUDE.md, kb-global-rules x2, kb-ui-ux x2, PLAYBOOK |
| className=layout / style=color | 5 | CLAUDE.md, kb-global-rules x2, kb-ui-ux x2, PLAYBOOK |
| 4-layer schema trace | 5 | CLAUDE.md, kb-global-rules x2, kb-database x2, PLAYBOOK |
| Logger over console.* | 4 | CLAUDE.md, kb-global-rules x2, kb-backend x2 |
| Don't abstract on first sighting | 3 | kb-global-rules x2, kb-agent-infra x2 |
| API pattern (createClassifiedError) | 4 | CLAUDE.md, kb-database x2, kb-backend x2 |
| Named export + default export | 3 | CLAUDE.md, kb-ui-ux x2, PLAYBOOK |
| schema.sql source of truth | 4 | CLAUDE.md, kb-database x2, PLAYBOOK |

**Estimated redundant tokens:** ~1,200 tokens of rule content repeated across non-duplicate files.

**Total redundancy: ~3,065 tokens (25% of total budget)**
- 1,865 from duplicate KB directory
- ~1,200 from same rules restated across CLAUDE.md, KB files, and PLAYBOOK

### Redundancy rate: 25%

---

## Finding 2: Noise Analysis

"Noise" = content loaded at startup that is rarely relevant to the active task.

| Content | Tokens | Why it's noise |
|---------|--------|----------------|
| Phone inbox (10 duplicate voicemails saying same commit hash) | ~400 | Same "branch main, commit 06d080e" repeated 10 times |
| Agent dispatch log (who joined #denis) | ~200 | Stale session state, not actionable |
| TODO items for unrelated projects (Guitar Practice, Algo VPN) | ~150 | Wrong project context |
| Completed TODO items (10 [x] entries) | ~300 | Historical, not actionable |
| Jitter patent details in TODO | ~200 | Highly specific, rarely needed |
| observations.md raw voicemail backfills | ~500 | Low-confidence findings, most from one day |
| contradictions.md (empty placeholder) | ~70 | No content |
| kb-audit.md (meta-analysis of the KB itself) | ~1,380 | Useful for this experiment, noise for real work |

**Estimated noise tokens: ~3,200 (26% of total budget)**

---

## Finding 3: Scenario Simulations

### Scenario A: "Fix a Safari CSS bug in WGH"

**Critical facts needed (15 items):**

| # | Fact | Covered? | Source |
|---|------|----------|--------|
| 1 | No ES2023+ methods (toSorted, .at, findLast) | YES (6x) | CLAUDE.md, KB, PLAYBOOK |
| 2 | className=layout, style=color split | YES (5x) | CLAUDE.md, KB, PLAYBOOK |
| 3 | CSS tokens: --color-* system | YES | CLAUDE.md, kb-ui-ux |
| 4 | Two themes: Appetite (light), Island Depths (dark) | YES | CLAUDE.md, PLAYBOOK |
| 5 | No hex colors in JSX | YES | CLAUDE.md, kb-ui-ux |
| 6 | Safari 15+ is the floor | YES | PLAYBOOK |
| 7 | MV tourists = older iPhones | YES | PLAYBOOK |
| 8 | ESBuild does NOT catch ES2023+ | YES | PLAYBOOK |
| 9 | Test on real Safari, not Chrome DevTools | YES | PLAYBOOK |
| 10 | Safari flex+gap bug (explicit width needed) | NO | Only in learned-rules, not in KB |
| 11 | Which CSS file to edit (src/index.css) | YES | CLAUDE.md |
| 12 | Component placement rules | YES | CLAUDE.md |
| 13 | Extract at ~400 lines | PARTIAL | CLAUDE.md mention, not in KB |
| 14 | Named + default export pattern | YES | CLAUDE.md, KB, PLAYBOOK |
| 15 | npm run build must pass before done | YES | CLAUDE.md |

**Coverage: 13/15 = 87%**
**Key gap:** Safari flex+gap bug (the most relevant Safari-specific CSS gotcha) is NOT in the loaded context. It lives only in learned-rules which aren't loaded.
**Noise for this task:** ~8,000 tokens of database/RPC/agent/TODO/phone content = irrelevant.
**Efficiency:** ~2,300 useful tokens / 10,335 total = **22% token efficiency**

---

### Scenario B: "Add a new RPC to the WGH schema"

**Critical facts needed (18 items):**

| # | Fact | Covered? | Source |
|---|------|----------|--------|
| 1 | Read schema.sql first | YES (5x) | CLAUDE.md, KB, PLAYBOOK |
| 2 | Trace 4 layers: schema > triggers > RPCs > api | YES (5x) | CLAUDE.md, KB, PLAYBOOK |
| 3 | p_ prefix inconsistency (geo=bare, entity=p_) | YES (3x) | CLAUDE.md, KB |
| 4 | Run in SQL Editor (doesn't auto-deploy) | YES (2x) | CLAUDE.md, KB |
| 5 | RETURNS TABLE cols become variables | YES | CLAUDE.md, kb-database |
| 6 | Always qualify column refs (tablename.column) | YES | CLAUDE.md, kb-database |
| 7 | ROUND() needs ::NUMERIC cast | YES | CLAUDE.md, kb-database (root) |
| 8 | API pattern: try/catch/createClassifiedError | YES (3x) | CLAUDE.md, KB |
| 9 | API file: one per domain (dishesApi, votesApi...) | YES | CLAUDE.md, kb-database |
| 10 | Hook pattern: useQuery wrapping | YES | CLAUDE.md |
| 11 | SET search_path = public for geo RPCs | YES | CLAUDE.md, shared-context |
| 12 | Test the RPC call after creation | YES | CLAUDE.md |
| 13 | Update SPEC.md if features changed | YES | CLAUDE.md |
| 14 | SECURITY DEFINER implications | NO | Not in any startup file |
| 15 | RLS interaction with new RPC | NO | Only mentioned as TODO, no rules |
| 16 | Where schema.sql lives (supabase/schema.sql) | PARTIAL | Implied but path not explicit |
| 17 | Trigger implications of new tables | YES | PLAYBOOK theory 1 |
| 18 | selectFields + .map() for table queries | YES | CLAUDE.md |

**Coverage: 15/18 = 83%**
**Key gaps:** SECURITY DEFINER behavior, RLS interaction rules, explicit file path for schema.sql.
**Noise for this task:** ~4,500 tokens of UI/CSS/phone/agent content.
**Efficiency:** ~3,200 useful tokens / 10,335 total = **31% token efficiency**

---

### Scenario C: "Dispatch and manage a team of 3 agents"

**Critical facts needed (14 items):**

| # | Fact | Covered? | Source |
|---|------|----------|--------|
| 1 | Use tmux with --dangerously-skip-permissions | YES | MEMORY.md, shared-context |
| 2 | agent-tmux.sh is the launcher script | YES | shared-context |
| 3 | Split send-keys text and Enter into separate calls | YES | MEMORY.md |
| 4 | Use -l flag for literal text | YES (3x) | MEMORY.md, kb-agent-infra, TODO |
| 5 | 2-3 agents max per call | YES | kb-agent-infra |
| 6 | PM dispatch pattern (one PM, workers via push) | PARTIAL | TODO mentions it, no details |
| 7 | Push: tmux > ring-file > Supabase (3 layers) | YES | shared-context |
| 8 | Agents register push_channel on boot | YES | MEMORY.md, shared-context |
| 9 | How to check who's online | YES | phone-inbox, shared-context |
| 10 | Team CLI commands (start/kill/list/push) | PARTIAL | shared-context mentions it |
| 11 | Agent naming convention (project-scoped IDs) | YES | kb-agent-infra |
| 12 | Haiku subagents for simple tasks | YES | CLAUDE.md |
| 13 | Code/architecture goes to Issues, not calls | YES | kb-agent-infra |
| 14 | How to push work to a running agent | PARTIAL | TODO says it's broken for idle agents |

**Coverage: 10/14 = 71%**
**Key gaps:** No concrete dispatch workflow documented (step-by-step). The PM dispatch pattern is mentioned as a TODO to "formalize" but never was. Push to idle agents is documented as broken.
**Noise for this task:** ~6,000 tokens of WGH app code rules, CSS, RPC details.
**Efficiency:** ~2,100 useful tokens / 10,335 total = **20% token efficiency**

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| **Total tokens loaded** | ~12,200 (raw), ~10,335 (de-duped) |
| **Redundancy rate** | 25% (3,065 tokens wasted on duplicates) |
| **Noise rate** | ~26% (3,200 tokens rarely relevant) |
| **Effective payload** | ~49% of loaded tokens are unique AND potentially useful |
| | |
| **Scenario A coverage** (Safari CSS) | 87% of critical facts |
| **Scenario A efficiency** | 22% of tokens useful |
| **Scenario B coverage** (New RPC) | 83% of critical facts |
| **Scenario B efficiency** | 31% of tokens useful |
| **Scenario C coverage** (Agent dispatch) | 71% of critical facts |
| **Scenario C efficiency** | 20% of tokens useful |
| | |
| **Average coverage** | **80%** |
| **Average efficiency** | **24%** |

---

## Key Findings

### What is working

1. **Project CLAUDE.md is the MVP.** At ~1,120 tokens, it covers 60-70% of critical facts for any WGH task. Dense, well-structured, high signal. This single file is doing most of the heavy lifting.

2. **PLAYBOOK-wgh.md adds genuine depth.** The "theories" framework (Data Contract, Boundary System, Safari Contract, Theme Contract) provides reasoning, not just rules. An agent that reads the PLAYBOOK understands WHY, not just WHAT.

3. **KB confidence levels are a good signal.** The 1/2/3 confidence system lets agents weigh rules appropriately. The format "[WHAT] -- [CONSEQUENCE]" is genuinely better than bare rules.

4. **Cross-scenario coverage is strong for the main project.** 80% average coverage means a cold-started agent gets most of what it needs for WGH tasks. The system IS working as a warm-up mechanism.

### What is wasted

1. **Duplicate KB directories waste 15% of budget.** `~/.claude/memory/knowledge_base/` and `~/.claude/knowledge_base/` contain near-identical files. One should be deleted or symlinked.

2. **6 rules appear in 3-6 places each.** ES2023 ban, hooks-before-returns, className-vs-style, 4-layer trace, logger rule, and schema source-of-truth are each restated across CLAUDE.md, KB global, KB domain, and PLAYBOOK. The PLAYBOOK versions add context (good), but the KB duplications between global and domain files are pure waste.

3. **Phone inbox is 80% duplicate voicemails.** 10 voicemails all containing "Branch: main. Last commit: 06d080e" is ~400 tokens of the same sentence. A dedup or "latest only" approach would cut this to ~50 tokens.

4. **Completed TODO items linger.** 10 checked-off items consume ~300 tokens of historical context that has zero bearing on current work. Archive completed items weekly.

5. **observations.md is ~900 tokens of raw backfill.** Most entries are from one day (2026-02-28) and include low-confidence findings about hall effect sensors, Chrome Web Store policies, and GAN spoofing costs. These are research notes, not operational context.

### What is missing

1. **No task-routing index.** MEMORY.md has a topic index but it points to `topics/` files that DON'T EXIST. The index promises routing ("When to pull: css, safari, components") but the destination files were never created. This is a broken pointer -- the system promises associative lookup but can't deliver it.

2. **Safari flex+gap bug not in KB.** The most actionable Safari CSS gotcha (explicit width needed on flex children) lives only in learned-rules, which isn't part of the startup load.

3. **No SECURITY DEFINER / RLS rules.** For a Supabase project, the startup context has zero guidance on when to use SECURITY DEFINER vs SECURITY INVOKER, or how RLS interacts with RPCs. This is a high-consequence gap.

4. **Agent dispatch workflow is undocumented.** Despite being used live, the PM dispatch pattern (how to brief workers, how to split tasks, how to collect results) exists only as a TODO to "formalize." A cold-started agent assigned to dispatch 3 workers would have to invent the workflow.

5. **No file-path cheat sheet.** Agents frequently need exact paths (where is schema.sql? where are API files? where is the test setup?). The project CLAUDE.md lists `src/api/` and `supabase/schema.sql` but many paths are implied rather than explicit.

---

## Recommendations

### Immediate (low effort, high impact)

1. **Delete one KB directory.** Pick `~/.claude/knowledge_base/` or `~/.claude/memory/knowledge_base/` and symlink the other. Saves 1,865 tokens instantly.

2. **Deduplicate KB domain files.** Remove the 6 rules that appear in both `kb-global-rules.md` and domain files. Domain files should say "See global rules" or add domain-specific detail only. Saves ~400 tokens.

3. **Archive completed TODOs.** Move `[x]` items to a `DONE.md` or delete them. Saves ~300 tokens, reduces visual clutter.

4. **Dedup phone voicemails.** Show only the latest voicemail per agent, or collapse identical messages. Saves ~350 tokens.

### Medium-term (moderate effort)

5. **Create the missing topic files.** MEMORY.md promises `topics/wgh-core.md`, `topics/brand-ui.md`, etc. but the directory is empty. Either create them or remove the index. A broken routing table is worse than no routing table -- it wastes time on reads that 404.

6. **Add the 14 missing rules to KB.** The kb-audit.md already lists them. Highest priority: Safari flex+gap, SECURITY DEFINER, RLS interaction, localStorage rules, .maybeSingle().

7. **Build a task-type router.** Instead of loading everything, have a lightweight index (200 tokens) that maps task types to file subsets:
   ```
   CSS/UI task -> CLAUDE.md + kb-ui-ux + PLAYBOOK theories 2,4
   Schema/RPC task -> CLAUDE.md + kb-database + PLAYBOOK theory 1
   Agent task -> CLAUDE.md + kb-agent-infra + shared-context
   ```
   This could bring token efficiency from 24% to 50%+ by loading only relevant slices.

8. **Write the agent dispatch playbook.** Document the PM dispatch pattern that was proven live: how to brief workers, task splitting conventions, result collection, error handling. This is the biggest coverage gap for the agent scenario (71%).

### Strategic (architectural)

9. **Separate "rules" from "state."** Current startup mixes timeless rules (ES2023 ban) with ephemeral state (who's online, last commit hash). These have different lifespans and should live in different tiers:
   - **Rules** (years): CLAUDE.md, KB files, PLAYBOOK
   - **State** (hours): phone inbox, active-work, branch/commit
   - **Backlog** (weeks): TODO.md

   Rules should be loaded always. State should be loaded only when the task involves coordination. Backlog should be loaded only when the user asks "what's next."

10. **Implement the confidence escalation pipeline.** observations.md and contradictions.md are both empty after 38+ sessions. The learning pipeline from observation -> pattern -> rule has never fired. The system currently only learns when a human manually edits CLAUDE.md. Fix the /end-session hook to actually write observations, and build the reviewer that promotes them.

---

## Conclusion

The compound knowledge system achieves **80% coverage** of critical facts for common tasks -- a meaningful improvement over a truly cold start (0%). However, it operates at only **24% token efficiency**, meaning 3 out of every 4 tokens loaded are redundant, noisy, or irrelevant to the active task.

The biggest wins are structural, not content:
- **Deduplication** would recover ~3,000 tokens (25% of budget)
- **Task-type routing** could double efficiency from 24% to 50%+
- **Separating rules from state** would let different tiers load on different triggers

The system's core design (CLAUDE.md as authoritative rules + PLAYBOOK as theories + KB as curated patterns) is sound. The problem is that everything loads for every task, redundancy has crept in across files, and the automated learning pipeline (observations -> patterns -> rules) has never actually run. The system warms up agents well but doesn't yet compound knowledge across sessions -- it's a static cache, not a learning loop.

**Bottom line:** You're at 80% coverage / 24% efficiency. Getting to 90% coverage / 50% efficiency requires dedup + routing + filling 3 specific gaps (Safari flex, SECURITY DEFINER, dispatch workflow). The token budget exists to do it -- it's just allocated poorly.
