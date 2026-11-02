"""Shared test data: cards that use every field, and a realistic multi-day history.

`python -m tests.storage.data <out.sql>` regenerates the frozen v1 fixture dump; do it
only while USER_SCHEMA_VERSION is 1 (the fixture must stay a v1 database forever).
"""

import sqlite3
import sys
import tempfile
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

from core.model import (
    THIS_ATTEMPT,
    Attempt,
    Card,
    CardMark,
    CardPart,
    CardRevision,
    CardUser,
    CheckerOptions,
    Choice,
    Course,
    CourseGoal,
    DiagnosticSet,
    Dispute,
    Exam,
    FlashcardState,
    GradedAnswer,
    ImplicitCredit,
    ImportRecord,
    Media,
    PackInfo,
    PackPace,
    PackPaceSection,
    PendingCheck,
    Provenance,
    Report,
    ReviewEvent,
    Section,
    SessionState,
    Skill,
    SkillShadow,
    SkillState,
    SkillTierState,
    SolutionStep,
    Unit,
    WeakSpot,
    WrongAnswer,
)
from core.storage.clock import FixedClock
from core.storage.packs import PackRecord
from core.storage.user_store import UserStore

START = datetime(2026, 11, 1, 15, 0, tzinfo=UTC)  # 10:00 in New York
ZONE = "America/New_York"
DAY_MS = 86_400_000


def some[T](value: T | None) -> T:
    """Narrow an Optional in tests: the value must be there."""
    assert value is not None
    return value


def new_clock() -> FixedClock:
    return FixedClock(START, tz=ZONE)


def tree() -> list[Course | Unit | Section]:
    return [
        Course(id="calc1", title="Calculus I", ord=1),
        Unit(id="calc1.u4", course_id="calc1", title="4 Applications", ord=4),
        Section(
            id="calc1.4-1",
            unit_id="calc1.u4",
            title="4.1 Max and Min",
            ord=1,
            textbook_ref="Stewart 4.1",
        ),
        Section(id="calc1.4-4", unit_id="calc1.u4", title="4.4 l'Hospital", ord=4),
    ]


def skills() -> list[Skill]:
    return [
        Skill(
            id="calc1.extrema.critical-numbers",
            name="Find critical numbers",
            deck="Calculus I::4 Applications::4.1 Max and Min",
            section_id="calc1.4-1",
            textbook_ref="Stewart 4.1",
            core=True,
            exam_tier=3,
            requires=("calc1.deriv.power-rule", "alg.factor.polynomials"),
            encompasses=(("calc1.deriv.power-rule", 0.5), ("alg.factor.polynomials", 0.25)),
            confusable=("calc1.shape.inflection-points",),
            notes_md="core skill",
        ),
        Skill(id="calc1.deriv.power-rule", name="Power rule", section_id="calc1.4-1"),
        Skill(id="alg.factor.polynomials", name="Factor polynomials", section_id="calc1.4-1"),
        Skill(
            id="calc1.select.limit-technique",
            name="Choose a limit technique",
            section_id="calc1.4-4",
            method_choice=True,
        ),
    ]


def full_card() -> Card:
    """A card that sets every field the card format has."""
    return Card(
        id="calc1.4-1.crit-numbers.001",
        rev=3,
        kind="problem",
        skill_id="calc1.extrema.critical-numbers",
        uses=("calc1.deriv.power-rule", "alg.factor.polynomials"),
        tier=3,
        time_minutes=7.5,
        answer_type="set",
        answer="-1, 0, 1",
        checker=CheckerOptions(
            vars="x", domain="x > 0", tolerance="1%", exact="yes", form="factored"
        ),
        wrong=(
            WrongAnswer(answer="0, 1", feedback="x + 1 = 0 gives a critical number too", step=3),
            WrongAnswer(answer="1"),
        ),
        plot="x^4 - 2x^2, x = -2..2",
        calculator=True,
        angles="degrees",
        cue_required=True,
        error_step=None,
        tagged="ai:model prompt-v3 0.86",
        deck="Calculus I::4 Applications::4.1 Max and Min",
        section_id="calc1.4-1",
        tags=("quartic", "exam"),
        question_md=r"Find all critical numbers of \(f(x) = x^4 - 2x^2\).",
        cued_question_md="Use f' = 0 to find all critical numbers of f.",
        choices=(Choice(text_md="a", correct=False), Choice(text_md="b", correct=True)),
        reasons=(Choice(text_md="r1", correct=True), Choice(text_md="r2", correct=False)),
        parts=(
            CardPart(
                label="a",
                prompt_md="Where is f increasing?",
                answer_type="interval",
                answer="(-1, 0) U (1, inf)",
                checker=CheckerOptions(endpoints="either"),
                skill_id="calc1.deriv.power-rule",
                choices=(Choice(text_md="p", correct=True),),
                wrong=(WrongAnswer(answer="(0, 1)", feedback="sign chart flipped", step=2),),
                time_minutes=2.5,
            ),
            CardPart(label="b", prompt_md="Local max point?", answer_type="point", answer="(0, 0)"),
        ),
        hints=("Find f'.", "Factor f'."),
        answer_md=r"\(x = -1, 0, 1\)",
        solution=(
            SolutionStep(
                number=0,
                skill_id="calc1.extrema.critical-numbers",
                label="Set up",
                body_md="where f' = 0",
            ),
            SolutionStep(
                number=1,
                skill_id="calc1.deriv.power-rule",
                label="Differentiate",
                body_md="4x^3 - 4x",
            ),
            SolutionStep(
                number=2, skill_id="alg.factor.polynomials", label="Factor", body_md="4x(x-1)(x+1)"
            ),
        ),
        solution_md="0. [x] Set up ...",
        rubric=("Differentiated", "Factored"),
        alternative_solution=(SolutionStep(number=0, skill_id=None, label="Graph it"),),
        alternative_solution_md="Graph f'.",
        front_md=None,
        back_md=None,
        text_md=None,
        extra_md="More detail",
        notes_md="author notes",
        template_id="calc1.4-1.crit.t01",
        seed=42,
        params="k = 3; m = 1/2",
        provenance=Provenance(
            source="Stewart Calculus 9e, 4.1 #31",
            source_url="https://example.org/stewart",
            license="CC BY-NC-SA 4.0",
            creators=("J. Stewart", "Toishi"),
            original_path="books/stewart/4.1.md",
            original_commit="abc123",
            modified=True,
            modification_note="numbers changed",
            third_party=("figure 4.1.2",),
            translation="from Spanish",
            unofficial_solution=True,
        ),
        verified="template+cas",
        status="active",
    )


def other_cards() -> list[Card]:
    return [
        Card(
            id="calc1.3-4.chain-error.001",
            kind="find-error",
            skill_id="calc1.extrema.critical-numbers",
            error_step=2,
            answer_type="expression",
            answer="6x(x^2 + 1)^2",
            question_md="Find f'(x).",
            shown_work=(
                SolutionStep(number=1, skill_id="calc1.deriv.power-rule", label="Outer"),
                SolutionStep(number=2, skill_id="calc1.deriv.power-rule", label="Differentiate"),
            ),
            reasons=(
                Choice(text_md="missing inner", correct=True),
                Choice(text_md="other", correct=False),
            ),
        ),
        Card(
            id="calc1.4-4.method-limit.001",
            kind="method",
            skill_id="calc1.select.limit-technique",
            answer_type="choice",
            question_md="Which method fits?",
            choices=(
                Choice(text_md="Substitution", correct=False),
                Choice(text_md="L'Hopital", correct=True),
            ),
        ),
        Card(id="calc1.mvt.001", kind="flashcard", front_md="State the MVT.", back_md="If f ..."),
        Card(id="calc1.cloze.001", kind="cloze", text_md="{{c1::f'(c)}} = ..."),
        Card(
            id="calc1.retired.001",
            skill_id="calc1.deriv.power-rule",
            question_md="Old",
            status="retired",
        ),
    ]


def pack_records() -> list[PackRecord]:
    return [
        *tree(),
        *skills(),
        full_card(),
        *other_cards(),
        CardRevision(card_id="calc1.4-1.crit-numbers.001", rev=2, changed_at=1, note="typo"),
        CardRevision(
            card_id="calc1.4-1.crit-numbers.001",
            rev=3,
            changed_at=2,
            note="key",
            answer_changed=True,
        ),
        Media(name="media/f-graph.svg", data=b"<svg/>"),
        PACE,
    ]


PACE = PackPace(
    minutes_per_step=1.25,
    weekly_hours=4.0,
    sections=(
        PackPaceSection(deck="calc1.4-1", hours=6.0),
        PackPaceSection(deck="calc1.4-4", hours=2.5),
    ),
)


PACK_INFO = PackInfo(id="calc1", title="Calculus I", version="2026.11", built_at=1_700_000_000_000)

SKILL = "calc1.extrema.critical-numbers"
CARD = "calc1.4-1.crit-numbers.001"


def populate(store: UserStore, clock: FixedClock, days: int = 3) -> list[Attempt]:
    """Write a multi-day history through the public API; returns the stored attempts."""
    store.set_settings(
        {"daily.problems": 25, "queue.easy_days": {"sat": 50}, "custom.flag": [1, 2]}
    )
    store.set_course_goal(
        CourseGoal(
            course_id="calc1", goal="custom", custom_retention=0.85, goal_date=date(2026, 12, 15)
        )
    )
    store.add_exam(
        Exam(
            course_id="calc1",
            name="Test 3",
            at=clock.now_ms() + 20 * DAY_MS,
            minutes=75,
            problems=12,
            sections=("calc1.4-1",),
        )
    )
    store.set_section_state("calc1.4-1", "learning")
    store.set_card_mark(CardMark(card_id="calc1.mvt.001", flagged=True, flag_note="typo?"))
    store.put_user_content(
        Course(id="mine", title="My deck"),
        Skill(id="mine.trig", name="Trig identities", requires=("calc1.deriv.power-rule",)),
        Card(
            id="mine.trig.001",
            skill_id="mine.trig",
            question_md="sin^2 + cos^2?",
            answer_type="number",
            answer="1",
        ),
    )
    store.log_import(
        ImportRecord(
            file="deck.apkg", kind="apkg", summary={"added": 3, "rejected": 0}, backup="b.db"
        )
    )
    attempts: list[Attempt] = []
    stability = 1.0
    for day in range(days):
        session = store.start_session(
            SessionState(
                study_day=store.study_day(),
                plan={"items": [CARD, "calc1.mvt.001"], "day": day},
                untimed=day == 1,
            )
        )
        # a wrong first try, then a correct second try: one presentation
        pres = f"p{day}"
        first = store.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    session_id=session.id,
                    presentation_id=pres,
                    card_id=CARD,
                    card_rev=3,
                    pack_id="calc1",
                    skill_id=SKILL,
                    tier=3,
                    seed=42,
                    template_id="t01",
                    reason_tag="due",
                    raw_input="0, 1",
                    parsed="{0, 1}",
                    verdict="incorrect",
                    attempt_number=1,
                    final=False,
                    matched_wrong=0,
                    active_ms=40_000,
                    solve_ms=35_000,
                    entry_ms=5_000,
                    raw_ms=41_000,
                    capped_ms=40_000,
                    shown_at=clock.now_ms() - 41_000,
                    app_version="0.1.0",
                ),
                changes=(
                    CardUser(card_id=CARD, last_seen_at=clock.now_ms(), times_seen=2 * day + 1),
                ),
                session=replace(session, position=0, draft="0, 1"),
            )
        )
        clock.advance(seconds=30)
        stability *= 2.5
        second = store.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    session_id=session.id,
                    presentation_id=pres,
                    card_id=CARD,
                    card_rev=3,
                    pack_id="calc1",
                    skill_id=SKILL,
                    tier=3,
                    seed=42,
                    raw_input="-1, 0, 1",
                    verdict="correct",
                    attempt_number=2,
                    hints_used=1,
                    confidence="unsure",
                    guessed=day == 2,
                    active_ms=70_000,
                    solve_ms=60_000,
                    entry_ms=10_000,
                    raw_ms=75_000,
                    capped_ms=70_000,
                    pause_count=1,
                    longest_pause_ms=4_000,
                    untimed=day == 1,
                    rating=2,
                    predicted_recall=0.91,
                    params_id="default-6",
                    rules_version="r1",
                    triage_policy="recommended",
                    error_choice="slip",
                    error_step=2,
                    app_version="0.1.0",
                    extra={"part_results": {"a": "correct"}},
                ),
                changes=(
                    SkillState(
                        skill_id=SKILL,
                        fsrs_state=2,
                        stability=stability,
                        difficulty=5.5,
                        due_at=clock.now_ms() + int(stability * DAY_MS),
                        last_review_at=clock.now_ms(),
                        reps=day + 1,
                        level="learned",
                        level_at=clock.now_ms(),
                        level_evidence={"days": day + 1},
                        elo_theta=0.1 * day,
                        elo_n=day + 1,
                        shaky=day == 1,
                        shaky_reviews=day,
                    ),
                    SkillTierState(
                        skill_id=SKILL,
                        tier=3,
                        target_ms=90_000,
                        baseline_median_ms=65_000,
                        baseline_n=day + 1,
                        first_correct_ms=(70_000,) * (day + 1),
                    ),
                    SkillShadow(
                        skill_id="calc1.deriv.power-rule", credited_stability=stability / 2
                    ),
                    CardUser(
                        card_id=CARD,
                        last_seen_at=clock.now_ms(),
                        times_seen=2 * day + 2,
                        last_correct_at=clock.now_ms(),
                        redo_due_at=clock.now_ms() + 4 * DAY_MS,
                    ),
                    PendingCheck(
                        skill_id="alg.factor.polynomials",
                        attempt_id=THIS_ATTEMPT,
                        card_id=None,
                        depth=1,
                    ),
                ),
                reviews=(
                    ReviewEvent(
                        target_kind="skill",
                        target_id=SKILL,
                        rating=2,
                        rules_version="r1",
                        params_id="default-6",
                        retention=0.85,
                        predicted_recall=0.91,
                    ),
                ),
                credits=(
                    ImplicitCredit(
                        from_skill=SKILL,
                        to_skill="calc1.deriv.power-rule",
                        weight=0.5,
                        mode="shadow",
                        stability_before=1.0,
                        stability_after=1.4,
                    ),
                ),
            )
        )
        clock.advance(minutes=1)
        flash = store.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    session_id=session.id,
                    card_id="calc1.mvt.001",
                    card_kind="flashcard",
                    verdict="self",
                    rating=3,
                    explicit_rating=True,
                    active_ms=8_000,
                ),
                changes=(
                    FlashcardState(
                        card_id="calc1.mvt.001",
                        fsrs_state=2,
                        stability=3.0 + day,
                        difficulty=4.0,
                        due_at=clock.now_ms() + 3 * DAY_MS,
                        last_review_at=clock.now_ms(),
                        reps=day + 1,
                    ),
                ),
                reviews=(
                    ReviewEvent(
                        target_kind="flashcard",
                        target_id="calc1.mvt.001",
                        rating=3,
                        rules_version="r1",
                    ),
                ),
            )
        )
        checks = [c for c in store.pending_checks() if c.attempt_id == second.id]
        clock.advance(minutes=1)
        check = store.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    session_id=session.id,
                    card_id="calc1.mvt.001",
                    card_kind="flashcard",
                    verdict="correct",
                    check_of=second.id,
                    reason_tag="check",
                ),
                changes=tuple(
                    replace(
                        c, status="passed", resolved_by=THIS_ATTEMPT, resolved_at=clock.now_ms()
                    )
                    for c in checks
                ),
            )
        )
        store.save_session(
            replace(
                session,
                position=4,
                current={"card_id": CARD, "seed": 42},
                active_ms=1234,
                draft="x^2",
            )
        )
        attempts += [first, second, flash, check]
        if day < days - 1:
            store.end_session(some(session.id))
        clock.advance(days=1)
    spot = store.apply(
        [
            WeakSpot(
                skill_id="alg.factor.polynomials",
                flagged_at=clock.now_ms(),
                study_day=store.study_day(),
                z=-2.4,
                evidence=6.0,
                misses=3,
                problems=6,
                days=2,
            )
        ]
    )[0]
    assert isinstance(spot, WeakSpot)
    store.apply(
        [
            DiagnosticSet(
                skill_id="alg.factor.polynomials",
                weak_spot_id=spot.id,
                created_at=clock.now_ms(),
                card_ids=("a.1", "a.2", "a.3"),
            )
        ]
    )
    store.add_dispute(
        Dispute(attempt_id=some(attempts[0].id), raw_input="0, 1", note="I was right")
    )
    store.add_report(
        Report(card_id=CARD, card_rev=3, attempt_id=attempts[1].id, reason="typo in key")
    )
    return attempts


def dump_state(conn: sqlite3.Connection) -> dict[str, list[tuple[object, ...]]]:
    """Every row of every table, for exact before/after comparisons."""
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_schema "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")]  # noqa: S608
        for t in tables
    }


def write_v1_fixture(out: Path) -> None:
    from core.storage import Storage
    from core.storage.profiles import ProfilePaths
    from core.storage.schema import USER_SCHEMA_VERSION

    assert USER_SCHEMA_VERSION == 1, "the v1 fixture must be written by schema v1"
    with tempfile.TemporaryDirectory() as tmp:
        clock = new_clock()
        storage = Storage.open(ProfilePaths(Path(tmp) / "p"), clock=clock, create=True)
        populate(storage.users, clock)
        storage.close(backup=False)
        conn = sqlite3.connect(Path(tmp) / "p" / "user.db")
        lines = list(conn.iterdump())
        conn.close()
    out.write_text(
        "-- Frozen user.db at schema v1 with data (tests/storage/data.py). Never edit.\n"
        + "\n".join(lines)
        + "\n"
    )


if __name__ == "__main__":
    write_v1_fixture(Path(sys.argv[1]))
