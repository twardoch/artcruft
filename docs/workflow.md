---
this_file: docs/workflow.md
---

# How agents work on mcruft

One **controller** session (Claude Code, Opus) owns the plan, writes briefs, reviews, and commits.
**Implementers** and **reviewers** are bounded, disposable workers. At most two run at once
(AGENTS.md).

## Roles and where they run

| Role | Default worker | When |
|---|---|---|
| Research with web search | `codex` via the codex-delegate relay, `--web-search live --network-access` | library/ecosystem surveys |
| Research on local sources | Claude subagent (Sonnet) | reading `../vendors/storytold/repos/<app>/`, running `<app>-cli` |
| Implementation | `codex` relay (workspace-write) or Claude subagent (Sonnet) | one task from `PLAN.md` per dispatch |
| Task review | Claude subagent (Sonnet; Opus for design-heavy diffs) or `codex --read-only` | after every implementation task |
| Design and final review | Opus (controller or subagent) | `SPEC.md` changes, whole-branch review |
| Deep research | `gdr` (Google Deep Research), `nlm` (NotebookLM) | multi-source questions; free under subscription |

Avoid `gemini-api` (billed per token) and pay-per-use MCP search servers unless nothing else works.

## The loop (per task in PLAN.md)

1. **Brief.** Extract the task to a file:
   `bash <superpowers>/subagent-driven-development/scripts/task-brief PLAN.md N`, which writes to
   `.superpowers/sdd/PLAN/`, a git-ignored workspace. Add what the worker cannot know: interfaces
   from earlier tasks, rulings, and the gate commands. Workers see only the brief.
2. **Dispatch.**
   - Codex: `node ~/.claude/skills/codex-delegate/scripts/relay.mjs --brief brief.txt --cd "$PWD"`,
     run in the background. Add `--read-only` for reviews and `--session <thread>` for follow-ups.
   - Claude: an Agent call with an explicit `model`, a report-file path, and "do not commit, do
     not spawn agents".
3. **Review.** Build a review package with `scripts/review-package PLAN.md BASE HEAD` and give it
   to a reviewer that did not write the code. Re-run the gates yourself; never trust a worker's
   "tests pass".
4. **Fix loop.** Send open Critical/Important findings back to the same worker (up to 3 rounds),
   then to a fresh, stronger one (up to 5 rounds in total). Minor findings go to the ledger.
5. **Land.** The controller commits, with one logical change per commit and the
   `Co-Authored-By` trailer. Codex never commits; its sandbox cannot reliably write `.git`.
6. **Ledger.** Append `Task N: complete (commits a..b, review …)` and every `Ruling:` to
   `.superpowers/sdd/PLAN/progress.md`. After a compaction, trust the ledger and `git log` over
   memory.

## Gates

```bash
uv sync --all-packages
uv run ruff check . && uv run ruff format --check .
uv run pytest -q                 # engine tests skip when <app>-cli is not installed
```

Tests that call real ArtCraft CLIs write only under `tmp_path`. MCP tests pass `--headless` and
an `--automation-write-root` inside `tmp_path`.

## Release

1. Update `CHANGELOG.md`, tag `vX.Y.Z` (hatch-vcs derives versions).
2. `uv build --all-packages` for the pure wheels; `uv run python tools/bundle_cli.py <product>` for
   per-architecture bundled wheels (macOS arm64 and x86_64).
3. Push to GitHub. PyPI uploads need an explicit owner decision; the bundled wheels carry
   third-party binaries and need NOTICE review first.
