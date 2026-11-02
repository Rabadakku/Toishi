# ADR-0021: Pack schema v3 for standard times and the pace standard

- Status: Accepted
- Date: 2026-11-02
- Context: ADR-0020 (component student model) and docs/card-format.md (`time:` key, the skills-file pace header and `## Section` blocks).

## Context

The student model needs two new things from a pack:
- each problem's standard time, which a card can override with `time:`;
- the course's pace standard: minutes per step, weekly class hours and section hours in order.

Packs are sealed read-only files, and the app reads every pack version it has ever shipped (ADR-0011).

## Decision

- **A new pack schema version, 3** (`core/storage/sql/pack_v3.sql`, `PRAGMA user_version = 3`). It adds three pack-only tables:
  - `card_time`: card, part, minutes;
  - `pace`: one row, minutes per step and weekly hours;
  - the section hours in course order.
- **v1 and v2 packs stay readable.** Cards in those packs take the default standard time, and the course has no pace standard: the planner falls back to a start date with no section schedule, and the owner sees that the pack has no pace data.
- **user.db is unchanged.** Personal decks imported into user.db drop `time:` with an import warning, so user.db's content tables keep exactly the shape of a pack's. A later user.db migration can add the column if personal decks need standard times.
- **The planner's type is `core.plan.types.PaceStandard`.** The pack-side record is named `PackPace`, and a converter maps one to the other.

## Consequences

- Pack builds write v3. Tests cover reading v1, v2 and v3.
- Packs are never migrated in place; a pack with new data is rebuilt.
