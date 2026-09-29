# Experiment 005: Graduation Replay on Real History

**Date:** 2026-09-29
**Investigator:** Claude Code research session
**Data:** The WGH app repository (`Denisgingras75/WGH`): 1,314 non-merge commits from 2026-01-06 to 2026-06-02, 1,159 of them co-authored by Claude, and 32 revisions of its CLAUDE.md
**Code:** [`005-graduation-replay/`](005-graduation-replay/). Standard-library Python. `./run.sh PATH_TO_REPO` reruns everything in about 15 seconds.
**Question:** The "aspirational metrics" from `patterns/graduation-pipeline.md`. How many findings does the pipeline promote, how many decay away, and do promoted rules prevent repeat mistakes?

---

## Summary

1. **Rules in CLAUDE.md work, and they keep working.** For 9 rules a regex can check, commits made with the rule in their starting CLAUDE.md added violations far less often:
   - `console.*` went from 11.6% of commits to 1.3%, and zero in the last 527 commits.
   - `toSorted()` went from 0.7% to 0%, with 30 correct sorts written after the rule.
   - Tailwind color classes went from 14.0% to 0.4%.
   - Direct Supabase calls in UI code went from 3.6% to 0.3%.

   No lint rule or CI check enforced any of them. None was ever removed for going quiet.
2. **The one rule that failed was the one that fought the design.** "Never hardcode hex colors in components" changed nothing (12.0% → 10.6%) and was reversed after 29 days.
3. **Replayed on 901 real bug-fix observations, the documented pipeline promoted 41 findings, locked 20 and nominated 11 for CLAUDE.md. Only 12 of the 41 were real lessons (29%).** The rest were feature hotspots or unrelated fixes that shared words. The most-confirmed clusters were the least coherent: confidence tracked how much work happened in an area, not whether a lesson was true.
4. **Decay deletes the rules that work.** A rule that prevents its mistake stops producing the collisions that re-confirm it. Suppose every real violation is fed to the pipeline, the way a PostToolUse hook would catch it. The pipeline would then have deleted the `toSorted()` rule on Feb 23, a rule that had zero violations across 698 later commits. It would also have locked the hex rule that the humans threw out. In this design, confidence measures how often a rule is broken.
5. **The humans skipped the thresholds, and it worked.** WGH's rules came from audits, single incidents or design decisions, often written the same day as the fix. Under the 3-confirmation ladder, the two rules that were rarely or never broken before they were written (`toSorted()`, `Array.at()`) would never have locked, and `toSorted()` would have been deleted.

Also: experiment 003's decay bug (BREAK 8) barely matters. The 30-day silence window is what matters.

---

## 1. The data, and what it can't show

The pipeline's own files (`auto-graduate.sh`, `observations.md`, `rules.jsonl`, CODEX.md) live on Denis's machine. They are not in any of Denis's repositories this session could reach. So this experiment runs on the next best thing: the git history of WGH, the production app the theory was built on.

WGH is a clean natural experiment for one tier, CLAUDE.md:

- ESLint has no `no-console` or custom rules, and CI only runs `build` and `test`. The CLAUDE.md text was the only enforcement.
- Rules landed on known dates (git pickaxe on CLAUDE.md), at different times, so each rule can be checked against its own date.
- 88% of commits carry a `Co-Authored-By: Claude` trailer that names the model, so model changes can be controlled for.

What it can't show:

- **The lower tiers never ran on this repo.** Observations, kb files and `rules.jsonl` were a separate system on Denis's machine. Part B replays the documented rules over commit history. It does not run the real script on real pipeline files. `pipeline_events.py` is included so that replay can be run on the real files (section 9).
- **Commit messages stand in for raw-log entries**, and sessions are inferred: same author, no gap over 2 hours. Parallel sessions by one person merge into one, which makes independent confirmation harder, never easier.
- **Coherence labels are one reader's judgment.** They're in `coherence_labels.json` so anyone can disagree line by line.

---

## 2. Part A: did locked rules prevent repeat mistakes?

**Method** (`scan_violations.py`, `rules.json`)

- For every commit, read the CLAUDE.md in its parent commit, which is the file the session started from, and ask whether it contained the rule.
- Count violations in the lines the commit added, minus matches it removed. Moving code around doesn't count as a new mistake.
- Also count the right way to do the same thing (`logger.error(`, `.slice().sort(`, `var(--color-`), so that zero violations can be told apart from zero opportunities.
- Skip four commits that bulk-copy code: a squash-import of 67 commits written in another repo, and three SQL consolidations or dumps. They're listed in `rules.json` with the reason for each.

| Rule | In CLAUDE.md | Commits adding a violation, without → with the rule | Right way / wrong way, with the rule | Risk ratio (95% CI) |
|---|---|---|---|---|
| No `toSorted()` / ES2023 array methods | Jan 24 | 0.7% → 0% (2/297 → 0/698) | 30 / 0 | 0.09 (0.00–1.77) |
| No `Array.at()` | Jan 24 | 0% → 0% | 6 / 0 | never violated |
| `logger`, never `console.*` | Jan 25 | 11.6% → 1.3% | 290 / 23 | 0.11 (0.06–0.23) |
| `localStorage` only via `storage.js` | Jan 24 | 3.0% → 0.6% | 24 / 6 | 0.19 (0.06–0.61) |
| No Supabase calls in components/pages/hooks | Jan 20 | 3.6% → 0.3% | – | 0.08 (0.01–0.37) |
| No Tailwind color classes | Feb 1 | 14.0% → 0.4% | 2,709 / 3 | 0.03 (0.01–0.11) |
| **Never hardcode hex in components** | **Feb 7, reversed Mar 8** | **12.0% → 10.6%** | **1,555 / 322** | **0.88 (0.58–1.34)** |
| Never render `{error}` directly | Jan 24 | 2.2% → 0.5% | 16 / 3 | 0.22 (0.06–0.86) |
| `.maybeSingle()` over `.single()` (soft) | Feb 1 | 2.3% → 0% | 6 / 0 | 0.04 (0.00–0.69) |
| `ROUND()` needs `::NUMERIC` (soft) | Feb 1 | 50% → 23.5% | 31 / 43 | 0.47 (0.24–0.93) |

"Soft" rules have a regex that counts candidates, not confirmed violations. `.single()` is correct when the row must exist, for example. Restricting to Claude co-authored commits gives the same picture, slightly stronger: `console.*` 12.2% → 0.6%. Full tables are in [`results/violations.md`](005-graduation-replay/results/violations.md).

### The drops happen on each rule's own date

Rules landed on different dates, so a rule's effect should show up at its own date, not whenever the codebase happened to mature. Share of commits adding a violation, per window between rule changes (bold = rule in force):

| Rule | → Jan 20 | Jan 20–24 | Jan 24–25 | Jan 25–Feb 1 | Feb 1–7 | Feb 7–Mar 8 | Mar 8 → |
|---|---|---|---|---|---|---|---|
| `console.*` | 11.1% | 11.1% | 13.0% | **5.9%** | **0%** | **0%** | **0%** |
| `localStorage` | 3.9% | 2.8% | **0%** | **2.4%** | **0%** | **0%** | **0%** |
| `toSorted()` | 0% | 2.8% | **0%** | **0%** | **0%** | **0%** | **0%** |
| Tailwind colors | 28.7% | 8.3% | 6.5% | 3.5% | **0%** | **0.8%** | **0%** |
| `.single()` | 3.3% | 2.8% | 2.2% | 1.2% | **0%** | **0%** | **0%** |

`console.*` sat at 11–13% until its rule, then fell to zero. All 9 commits that broke it with the rule loaded fell on Jan 25–27, mostly debug logging during a radius bug hunt, and 5 of them carry no Claude trailer. After Jan 27 there were none. Tailwind colors and `.single()` were already falling before their rules. For Tailwind, the color-token migration had started on Jan 14. Both rules partly codified a change already underway, so their risk ratios overstate what the text itself did.

### Confounders

- **Model upgrades.** Sessions ran Opus 4.5 until Feb 2 and Opus 4.6 from Feb 7. The January rules can be checked within Opus 4.5 alone:
  - `console.*`: 12.3% → 2.3%
  - Supabase calls in UI code: 3.5% → 0%
  - rendering `{error}`: 2.2% → 0%
  - `toSorted()`: 0.8% → 0%
  - `localStorage`: 3.3% → 1.1%

  The Feb 1 rules (Tailwind, `.single()`) land exactly on the model change. Opus 4.5 made only 5 commits after them, so their effect can't be separated from the model's.
- **Cleanups.** Most rules came with, or were followed within days by, a sweep that removed existing violations. `682e60a` documented `logger` and resolved ESLint warnings the same day. `6d84874` replaced hardcoded colors across 32 files a week after the color rule. Later sessions then copied clean code. What's measured is rule plus cleanup, not rule text alone.
- **Untestable rule.** The migration-rollback rule (Apr 17) had zero migrations after it.

### The failure

The hex rule was broken in 27 of the 255 commits that could see it. In that month, sessions wrote 1,555 CSS-variable uses and 322 lines with raw hex colors. The top three values were:

- `#1A1A1A`, the black borders and shadows of the new neo-brutalist look: 22%
- `#FFFFFF`: 19%
- `#E4440A`, the brand's own primary color from the CLAUDE.md token table: 14%

On Mar 8 the rule was rewritten to "Hex is fine for one-off colors." This is the "evolving convention" case from `models/trust-decay.md`. People handled it by editing the rule. Section 4 shows the pipeline would have done the opposite.

---

## 3. Part B: replaying the graduation pipeline on real bug fixes

**Method** (`git_events.py`, `replay.py`)

- 292 fix commits became 901 observations: one per bullet in the commit body, plus the subject line.
- All commits were grouped into 133 sessions, with one pipeline run at the end of each.
- The observations were replayed through the rules as the docs describe them:
  - keywords are words of 4+ characters, minus stopwords
  - entries are related when they share 3+ keywords
  - confidence 2 needs 2 independent sessions; confidence 3 (locked) needs 3+ sessions and 30 days alive; CLAUDE.md candidates need 6+ sessions
  - decay runs at every SessionEnd
- `auto-graduate.sh` isn't available, so this is a reimplementation from the docs. Decay runs under three readings:

| | As built: decay can fire every run (003, break 8) | 30-day window: once per 30 silent days |
|---|---|---|
| Observations | 901 | 901 |
| Findings | 604 | 601 |
| Seen once, never again | 524 (87%) | 524 (87%) |
| Reached 2 (confirmed) | 44 | 41 |
| Reached 3 (locked) | 19 | 20 |
| CLAUDE.md candidates | 9 | 11 |
| Dropped by decay | 580 | 577 |
| ...after reaching 2 | 20 | 17 |
| Median days to confirmation / to lock | 5.5 / 31 | 6 / 31 |

Dropping singletons is the garbage collector doing its job. Most one-off fixes, like a copy change or a one-time data fix, should be forgotten.

### Were the promoted findings real lessons?

Every finding that reached confidence 2 was read in full and labeled (`coherence_labels.json`):

| Stage (30-day window) | Lesson | Situational | Hotspot | Noise |
|---|---|---|---|---|
| Reached 2 (41) | **12** | 4 | 8 | 17 |
| Locked (20) | **5** | 0 | 8 | 7 |
| CLAUDE.md candidate (11) | **4** | 0 | 3 | 4 |

- **Lesson:** one root cause a future session could act on.
- **Situational:** true once, fine to forget.
- **Hotspot:** the same feature, but different causes.
- **Noise:** shared words, not a cause.

The biggest clusters were the worst:
- **Search, 50 observations from 22 sessions:** search bugs from January to April, with many different causes. It locked on Feb 24 and became a CLAUDE.md candidate the same day. There is no rule in it.
- **38 observations from 27 sessions:** held together by words like *page*, *restaurant* and *error*.

Keyword overlap with single linkage snowballs. Every generic word a cluster collects makes the next unrelated fix more likely to join, and each join from a new session counts as independent confirmation. So confidence ends up measuring activity, not truth.

It also can't tell agreement from disagreement. "Enable `-webkit-overflow-scrolling`" and, a week later, "Remove deprecated `-webkit-overflow-scrolling`" confirmed each other.

### What it found that humans didn't write down

Some real lessons the replay promoted never made it into CLAUDE.md:
- **Don't nest interactive elements** (a button inside a button): 5 sessions, Jan 16 to Apr 12.
- **DROP before changing a function's RETURNS TABLE shape:** hit on Apr 9 and again on Apr 13.
- **Escape LIKE wildcards in search queries.**
- **Clean up listeners and timers in `useEffect`.**
- **Keep images under the PWA precache limit.**

### What decay threw away

As built, decay dropped 7 of the 12 lessons, and some came straight back:

- **Nested buttons:** dropped Feb 28, then recurred on Mar 23, Mar 29 and Apr 12.
- **RETURNS TABLE:** dropped Mar 29, then recurred on Apr 9 and Apr 13.
- **"Show `error.message`, never the error object":** dropped Feb 25. This is the human rule that took violations to near zero.

Under the 30-day window, 5 lessons were dropped and the first two survived long enough to lock.

Of 7 findings that re-learned a dropped one, 2 were real recurrences. A bottom-sheet modal was fixed to be centered on Jan 22 and again on Apr 7. Duplicated constants were fixed on Jan 24 and again on Apr 16, despite CLAUDE.md's "Don't duplicate constants". The other 5 were keyword coincidences.

---

## 4. Part C: would the pipeline have written the rules that worked?

**Method** (`rule_lifecycle.py`)

`graduation-pipeline.md` lists PostToolUse hooks as an entry point, for detecting hex in JSX, `console.log` and ES2023+. So give the pipeline perfect hooks: every commit that added a violation is a sighting of that rule, matched exactly, with no keyword guessing. Then replay the ladder and decay over the real sessions.

| Rule | Human rule | Sessions that broke it first | Pipeline confirmed | Pipeline locked | Deleted: as built / window |
|---|---|---|---|---|---|
| `toSorted()` | Jan 24 | 2 | Jan 23 | **never** | **Feb 23 / Mar 25** |
| `Array.at()` | Jan 24 | 0 | **never** | never | – |
| `console.*` | Jan 25 | 13 | Jan 11 | Feb 7 | – |
| `localStorage` | Jan 24 | 7 | Jan 14 | Feb 12 | – |
| Supabase in UI | Jan 20 | 5 | Jan 12 | Feb 7 | – |
| Tailwind colors | Feb 1 | 23 | Jan 7 | Feb 7 | – |
| **Hex in components** | Feb 7 (reversed Mar 8) | 39 | Jan 12 | **Feb 7** | – |
| Rendering `{error}` | Jan 24 | 5 | Jan 14 | Feb 7 | – |
| `.single()` | Feb 1 | 11 | Jan 12 | Feb 7 | – |

- **With exact detection, the pipeline is faster than the humans on common mistakes.** It confirmed Tailwind colors on Jan 7, while the human rule came on Feb 1.
- **The `toSorted()` rule dies.** Two sessions broke it, the rule stopped it, and nothing was left to re-confirm it. The pipeline would have deleted it on Feb 23. Under the human rule it had 30 correct uses and zero violations in 698 commits. This is the "true but rare" case from `trust-decay.md`. The escape hatch there is to reach confidence 3, but a rule that works stops the sightings that would get it to 3.
- **`Array.at()` is never born.** Nobody broke it, so there was nothing to learn from. The humans wrote it from knowledge.
- **The hex rule locks.** It was broken constantly, so it was confirmed constantly. The pipeline would have locked on Feb 7 the rule the humans rewrote a month later.

**Rules that work go quiet and decay. Rules that fail keep being "confirmed" and lock.** The immune-system model counts a collision as confirmation. Once a rule is loaded, a collision means the rule failed.

---

## 5. Part D: what does decay cost in repeat mistakes? (a model)

History shows only one world: the rules humans wrote. `counterfactual.py` builds a second one from measured rates.

**How the model works**

- It uses the real commits that touched each rule's files, in their real sessions, with a pipeline run at every real SessionEnd.
- Each commit breaks the rule at random. It uses the rate measured without the rule when the rule isn't injected, and the rate measured with it when it is (confidence 2 or higher).
- Each break is a hook sighting.
- The numbers are means over 500 seeded runs.

**Assumptions:**
- Injection at confidence 2 works as well as CLAUDE.md did.
- Violations are independent from commit to commit.

Expected commits that add a violation over the whole history:

| Rule | No rule | Human rule | Pipeline, as built | Pipeline, window | Pipeline, no decay | Times it deleted a promoted rule (as built / window) |
|---|---|---|---|---|---|---|
| `toSorted()` | 6.7 | 2.5 | 3.7 | 3.2 | 2.6 | 0.84 / 0.18 |
| `console.*` | 115.3 | 44 | 14.7 | 14.7 | 14.7 | 0 / 0 |
| `localStorage` | 30.2 | 13 | 7.5 | 7.4 | 7.4 | 0.05 / 0 |
| Supabase in UI | 32.4 | 8 | 5.4 | 4.8 | 4.5 | 0.4 / 0 |
| Tailwind colors | 138.9 | 69 | 6.3 | 6.2 | 6 | 0.08 / 0 |
| Hex in components | 105.6 | 102 | 93.8 | 93.8 | 93.8 | 0 / 0 |
| Rendering `{error}` | 19.8 | 9 | 6.2 | 6 | 5.9 | 0.16 / 0 |
| `.single()` | 22.8 | 11.5 | 4.9 | 3.6 | 3 | 0.93 / 0 |

- **Detection speed dominates.** The humans wrote most rules two to four weeks into the project, and a hook-fed pipeline confirms a mistake at its second session. For Tailwind colors, that's about 6 violating commits against 69.
- **Decay costs little on common rules and bites on rare ones.** Common rules keep being re-confirmed. The pipeline deletes `toSorted()` and `.single()` about once each, costing roughly one extra violation per rule over four months. For `toSorted()`, one violation means a crash on Safari before version 16. The 30-day-window reading cuts those deletions by about 5x.
- **The catch.** A detector hook only exists for a mistake someone already understands, and once you can write the hook you can write the rule. For mistakes nobody understands yet, the pipeline has the free-text path from section 3, at 29% precision.

---

## 6. BREAK 8 revisited

Experiment 003 warned that decay without a daily debounce would "aggressively decay [observations] to 0." At WGH's real cadence the two behaved the same. At 20 runs a day, closer to 20+ sessions a day (`--runs-per-day 20`):

| | As built (every run) | Daily debounce | 30-day window |
|---|---|---|---|
| Median days silent before a confirmed finding is deleted | 30.1 | 30.3 | 60.1 |
| Confirmed findings deleted | 24 | 24 | 17 |

The debounce buys about five hours, because decay only starts once a finding has been silent for 30 days. After that, one decrement or two makes little difference. What matters is the length of the window, and what counts as re-confirmation.

---

## 7. What the humans actually did

- **Growth:** CLAUDE.md grew from 52 lines (Jan 20) to 95 (Jan 24) to 453 (Feb 26), and was 464 lines at the end. By then it had 30 non-negotiables and 9 forbidden actions. 9 of its 32 revisions landed on Feb 1.
- **Sources were audits, single incidents and design decisions.** The first CLAUDE.md (Jan 20) already had "No direct Supabase calls" as an architecture principle.
  - `88d4359` (Jan 24): "Document rules learned from codebase cleanup audit"
  - `b50197a` (Feb 1): "Add error handling rules based on audit findings"
  - 37 commits mention an audit.
  - `toSorted()` and `[object Object]` were fixed in `5ab4263` and became rules the same day. The ambiguous `dish_id` fix (`a4e9504`) became a rule the same day (`f4b6f78`).
  - A fresh session sweeping the codebase did the job the confirmation threshold was meant to do.
- **Nothing was removed for going quiet.** One rule was rewritten because the design changed.
- **Rules doubled as review checklists.** An Apr 15 review fixed bare column references "per CLAUDE.md §1.5" (`c43f618`).
- **What they missed:** nested interactive elements, and DROP before changing a function's shape. Both recurred and neither became a rule.

---

## 8. What to change in the theory

1. **Count compliance as re-confirmation.** A rule's "right way" showing up in new code is evidence the rule is alive: 290 `logger` calls, 30 `.slice().sort()` calls. Decay a rule when the thing it names disappears from the codebase (the file, function or pattern it references is gone), not when it goes quiet.
2. **Treat "broken while loaded" as failure, not confirmation.** A rule violated in 10% of the commits that can see it should go to the contested path in `graduation-pipeline.md` for human review, not to locked.
3. **Allow one-strike graduation for crash-class findings, with human review.** That's how the rules with perfect records here were made.
4. **Cluster on root causes, not words.** Have the session that fixes a bug write the `When [trigger] → Do [action]` line at fix time and cluster on the trigger. Or match on code identifiers (`toSorted`, `maybeSingle`, `RETURNS TABLE`) instead of common words. Experiment 006 could rerun this replay with both matchers and the same labeling method.
5. **Keep auditing.** Periodic fresh-session sweeps produced WGH's rules, and they also catch violations of existing ones.
6. **BREAK 8 can wait.** Change the window and the re-confirmation signal instead.

---

## 9. Run it yourself

The WGH numbers:

```bash
git clone https://github.com/Denisgingras75/WGH ~/code/wgh
cd experiments/005-graduation-replay && ./run.sh ~/code/wgh
```

The real pipeline files, on the machine that has them:

```bash
python3 pipeline_events.py ~/.claude/memory/knowledge_base/observations.md path/to/CODEX.md \
    --out results/pipeline_events.jsonl
python3 replay.py --events results/pipeline_events.jsonl --out results/pipeline --classes none --labels none
```

The adapter reads the formats documented in this repo. If the real files differ, adjust its two patterns.

Another repo with a CLAUDE.md: edit `rules.json`. `anchor` is text that marks the rule in CLAUDE.md, `pattern` is the violation, and `compliant` is the right way.

Git history is the longest record most projects have. Claude Code's local transcripts are pruned after 30 days by default.

---

## 10. Verdict

The top of the hierarchy works. A rule written into CLAUDE.md after one incident or one audit held for months, with no decay and no confirmation count. The machinery underneath has the right parts but the wrong signals:
- keyword overlap confirms activity, not truth
- decay reads the silence of a working rule as irrelevance
- confidence rises fastest for the rules that fail

Swapping those signals means counting compliance, decaying on reference rot, and treating violations-while-loaded as contest. Then the pipeline would do automatically what the WGH team did by hand.

---

*Experiment run 2026-09-29. Read-only against WGH; no scripts from the real pipeline were run. Every number above is in [`005-graduation-replay/results/`](005-graduation-replay/results/) and regenerates with `./run.sh`.*
