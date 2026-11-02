"""Robust-evaluation simulator for the student model and planner (design v1.1, section 6.2).

A policy (the new design, P1, or the skill-level FSRS baseline, P0) plans and serves practice
day by day to a simulated student whose answers come from one of several truth models. The
harness records what each policy certified, what the truth says the student can do, the
policy's calibration and the daily minutes, and checks the 6.2 gates.

Modules:
- `course`: a synthetic course built from a real component map, or a small toy course;
- `truth`: the truth models (a) to (f) and the student profiles;
- `policies`: the baseline P0 and the design policy P1 (through `adapters`);
- `adapters`: where `core.learner` and `core.plan` plug in; `standin` until they land;
- `harness`: the day-by-day loop; `metrics`: summaries and gates; `report`: Markdown;
- `run`: the command line, `python -m tools.sim2.run --out docs/design/sim2-report.md`.
"""
