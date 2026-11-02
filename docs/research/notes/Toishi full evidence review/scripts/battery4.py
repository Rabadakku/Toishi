import sys, time
sys.path.insert(0, "/home/claude/toishi")
from core.grader import AnswerSpec, grade
def S(t, a, **kw): return AnswerSpec(answer_type=t, answer=a, **kw)
E = lambda a, **kw: S("expression", a, **kw)
N = lambda a, **kw: S("number", a, **kw)
cases = [
 ("T1 simplified key sqrt(2) | 2/sqrt(2)", N("sqrt(2)", form="simplified"), "2/sqrt(2)"),
 ("T2 simplified key 2*sqrt(3) | sqrt(12)", N("2*sqrt(3)", form="simplified"), "sqrt(12)"),
 ("T3 simplified key 2*sqrt(3) | 6/sqrt(3)", N("2*sqrt(3)", form="simplified"), "6/sqrt(3)"),
 ("T4 simplified key 3*sqrt(5) | sqrt(45)", N("3*sqrt(5)", form="simplified"), "sqrt(45)"),
 ("T5 simplified key 5*sqrt(2)/2 | 5/sqrt(2)", N("5*sqrt(2)/2", form="simplified"), "5/sqrt(2)"),
 ("T6 simplified key 5*sqrt(2)/2 | sqrt(50)/2", N("5*sqrt(2)/2", form="simplified"), "sqrt(50)/2"),
 ("T7 simplified key (x+1)/(x-1) | (x^2+x)/(x^2-x)", E("(x+1)/(x-1)", form="simplified"), "(x^2+x)/(x^2-x)"),
 ("T8 simplified key x^2 | x*x", E("x^2", form="simplified"), "x*x"),
 ("T9 simplified key 2*x | x+x", E("2*x", form="simplified"), "x+x"),
 ("T10 simplified key 1/2 | 3/6", N("1/2", form="simplified"), "3/6"),
 ("T11 simplified key 7/3 | 2+1/3", N("7/3", form="simplified"), "2+1/3"),
 ("T12 simplified key sqrt(3)/3 | 1/sqrt(3)", N("sqrt(3)/3", form="simplified"), "1/sqrt(3)"),
 ("T13 default key 2*sqrt(2) | sqrt(8) (no form)", N("2*sqrt(2)"), "sqrt(8)"),
]
w = max(len(c[0]) for c in cases)
if __name__ == "__main__":
    for label, spec, student in cases:
        t0 = time.perf_counter()
        r = grade(student, spec, "text")
        dt = (time.perf_counter()-t0)*1000
        print(f"{label:<{w}} -> {r.status.value:<11} {dt:5.0f} ms  {(r.message or '')[:70]}", flush=True)
