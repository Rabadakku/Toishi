# How agents are used on this project

Agreed with the student on 2026-11-01 and revised the same day after research into Claude Code's
agent controls and published multi-agent practice (notes in the coordinator's
research_notes/agent-efficiency/). Goal: an app that works correctly, built with the most
quality per token.

## What the evidence says

- Multi-agent work costs several times the tokens of one agent; it pays off for independent,
  well-specified pieces, isolated context and fresh-eyes review — not for splitting one task by
  role. Coding parallelizes less well than research. (Anthropic engineering posts.)
- The biggest quality lever is a verifier the builder cannot fool: tests it did not write or
  cannot edit, an oracle (a reference implementation or CAS), and held-out checks. Visible tests
  saturate; hidden tests expose gaps.
- Fresh reviewers find real bugs (here: 74 false accepts in the checker for ~480K tokens, 9
  data-safety bugs in storage for ~290K) but LLM reviewers also reject correct code, so every
  finding must come with a failing test.
- Token use for the same task varies about 2x between runs; expensive runs mostly re-read files
  and redo edits. Long-lived agents with large contexts dominate cost (every turn re-reads context).
- Sonnet 5.5 is close to Opus 5.5 on coding benchmarks at half the price, and subscription plans
  meter Opus and Sonnet separately, so routing well-specified work to Sonnet also spreads load.
- Effort defaults to medium on current models; high helps edge-case-heavy work; max overthinks.

## Roles

- **Coordinator** (one session): plans, writes briefs, owns acceptance tests for critical pieces,
  merges sequentially, runs the full checks, syncs a git bundle to the Mac, tests the built app.
- **Builders**: one per independent piece, each in its own worktree with a disjoint set of files.
- **Reviewers**: fresh context, critical code only; each finding ships with a failing test.

## Routing

| Work | Model | Effort |
|---|---|---|
| Design decisions, spec gaps, merges | Opus (coordinator) | default |
| Correctness-critical algorithms: grader, FSRS/engine, storage, migrations, importers | Opus | high when edge-case heavy |
| Reviews of the above, oracle/differential testing | Opus | high |
| Well-specified implementation with tests given (UI wiring, screens, stats, scripts) | Sonnet | default (medium) |
| Doc lookups, research of settled facts | Sonnet | default |
| Mechanical bulk work (reformatting, dedup flags, summarizing logs) | Haiku | default |

## Brief template (every agent)

1. Goal in one paragraph; the exact files/dirs it owns; what is out of scope.
2. What to read: named spec sections and files (never the whole spec).
3. Done = a named command passes (e.g. `./scripts/check.sh fast`) plus listed acceptance tests;
   report the command's last lines as evidence.
4. Stop rules: after 2 failed fixes of the same failure, stop and report the diagnosis. If the
   spec is ambiguous, report `BLOCKED: <question>` instead of guessing. If a test you didn't write
   seems wrong, report it — never edit or weaken it. Minimal diffs; no refactors outside scope.
5. Token hygiene: grep and read line ranges; quiet test runs (`-q -x`, failures only); no pasting
   large outputs; no "double-check everything" passes.
6. Report ≤ 300 words: status, evidence, deviations, open questions.

## Process rules

1. Code over judgment: correctness comes from tests, oracles and computer algebra.
2. Acceptance tests first for critical work, written or approved by the coordinator; builders
   may add tests but not edit those.
3. 3–5 agents at a time, disjoint files, sequential merges with `./scripts/check.sh full`.
4. ADR numbers: take the next free number on main at merge time; the coordinator renumbers on
   collision.
5. Ledger: record each agent's model, tokens and outcome (gate passed, bugs found) in
   `docs/agent-ledger.md`; stop reviews that stop finding bugs.
6. Real-machine testing: the coordinator syncs main to the Mac, starts `scripts/mac-run.sh`
   through the runner (write a mode to `.runner/requests/<unique id>` in the linked folder, then
   poll `.runner/status` until `state=done`; read `logs/mac-run.log`), tests the built app in the
   background and records findings in `docs/backlog.md`. Never sync while `state=running`.
