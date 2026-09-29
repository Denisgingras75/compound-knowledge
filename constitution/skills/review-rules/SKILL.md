---
name: review-rules
description: Review proposed rules for Denis's constitution (approve, edit or reject each one), or run the monthly check on existing rules. Use when Denis says review rules, review proposals, check my rules, or runs /constitution:review-rules.
---

# Review the constitution

The constitution lives in `${CONSTITUTION_DIR:-~/.claude/constitution}`:

- `RULES.md`: the amendment clause and the approved articles. Every Claude Code session loads the articles.
- `PENDING.md`: proposals the curator wrote after past sessions.
- `AMENDMENTS.md`: a log of every decision.

Read `RULES.md` in full first. Follow its amendment clause. Never edit the amendment clause yourself.

## Reviewing proposals

1. Read `PENDING.md`. If it is empty, say so and offer the monthly check.
2. Go through the proposals with Denis, a few at a time. For each one, show:
   - the rule
   - its scope
   - the evidence
   - your one-line recommendation, flagging anything that is general knowledge, a one-off, a duplicate of an existing article, or in conflict with one
3. Ask Denis for a decision on each: approve, edit, or reject. Only Denis decides.
4. For each approved rule, append it to `## Articles` in `RULES.md` using the next free id:

   ```
   ### A007 · global
   When X → do Y — because Z
   - added: YYYY-MM-DD · from: project · check: `regex`
   ```

   - Use `· project: NAME` for project scope.
   - Keep the check regex if it is useful, and suggest one when the mistake can be spotted in code.
5. Remove every decided proposal from `PENDING.md`.
6. Log each decision in `AMENDMENTS.md` as `YYYY-MM-DD · approved|edited|rejected · <rule> · <reason>`.

## Monthly check

1. Ask Denis which repos to check.
2. Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check.py" REPO...
   ```

3. For any article marked NOT WORKING, propose a rewording or a repeal, and let Denis decide.
4. Also flag articles whose files, functions or tools no longer exist in those repos.
5. Log every change in `AMENDMENTS.md`.

Keep the articles short. If there are more than about 40, suggest merging overlaps.
