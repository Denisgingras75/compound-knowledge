# Constitution

The simple version of compound knowledge, built from what [experiment 005](../experiments/005-graduation-replay.md) showed works. That's one rules file, written from real mistakes, approved by a human, and checked against the code.

| When | What happens |
|---|---|
| Every session starts | The approved articles that apply to that project go into the session's context |
| Every session ends | A curator reads the transcript in the background. It proposes at most 3 rules, and only for things Claude got wrong in your work. Proposals go to `PENDING.md`. |
| Weekly | `/constitution:review-rules`: you approve, edit or reject each proposal |
| Monthly | `/constitution:review-rules` → monthly check: which rules actually stopped their mistake |

Everything lives in `~/.claude/constitution/`:

| File | Contents |
|---|---|
| `RULES.md` | The amendment clause (yours to edit) and the articles |
| `PENDING.md` | Proposals waiting for review |
| `AMENDMENTS.md` | Every decision, with the reason |
| `curator.log` | What the curator did after each session |

## Install (on your Mac)

```bash
git clone -b ccr-d1803c5a-szza4y https://github.com/Denisgingras75/compound-knowledge ~/code/compound-knowledge
claude plugin marketplace add ~/code/compound-knowledge
claude plugin install constitution@compound-knowledge
```

Or, once this is merged to `main`:

```
/plugin marketplace add Denisgingras75/compound-knowledge
/plugin install constitution@compound-knowledge
```

It installs at user level, so every Claude Code session in every repo gets it.

It only adds hooks. Your existing ones (`inject-rules.sh`, `sleep-agent.sh`, …) keep running. Turn them off once you trust this.

## Options

| Environment variable | Default | What it does |
|---|---|---|
| `CONSTITUTION_DIR` | `~/.claude/constitution` | Where the files live. Point it at a clone of a private repo to sync across machines and cloud sessions. |
| `CONSTITUTION_MODEL` | `sonnet` | Model the curator uses. `haiku` is cheaper. |

Try the curator by hand on any past session. `--dry-run` prints the proposals and writes nothing:

```bash
python3 scripts/curate.py --transcript ~/.claude/projects/<project>/<session>.jsonl --cwd ~/code/wgh --dry-run
```

## Costs and limits

- **One curator call per session** with 2 or more prompts, using your own Claude account. It sends up to 80,000 characters of the transcript: your messages, Claude's replies and tool errors.
- **Claude Code only.** Claude app chats don't run hooks.
- **Cloud sessions** need `CONSTITUTION_DIR` on a synced repo, plus the plugin installed by the environment's setup script.
- **The monthly check only covers rules with a `check:` regex.** For the rest, judge from your own experience.
