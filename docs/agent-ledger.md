# Agent ledger

Tokens are the harness's per-agent total (includes cache reads). Outcome: did the gate pass on
merge, and what did reviews find.

| Date | Agent | Model | Tokens | Outcome |
|---|---|---|---|---|
| 2026-11-01 | M0 setup and spike | Opus | 332K | Gate passed; spike confirmed on the Mac |
| 2026-11-01 | M1 storage | Opus | 406K | Gate passed; 1 flaky test fixed at merge |
| 2026-11-01 | UI design system | Sonnet | 135K | Gate passed |
| 2026-11-01 | M3 answer checker | Opus | 516K | Gate passed |
| 2026-11-01 | M4a engine | Opus | 445K | Gate passed; dependency pin conflict at merge |
| 2026-11-01 | Storage review | Opus | 289K | 9 real bugs (1 high), all fixed with tests |
| 2026-11-01 | Checker review | Opus | 481K | 74 false accepts + 2 false rejects, all fixed |
| 2026-11-01 | M2 cards and packs | Opus | 561K | Gate passed |
| 2026-11-01 | M4b diagnosis | Opus | 413K | Gate passed |
| 2026-11-01 | M5 queue | Opus | 513K | Gate passed; listed 7 spec gaps |
| 2026-11-01 | Storage schema v2 | Opus | 500K | Gate passed |
| 2026-11-01 | Engine/queue gaps | Opus | 404K | Gate passed; 6 gaps closed |
| 2026-11-01 | App wiring (bridge + UI) | Opus | 573K | Gate passed; WebKit focus bug found on the Mac afterwards |
| 2026-11-01 | Research: agent efficiency (2) | Sonnet | 438K | Fed the playbook revision |
| 2026-11-01 | Research: SRS gap audit (5) + report | Opus/Sonnet | ~1.9M | 8 bugs + 9 gaps vs Anki; 6 critical fixes |
| 2026-11-01 | Fit, clocks, memory | Opus high | 429K | All golden vectors matched; cross-impl error 3.9e-6 |
| 2026-11-01 | Grading paths and queue | Opus high | 475K | Stopped correctly on a wrong report number (Easy Days) |
| 2026-11-01 | M7 Anki import | Opus | 653K | Gate passed; 160 tests, renderer parity vs anki 26.9.3 |
| 2026-11-01 | Integrate fit + grading + Anki wiring | Opus high | 339K | Gate passed; 2 semantic merge breaks fixed; stopped correctly on a test it may not edit (learning replay) |
| 2026-11-01 | Anki card rendering and media | (not recorded) | 375K | Gate passed (Chromium); found cloze asterisks and unreachable tier-3 pack cards |
| 2026-11-01 | Study-screen fixes (wave9-ui) | Sonnet | 175K | Gate passed (Chromium); 4 fixes, 5 page tests + menu test |
| 2026-11-01 | Research: practice platforms | Sonnet | 325K | Teardown of ~20 platforms; Math Academy book read directly |
| 2026-11-01 | Research: gaokao and exam prep | Sonnet | 163K | Strong on methods; Zhihu/Baike blocked, follow-up spawned |
| 2026-11-01 | Research: skill trainers and SRS apps | Sonnet | 178K | Drop-off causes; Reddit blocked |
| 2026-11-01 | Research: science of practice | Sonnet | 299K | New nulls (interleaving, math testing effect) flagged |
| 2026-11-01 | Research: engineering process | Sonnet | 247K | SQLite WAL bug, notarization costs, agent test-editing risk |
| 2026-11-01 | Research: Asian practice tools | Sonnet | 245K | 15 ranked mechanics; mistake lifecycle, attempt labels, blueprints |
| 2026-11-01 | Research report writer | Opus | 426K | 24 mechanics + 8 engineering items, must/should/later; owner adopted must + should |
| 2026-11-01 | Spec update from the research (3 follow-ups) | Opus high | ~300K | Rev 107 -> 155; must+should folded in, Calc I-first timeline, slips match ADR-0014 |
| 2026-11-01 | Full review: spec and decisions | Opus | 432K | 10 High / 24 Medium / 34 Low findings; spec lagged its ADRs |
| 2026-11-01 | Full review: built system | Opus | 426K | 41 requirement rows sampled; 8 deviate, 3 not built; no in-app restore |
| 2026-11-01 | Research: engine decisions | Sonnet | 328K | Placement walk and credit switch defects found by simulation |
| 2026-11-01 | Research: diagnosis, feedback, photos | Sonnet | 379K | Tap + check kept; photos with AI not accurate enough |
| 2026-11-01 | Research: Anki and SRS inventory | Sonnet | 357K | 137 features; flashcard fidelity gaps |
| 2026-11-01 | Research: Asian exam tools | Sonnet | 285K | Printed retest papers, step marks, localization R1-R14 |
| 2026-11-01 | Research: UX, input, accessibility | Sonnet | 174K | WCAG 2.1.4 and 1.4.4 unmet; onboarding order |
| 2026-11-01 | Research: content and answer checking | Sonnet | 245K | Grader probes: intervals, simplified, holes; sampled audits |
| 2026-11-01 | Research: architecture | Sonnet | 279K | Bridge dispatcher runs private names; PanicException escapes |
| 2026-11-01 | Research: STEM beyond math | Sonnet | 230K | Seams for 1.0; physics in 1.1 |
| 2026-11-01 | Research: AI tutors | Sonnet | 326K | Supports the no-AI decision (RCT harms) |
| 2026-11-01 | Research: reach and platforms | Sonnet | 301K | Mac-only reach is small; web via Pyodide is the cheap path |
| 2026-11-01 | Full review report writer | Opus | 304K | 20 ranked defects, verdict map, plan |
| 2026-11-01 | Spec update from the full review | Opus high | ~535K | Rev 155 -> 261+; ~45 new requirements with release tags |
