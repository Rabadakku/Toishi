import sys, time
sys.path.insert(0, "/home/claude/toishi")
from core.grader import AnswerSpec, grade

def S(t, a, **kw):
    return AnswerSpec(answer_type=t, answer=a, **kw)
E = lambda a, **kw: S("expression", a, **kw)
N = lambda a, **kw: S("number", a, **kw)

cases = [
 ("D2b interval [1,3) U (3,5] | 1<=x<=5 and x!=3", S("interval","[1, 3) U (3, 5]"), "1 <= x <= 5 and x != 3"),
 ("D10 interval empty | empty", S("interval","empty"), "empty"),
 ("H1 tiny diff: key x^2 | x^2+10^(-50)*x", E("x^2"), "x^2+10^(-50)*x"),
 ("H2 tiny diff: key x | x+sin(10^6*x)*10^(-12)", E("x"), "x+sin(10^6*x)*10^(-12)"),
 ("H3 tiny diff: key 1 | 1+10^(-45)", N("1"), "1+10^(-45)"),
 ("H4 tiny diff: key 1 | 1.000000000000000000000000000000000000000000001", N("1"), "1.000000000000000000000000000000000000000000001"),
 ("S1a simplified key 2*sqrt(2) | sqrt(8)", E("2*sqrt(2)", form="simplified"), "sqrt(8)"),
 ("S1b simplified key 2*sqrt(2) | 2*sqrt(2)", E("2*sqrt(2)", form="simplified"), "2*sqrt(2)"),
 ("S1c simplified key 2*sqrt(2) | 4/sqrt(2)", E("2*sqrt(2)", form="simplified"), "4/sqrt(2)"),
 ("S1d simplified key 2*sqrt(2) | sqrt(2)*2", E("2*sqrt(2)", form="simplified"), "sqrt(2)*2"),
 ("S1e simplified key 2*sqrt(2) | sqrt(2)+sqrt(2)", E("2*sqrt(2)", form="simplified"), "sqrt(2)+sqrt(2)"),
 ("S1f simplified key 2*sqrt(2) | 2^(3/2)", E("2*sqrt(2)", form="simplified"), "2^(3/2)"),
 ("S2a factored key (x+1)^2 | x^2+2x+1", E("(x+1)^2", form="factored"), "x^2+2x+1"),
 ("S2b factored key (x+1)^2 | (x+1)*(x+1)", E("(x+1)^2", form="factored"), "(x+1)*(x+1)"),
 ("S2c factored key (x+1)^2 | (x+1)^2", E("(x+1)^2", form="factored"), "(x+1)^2"),
 ("S2d factored key (x+1)^2 | 1*(x+1)^2", E("(x+1)^2", form="factored"), "1*(x+1)^2"),
 ("S2e factored key (x+1)^2 | x*(x+2)+1", E("(x+1)^2", form="factored"), "x*(x+2)+1"),
 ("S2f factored key (x-1)(x+1) | (x^2-1)", E("(x-1)*(x+1)", form="factored"), "x^2-1"),
 ("S2g factored key (x-1)(x+1) | (x-1)*(x+1)*1", E("(x-1)*(x+1)", form="factored"), "(x-1)*(x+1)*1"),
 ("S3a expanded key x^2+2x+1 | (x+1)^2", E("x^2+2*x+1", form="expanded"), "(x+1)^2"),
 ("S3b expanded key x^2+2x+1 | x*x+2*x+1", E("x^2+2*x+1", form="expanded"), "x*x+2*x+1"),
 ("S3c expanded key x^2+2x+1 | 1+2*x+x^2", E("x^2+2*x+1", form="expanded"), "1+2*x+x^2"),
 ("S3d expanded key x^2+2x+1 | x^2+x+x+1", E("x^2+2*x+1", form="expanded"), "x^2+x+x+1"),
 ("S3e expanded key x^2+2x+1 | x^2+2*x+1+0", E("x^2+2*x+1", form="expanded"), "x^2+2*x+1+0"),
 ("S4a lowest-terms key 3/4 | 6/8", N("3/4", form="lowest-terms"), "6/8"),
 ("S4b lowest-terms key 3/4 | 3/4", N("3/4", form="lowest-terms"), "3/4"),
 ("S4c lowest-terms key 3/4 | 0.75", N("3/4", form="lowest-terms"), "0.75"),
 ("S4d lowest-terms key 3/4 | -3/-4", N("3/4", form="lowest-terms"), "-3/-4"),
 ("S4e lowest-terms key 3/4 | 1.5/2", N("3/4", form="lowest-terms"), "1.5/2"),
 ("S4f lowest-terms key -3/4 | 3/-4", N("-3/4", form="lowest-terms"), "3/-4"),
 ("S4g lowest-terms key 3/4 | (3/4)", N("3/4", form="lowest-terms"), "(3/4)"),
 ("S4h lowest-terms key 3/4 | 1/2+1/4", N("3/4", form="lowest-terms"), "1/2+1/4"),
 ("S5 simplified key sqrt(2)/2 | 1/sqrt(2)", N("sqrt(2)/2", form="simplified"), "1/sqrt(2)"),
 ("S5b simplified key 1/2 | 2/4", N("1/2", form="simplified"), "2/4"),
]
w = max(len(c[0]) for c in cases)
if __name__ == "__main__":
    for label, spec, student in cases:
        t0 = time.perf_counter()
        try:
            r = grade(student, spec, "text")
            dt = (time.perf_counter()-t0)*1000
            msg = (r.message or "")[:75].replace("\n"," ")
            print(f"{label:<{w}} -> {r.status.value:<11} {dt:6.0f} ms  {msg}", flush=True)
        except Exception as e:
            print(f"{label:<{w}} -> EXC {type(e).__name__}: {str(e)[:80]}", flush=True)
