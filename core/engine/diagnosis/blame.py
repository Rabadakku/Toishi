"""Who gets the blame for a miss ("What went wrong?", ENG-15), and how far taps are trusted.

A tap is evidence, not a verdict: it puts 0.6 of the blame on the tapped step's skill (0.8
when the typed answer matched a known wrong answer of that step) and spreads the rest over
the other steps' skills by weakness (1 - recall) times tag weight. Without a tap the blame
goes toward the weakest tagged skill by (1 - recall) times tag weight. Main tags weigh 1,
uses tags 0.4. Taps whose checks keep passing count for less (self-calibration).
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from core.engine.diagnosis.config import (
    MAIN_TAG_WEIGHT,
    TAP_CONFIRM_TARGET,
    TAP_MIN_SAMPLE,
    TAP_SHARE,
    TAP_SHARE_FLOOR,
    TAP_SHARE_MATCHED,
    UNKNOWN_RECALL,
    USES_TAG_WEIGHT,
)
from core.model import Card, ErrorChoice

type RecallOf = Callable[[str], float | None]


@dataclass(frozen=True, slots=True, kw_only=True)
class Step:
    number: int
    skill_id: str
    label: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Tags:
    """A problem's skills: main tags (the card's skill, part skills), uses tags (the card's
    uses and any other step skill, e.g. a method-choice skill on Step 0) and its steps."""

    main: tuple[str, ...]
    uses: tuple[str, ...] = ()
    steps: tuple[Step, ...] = ()

    def weight(self, skill_id: str) -> float:
        if skill_id in self.main:
            return MAIN_TAG_WEIGHT
        return USES_TAG_WEIGHT if skill_id in self.uses else 0.0

    @property
    def skills(self) -> tuple[str, ...]:
        return (*self.main, *self.uses)

    def step(self, number: int | None) -> Step | None:
        return next((s for s in self.steps if s.number == number), None)

    def weights(self) -> dict[str, float]:
        return {k: self.weight(k) for k in self.skills}


def card_tags(card: Card | None, skill_id: str) -> Tags:
    """Tags of a problem; without the card only its skill is known."""
    main: list[str] = [skill_id]
    if card is None:
        return Tags(main=(skill_id,))
    for part in card.parts:
        if part.skill_id and part.skill_id not in main:
            main.append(part.skill_id)
    steps = tuple(
        Step(number=s.number, skill_id=s.skill_id, label=s.label)
        for s in card.solution
        if s.skill_id
    )
    uses: list[str] = []
    for k in (*card.uses, *(s.skill_id for s in steps)):
        if k not in main and k not in uses:
            uses.append(k)
    return Tags(main=tuple(main), uses=tuple(uses), steps=steps)


def weakness(recall: float | None) -> float:
    return 1.0 - (UNKNOWN_RECALL if recall is None else max(0.0, min(1.0, recall)))


def _spread(skills: Iterable[str], mass: float, tags: Tags, recall: RecallOf) -> dict[str, float]:
    skills = list(dict.fromkeys(skills))
    if not skills or mass <= 0:
        return {}
    raw = {k: weakness(recall(k)) * max(tags.weight(k), USES_TAG_WEIGHT) for k in skills}
    total = sum(raw.values())
    if total <= 0:  # every skill fully recalled: spread by tag weight alone
        raw = {k: max(tags.weight(k), USES_TAG_WEIGHT) for k in skills}
        total = sum(raw.values())
    return {k: mass * v / total for k, v in raw.items()}


def untapped_blame(tags: Tags, recall: RecallOf) -> dict[str, float]:
    """No tap: toward the weakest tagged skill, by (1 - recall) x tag weight."""
    return _spread(tags.skills, 1.0, tags, recall)


def tapped_blame(tags: Tags, tapped: Step, share: float, recall: RecallOf) -> dict[str, float]:
    others = [s.skill_id for s in tags.steps if s.skill_id != tapped.skill_id]
    if not others:
        return {tapped.skill_id: 1.0}
    blame = _spread(others, 1.0 - share, tags, recall)
    blame[tapped.skill_id] = blame.get(tapped.skill_id, 0.0) + share
    return blame


def tap_share(*, matched: bool, factor: float = 1.0) -> float:
    base = TAP_SHARE_MATCHED if matched else TAP_SHARE
    return base if factor >= 1.0 else max(TAP_SHARE_FLOOR, base * factor)


def blame(
    tags: Tags,
    *,
    choice: ErrorChoice | None,
    step: int | None = None,
    matched_step: int | None = None,
    matched: bool = False,
    recall: RecallOf,
    tap_factor: float = 1.0,
) -> dict[str, float]:
    """Blame shares (summing to 1) of one miss. `matched`: the typed answer matched a known
    wrong answer, whose @step is `matched_step` (None: the wrong answer names no step).
    Step 0 ("didn't know where to start") blames Step 0's skill like a tap. A different
    valid method blames only the problem's skill; an accepted slip is not handled here."""
    problem = tags.main[0]
    if choice == "other-method":
        return {problem: 1.0}
    if choice in ("step", "setup"):
        number = 0 if choice == "setup" else step
        tapped = tags.step(number)
        if tapped is None and choice == "setup":
            tapped = Step(number=0, skill_id=problem, label="Set up")
        if tapped is not None:
            agrees = matched and (matched_step is None or matched_step == tapped.number)
            return tapped_blame(tags, tapped, tap_share(matched=agrees, factor=tap_factor), recall)
    return untapped_blame(tags, recall)


def heaviest(shares: Mapping[str, float]) -> str | None:
    """The most-blamed skill (ties: the first listed)."""
    if not shares:
        return None
    return max(shares.items(), key=lambda kv: kv[1])[0]


# ---------------------------------------------------------------- self-calibration


@dataclass(frozen=True, slots=True, kw_only=True)
class TapRecord:
    """One resolved diagnosis: the choice, the skill it pointed at, and whether the check
    confirmed it (a step check failed: that skill really was weak)."""

    at: int
    choice: str
    skill_id: str
    kind: str  # the check kind that resolved it
    confirmed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class TapCalibration:
    taps: int  # step taps whose check resolved
    confirmed: int

    @property
    def rate(self) -> float | None:
        return None if self.taps == 0 else self.confirmed / self.taps

    @property
    def factor(self) -> float:
        """Multiplier on a tap's share: 1 until at least 20 taps show fewer than half
        confirmed, then rate / 0.5."""
        rate = self.rate
        if rate is None or self.taps < TAP_MIN_SAMPLE or rate >= TAP_CONFIRM_TARGET:
            return 1.0
        return rate / TAP_CONFIRM_TARGET


def tap_calibration(records: Iterable[TapRecord]) -> TapCalibration:
    taps = [r for r in records if r.choice == "step" and r.kind == "step"]
    return TapCalibration(taps=len(taps), confirmed=sum(r.confirmed for r in taps))
