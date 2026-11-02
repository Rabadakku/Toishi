"""Seeded-error test of the acceptance pipeline (review R8.1): how many wrong keys it rejects.

    uv run python content-tools/seeded_errors.py          # prints the table

Fixture: verified Calculus I cards (derivatives, antiderivatives, limits, values), each with
a worked solution whose steps carry `check:` claims (MATH-17) and, as real cards do, the
chain-rule slip as a known `wrong` answer where one exists. Each card is then given
plausible wrong keys of four kinds (sign, factor, chain rule, off by one): about 100 in all.
Every mutated card goes through the pack build twice: the whole pipeline (self-check,
differential checks, worked-solution checks) and the self-check alone. The table is the
fraction rejected, by error type. The unmutated cards must build clean (control).
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.cards.load import Source  # noqa: E402
from core.cards.mepack import PackBuild, PackMeta, check_pack  # noqa: E402

ERROR_TYPES = ("sign", "factor", "chain-rule", "off-by-one")
SKILLS = "---\nformat: mastery-skills 1\ndeck: S::U::S\n---\n\n## Skill s.calc\nname: Calculus\n"
HEAD = "---\nformat: mastery-cards 1\ndeck: S::U::S\nsource: original\nlicense: personal\n---\n"


@dataclass(frozen=True)
class Fixture:
    id: str
    kind: str  # answer-type
    key: str
    claims: tuple[str, ...]  # check: lines of the one working step; the last gives the final line
    seeded: dict[str, str]  # error type -> plausible wrong key
    wrong: str = ""  # a known wrong answer on the card (the chain-rule slip), if any
    extra: str = ""  # other key lines (domain)


def d(fid: str, f: str, key: str, sign: str, factor: str, chain: str | None, off: str) -> Fixture:
    seeded = {"sign": sign, "factor": factor, "off-by-one": off}
    if chain is not None:
        seeded["chain-rule"] = chain
    return Fixture(
        fid, "expression", key, (f"diff({f}, x) = {key}",), seeded,
        wrong=f"{chain} => Use the chain rule. @1" if chain else "",
    )  # fmt: skip


def i(fid: str, f: str, key: str, sign: str, factor: str, chain: str | None, off: str,
      extra: str = "") -> Fixture:  # fmt: skip
    seeded = {"sign": sign, "factor": factor, "off-by-one": off}
    if chain is not None:
        seeded["chain-rule"] = chain
    claims = (f"diff({key}, x) = {f}", f"integrate({f}, x) = {key}")
    return Fixture(fid, "antiderivative", f"{key} + C", claims, seeded, extra=extra)


def v(
    fid: str, claim: str, key: str, sign: str, factor: str, chain: str | None, off: str
) -> Fixture:
    seeded = {"sign": sign, "factor": factor, "off-by-one": off}
    if chain is not None:
        seeded["chain-rule"] = chain
    return Fixture(fid, "number", key, (f"{claim} = {key}",), seeded)


FIXTURES: tuple[Fixture, ...] = (
    d("s.d.01", "sin(3x)", "3cos(3x)", "-3cos(3x)", "6cos(3x)", "cos(3x)", "4cos(3x)"),
    d("s.d.02", "(2x+1)^5", "10(2x+1)^4", "-10(2x+1)^4", "20(2x+1)^4", "5(2x+1)^4", "10(2x+1)^5"),
    d("s.d.03", "e^(x^2)", "2x*e^(x^2)", "-2x*e^(x^2)", "4x*e^(x^2)", "e^(x^2)", "(2x+1)*e^(x^2)"),
    d("s.d.04", "ln(x^2+1)", "2x/(x^2+1)", "-2x/(x^2+1)", "x/(x^2+1)", "1/(x^2+1)", "2x/(x^2+2)"),
    d(
        "s.d.05",
        "cos(x^3)",
        "-3x^2*sin(x^3)",
        "3x^2*sin(x^3)",
        "-6x^2*sin(x^3)",
        "-sin(x^3)",
        "-3x^3*sin(x^3)",
    ),
    d(
        "s.d.06",
        "sqrt(4x+1)",
        "2/sqrt(4x+1)",
        "-2/sqrt(4x+1)",
        "4/sqrt(4x+1)",
        "1/(2sqrt(4x+1))",
        "2/sqrt(4x+2)",
    ),
    d(
        "s.d.07",
        "(x^2+3)^4",
        "8x(x^2+3)^3",
        "-8x(x^2+3)^3",
        "16x(x^2+3)^3",
        "4(x^2+3)^3",
        "8x(x^2+3)^4",
    ),
    d("s.d.08", "tan(2x)", "2sec(2x)^2", "-2sec(2x)^2", "4sec(2x)^2", "sec(2x)^2", "2sec(2x)"),
    d("s.d.09", "e^(-3x)", "-3e^(-3x)", "3e^(-3x)", "-6e^(-3x)", "e^(-3x)", "-2e^(-3x)"),
    d(
        "s.d.10",
        "sin(x)^2",
        "2sin(x)cos(x)",
        "-2sin(x)cos(x)",
        "4sin(x)cos(x)",
        "2sin(x)",
        "3sin(x)cos(x)",
    ),
    d("s.d.11", "x^5", "5x^4", "-5x^4", "10x^4", None, "5x^5"),
    d(
        "s.d.12",
        "1/(3x-2)",
        "-3/(3x-2)^2",
        "3/(3x-2)^2",
        "-6/(3x-2)^2",
        "-1/(3x-2)^2",
        "-3/(3x-2)^3",
    ),
    d("s.d.13", "ln(5x)", "1/x", "-1/x", "5/x", "1/(5x)", "1/(x+1)"),
    d(
        "s.d.14",
        "sin(x)^3",
        "3sin(x)^2*cos(x)",
        "-3sin(x)^2*cos(x)",
        "6sin(x)^2*cos(x)",
        "3sin(x)^2",
        "3sin(x)^3*cos(x)",
    ),
    d(
        "s.d.15",
        "sqrt(x^2+9)",
        "x/sqrt(x^2+9)",
        "-x/sqrt(x^2+9)",
        "2x/sqrt(x^2+9)",
        "1/(2sqrt(x^2+9))",
        "x/sqrt(x^2+10)",
    ),
    i("s.i.01", "2x*cos(x^2)", "sin(x^2)", "-sin(x^2)", "2sin(x^2)", "2x*sin(x^2)", "sin(x^2+1)*x"),
    i("s.i.02", "x^3", "x^4/4", "-x^4/4", "x^4/2", None, "x^4/3"),
    i("s.i.03", "e^(2x)", "e^(2x)/2", "-e^(2x)/2", "2e^(2x)", "e^(2x)", "e^(2x+1)/2"),
    i(
        "s.i.04",
        "3/(3x+1)",
        "ln(3x+1)",
        "-ln(3x+1)",
        "3ln(3x+1)",
        "ln(3x+1)/3",
        "ln(3x+2)",
        extra="domain: x > 0",
    ),
    i("s.i.05", "cos(4x)", "sin(4x)/4", "-sin(4x)/4", "sin(4x)/2", "4sin(4x)", "sin(4x)/3"),
    i("s.i.06", "(x+1)^3", "(x+1)^4/4", "-(x+1)^4/4", "(x+1)^4/2", None, "(x+1)^3/3"),
    v("s.v.01", "limit(sin(5x)/x, x, 0)", "5", "-5", "10", "1", "6"),
    v("s.v.02", "limit((x^2-4)/(x-2), x, 2)", "4", "-4", "8", None, "3"),
    v("s.v.03", "subs(diff(x^3 - 3x, x), x, 2)", "9", "-9", "18", None, "10"),
    v("s.v.04", "integrate(3x^2, x, 0, 2)", "8", "-8", "16", None, "9"),
    v("s.v.05", "subs(diff(e^(2x), x), x, 0)", "2", "-2", "4", "1", "3"),
    v("s.v.06", "subs(diff(x^2*e^x, x), x, 1)", "3e", "-3e", "6e", None, "4e"),
)


def card_text(fx: Fixture, key: str, cid: str) -> str:
    claims = "\n".join(f"   check: {c}" for c in fx.claims)
    wrong = f"wrong: {fx.wrong}\n" if fx.wrong else ""
    extra = f"{fx.extra}\n" if fx.extra else ""
    return f"""
## Card {cid}
skill: s.calc
difficulty: 2
answer-type: {fx.kind}
answer: {key}
{wrong}{extra}
### Question
Work it out.

### Hints
1. Write down the rule first.

### Solution
0. [s.calc] Set up: choose the rule.
1. [s.calc] Work: the result is below.
{claims}
"""


def _build(cards: list[str], verify: bool) -> PackBuild:
    meta = PackMeta("seeded", "Seeded", "1.0.0", "personal")
    source = Source("seeded.cards.md", HEAD + "".join(cards))
    return check_pack(meta, [source], [Source("skills.md", SKILLS)], built_at=1, verify=verify)


@dataclass
class Report:
    control_errors: list[str] = field(default_factory=list)
    total: dict[str, int] = field(default_factory=dict)
    rejected: dict[str, dict[str, int]] = field(default_factory=dict)  # mode -> type -> count
    missed: list[str] = field(default_factory=list)  # "id type key" passed by the whole pipeline

    def fraction(self, mode: str, kind: str) -> float:
        return self.rejected[mode].get(kind, 0) / self.total[kind] if self.total.get(kind) else 0.0

    def table(self) -> str:
        lines = [f"{'error type':<12} {'seeded':>6} {'pipeline':>9} {'self-check':>11}"]
        for kind in ERROR_TYPES:
            whole, alone = self.fraction("pipeline", kind), self.fraction("self-check", kind)
            lines.append(f"{kind:<12} {self.total.get(kind, 0):>6} {whole:>9.0%} {alone:>11.0%}")
        n = sum(self.total.values())
        caught = {m: sum(self.rejected[m].values()) for m in self.rejected}
        lines.append(
            f"{'all':<12} {n:>6} {caught['pipeline'] / n:>9.0%} {caught['self-check'] / n:>11.0%}"
        )
        return "\n".join(lines)


def run() -> Report:
    report = Report()
    control = _build([card_text(fx, fx.key, fx.id) for fx in FIXTURES], verify=True)
    report.control_errors = list(control.errors)
    mutated: list[tuple[str, str, str]] = []  # (card id, error type, key)
    cards: list[str] = []
    for fx in FIXTURES:
        for kind, key in fx.seeded.items():
            cid = f"{fx.id}.{kind}"
            key = key if fx.kind != "antiderivative" else f"{key} + C"
            mutated.append((cid, kind, key))
            cards.append(card_text(fx, key, cid))
            report.total[kind] = report.total.get(kind, 0) + 1
    for mode, verify in (("pipeline", True), ("self-check", False)):
        build = _build(cards, verify=verify)
        failed = {cid for cid, _, _ in mutated if any(f"card {cid}" in e for e in build.errors)}
        rejected_ids = {r.card_id for r in build.loaded.rejected} | failed
        report.rejected[mode] = {}
        for cid, kind, key in mutated:
            if cid in rejected_ids:
                report.rejected[mode][kind] = report.rejected[mode].get(kind, 0) + 1
            elif mode == "pipeline":
                report.missed.append(f"{cid} {key}")
    return report


def main() -> int:
    from core.cards import shutdown
    from core.grader import shutdown as grader_shutdown

    try:
        report = run()
    finally:
        shutdown()
        grader_shutdown()
    if report.control_errors:
        print("control cards do not build clean:", *report.control_errors, sep="\n  ")
        return 1
    print(report.table())
    for m in report.missed:
        print(f"passed: {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
