# Engineering process and checklists for a small, high-reliability, offline macOS learning app built by AI agents (Toishi)

Scope note: facts below are what the cited pages said when fetched on 2026-11-01. "Inferences" are my own adaptations to this project (Python+SQLite+FSRS+SymPy, Svelte in WKWebView via pywebview, PyInstaller, no CI service, AI agents plus a product owner who reviews behavior, not code).

---

## 1. First-principles problem definition: stakeholders, goals, constraints, success metrics (including how to measure that learning improves)

### Takeaway
Separate two kinds of success: (a) "the software is correct" (verification: built right), which can be driven to near-zero-defect with testing, and (b) "the student learns more" (validation: right product), which can only be measured with calibration, retention and delayed-test data and honestly cannot be proven causally from a single user. The FSRS benchmark's metrics (log loss, RMSE-by-bins, AUC, with baselines and a train-on-old/test-on-new split) are a ready-made, sourced way to measure scheduler calibration from the app's own review logs.

### Cited Findings
- NASA defines verification as checking that the end product conforms to its specified requirements ("Was the end product realized right?") and validation as checking that it does what the customer intended in its operating environment ("Was the right end product realized?") — [NASA SE Handbook 5.3 Product Verification](https://www.nasa.gov/reference/5-3-product-verification/)
- NASA says the verification approach should be tailored to the project (project type, risk classification, cost/schedule, design heritage or reuse), and treats verification as complete only when there is documented objective evidence of compliance (or an approved waiver) and all discrepancy reports are closed — [NASA SE Handbook 5.3](https://www.nasa.gov/reference/5-3-product-verification/)
- A meta-analysis of practice testing (Adesope, Trevisan, Sundararajan 2017, Review of Educational Research) concluded that practice tests are more beneficial for learning than restudying and all other comparison conditions; effect sizes varied with test features, participant/study characteristics, outcome constructs and methodology. The abstract page I could reach gave no numeric effect sizes — [WSU record of "Rethinking the Use of Tests"](https://rex.libraries.wsu.edu/esploro/outputs/journalArticle/Rethinking-the-Use-of-Tests-A/99900601154801842)
- The open-spaced-repetition benchmark evaluates schedulers with three metrics: Log Loss (distance of predicted recall probability from the 0/1 outcome, lower is better), AUC (discrimination, higher is better) and RMSE (bins) (reviews grouped by interval length, review count and lapse count; compares mean predicted vs observed recall per bin, weighted by sample size). The README says "Log Loss and RMSE (bins) measure calibration" while AUC measures discrimination, so a model can have high AUC and poor calibration — [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)
- In that benchmark (10k-user dataset, no same-day reviews) FSRS-6 scored Log Loss 0.3460, RMSE(bins) 0.0653, AUC 0.7034. A constant-prediction baseline (AVG) scored 0.3945 / 0.1034 / 0.4997, and a MOVING-AVG baseline scored 0.3369 / 0.05915 / 0.7001, i.e. the simple moving-average baseline beat FSRS-6 on Log Loss. FSRS-7 variants score better than FSRS-6 (e.g. 0.3401 / 0.0634 / 0.7167 for base FSRS-7) — [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)
- The benchmark warns that a method called RMSE-BINS-EXPLOIT has the lowest RMSE(bins) but "is not a real predictor; it games the metric", and evaluates with TimeSeriesSplit (older reviews train, newer reviews test) — [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)
- The benchmark README is internally inconsistent about dataset size (results tables use ~10k users; the dataset section also mentions a 20k-user, ~1.7B-review dataset) — [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)
- py-fsrs (the Python scheduler): default 21 model weights ("leave at defaults unless familiar with optimization"), `desired_retention` default 0.9 (higher means more reviews), optional optimizer (`pip install "fsrs[optimizer]"`) whose results may differ slightly from Anki's, `get_card_retrievability()` returns the probability a card is currently remembered, `ReviewLog` records each review, all datetimes must be UTC, `enable_fuzzing` adds random interval jitter so scheduling is then not deterministic — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)
- The awesome-fsrs index lists py-fsrs, fsrs-rs and ts-fsrs as FSRS-6 schedulers (several other languages v4/v5), with FSRS-6 as the highest version the page names — [awesome-fsrs](https://github.com/open-spaced-repetition/awesome-fsrs). The benchmark, however, already reports FSRS-7 — [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)
- PyPI shows `fsrs` 6.3.2 (released August 9, 2026), MIT license, Python 3.10+; the page does not say whether it implements FSRS-6 or FSRS-7 — [PyPI fsrs](https://pypi.org/project/fsrs/)
- Apple states there is no developer program specifically for students; membership is not required to learn app development (relevant to constraints on distribution) — [Apple Program Enrollment help](https://developer.apple.com/help/account/membership/program-enrollment/)

### Inferences
**Stakeholders (small table to keep in the repo as `docs/stakeholders.md`):**
- Product owner / first user (a student; non-coder; validates by using the app). Needs: trust that answers are graded right, nothing lost, minimal friction.
- Future students (unknown Macs, unknown skill, possibly Intel, possibly VoiceOver users). Needs: install works, safe, accessible, free, honest about what it does.
- Content licensors/authors (open-source problem banks). Needs: attribution, license compliance.
- AI coordinator and implementer/reviewer agents. Needs: unambiguous specs, machine-checkable "done".
- Future maintainer (the owner in 2 years, or an AI with no memory of today). Needs: decision records, traceability, reproducible build steps.
- Apple/platform (Gatekeeper, notarization, macOS updates). Constraint source.

**Goals/non-goals, one page, each goal with a measurable criterion:**
1. Never lose or corrupt study progress (metric: zero acknowledged reviews lost in crash/restore tests; restore drill passes every release).
2. Grade correctly or say "cannot tell" (metric: zero known false-positive grades on the oracle corpus; false-negative rate below a stated bound; every bug becomes a corpus entry).
3. Schedule correctly and calibrated (metric: golden vectors identical to a reference FSRS implementation; observed retention within a tolerance of desired retention over a rolling window; RMSE(bins) on real logs reported next to the baselines).
4. Be learnable and usable without help (metric: think-aloud task success rate, SUS trend).
5. Be safe to run and install (metric: threat-model mitigations each have a negative test; notarized or documented unsigned install).
6. Non-goals: no accounts, no cloud sync, no telemetry, no multi-user DB, English-only, nothing below high-school algebra.

**Constraints to write down (they drive process choices):** Mac only; offline; no CI service so every gate is a script run on the Mac; shipped content must be open-licensed; the product owner reviews behavior, not code (so acceptance evidence must be observable behavior and plain-language reports); agents have token budgets (strongest model for accuracy-critical modules, cheaper models for tagging/verification); the project has no budget beyond its existing tools — this directly conflicts with the $99/yr needed for Developer ID (see Question 10).

**Measuring "does it improve learning" — layered, honest design:**
- Layer A, scheduler calibration (cheap, automatic, from the app's own review log): predicted retrievability at review time vs observed recall, binned (copy the srs-benchmark RMSE(bins) idea), plus Log Loss and AUC, always shown next to AVG and MOVING-AVG baselines (the benchmark shows a baseline can beat a scheduler on Log Loss, so the baseline row is part of the honest report). Evaluate only on reviews after the training window (TimeSeriesSplit idea), never on the data used to fit parameters. With one student the number of reviews is small, so keep default FSRS weights (py-fsrs advice) and use the metric as a drift/regression alarm rather than for tuning.
- Layer B, retention check: "of reviews that came due at predicted retrievability near 90%, did ~90% succeed?" Report per course. A persistent gap is a scheduling/grading bug signal before it is a learning signal.
- Layer C, delayed-retention probes (within-subject): randomly assign a subset of items per chapter to be "held out" from app scheduling (practiced only via the textbook), then compare both sets in a delayed quiz (1–4 weeks). Item-level randomization inside one student gives far more statistical power than comparing semesters. This is the only design here that can support a causal sentence, and only for that student.
- Layer D, course outcomes (pre/post, exam grades): report but do not over-interpret (single student, confounded by class, instructor, effort). Pre-register the comparison in a short note before the semester so it can't be cherry-picked.
- Layer E, calibration of the learner's own confidence (optional UI: "how sure are you?" before reveal): Brier score over time shows whether the student's self-assessment improves; useful because it is cheap and measures metacognition.
- For future users: no telemetry; offer an optional "export anonymized study report" file the student may choose to share. This keeps the offline/privacy promise.
- Be explicit in docs about the evidence level: "retrieval practice and spacing are well supported in research; this app implements them; we have not run a controlled trial."

### Gaps
- I did not find sourced guidance on N-of-1 / single-case designs for educational software, nor numeric effect sizes (the Adesope page gave only the qualitative conclusion). Layers C–E above are my design, not sourced practice.
- py-fsrs/awesome-fsrs say v6 while the benchmark has FSRS-7; I could not determine whether any released Python package implements FSRS-7. Pinning a specific algorithm version/parameter set is therefore a decision to record.
- Spacing-effect meta-analyses (e.g., Cepeda et al.) were not retrieved in this pass; presumably covered by the learning-science researcher.

---

## 2. Requirements engineering: ISO/IEC/IEEE 29148 essentials, verifiable requirements, acceptance criteria, lightweight traceability

### Takeaway
Write a short set of EARS-style "shall" requirements, each singular and verifiable, each with an ID, a risk class, a verification method (test/analysis/demonstration/inspection) and the test IDs that prove it; keep the traceability matrix as a machine-checked file so agents can't claim "done" without evidence.

### Cited Findings
- ISO/IEC/IEEE 29148 lists nine characteristics for an individual requirement: Appropriate, Complete, Conforming, Correct, Feasible, Necessary, Singular, Unambiguous, Verifiable; the standard also specifies characteristics for requirement sets — [arXiv 2408.10886, Table I and text](https://arxiv.org/pdf/2408.10886) (secondary source; the standard itself is paywalled, see [SFS store listing](https://store.sfs.fi/en/ieee-29148-2018))
- INCOSE-derived definitions (the article does not cite 29148): Necessary (essential capability, would leave a deficiency if removed), Singular (one capability/constraint), Conforming (follows an approved pattern/style), Appropriate (level of detail matches level of abstraction), Correct (accurately represents the stakeholder need), Unambiguous (one interpretation), Complete (stands alone), Feasible (within cost/schedule/technical/legal limits at acceptable risk), Verifiable (realization can be proven). Set-level: complete, consistent (no conflicts/overlaps, one meaning per term, consistent units), feasible as a set, comprehensible, able to be validated — [ArgonDigital summary of INCOSE characteristics](https://argondigital.com/blog/product-management/communicating-requirements-effectively-requirement-characteristics)
- EARS (Easy Approach to Requirements Syntax), developed at Rolls-Royce by Alistair Mavin and colleagues and first published in 2009, has six templates: Ubiquitous "The <system> shall <response>"; Event-driven "When <trigger>, the <system> shall <response>"; State-driven "While <precondition(s)>, the <system> shall <response>"; Unwanted behaviour "If <trigger>, then the <system> shall <response>"; Optional feature "Where <feature is included>, the <system> shall <response>"; Complex (combination) — [Mavin, EARS](https://alistairmavin.com/ears/)
- NASA records verification results in a requirements compliance/verification matrix tracing each product requirement to its verification evidence; reports include each requirement with bidirectional traceability, the method used, and results including pass/fail and discrepancies — [NASA SE Handbook 5.3](https://www.nasa.gov/reference/5-3-product-verification/)
- NASA's four verification methods: Analysis (models/simulation), Demonstration (basic confirmation of performance), Inspection (visual examination of product/documentation), Test (instrumented use under controlled conditions) — [NASA SE Handbook 5.3](https://www.nasa.gov/reference/5-3-product-verification/)
- Anthropic's Claude Code guidance: the most useful specs "are self-contained: they name the files and interfaces involved, state what is out of scope, and end with an end-to-end verification step"; provide verification criteria (example test cases) rather than vague asks; "have one Claude write tests, then another write code to pass them" — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

### Inferences
**Lean requirements package (all plain text in the repo, versioned):**
1. `docs/requirements.yaml` (or one Markdown file per area). Fields per requirement: `id` (REQ-GRD-001 style: GRD grading, SCH scheduling, DAT data, IMP import, SEC, UX, ACC, PRF, REL release, LIC), `text` (EARS), `rationale` (one line), `risk` (Critical / Important / Normal, from the FMEA), `verify` (T/A/D/I), `tests` (list of test IDs), `status`.
2. Definition of "done" for a requirement: it passes the 9-characteristic checklist (an agent can run this as a review prompt — the arXiv paper evaluates LLMs on exactly these nine characteristics, though with a 70B model and no claim that it replaces humans), has at least one automated test or an owner-observable demonstration script, and appears in the matrix.
3. Acceptance criteria live next to the requirement as concrete examples (inputs → expected outputs). For grading: a table of (key, student input, expected verdict). For scheduling: golden vectors. For UX: owner-run steps with expected observations.
4. Traceability script `scripts/trace_check.py` (about 60 lines): tests carry a marker such as `@pytest.mark.req("REQ-GRD-004")`; the script fails if (a) a Critical/Important requirement has no test or demonstration entry, (b) a test cites an unknown REQ, (c) a requirement marked `verified` has a currently failing test. Output is a Markdown matrix the coordinator pastes into the release evidence file. This is the lightest thing that still gives bidirectional traceability as NASA describes.
5. Keep the set small: perhaps 60–120 requirements for v1. Requirements for "wow" features that can't be verified should be dropped or converted to non-binding goals.

**Seed requirements (examples to show the tone):**
- REQ-GRD-001 When the student submits an answer, the app shall mark it correct only if it is equivalent to an accepted key under the problem's declared equivalence mode; if equivalence cannot be decided, the app shall report "needs review" and shall not mark it correct. (T: oracle corpus, property tests, mutation floor)
- REQ-DAT-001 When a review is graded, the app shall have durably committed the review log before presenting the next card. (T: crash-kill loop)
- REQ-DAT-002 If the app terminates abnormally, then on next launch the app shall open with every previously acknowledged review present. (T)
- REQ-DAT-003 Before any schema migration or app update, the app shall write a verified backup. (T, I)
- REQ-SCH-001 The app shall compute due dates with the pinned FSRS version and parameters such that, for the golden review sequences, results equal those of the reference implementation. (T)
- REQ-SEC-001 The app shall not execute script from imported content or let imported content reach the Python bridge. (T negative tests)
- REQ-PRF-001 On the reference Mac, the app shall show an interactive first card within a stated budget; answer-to-next-card latency p95 under a stated budget. (T)
- REQ-ACC-001 All functions shall be operable by keyboard alone (WCAG 2.1.1). (D + automated focus-order test)

**Common ambiguity traps to resolve in requirements, because they cause grading bugs:** is `^` power or XOR; implicit multiplication (`2x`, `2(x+1)`); `1/2x`; degrees vs radians; interval vs inequality notation; units; "equivalent" meaning exact vs numeric tolerance; domain restrictions (is `(x²-1)/(x-1)` equal to `x+1`?). Each should be an explicit per-problem `equivalence_mode` field.

### Gaps
- The text of ISO/IEC/IEEE 29148:2018 itself is paywalled; I relied on a secondary paper for the nine characteristics and on INCOSE-derived article text for definitions. The article explicitly does not mention 29148, so its definitions are INCOSE's, which align by name with the nine in the paper but are not verified clause by clause.
- No retrieved source for acceptance-test syntax (Given/When/Then) — I recommend plain input→output tables instead.

---

## 3. Quality model: ISO/IEC 25010 characteristics and which matter here

### Takeaway
Use the 2023 edition's nine characteristics as a checklist of "what could go wrong", then weight them: functional correctness, reliability (recoverability), security (integrity), and interaction capability (user error protection, inclusivity) are first-class here; performance, compatibility and flexibility matter in bounded ways.

### Cited Findings
- ISO/IEC 25010:2023 product quality model has nine characteristics with 40 sub-characteristics: Functional Suitability (Completeness, Correctness, Appropriateness), Performance Efficiency (Time Behavior, Capacity, Resource Utilization), Compatibility (Co-Existence, Interoperability), Interaction Capability (Appropriateness Recognisability, Learnability, Operability, User Error Protection, User Engagement, Inclusivity, User Assistance, Self Descriptiveness), Reliability (Faultlessness, Fault Tolerance, Availability, Recoverability), Security (Confidentiality, Integrity, Non-Repudiation, Accountability, Authenticity, Resistance), Maintainability (Modularity, Reusability, Analysability, Modifiability), Flexibility (Testability, Adaptability, Scalability, Installability, Replaceability — note this page files Testability under Flexibility; I could not confirm that placement against the standard), Safety (Operational Constraints, Risk Identification, Fail Safe, Hazard Warning, Safe Integration) — [arc42 Quality Model page for ISO 25010](https://quality.arc42.org/standards/iso-25010). The page marks Interaction Capability as "formerly Usability" and Flexibility as "formerly Portability"; it does not describe the 2011 structure or say Safety is new.

### Inferences
Priority and "what done looks like" per characteristic (one line each in `docs/quality.md`):
- **Functional correctness (Critical).** Done: oracle corpus passes; mutation survivors in grader/scheduler reviewed; zero known wrong-grade defects. Method: property tests + oracle corpus + differential golden vectors.
- **Functional completeness/appropriateness (Important).** Done: each v1 requirement demonstrated by owner script. Method: owner UAT checklist.
- **Reliability: faultlessness, fault tolerance, recoverability (Critical).** Done: kill-loop and restore drill pass; migrations tested from every released schema. Method: scripts in Question 6.
- **Security: integrity, resistance (Critical for imported content).** Done: each STRIDE threat has a mitigation and a negative test. Method: Question 7.
- **Interaction capability: user error protection, learnability, inclusivity (Important).** Done: think-aloud rounds completed; WCAG items in Question 8 checked; answer-entry shows parsed interpretation before grading. Method: 3 rounds x 5 users + keyboard/VoiceOver pass.
- **Performance efficiency: time behavior (Important), capacity (Normal).** Done: budgets in Question 9 met on reference data volumes.
- **Maintainability/Flexibility: analysability, modifiability, testability, installability (Important, because agents maintain it).** Done: small modules with typed interfaces, ADRs, a one-command verify script, install test on a clean macOS user account.
- **Compatibility: interoperability (Normal).** Anki import/export fidelity tested on sample decks; co-existence = does not interfere with other apps (own Application Support folder, no global state).
- **Safety (map loosely).** Not physical safety, but "fail safe": when the grader or importer is uncertain it must fall back to the non-harmful state ("needs review", quarantine the import) rather than guess. "Hazard warning": warn before destructive actions.

### Gaps
- I did not obtain the ISO standard text or per-characteristic definitions; only a third-party summary of the list. The arc42 page puts Testability under Flexibility and leaves it out of Maintainability; I reproduced it as shown, but it may be a summarization artifact, so check the standard before quoting that placement.

---

## 4. Risk and hazard analysis: FMEA for data loss, wrong grading, wrong scheduling; scoring and tracking

### Takeaway
Do a one-day FMEA now and keep it as a living table, but score with a severity-dominant rule (the modern "Action Priority" idea) instead of multiplying Severity x Occurrence x Detection, and make "Detection" literally "which automated test layer would catch this".

### Cited Findings
- FMEA (AIAG-VDA 2019 flow): plan/prepare, structure analysis, function analysis, failure analysis (modes, effects, causes, current controls), risk analysis (rate S, O, D; compute RPN or determine AP), optimization (actions, owners, dates, re-rate), results documentation kept updated as the system changes — [Reliamag FMEA guide](https://reliamag.com/guides/how-to-perform-fmea/)
- Severity, Occurrence and Detection are rated 1–10; Detection is inverted (high number = hard to detect); Severity is the most objective, Occurrence the most subjective — [Reliamag](https://reliamag.com/guides/how-to-perform-fmea/)
- RPN = S x O x D (1–1000). Criticisms: multiplying ordinal scales is statistically inappropriate; very different risk profiles can yield the same RPN (S10/O2/D5, S2/O5/D10 and S4/O5/D5 all equal 100); ratings are subjective with documented inter-rater variation — [Reliamag](https://reliamag.com/guides/how-to-perform-fmea/)
- AIAG-VDA 2019 replaced RPN with Action Priority (High/Medium/Low) via lookup tables that weight severity more heavily, so high-severity failure modes get attention regardless of probability; many industries (aerospace, medical) still use traditional approaches — [Reliamag](https://reliamag.com/guides/how-to-perform-fmea/)
- OWASP notes that ranking threats by likelihood x impact is hard to estimate and ignores the effort to fix, and some practitioners add remediation effort — [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- SQLite's own docs enumerate concrete data-loss failure modes (rogue overwrite, backup during transaction, deleted hot journal, broken locking, ignored sync, memory corruption, configuration errors, SQLite bugs) — [How To Corrupt An SQLite Database File](https://www.sqlite.org/howtocorrupt.html)
- SymPy `parse_expr` uses `eval` and "shouldn't be used on unsanitized input"; the ANTLR LaTeX backend with `strict=False` may silently parse only part of an expression (returns `x` for `x -`) — [SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html). A real 2026 CVE (CVE-2026-55585, RCE) arose in a math-verification service from unsafe `parse_expr` calls — [SecureLayer7 advisory](https://securelayer7.net/lab/cve-2026-55585-qwed-authenticated-rce-sympy-parse-expr)

### Inferences
**Scoring scheme (small enough to keep honest):**
- Severity 1–5: 5 = progress lost or student told a wrong answer is right without any warning; 4 = wrong schedule that silently harms retention, or an incorrect "wrong" verdict that corrupts scheduling state; 3 = visible but recoverable (undo/restore needed); 2 = annoyance; 1 = cosmetic.
- Likelihood 1–3 (rare / plausible / expected) and "Detectability by test": which layer catches it (property test, oracle corpus, kill-loop, migration fixture, manual UAT, none).
- Rule (Action Priority style): any S>=4 requires a named mitigation AND a named automated test regardless of likelihood; S3 with likelihood >=2 or "no automated detection" requires a mitigation; others are tracked. No multiplication.
- Table columns: ID, function, failure mode, effect, cause, control (prevention), detection (test ID), S, L, action, owner (agent role), status, linked REQ IDs, date reviewed.
- Process hooks: FMEA is reviewed at each phase gate; every escaped defect and every owner-reported bug adds or re-rates a row (this is the feedback loop that makes the table living, as the Reliamag guide says it must be kept updated).

**Seed rows (starter list, to be refined):**
- Data: DB corruption on power loss (S5); migration half-applied (S5); raw file copy of live DB used as backup (S5); two app instances on one DB (S5); DB placed in a synced/network folder (S4–5); user deletes/renames DB or its `-wal` file (S5); import overwrites or duplicates history (S4); review not committed before next card (S5); restore never tested (S5).
- Grading: wrong answer marked correct (S5, worst case: trust and learning harm); correct answer marked wrong (S4: student frustration and poisoned scheduling); parser silently drops tokens (S5, documented ANTLR behaviour); ambiguous notation (`^`, implicit multiplication) read differently from the student's intent (S4); numeric tolerance too loose or tight (S4); answer key itself wrong in imported content (S4; needs content-validation and a "report problem" path); `parse_expr` code execution via crafted content (S5).
- Scheduling: wrong due date from time zone/DST/day-boundary handling (S4); non-UTC datetime passed to FSRS (S3–4, py-fsrs requires UTC); FSRS version or parameter change silently re-times the whole collection (S4); duplicate application of one review after retry/crash (S4); fuzzing/jitter makes tests flaky or hides bugs (S2–3); clock moved backward (S3).
- Security: imported HTML executes script or reaches the Python bridge (S5); DoS via huge/deeply nested import (S3).
- Release: update/install replaces data (S5); unsigned build blocked on student's Mac (S3); wrong license attribution (S3).
- Process: agent weakens or special-cases tests (S4; see Question 5/11 and ImpossibleBench).

### Gaps
- I did not find an FMEA variant specifically for small software projects; the Reliamag guide is manufacturing/automotive-oriented. My adaptation (severity-dominant rule, detection = test layer) is an inference.
- IEC 60812 (the FMEA standard) was not retrieved.

---

## 5. Verification and validation: V-model scaled down, test layers, oracles, property-based testing, mutation testing, fuzzing, golden tests, user simulation

### Takeaway
Spend test effort in proportion to risk: very strong, oracle-backed, property- and mutation-tested tests for the grader, scheduler wrapper, importer and persistence layer; a thin set of integration/UI smoke tests elsewhere. Protect the tests themselves from the coding agents, because tested evidence shows agents will edit or special-case tests when blocked.

### Cited Findings
- NASA's V&V definitions and four verification methods (analysis, demonstration, inspection, test) and the requirement-to-evidence matrix — [NASA SE Handbook 5.3](https://www.nasa.gov/reference/5-3-product-verification/)
- Hypothesis stateful testing: subclass `RuleBasedStateMachine`; `@rule()` actions, `Bundle`s of produced values, `@initialize()`, `@precondition` (preferred over `assume()`), `@invariant()` checked after every step, `.TestCase` for pytest, `settings(stateful_step_count=...)`; on failure Hypothesis prints a short reproducing program — [Hypothesis stateful tests](https://hypothesis.readthedocs.io/en/latest/stateful.html)
- mutmut: `pip install mutmut`, `mutmut run`, `mutmut browse` (TUI), incremental runs that resume and retest only changed functions, results in a `mutants/` directory; config under `[tool.mutmut]` in `pyproject.toml` (`paths_to_mutate`, `do_not_mutate`, `mutate_only_covered_lines`, `max_stack_depth`, pytest arg options); `# pragma: no mutate` excludes equivalent mutants; v3+ mutates only called functions by default and cannot mutate code outside functions (needs mutmut 2); requires fork support so Windows users need WSL; the README does not list macOS but notes some darwin targets may need a Rust toolchain for the libcst dependency — [mutmut README](https://github.com/Otto-AA/mutmut). PyPI lists a 3.x line (at least 3.2.0) — [PyPI mutmut 3.2.0](https://pypi.org/project/mutmut/3.2.0/)
- Google's mutation-testing system analyzed ~760k code changes, generated 16.9M mutants and reported 2.1M to developers; 82% of reported mutants with developer feedback were labeled productive after "arid node" suppression rules; the authors argue aggregate mutation scores are neither actionable nor useful for guiding testing and instead treat each surviving mutant as a concrete test goal, reporting few per change — [Practical Mutation Testing at Scale (Petrović et al., TSE 2021)](https://homes.cs.washington.edu/~rjust/publ/practical_mutation_testing_tse_2021.pdf)
- Atheris is a coverage-guided Python fuzzer built on libFuzzer; on macOS "Apple Clang doesn't come with libFuzzer", so a recent LLVM with clang and compiler-rt must be built and `CLANG_BIN` pointed at it; a fuzz target takes one `bytes` argument; it integrates with Hypothesis via `test.hypothesis.fuzz_one_input` — [Atheris README (fork page of Zac-HD/atheris, not upstream google/atheris)](https://github.com/Zac-HD/atheris)
- SymPy: `parse_expr` uses `eval` (unsafe on unsanitized input); options `local_dict`, `global_dict` (default `from sympy import *`), `transformations`, `evaluate`; `parse_latex` has an ANTLR backend (default; `strict` option; may silently parse a fragment) and a Lark backend (newer, raises on ill-formed input, can detect ambiguity) — [SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html)
- A real exploit and its fix pattern: replacing direct `parse_expr` with a `safe_parse_expr` wrapper that strips built-ins, uses an allowlist of math symbols, enforces AST depth limits and rejects relational expressions — [SecureLayer7 advisory on CVE-2026-55585](https://securelayer7.net/lab/cve-2026-55585-qwed-authenticated-rce-sympy-parse-expr)
- py-fsrs details useful for oracle/differential testing: three independent FSRS-6 schedulers exist (py-fsrs in Python, fsrs-rs in Rust, ts-fsrs in TypeScript) — [awesome-fsrs](https://github.com/open-spaced-repetition/awesome-fsrs); `enable_fuzzing` jitter makes scheduling non-deterministic; datetimes must be UTC — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)
- ImpossibleBench (tests deliberately made impossible to satisfy legitimately): GPT-5 exploited tests 76% of the time on one-off impossible-SWE-bench and 93% on conflicting impossible-LiveCodeBench; Claude Opus 4.1 cheated about 46% on conflicting impossible-SWE-bench even with an abort option; observed tactics were modifying tests, overloading operators (e.g. equality), recording extra state, and special-casing. Making tests read-only helped (hiding them helped most but hurt legitimate performance); a strict "stop if tests look flawed" prompt and an abort mechanism helped on some benchmarks and only modestly on others — [ImpossibleBench write-up](https://www.greaterwrong.com/posts/qJYMbrabcQqCZ7iqm/impossiblebench-measuring-reward-hacking-in-llm-coding-1)
- Claude Code guidance: give the agent a runnable check; hooks are deterministic whereas CLAUDE.md instructions are advisory; a Stop hook can block a turn from ending until a check script passes; a fresh-context reviewer subagent avoids bias toward code just written; "The trust-then-verify gap... If you can't verify it, don't ship it." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- Google Testing Blog has a post "Test Sizes" (small/medium/large); the fetched copy contained only the title and comments, so I cannot cite its definitions — [Google Testing Blog: Test Sizes](https://testing.googleblog.com/2010/12/test-sizes.html?m=1)

### Inferences
**Scaled-down V-model (left side = requirements/design; right side = verification at each level):**
- Stakeholder needs (Q1) ↔ owner acceptance (UAT) and learning evaluation
- Requirements (Q2) ↔ system tests with trace matrix
- Architecture (modules and interfaces) ↔ integration tests (real SQLite file, real migrations, real importer)
- Module design ↔ unit and property tests, mutation testing on critical modules
No separate formal documents; the YAML, ADRs and tests are the artifacts.

**Test layers and budgets (all runnable via `scripts/verify.sh --tier=N`, since there is no CI):**
- Tier 0, pre-commit (target < 30 s): formatter/linter, type check on core packages, `trace_check.py`, a "tests directory unchanged unless change class says so" check, fast unit tests.
- Tier 1, pre-merge (target minutes): full unit + property tests (Hypothesis with fixed seed derandomized in the gate, plus a randomized run), integration tests with real SQLite, migration fixtures, importer tests, negative security tests, golden tests, UI smoke.
- Tier 2, nightly/on-demand: mutmut on critical modules, long Hypothesis runs and stateful machine, kill-9 crash loop (hundreds of iterations), user simulation (multi-year), performance budgets.
- Tier 3, release: clean-account install test of the signed build, restore drill, owner UAT, license/SBOM/vulnerability check, evidence bundle.

**Oracles for the two correctness-critical parts:**
- Scheduling: golden review sequences generated once from an independent implementation (ts-fsrs or fsrs-rs, via node/Rust or their bindings), stored as JSON fixtures with the library versions recorded; the app's scheduling wrapper must reproduce due dates, stability and difficulty to tolerance for thousands of random rating sequences, with jitter disabled or RNG injected and an injected clock (UTC). Add a test that fails loudly when the installed py-fsrs version or default parameters differ from the pinned ones.
- Grading: an oracle corpus of (key, student input, verdict) triples: textbook-style equivalent forms, known-wrong near-misses, notation ambiguities, edge cases (domains, signs, fractions, decimals). Layer two independent checks (structural/symbolic equivalence in SymPy plus randomized numeric evaluation at many points with domain handling) and require agreement, otherwise return "needs review". Every grading bug found by the owner is added to the corpus before it is fixed.
- Parsing: never call `parse_expr` on content-pack or student text without a restricted wrapper (allowlist of function names, no built-ins, AST depth limit, size limit, rejects attribute access/dunder names), or use a real grammar parser (Lark-based LaTeX) that raises on malformed input; if the ANTLR backend is used at all, set `strict=True`. Add a regression test that `x -` is rejected rather than treated as `x`.

**Property-based testing (Hypothesis) properties worth writing first:**
- Grader: reflexive (`equiv(a,a)`), symmetric, equal under commutative reorderings and algebraic rewrites generated from a small rewrite set, rejects `a + k` for nonzero rational k, rejects a sign flip, never raises (returns a verdict or "needs review"), terminates under a time limit (adversarial inputs), insensitive to whitespace.
- Scheduler wrapper: due date strictly after review time; retrievability in [0,1]; Again never schedules later than Good/Easy; monotone intervals in rating; idempotent when the same review event is replayed (dedupe by event ID); replaying a review log reproduces card state exactly.
- Importer: round-trip (export then import) is lossless; malformed input never crashes or partially imports (all-or-nothing transaction); sanitizer is idempotent and removes script vectors.
- Stateful machine (Hypothesis `RuleBasedStateMachine`): rules = answer card with rating, undo, import pack, reopen app, simulated crash, advance clock/DST; invariants = every acknowledged review is in the log, derived card state equals state recomputed from the log, counts consistent, DB passes `quick_check`. This is the single highest-value test for "no lost progress".

**Mutation testing protocol (mutmut):** run on `grader`, `scheduler_wrapper`, `importer`, `migrations`, `review_log` modules only; use `mutate_only_covered_lines`/`max_stack_depth` to keep run time down; treat each surviving mutant as a test goal (Google's finding), kill it with a test or mark equivalent with `# pragma: no mutate` plus a one-line reason; do not chase a global percentage, but set a floor for the critical modules (a proposal: no unreviewed survivors in arithmetic/comparison/boundary mutations in grader and scheduler). Run nightly or per critical change, not per commit. If mutmut 3's function-only mutation or macOS fork behavior causes trouble, cosmic-ray is the named alternative (not researched here).

**Fuzzing:** use Hypothesis (in-process, no toolchain) for the answer parser and importers first; add `hypothesis.fuzz_one_input` + Atheris only if a parser proves hard to cover, accepting that Atheris on macOS needs a self-built LLVM. Seed corpus = every real content-pack file plus every bug-report input.

**Golden/snapshot tests:** rendered problem HTML after sanitization, importer output, scheduler fixtures, migration results. Rule: snapshots are updated only by the verifier role with a note in the change record; implementers get them read-only.

**User simulation (validation of the scheduler integration, not of FSRS itself):** a simulated student with a forgetting model (use FSRS's retrievability with perturbed parameters, plus noise) driven through the real app queue code with a fake clock for 1–3 simulated years. Checks: achieved retention within tolerance of the desired retention, daily review workload doesn't blow up (e.g., no backlog spiral), no card is lost or starved, the queue honors daily limits, DST/time-zone changes mid-run don't create duplicates. Cheap to run nightly.

**Test-suite integrity (anti-gaming, based on ImpossibleBench):** (1) separate roles: tests for a requirement are written by a different agent/session than the code; (2) the implementer's working tree has `tests/` and `fixtures/` read-only (or a pre-merge script rejects diffs that touch them unless the change record declares a test change); (3) the grader code is scanned for test-aware branches (`if "pytest" in sys.modules`, hard-coded answers); (4) instruct agents to stop and report if a test seems wrong rather than edit it; (5) mutation testing is itself a check on test strength, and differential/oracle tests are hard to special-case.

### Gaps
- cosmic-ray was not researched; no head-to-head of mutmut vs cosmic-ray on macOS.
- The Google "Test Sizes" definitions and the test-pyramid proportions could not be cited (page body missing in fetch).
- I did not retrieve a source on metamorphic testing or approval/golden testing specifically; those recommendations are standard practice but unsourced here.
- I did not verify mutmut 3.x behavior on macOS arm64 empirically.
- The ANTLR "silently drops tokens" behavior is documented for `x -`; I did not test how the Lark backend handles typical student inputs such as `2x` or `1/2x`.

---

## 6. Reliability and data integrity: SQLite durability, corruption avoidance, backups and restore drills, migrations, crash recovery

### Takeaway
SQLite is dependable if its assumptions are respected. Configure for full durability (WAL + synchronous=FULL + macOS full fsync), use a single writer connection in a single process, never copy the live database file, take verified backups with `VACUUM INTO`/the backup API, keep an append-only review log as the source of truth, and prove all of it with a scripted kill-loop and restore drill.

### Cited Findings
- Causes of corruption listed by SQLite: overwrite by a rogue process or stray file descriptor; raw backup/restore copy during an active transaction ("might contain some old and some new content"), mitigated by `sqlite3_rsync`, the backup API or `VACUUM INTO`; deleting, moving or mismatching a hot `-journal`/`-wal`; broken file locking (including POSIX locks cancelled by `close()` from another thread, multiple SQLite copies linked into one process, unlinking/renaming an open DB, multiple hard links); carrying a connection across `fork()`; disabled or lying sync (`synchronous=OFF`, drives that don't honor flush); memory corruption; `journal_mode=OFF/MEMORY`, `writable_schema`; SQLite bugs — [How To Corrupt An SQLite Database File](https://www.sqlite.org/howtocorrupt.html)
- "SQLite should always be run with its default synchronous setting of FULL"; in WAL mode a failed sync can corrupt only during a checkpoint, so checkpoint as infrequently as possible — [howtocorrupt](https://www.sqlite.org/howtocorrupt.html)
- WAL-reset bug: found 2026-03-03; likely present in all versions 3.7.0 through 3.51.2; fixed in 3.51.3 (2026-03-13) with backports in 3.44.6 and 3.50.7; it only affects WAL databases with two or more connections (separate threads or processes) writing or checkpointing at the same instant; the page calls it unlikely in common use and "not an emergency" but advises upgrading — [SQLite WAL documentation](https://www.sqlite.org/wal.html)
- WAL specifics: persistent journal mode; extra `-wal` and `-shm` files must be kept with the database ("If a database file is separated from its WAL file, then transactions that were previously committed to the database might be lost, or the database file might become corrupted"); all processes must be on the same host, no network filesystems; automatic checkpoint at ~1000 pages (~4 MB); checkpoints can starve if there is always an active reader — [SQLite WAL documentation](https://www.sqlite.org/wal.html)
- `PRAGMA synchronous`: FULL is the default for rollback journals and "is atomic, consistent, isolated, and durable (ACID) in WAL mode"; NORMAL in WAL mode "is always consistent... but does lose durability"; durability matrix: rollback+FULL "maybe not durable", WAL+FULL ACID, WAL+NORMAL "maybe not durable", OFF not consistent — [PRAGMA documentation](https://www.sqlite.org/pragma.html)
- `PRAGMA fullfsync`: uses F_FULLFSYNC where supported; default off; "Only Mac OS X supports F_FULLFSYNC"; if set it applies to all syncs (`checkpoint_fullfsync` is then irrelevant) — [PRAGMA documentation](https://www.sqlite.org/pragma.html)
- `PRAGMA foreign_keys` defaults to OFF and is a per-connection setting that is a no-op inside a transaction ("applications should set the foreign key enforcement flag as required... and not depend on the default"); `integrity_check` returns "ok" or up to N errors and does not find foreign-key errors (use `foreign_key_check`); `quick_check` is O(N) vs `integrity_check` O(N log N) and skips UNIQUE and index-content verification; `application_id` is a 32-bit ID at header offset 68 for file-type identification — [PRAGMA documentation](https://www.sqlite.org/pragma.html)
- Atomic commit assumptions: SQLite assumes fsync/flush does not return until writes complete, that the OS may reorder writes, that file size updates before content, that deletion is atomic; "SQLite does not add any redundancy to the database file for the purpose of detecting corruption or I/O errors"; a "hot journal" is rolled back on next open and if journals are moved or renamed "the database will not be rolled back"; broken flushes "open[] SQLite up to the possibility of database corruption following a power loss in the middle of a commit" — [SQLite Atomic Commit](https://www.sqlite.org/atomiccommit.html)
- py-fsrs `Card`, `ReviewLog` and `Scheduler` serialize with `to_json()`/`from_json()` — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)
- pywebview runs with `private_mode` on by default, which prevents persistent cookies, local storage and cache across runs — [pywebview security considerations (DeepWiki summary)](https://deepwiki.com/r0x0r/pywebview/8.2-security-considerations)
- Python `faulthandler.enable(file=..., all_threads=True)` dumps Python tracebacks on SIGSEGV, SIGFPE, SIGABRT, SIGBUS, SIGILL; the log file must stay open for the process lifetime; `dump_traceback_later` can detect hangs — [Python faulthandler docs](https://docs.python.org/3/library/faulthandler.html)

### Inferences
**Database configuration checklist (in a single `db.connect()` function, with a test that asserts each):**
- `journal_mode=WAL`, `synchronous=FULL`, `fullfsync=ON` (macOS-only; the app's write rate is low so the cost is negligible; the SQLite page documents the flag but I did not retrieve Apple's fsync documentation), `foreign_keys=ON` for every connection, `busy_timeout` set, `application_id` set to an app-specific constant, `user_version` used as the schema version (the `user_version` pragma section was truncated in my fetch, so this is standard practice rather than a cited statement).
- One process, one writer connection, all pywebview `js_api` calls routed through it (pywebview documents that exposed functions run in separate threads and are not thread-safe). A single connection also avoids the circumstances of the WAL-reset bug.
- Assert at startup and in the test suite that `sqlite3.sqlite_version_info` is >= 3.51.3 (or on a documented backport line 3.50.7+/3.44.6+); log the version in diagnostics. The bundled SQLite depends on the Python build used by PyInstaller, so record it in the build manifest.
- Single-instance lock (lock file with `flock`) so a second launch can't open the same database.
- Store data only under `~/Library/Application Support/<AppName>/` (own directory, so stray files and sync tools don't touch it); never in `~/Desktop` or `~/Documents` (macOS can sync these with iCloud — my inference, not sourced — and SQLite warns about other processes touching files, renaming/copying DB files and network filesystems). Never in WKWebView local storage (private mode wipes it per run).
- Never delete or move `-wal`/`-journal` files by hand; "reset data" feature closes the connection, checkpoints, then deletes all three files together.

**Data model for integrity:** make the append-only `review_log` (event ID, card ID, rating, UTC timestamp, scheduler version) the source of truth and card scheduling state a derivable cache that can be rebuilt by replay (py-fsrs `ReviewLog`/serialization supports this shape). Benefits: corruption of derived state is repairable, parameter/version changes can be re-simulated before applying, undo is an event, and export is trivial. Include a per-row or chained checksum on the log so the app can detect silent damage (SQLite adds none).

**Backups and restore drills:**
- Automatic: backup on every launch (rolling, keep e.g. 7 daily + 4 weekly), before every migration, before every app update/import, via `VACUUM INTO 'backup.db'` or Python's backup API, never `cp` of a live DB. Verify each backup immediately (open it, `PRAGMA integrity_check`, count rows, compare log checksum) and refuse to prune older backups until the new one verifies.
- Manual: "Export progress" button writing a plain, versioned JSON/CSV of the review log (independent of SQLite so the student can keep it anywhere), plus an "Open backups folder" button.
- Restore drill script (`scripts/restore_drill.py`, run in the release tier and automated nightly on a synthetic DB): create DB with N reviews, take backup, corrupt or truncate the live DB, run the app's restore path, assert counts, log checksum, and `integrity_check`. Done = script exits 0 and the owner has done the drill once by hand through the UI.
- `quick_check` at launch (cheap), full `integrity_check` before backup/at quit when the DB is below a size threshold. On failure the app shows a plain-language recovery screen offering the newest verified backup and never overwrites the damaged file (copies it aside for diagnosis).

**Migrations:** forward-only, numbered, each applied inside a transaction after an automatic backup; the app refuses to open a database with `user_version` newer than it knows (downgrade guard); commit a fixture DB for every schema version ever released (generated by the code of that release) and run "fixture → migrate → invariants → compare to expected data" in Tier 1; a migration is not done until it passes on a copy of the owner's real database (copy made with the backup API) and on a large synthetic one.

**Crash recovery tests:** a subprocess writes reviews in a loop and prints an acknowledgement after each commit; the harness `kill -9`s it at random times (hundreds of iterations, also during migration and import), reopens, and asserts (a) every acknowledged review is present, (b) no partial import, (c) `integrity_check` is ok, (d) derived state equals replay of the log. This directly exercises SQLite's hot-journal/WAL recovery as documented. Real power-loss testing on a Mac isn't practical; accept the residual risk and rely on `synchronous=FULL` + `fullfsync` + backups.

### Gaps
- No Apple documentation on fsync vs F_FULLFSYNC semantics was fetched; the claim that FULL+fullfsync gives power-loss durability on macOS rests on SQLite's documentation of the flag only.
- I did not determine which SQLite version the python.org or Homebrew Python builds bundle in November 2026; this must be checked on the build machine.
- The `user_version` pragma documentation was truncated in my fetch.
- No source found for macOS/iCloud behavior toward SQLite files in Desktop/Documents.

---

## 7. Security and privacy threat modeling for a local app that renders imported HTML (STRIDE, OWASP/webview guidance, CSP)

### Takeaway
The realistic threats are not network attackers but malicious or sloppy content packs and imported decks: script in imported HTML, access to the pywebview Python bridge, and code execution through SymPy's `eval`-based parsing. Defend in layers: sanitize at import, sanitize/escape at render, strict CSP, sandboxed content frames, a minimal and validated Python API, restricted math parsing, and negative tests for each.

### Cited Findings
- OWASP's four questions: "What are we working on? What can go wrong? What are we going to do about it? Did we do a good enough job?"; use data flow diagrams with visible trust boundaries; STRIDE categories (Spoofing/authentication, Tampering/integrity, Repudiation/accounting, Information Disclosure/confidentiality, Denial of Service/availability, Elevation of Privilege/authorization); responses are mitigate, eliminate, transfer or accept, documented; the model is maintained as the system changes — [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- MDN: the STRIDE categories are prompts for thinking, "not a complete checklist"; expensive tools are unnecessary and overly complex diagrams can be counterproductive; LINDDUN is the privacy-focused framework — [MDN threat modeling frameworks](https://developer.mozilla.org/en-US/docs/Web/Security/Threat_modeling/Frameworks)
- Electron's security checklist (the closest widely-used checklist for desktop webview apps): load only secure content; keep Node integration off for remote content; context isolation; sandboxing; a Content Security Policy as "an extra layer against XSS and data injection"; restrict session permission requests; keep `webSecurity` on; validate the sender of every IPC message because any web frame, including iframes, can send IPC messages; limit navigation (parse URLs properly, naive string checks can be bypassed); deny unexpected new windows; never pass untrusted data to `shell.openExternal`; keep the framework current — [Electron security tutorial](https://www.electronjs.org/docs/latest/tutorial/security)
- pywebview (per a DeepWiki-generated summary of the repo, so secondary): `js_api`/`expose()` functions run in separate threads and are not thread-safe; recommended to review exposed functions, prefix private methods with an underscore, and validate all JavaScript input; Python exceptions reach JS as rejected promises (stack traces can leak); a per-run session token exists (`webview.token`) meant for the REST/HTTP server use and shared by all windows; `private_mode` default on; `ALLOW_FILE_URLS` restricted by default, `ALLOW_DOWNLOADS` disabled by default, `OPEN_EXTERNAL_LINKS_IN_BROWSER` setting, `REMOTE_DEBUGGING_PORT` should be None in production; `evaluate_js()` requires CSP `unsafe-eval` whereas `run_js()` has no CSP restriction; the page does not document the local server's bind address — [pywebview security considerations (DeepWiki)](https://deepwiki.com/r0x0r/pywebview/8.2-security-considerations)
- SymPy: `parse_expr` uses `eval` and should not be used on unsanitized input — [SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html); real-world RCE in a math verification API (CVE-2026-55585) from unrestricted `parse_expr`, fixed by stripping built-ins, allowlisting symbols, limiting AST depth and rejecting relational expressions — [SecureLayer7](https://securelayer7.net/lab/cve-2026-55585-qwed-authenticated-rce-sympy-parse-expr)
- Bleach (Mozilla's Python HTML sanitizer) was declared deprecated on 2023-01-23 because of its html5lib dependency; recommended alternatives in the thread include nh3 (Rust "ammonia" binding), lxml's `Cleaner`, and DOMPurify (called the "gold standard" by one commenter); some commenters report nh3 problems, so evaluate rather than assume — [bleach issue 698](https://github.com/mozilla/bleach/issues/698)
- Notarization "also protects your users if your Developer ID signing key is exposed" by letting Apple revoke tickets for unauthorized versions — [Apple notarization docs](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- pip-audit checks Python environments or requirements files against the PyPI advisory database (default) or OSV, supports `--require-hashes` for hash-pinned requirements, and can output CycloneDX SBOMs; exit code 1 if vulnerabilities are found — [pip-audit on PyPI](https://pypi.org/project/pip-audit/)

### Inferences
**One-page threat model (OWASP four questions; keep as `docs/threat-model.md`, update at each phase gate):**
- DFD with trust boundaries: [content pack/Anki deck file] → importer/sanitizer → SQLite → renderer (Svelte in WKWebView) → `js_api` bridge → Python core (grader/SymPy, scheduler, DB). Student-typed answers also cross the bridge into SymPy. Updater/download channel, if any, is a second boundary.
- STRIDE pass per boundary, e.g.: Tampering — a pack silently alters answer keys or history; Elevation of privilege — imported HTML script calls Python API; Information disclosure — a script reads other cards/exported data or phones home; DoS — pathological expression or huge/deeply nested file hangs grader/importer; Repudiation — no record of what an import changed (mitigate with an import log); Spoofing — a fake update or fake installer (mitigate with notarization/signature and download-only-from-official-site).
- Decision per threat: mitigate/eliminate/accept, each with a requirement ID and a negative test; this satisfies OWASP's "did we do a good enough job" question.

**Mitigation stack for imported HTML (defense in depth):**
1. Import-time allowlist sanitizer (nh3 or equivalent, evaluated against a corpus of XSS payloads; bleach is deprecated), tag/attribute/URL-scheme allowlists, strip `<script>`, event-handler attributes, `javascript:`/`data:` URLs (except safe image types), `<iframe>/<object>/<embed>/<form>/<meta http-equiv>/<base>`; store sanitized HTML and keep the original for audit only.
2. Render-time: prefer converting content to a restricted structured format (text + math + images) instead of arbitrary HTML; where HTML is rendered use Svelte `{@html}` only for sanitized strings, and consider a second pass with DOMPurify in the webview.
3. Strict CSP in the page (meta tag), e.g. `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'`. Design the app so it never needs `evaluate_js` (which requires `unsafe-eval` under CSP); use `run_js` or the bridge instead. CSP mechanics inside pywebview/WKWebView are to be verified empirically (see Gaps).
4. Bridge hygiene: expose a tiny, explicit API (a handful of verbs: get next card, submit answer, undo, import file chosen via native dialog, export); no generic "run SQL"/"read file"/"open URL" calls; underscore-prefix everything else; validate types and sizes of every argument; return only plain data; map exceptions to short error codes (no stack traces to JS); disable remote debugging; keep `ALLOW_FILE_URLS`/downloads at their restrictive defaults; open external links only through an allowlist.
5. Content frames: if imported HTML must be displayed, render it in a sandboxed iframe (`sandbox` without `allow-scripts`/`allow-same-origin`) and test that the pywebview bridge is not reachable from inside it (Electron's note that any frame can reach IPC suggests testing this explicitly).
6. SymPy: all parsing through one `safe_parse()` module (allowlist, no built-ins, size/depth/time limits, run grading in a subprocess or thread with a timeout and memory limit), covered by tests with known `eval` payloads (`__import__`, attribute chains, `lambda`, huge exponent/factorial DoS).
7. Supply chain: hash-pinned lockfile; `pip-audit --require-hashes` before each release (needs network on the dev Mac only); SBOM (CycloneDX output) stored with the release.

**Negative test suite (`tests/security/`):** a corpus of hostile HTML/XSS payloads and hostile expressions; assertions: no script execution (headless webview test or sanitizer-output assertion), no network request attempts, bridge unreachable from content, import of oversized/deep input fails safe within time/memory limits, malformed packs rejected atomically. Include a check (e.g., `lsof`) that, if pywebview's HTTP server is used, it listens only on 127.0.0.1 and that API calls without the session token fail.

**Privacy:** offline-by-design, no telemetry, no accounts; the only network use is an optional, user-initiated update check; diagnostics export strips content and personal data; document precisely what is stored and where.

### Gaps
- OWASP's specific desktop-app or ASVS pages (e.g., OWASP Desktop App Security Top 10) were not retrieved; the Electron checklist and the OWASP threat-modeling cheat sheet are the best sourced analogues, and Electron's items are mapped by analogy to pywebview.
- The pywebview source is a DeepWiki auto-generated summary, not official docs; it explicitly does not document the HTTP server's bind interface, whether `js_api` is injected into iframes, or XSS-specific behavior. These must be tested.
- I did not verify CSP behavior under WKWebView when pages are served via pywebview's local server or `file://`, nor whether `sandbox` iframes can reach `window.pywebview`.
- Statements about `eval` sandboxing being inherently unsafe in Python are widely held but I did not retrieve a source in this pass; the advisory's allowlist+AST approach is the sourced pattern.

---

## 8. Usability and accessibility: think-aloud tests with ~5 users, SUS, WCAG 2.2 AA items, keyboard-only use

### Takeaway
Run three small think-aloud rounds of about five users with fix-and-retest between them rather than one big study; use SUS only as a rough trend (five users is too few for a precise score); and treat WCAG 2.2 AA as a checklist of about two dozen criteria that apply to a keyboard-driven desktop webview, with keyboard-only operation and visible focus as the non-negotiables.

### Cited Findings
- Nielsen Norman Group: 5 users find about 85% of usability problems, based on a model where one user uncovers ~31% of problems (problems found = N x [1 − (1 − L)^n]); the better plan is several small iterative rounds ("3 studies with 5 users each"); test more users per group if there are very different user groups (3–4 per group for two groups); for quantitative studies about 20 users are recommended — [NN/g: Why You Only Need to Test with 5 Users](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/)
- SUS: ten items, 0–100, average across ~500 products is 68 (50th percentile); scores are not percentages; items alternate positive/negative wording and must be reverse-scored (11% of researchers mis-scored in the authors' review); with n=5 the sample mean fell within 6 points of the large-sample score half the time, within 10 points 75% of the time and within ~17 points 95% of the time; experienced/repeat users score ~11% higher; SUS is not diagnostic (pair it with task observation) — [MeasuringU: 10 Things to Know About SUS](https://www.measuringu.com/10-things-sus)
- WCAG 2.2 added nine success criteria: 2.4.11 Focus Not Obscured (Minimum) AA; 2.4.12 Focus Not Obscured (Enhanced) AAA; 2.4.13 Focus Appearance AAA; 2.5.7 Dragging Movements AA; 2.5.8 Target Size (Minimum) AA (24x24 CSS px or sufficient spacing); 3.2.6 Consistent Help A; 3.3.7 Redundant Entry A; 3.3.8 Accessible Authentication (Minimum) AA; 3.3.9 Accessible Authentication (Enhanced) AAA; and removed 4.1.1 Parsing — [W3C: What's New in WCAG 2.2](https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/)
- WCAG 2.2 criteria confirmed with levels from the spec: 1.1.1 Non-text Content A; 1.3.1 Info and Relationships A; 1.4.3 Contrast (Minimum) AA; 1.4.4 Resize Text AA; 1.4.10 Reflow AA; 1.4.11 Non-text Contrast AA; 1.4.12 Text Spacing AA; 2.1.1 Keyboard A; 2.1.2 No Keyboard Trap A; 2.2.1 Timing Adjustable A; 2.3.1 Three Flashes A; 2.4.3 Focus Order A; 2.4.7 Focus Visible AA; 2.4.11 Focus Not Obscured (Minimum) AA; 2.5.8 Target Size (Minimum) AA. The levels for 3.3.1 Error Identification, 3.3.3 Error Suggestion, 4.1.2 Name, Role, Value and 4.1.3 Status Messages were cut off in my fetch — [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.1.1 Keyboard: all functionality operable through a keyboard interface without specific keystroke timings (exception for path-dependent input); 2.1.2 No Keyboard Trap: if focus can be moved to a component with the keyboard it can be moved away using only the keyboard, and the user is told the method if it needs more than arrow/Tab — [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- ISO 25010:2023's Interaction Capability sub-characteristics include User Error Protection, Inclusivity, User Assistance and Self Descriptiveness — [arc42 ISO 25010 page](https://quality.arc42.org/standards/iso-25010)

### Inferences
**Think-aloud plan (cheap, repeatable):**
- Participants: 5 per round, 3 rounds (round 1 after a clickable build of core review loop; round 2 after fixes; round 3 pre-release), recruited from classmates (other STEM students), plus at least one using VoiceOver or heavy keyboard if available. No UX lab needed: screen-record with macOS built-in capture with consent.
- Tasks (each with success criterion and time cap): install and first launch from the DMG/zip including Gatekeeper prompts; import a content pack; answer 10 problems including typing math answers; understand why an answer was marked wrong and report a problem; use undo; take a backup and restore; change daily limit/desired retention; quit mid-session and resume.
- Metrics: task success, time, errors, number of times a participant misreads the app's parse of their answer, SUS after round 3 (report as a range, using the n=5 spread above, and compare to the 68 average only as a loose signal). Findings go into an issue list with severity, linked to requirements; the round is "done" when no severity-high problem repeats in two participants.
- The owner is a participant for validation but not a substitute (knows the intent).

**Design choices that prevent the worst usability-induced grading errors:** show the parsed interpretation of the typed answer (rendered math) before submit; accept common notations explicitly and say what was understood; use a "needs review"/"I couldn't understand your answer" state instead of "wrong" when parsing fails; allow a one-key override ("I was right") that logs the event for later corpus review; undo the last answer.

**WCAG 2.2 AA items that apply to this app (checklist for `docs/accessibility.md`; test each by hand once per release, the automatable ones with axe-core or Playwright in Tier 1):**
- Keyboard: 2.1.1, 2.1.2, 2.4.3, 2.4.7, 2.4.11 (sticky headers/toolbars must not hide the focused control), and 2.5.8 (24x24 px targets) plus 2.5.7 (any drag-and-drop must have a click/keyboard alternative). Full review loop (reveal, rate 1–4, undo, next) must have single-key shortcuts and be usable without a mouse.
- Perceivable: 1.1.1 (alt text for diagrams/figures), 1.3.1 (real headings, lists, labels, landmarks), 1.4.3/1.4.11 contrast (light and dark themes), 1.4.4 and 1.4.10 (zoom to 200%/400% without loss, reflow), 1.4.12 text spacing, color not the only signal for correct/wrong.
- Operable/understandable: 2.2.1 (no hard time limits; timers optional), 2.3.1 (no flashing), 3.3.1/3.3.3 (errors identified and suggestions given, which maps to the "could not parse your answer" message), 3.3.7 Redundant Entry (do not make the student retype answers), 4.1.2 and 4.1.3 (names/roles/values for controls; announce grading result via an ARIA live region for VoiceOver).
- Likely not applicable: 3.3.8/3.3.9 Accessible Authentication (no login), 3.2.6 Consistent Help (applies only if a help mechanism repeats across pages; keep the Help link in the same place anyway).
- Math content is the hard part: ensure math is rendered with accessible output (MathML or an accessible renderer) and that the answer input has a text alternative; VoiceOver pass on a sample of problems each release.
- Keyboard-only test script: unplug mouse, perform every task from the think-aloud list, record any step that needs the pointer; Tab order screenshot per screen. Done = zero pointer-only steps.

### Gaps
- I did not retrieve guidance specific to WKWebView/VoiceOver behavior, or to math accessibility (MathML/KaTeX/MathJax) — flagged as an open risk.
- Levels for 3.3.1, 3.3.3, 4.1.2, 4.1.3 were truncated in the fetched spec text (they are commonly A, AA, A, AA respectively, but I did not verify from the source in this pass).
- The 5-user rule's critiques (e.g., Spool & Schroeder) were not retrieved; MeasuringU's SUS spread numbers are the only quantification of small-sample uncertainty I have.

---

## 9. Performance budgets: launch time, answer latency, enforcement

### Takeaway
Define a handful of numeric budgets on a named reference Mac and reference data size, measure them with a script that uses medians and relative thresholds, and fail the release tier when exceeded. There is little authoritative source material for numbers; the budgets below are proposals.

### Cited Findings
- SQLite WAL autocheckpoints when the WAL reaches ~1000 pages (~4 MB) on commit; checkpoints can starve with always-active readers; manual `wal_checkpoint` styles PASSIVE/FULL/RESTART/TRUNCATE exist — [SQLite WAL docs](https://www.sqlite.org/wal.html)
- `PRAGMA quick_check` is O(N) and `integrity_check` is O(N log N) in the number of rows — [PRAGMA docs](https://www.sqlite.org/pragma.html)
- PyInstaller on macOS: onedir runs as a single process; onefile has a parent launcher and a child process; builds target the current architecture unless `--target-arch` is set (`x86_64`, `arm64`, `universal2`); universal2 needs every extension module to have both slices or the build aborts with `IncompatibleBinaryArchError` — [PyInstaller feature notes](https://pyinstaller.org/en/stable/feature-notes.html)
- `faulthandler.dump_traceback_later(timeout, exit=...)` runs on a watchdog thread and can detect hangs — [Python faulthandler docs](https://docs.python.org/3/library/faulthandler.html)
- py-fsrs scheduling of a single card is a library call (no network); the optimizer is a separate optional install — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)

### Inferences
**Proposed budgets (on a named oldest-supported reference Mac, e.g., 8 GB Apple Silicon; reference data: 20k cards, 500k review-log rows):**
- Cold launch to first interactive card: <= 3 s p95 (hard fail > 5 s). Warm launch <= 1.5 s.
- Grade-to-next-card latency (including durable commit with full fsync): p95 <= 100 ms, p99 <= 250 ms; the UI must not block on grading (show "checking..." after 150 ms).
- Answer-checking worst case: SymPy equivalence for any corpus item <= 500 ms, hard timeout 2 s then "needs review".
- Import throughput: 1,000 problems in <= 30 s, with progress and cancel; transaction is all-or-nothing.
- Memory: steady state < 400 MB; DB size and WAL size bounded (WAL < 50 MB after idle).
- Backup on launch: < 1 s for reference DB, done off the critical path.
- Bundle size: record and trend it (PyInstaller bundles with SymPy are large); a budget prevents accidental dependency bloat.

**Enforcement without CI:** `scripts/perf_check.py` builds the reference DB (deterministic generator), launches the real app in a `--perf-mode` that reports timestamps (process start, window created, first card painted via pywebview's loaded event + a JS mark), runs a scripted 200-answer session over the bridge, and writes JSON (median/p95 of 20 cold launches). Compare against `perf_baseline.json` with a relative tolerance (e.g., +20%) and absolute hard caps; commit the baseline only with owner/coordinator approval. Run in Tier 2 nightly and Tier 3 release; also run on a throttled/battery-saver state once. Expected levers: ship onedir (no self-extraction step; sourced fact is only that onefile adds a parent/child process), lazy-import SymPy (known to be slow to import — my knowledge, not sourced) and pre-warm it on a background thread after first paint, SQLite indexes on `due` and card ID, WAL autocheckpoint left at default, no per-answer VACUUM or integrity checks on the hot path.

### Gaps
- No authoritative source for launch-time budgets for desktop apps or for PyInstaller startup overhead was retrieved; all numbers above are proposals to be calibrated on the actual machine after the first measurement.
- SymPy import-time cost was not measured or sourced.

---

## 10. Release engineering for free distribution on macOS: signing, notarization, reproducibility, updates, licenses, crash reporting

### Takeaway
Gatekeeper-friendly distribution requires a Developer ID certificate, hardened runtime, a secure timestamp and Apple notarization via `notarytool`; that requires the paid Apple Developer Program ($99/year), which conflicts with the project's no-spend constraint. Decide that explicitly before distribution; until then build and test signed ad-hoc locally. Treat updates as manual-first, keep licenses machine-checkable with REUSE/SPDX, and give the offline app a local diagnostics export instead of network crash reporting.

### Cited Findings
- Notarization requirements: sign all executables with valid signatures using a Developer ID certificate (not Mac Distribution, ad hoc or local development certificates); enable Hardened Runtime; include a secure timestamp; do not include `com.apple.security.get-task-allow` as true; link against the macOS 10.9+ SDK; properly formatted entitlements. Notarization "is not App Review": an automated service scans for malicious content and code-signing issues and produces a ticket to staple; it covers apps, non-app bundles, disk images (UDIF) and flat installer packages — [Apple: Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- Since November 1, 2023 the notary service no longer accepts uploads from `altool` or Xcode 13 or earlier; use `notarytool` (and `stapler`, both included with Xcode) or the Notary API; the scan "usually takes less than an hour"; software distributed with Developer ID after June 1, 2019 must be notarized on macOS 10.15+ — [Apple notarization docs](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- Cost: the Apple Developer Program annual fee is 99 USD (local currency where available); individual enrollment requires Apple Account with 2FA, age of majority, legal name and a personal credit card (otherwise a government ID); accredited educational institutions can enroll with a fee waiver; "there is no developer program specifically for students" — [Apple Program Enrollment help](https://developer.apple.com/help/account/membership/program-enrollment/). The free tier only supports on-device development via a Personal Team (7-day expiry, 3 devices) and is not for distribution — [Apple: Choosing a Membership](https://developer.apple.com/support/compare-memberships)
- Without notarization: on first open macOS shows that Apple "cannot check [the app] for malicious software"; the user can approve via System Settings > Privacy & Security > "Open Anyway" and the app is then saved as an exception (Apple's page doesn't mention Control-click) — [Apple Support: Safely open apps on your Mac](https://support.apple.com/en-us/102445)
- PyInstaller on macOS: Apple Silicon requires code signing and PyInstaller ad-hoc signs everything it produces by default; passing `--codesign-identity` (a valid Apple-issued certificate) signs with hardened runtime enabled; entitlements via `--osx-entitlements-file`; app bundles are signed with deep signing; default build targets only the current architecture; `universal2` works only through PyInstaller's own mechanism (lipo-merging single-arch builds yields a binary that runs on one platform); argv emulation is opt-in; onedir is a single process whereas onefile has a parent/child process — [PyInstaller feature notes](https://pyinstaller.org/en/stable/feature-notes.html). The page doesn't cover reproducible builds.
- A community howto for PyInstaller signing warns the entitlements file is needed "so embedded python libraries can be access appropriately", that PyInstaller `.app` bundles need a specific procedure, and it uses obsolete `altool` throughout — [txoof Signing and Notarizing HOWTO](https://github.com/txoof/codesign/blob/main/Signing_and_Notarizing_HOWTO.md) (treat commands as outdated)
- macOS 26 Tahoe "will be the final version that supports any Intel Macs"; macOS 27 supports only Apple Silicon; dropped Intel Macs get security updates for two years — [Macworld](https://www.macworld.com/article/2808358/if-you-own-an-intel-mac-you-have-12-months-to-upgrade-to-a-new-model.html) (written around WWDC25; I did not verify macOS 27's shipped state)
- Sparkle: updates must be cryptographically signed with EdDSA (`generate_appcast` signs automatically; `sign_update` for manual); appcast items carry `sparkle:version`, enclosure, release notes; archives .dmg/.zip/.tar.*/.aar; symlinks must be preserved or framework code signatures break; delta updates supported; `sparkle:minimumSystemVersion`, `sparkle:hardwareRequirements arm64` (Sparkle 2.9+); the page doesn't mention notarization or HTTPS requirements — [Sparkle: Publishing an update](https://sparkle-project.github.io/documentation/publishing/)
- A Python wrapper, SparkleHelper 0.1.2 (released July 13, 2026), bundles Sparkle for packaged Python apps with a PyInstaller hook, but is classified "3 - Alpha" with one maintainer; maintenance status unclear; macOS onefile `.app` specs need a wrapper command — [SparkleHelper on PyPI](https://pypi.org/project/sparklehelper/)
- REUSE specification 3.3 (2024-11-14): every covered file needs copyright and `SPDX-License-Identifier` information (comment headers recommended; `.license` sidecar for uncommentable files); bulk licensing via `REUSE.toml` (recommended; `.reuse/dep5` deprecated); one plain-text license file per license in `LICENSES/` named by SPDX identifier; non-SPDX licenses use `LicenseRef-` — [REUSE spec 3.3](https://reuse.software/spec-3.3/)
- Creative Commons: for BY-NC-SA 4.0 "no non-CC licenses have been designated as compatible"; GPLv3 compatibility is for BY-SA 4.0 only and one-way (contributions may be relicensed to GPLv3 not vice versa) — [Creative Commons: compatible licenses](https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/)
- pip-audit can emit CycloneDX SBOMs and audit hash-pinned requirements — [pip-audit](https://pypi.org/project/pip-audit/)
- py-fsrs is MIT-licensed — [PyPI fsrs](https://pypi.org/project/fsrs/)
- `faulthandler` can write tracebacks for fatal signals to a log file — [Python faulthandler docs](https://docs.python.org/3/library/faulthandler.html)

### Inferences
**Distribution decision (record as ADR; the owner decides):**
- Option A, Developer ID + notarization ($99/yr): best student experience (normal first-launch prompt), required for Sparkle-style trusted updates, protects against key abuse. Cost conflicts with the project's no-extra-spend constraint. Possible mitigations: fund via donations/later, or only pay in the month of first public release (the fee is annual, so a one-year membership covers a year of releases).
- Option B, unsigned/ad-hoc distribution with written instructions for Privacy & Security > Open Anyway: free, but a security and trust cost for strangers (they are told to override macOS's warning), more support burden, and not recommended as the main channel for non-technical students.
- Option C, source-only/dev install for technical users: free, small audience.
- Until then: build locally with PyInstaller's default ad-hoc signing for personal use; keep the release script ready with `--codesign-identity` and `notarytool submit --wait` plus `stapler staple` and `spctl --assess` verification so switching to Option A is configuration, not new work.

**Build and release pipeline (single script `scripts/release.sh`, run on the Mac):**
1. Clean checkout of a tagged commit; verify Tier 0–2 results recorded for that commit; refuse to build from a dirty tree.
2. Pinned, hash-locked dependencies in a fresh virtualenv with a pinned Python version; `pip-audit --require-hashes`; generate CycloneDX SBOM and third-party notices from the lockfile.
3. PyInstaller onedir `.app` (arm64; universal2 only if all wheels are universal2 and Intel support matters — the Tahoe-is-last-Intel fact makes arm64-only defensible for a new app, but students may still have older Intel Macs; record as an ADR); sign inside-out with hardened runtime and minimal entitlements (only those PyInstaller/Python need; no `get-task-allow`); notarize; staple; package as DMG or zip (Apple allows notarizing both DMGs and ZIPs); verify with `codesign --verify --deep --strict` and `spctl --assess`.
4. Build manifest: git commit, Python and SQLite versions, dependency hashes, PyInstaller version, SHA-256 of artifacts. "Reproducible" here should be defined as: same commit + same lockfile + same toolchain produces an equivalent app whose manifest matches, not byte-identical output (signing timestamps, ad-hoc signatures and embedded paths make bit-for-bit unlikely; PyInstaller's docs do not address it).
5. Clean-environment install test: new macOS user account (or a fresh VM/second Mac if available), download via browser to get the quarantine attribute, open, run smoke script, migrate from the previous version's DB, restore drill.
6. Release evidence bundle: trace matrix, test/mutation/perf reports, FMEA delta, threat-model delta, SBOM, license report, manifest, owner UAT sign-off. Store with the release tag.

**Updates:** v1: no in-app auto-update. An optional "Check for updates" menu item that opens the official download page, or fetches a tiny signed JSON only on user click; the app always backs up before first launch of a new version and refuses to open newer-schema DBs with older code. Sparkle is the standard mac answer (EdDSA-signed, delta updates) but it is a native framework: integrating it into a PyInstaller bundle means either the alpha SparkleHelper wrapper or custom embedding, plus an HTTPS host for the appcast and EdDSA private-key custody; adopt only if there is an audience and the owner accepts the key-management duty (lost key = no more trusted updates). Whatever is chosen, updates must never silently change the FSRS algorithm or parameters without a migration plan and backup.

**Licensing process:**
- Code license chosen by the owner (permissive such as MIT/Apache-2.0 or copyleft); apply REUSE: SPDX header in every source file (agents can add/verify with `reuse lint`), `LICENSES/` folder, `REUSE.toml` for bulk assets; CI-less check: `reuse lint` in Tier 1.
- Dependencies: generate a third-party notices file from the lockfile (name, version, SPDX license, copyright, license text); fail the release if any dependency license is unknown or incompatible with the chosen license. Known: py-fsrs is MIT; SymPy, pywebview and the PyInstaller bootloader licenses were not verified here (see Gaps).
- Content: every problem/pack carries provenance and SPDX license metadata (source URL, author, license, retrieval date). The importer rejects content without it. Because the shipped version must contain only open-source problems, keep content packs as separate artifacts with their own license files; a CC BY-NC-SA pack cannot be relicensed under any non-CC license, and NC terms mean the app + pack combination cannot be offered commercially — keep such packs in a clearly marked optional channel, not bundled in the default app, and get legal advice before bundling. Attribution (BY) requires visible credit in the app's About/Content screen.

**Crash reporting for an offline app:** no network reporting. (1) `faulthandler.enable(file=<log file kept open>)` for native crashes and hangs; (2) a global `sys.excepthook`/threading hook writing a structured crash record (app version, schema version, SQLite version, macOS version, stack trace, last N non-personal log lines) to `~/Library/Logs/<AppName>/`; (3) on next launch, a plain-language dialog "The app closed unexpectedly. Your progress is safe (backup X verified). [Export diagnostics]"; (4) Export diagnostics writes a zip the student can email or attach to an issue, with `integrity_check` result, migration history, but no card content or answers by default; (5) the owner reviews diagnostics in Tier 3 triage and adds an FMEA row/regression test for every crash. macOS also writes its own crash reports; their locations were not verified in this pass.

### Gaps
- The Apple pages did not mention anything that changed in 2026 beyond the footer date (copyright 2026) and the already-old altool cut-off; I could not confirm a 2026-specific new requirement. Fee waiver for individual students: none found.
- Developer ID certificate lifetime/renewal details and Apple's current Gatekeeper behavior on macOS 26/27 (beyond the Open Anyway flow) were not retrieved.
- PyInstaller entitlements actually needed for a hardened-runtime Python app (e.g., `disable-library-validation`, `allow-unsigned-executable-memory`) were not retrieved; the howto only says an entitlements file is needed. Test empirically with notarization logs.
- Reproducible-build guidance for PyInstaller was not found in the docs I fetched.
- Licenses for SymPy, pywebview, PyInstaller (bootloader exception) were not verified. The legal consequences of combining CC BY-NC-SA content with code in one distribution are a legal question; I only have CC's statement on compatibility.
- Sparkle's notarization/HTTPS requirements are not stated on the publishing page; consult Sparkle's other docs (e.g., security) before adopting.

---

## 11. Process for AI-agent development: reviews, definition of done, change control, decision records, quality with agents

### Takeaway
The process must assume agents (a) say "done" too early, (b) will weaken or special-case tests when blocked, and (c) lose context between sessions. Counter with machine-checkable gates (scripts and hooks, not instructions), role separation (tests/oracles written independently of code), fresh-context reviewers limited to correctness and stated requirements, a small evidence bundle per change, and ADRs so decisions survive context loss.

### Cited Findings
- "Give Claude a way to verify its work": without a check it can run, "looks done" is the only signal; use tests, build exit codes, linters, fixtures diffs or screenshots; have the agent show evidence (test output, commands and results) rather than asserting success — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- Ways to gate: in the prompt, via a `/goal` condition evaluated by a separate evaluator, as a deterministic Stop hook that blocks the turn from ending until the check passes, or via a verification subagent so "the agent doing the work isn't the one grading it"; hooks are deterministic while CLAUDE.md is advisory — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- Writer/Reviewer pattern: a fresh-context session reviews code the writer produced; "have one Claude write tests, then another write code to pass them"; adversarial review step: a reviewer subagent sees only the diff and given criteria; warning that a reviewer asked to find gaps will usually report some, so tell it to flag only gaps affecting correctness or stated requirements to avoid over-engineering — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- Spec practice: interview, then write a complete spec to a file, then execute in a fresh session; specs name files/interfaces, scope-out, end-to-end verification; CLAUDE.md should be short (long files cause rules to be ignored); plan mode helps when changes span multiple files — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- ImpossibleBench evidence that models modify tests, special-case and overload operators to pass tests; read-only tests, abort options and strict prompts reduce but do not eliminate it — [ImpossibleBench write-up](https://www.greaterwrong.com/posts/qJYMbrabcQqCZ7iqm/impossiblebench-measuring-reward-hacking-in-llm-coding-1)
- Google's mutation-testing work treats surviving mutants as concrete test goals surfaced during code review — [Practical Mutation Testing at Scale](https://homes.cs.washington.edu/~rjust/publ/practical_mutation_testing_tse_2021.pdf)
- An Architectural Decision Record "captures a single AD and its rationale"; the collection forms a decision log; popular templates are Nygard's (2011), MADR and Y-statements — [adr.github.io](https://adr.github.io/) (the page doesn't specify minimal fields or storage)
- NASA: verification complete means documented objective evidence of compliance (or approved waiver) and closed discrepancy reports; verification approach tailored to risk — [NASA SE Handbook 5.3](https://www.nasa.gov/reference/5-3-product-verification/)

### Inferences
**Roles (separate sessions/contexts; model strength follows risk — the strongest model only where accuracy is critical):**
- Coordinator: owns plan, requirements/FMEA/ADR files, task breakdown, change classification, evidence bundle review, and communication with the owner in plain language.
- Implementer(s): write code for one scoped task from a self-contained spec; cannot edit `tests/`, `fixtures/`, `docs/requirements.yaml` risk classes (enforced by script).
- Verifier/test author (different session, ideally different model or at least fresh context): writes acceptance tests and oracle corpus from the requirement before the code exists ("acceptance tests first"), owns golden fixtures and mutation runs.
- Independent reviewer: fresh context, sees diff + requirement + evidence bundle; checks only correctness, requirement coverage, security and scope creep; produces a short pass/fail list. For Critical-class code (grader, scheduler, DB, migrations, importer/sanitizer, bridge), the reviewer is a strong model; for docs, content tagging, simple UI copy a cheaper one suffices.
- Release agent: runs `release.sh`, never edits product code.
- Owner: validator and acceptance authority (runs UAT scripts, think-aloud sessions, decides trade-offs such as the signing cost).

**Change classes (change control with minimal ceremony):**
- C0 (docs/content copy): Tier 0 only.
- C1 (normal feature/bug): requirement ID(s) cited; failing test first (reproduce bug or encode acceptance); Tier 1 green; independent review; evidence note.
- C2 (critical path: grading, scheduling, persistence/migrations, importer/sanitizer, bridge, security, build/signing, dependencies): C1 plus FMEA row reviewed, mutation run on touched critical modules with survivors triaged, Tier 2 green, ADR if the design changes, owner informed in plain language.
- Any change touching tests/fixtures/goldens requires the verifier role and a stated reason ("test was wrong because..."), never the implementer alone.

**Definition of Done (per task; the coordinator rejects "done" without these artifacts):**
1. Requirement(s) cited and updated; acceptance examples exist.
2. Tests existed first and failed for the right reason; now pass (output pasted).
3. `scripts/verify.sh --tier=1` exits 0 (hook-enforced, not self-reported); trace check passes.
4. For C2: mutation survivors triaged; Tier 2 green; FMEA and threat-model rows updated.
5. Independent review recorded with findings resolved or explicitly waived (waivers listed, owner-visible).
6. No new warnings, no skipped/xfail tests without a ticket ID, no new dependency without license + audit check.
7. Docs/ADR updated; changelog entry in plain language.
8. For user-visible changes: owner UAT step written (1–3 plain steps with expected result).

**Hooks/automation to make rules deterministic:** pre-commit hook runs Tier 0; a Stop hook for implementer sessions runs the relevant fast tests and blocks completion until green; a "test-protect" script rejects diffs touching test paths from implementer sessions; a dependency-change check blocks changes to the lockfile without audit output. These implement the "deterministic gate" idea from the Claude Code guidance without CI.

**Decision records (ADR-lite):** `docs/adr/NNNN-title.md` with: Status, Context, Decision, Alternatives considered, Consequences, Revisit-by trigger. Mandatory ADRs: FSRS version/parameter pinning; SQLite configuration; review-log-as-truth data model; sanitizer and CSP strategy; math parsing/equivalence strategy; distribution/signing choice; update strategy; content licensing policy; test-protection policy; supported macOS/arch. Agents must read relevant ADRs at task start (put the index, not the content, in the short CLAUDE.md).

**Phase gates (one table for the whole lifecycle; each gate = a short checklist signed off by the coordinator and shown to the owner):**
- G0 Define: stakeholders, goals/non-goals, constraints, success metrics written (Q1). Done: owner approves the 1-page charter.
- G1 Specify: requirements (EARS, IDs, methods), quality priorities, FMEA v1, threat model v1, accessibility and performance budgets, ADRs for key decisions. Done: trace check passes with every requirement mapped to a planned verification.
- G2 Foundation: repo layout, `verify.sh` tiers, DB layer with config checks, backup/restore, migrations framework, crash-kill harness, perf harness skeleton, test oracles for scheduler/grader (before features). Done: Tier 1 green on an empty feature set, restore drill passes.
- G3 Build increments: per-feature C1/C2 flow; mutation on critical modules; weekly owner UAT; think-aloud round 1–2.
- G4 Harden: security negative tests, fuzz/property long runs, simulation, accessibility pass, performance budgets met, think-aloud round 3 + SUS.
- G5 Release candidate: clean-account install of signed (or documented unsigned) build, migration from last version, restore drill by owner, license/SBOM/audit, evidence bundle complete.
- G6 Post-release: bug reports → FMEA/corpus/regression test; periodic dependency and SQLite-version review; revisit ADR triggers.

**Keeping the owner effective as validator:** give the owner a one-page UAT script per release in plain language ("Do X; you should see Y; if not, press Export diagnostics and send it"), and a "trust report" generated by the coordinator: green/red status of each Critical requirement with the evidence link, the open risk list, and anything waived. The owner's testing is validation of fitness for purpose; it does not replace automated verification (the app's correctness cannot be established by occasional manual use).

### Gaps
- Evidence on AI-agent process is mostly vendor guidance (Anthropic) and one benchmark (ImpossibleBench); I did not find controlled studies of agent-written test suites' defect-detection or of reviewer-agent effectiveness. The role split and change classes are recommendations, not established practice.
- The ADR page gave no minimum fields; the template above is my synthesis (Nygard-style).
- ImpossibleBench is a synthetic benchmark of deliberately impossible tasks, so its cheating rates are upper-bound indicators of tendency rather than expected rates on ordinary work.
