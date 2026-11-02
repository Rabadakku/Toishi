import sys, time
sys.path.insert(0, "/home/claude/toishi")
from core.grader import AnswerSpec, grade

def S(t, a, **kw):
    return AnswerSpec(answer_type=t, answer=a, **kw)

cases = [
 ("V1 interval (1,inf) vars=(sigma,) | sigma > 1", S("interval", "(1, inf)", vars=("sigma",)), "sigma > 1"),
 ("V2 interval (1,inf) vars=(sigma,) | x > 1", S("interval", "(1, inf)", vars=("sigma",)), "x > 1"),
 ("V3 interval (1,inf) vars=(sigma,) | t > 1", S("interval", "(1, inf)", vars=("sigma",)), "t > 1"),
 ("V4 interval (1,inf) no vars | t > 1", S("interval", "(1, inf)"), "t > 1"),
 ("V5 interval (1,inf) no vars | (1, inf)", S("interval", "(1, inf)"), "(1, inf)"),
 ("V6 interval (1,inf) no vars | x > 1 and y > 1", S("interval", "(1, inf)"), "x > 1 and y > 1"),
 ("V7 interval (1,inf) no vars | x > 1 or t < 0", S("interval", "(1, inf)"), "x > 1 or t < 0"),
 ("V8 expr e^(2x) | e^2x", S("expression", "e^(2*x)", vars=("x",)), "e^2x"),
 ("V9 expr e^(2x) | e^(2x)", S("expression", "e^(2*x)", vars=("x",)), "e^(2x)"),
 ("V10 expr e^(2x) | (e^2)*x", S("expression", "e^(2*x)", vars=("x",)), "(e^2)*x"),
 ("V11 expr (e^2)*x | e^2x", S("expression", "(e^2)*x", vars=("x",)), "e^2x"),
]
if __name__ == "__main__":
    for label, spec, student in cases:
        t0 = time.perf_counter()
        try:
            r = grade(student, spec, "text")
            dt = (time.perf_counter()-t0)*1000
            msg = (r.message or "")[:90].replace("\n"," ")
            extra = {k: v for k, v in vars(r).items() if k not in ("status","message")} if hasattr(r, "__dict__") else {}
            print(f"{label:<50} -> {r.status.value:<11} {dt:6.0f} ms  {msg}  {str(extra)[:160]}")
        except Exception as e:
            print(f"{label:<50} -> EXC {type(e).__name__}: {str(e)[:120]}")
