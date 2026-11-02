import sys, time
sys.path.insert(0, "/home/claude/toishi")
from core.grader import AnswerSpec, grade
def S(t, a, **kw): return AnswerSpec(answer_type=t, answer=a, **kw)
E = lambda a, **kw: S("expression", a, **kw)
N = lambda a, **kw: S("number", a, **kw)
cases = [
 ("U1 key 1 | 1+10^(-300)", N("1"), "1+10^(-300)"),
 ("U2 key 2 | sqrt(2)*sqrt(2)+10^(-200)", N("2"), "sqrt(2)*sqrt(2)+10^(-200)"),
 ("U3 key 2^1000 | 2^1000+1", N("2^1000"), "2^1000+1"),
 ("U4 key 0 | exp(-1000)", N("0"), "exp(-1000)"),
 ("U5 key x | x+exp(-1000*x^2)", E("x"), "x+exp(-1000*x^2)"),
 ("U6 key 0 | sin(pi)", N("0"), "sin(pi)"),
 ("U7 key 1 | cos(1)^2+sin(1)^2", N("1"), "cos(1)^2+sin(1)^2"),
 ("U8 key 5 | ln(exp(5))", N("5"), "ln(exp(5))"),
 ("U9 key sqrt(x*y) | sqrt(x)*sqrt(y)", E("sqrt(x*y)", vars=("x","y")), "sqrt(x)*sqrt(y)"),
 ("U10 key sqrt(x)*sqrt(y) | sqrt(x*y)", E("sqrt(x)*sqrt(y)", vars=("x","y")), "sqrt(x*y)"),
 ("U11 key -2 | (-8)^(1/3)", N("-2"), "(-8)^(1/3)"),
 ("U12 key root(-8,3) | -2", N("root(-8,3)"), "-2"),
 ("U13 key 2*sin(x)*cos(x) | sin(2*x)", E("2*sin(x)*cos(x)"), "sin(2*x)"),
 ("U14 key (1-cos(2*x))/2 | sin(x)^2", E("(1-cos(2*x))/2"), "sin(x)^2"),
 ("U15 key arctan(x)+arctan(1/x) domain x>0 | pi/2", E("arctan(x)+arctan(1/x)", domain="x > 0"), "pi/2"),
 ("U16 key x^x | exp(x*ln(x))", E("x^x"), "exp(x*ln(x))"),
 ("U17 key x^x domain x>0 | exp(x*ln(x))", E("x^x", domain="x > 0"), "exp(x*ln(x))"),
]
w = max(len(c[0]) for c in cases)
if __name__ == "__main__":
    for label, spec, student in cases:
        t0 = time.perf_counter()
        try:
            r = grade(student, spec, "text")
            dt = (time.perf_counter()-t0)*1000
            print(f"{label:<{w}} -> {r.status.value:<11} {dt:5.0f} ms  {(r.message or '')[:72]}", flush=True)
        except Exception as e:
            print(f"{label:<{w}} -> EXC {type(e).__name__}: {str(e)[:70]}", flush=True)
