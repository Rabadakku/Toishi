import sys, time
sys.path.insert(0, "/home/claude/toishi")
from core.grader import AnswerSpec, grade

def S(t, a, **kw):
    return AnswerSpec(answer_type=t, answer=a, **kw)

E = lambda a, **kw: S("expression", a, **kw)
N = lambda a, **kw: S("number", a, **kw)

cases = [
 # --- A. holes / direction asymmetry
 ("A1 key tan(x) | sin(x)/cos(x)", E("tan(x)"), "sin(x)/cos(x)"),
 ("A2 key sin(x)/cos(x) | tan(x)", E("sin(x)/cos(x)"), "tan(x)"),
 ("A3 key 1/(1-cos(x)) | (1+cos(x))/sin(x)^2", E("1/(1-cos(x))"), "(1+cos(x))/sin(x)^2"),
 ("A4 key 1/(x-1) | x/(x^2-x)", E("1/(x-1)"), "x/(x^2-x)"),
 ("A5 key x/(x^2-x) | 1/(x-1)", E("x/(x^2-x)"), "1/(x-1)"),
 ("A6 key ln(x^2) | 2*ln(x)", E("ln(x^2)"), "2*ln(x)"),
 ("A7 key 2*ln(x) | ln(x^2)", E("2*ln(x)"), "ln(x^2)"),
 ("A8 key (x^2-4)/(x-2)+x | 2x+2", E("(x^2-4)/(x-2)+x"), "2x+2"),
 ("A9 key x+1 | (x^2-1)/(x-1)", E("x+1"), "(x^2-1)/(x-1)"),
 ("A10 key 1 | x/x", E("1"), "x/x"),
 ("A11 key sin(x) | tan(x)*cos(x)", E("sin(x)"), "tan(x)*cos(x)"),
 ("A12 key sin(x) | tan(x)*cos(x), domain -1<x<1", E("sin(x)", domain="-1 < x < 1"), "tan(x)*cos(x)"),
 ("A13 key (x-1)/(x^2-1) | 1/(x+1)", E("(x-1)/(x^2-1)"), "1/(x+1)"),
 ("A14 key 1/(x+1) | (x-1)/(x^2-1)", E("1/(x+1)"), "(x-1)/(x^2-1)"),
 # --- B. parsing / precedence / implicit multiplication
 ("B1 key x/2 | 1/2x", E("x/2"), "1/2x"),
 ("B2 key 1/(2*x) | 1/2x", E("1/(2*x)"), "1/2x"),
 ("B3 key 1/(2*x) | 1/2*x", E("1/(2*x)"), "1/2*x"),
 ("B4 key sin(2*x) | sin 2x", E("sin(2*x)"), "sin 2x"),
 ("B5 key sin(2*x) | sin2x", E("sin(2*x)"), "sin2x"),
 ("B6 key sin(x)^2 | sin^2(x)", E("sin(x)^2"), "sin^2(x)"),
 ("B7 key sin(x)^2 | sin^2 x", E("sin(x)^2"), "sin^2 x"),
 ("B8 key arcsin(x) | sin^-1(x)", E("arcsin(x)"), "sin^-1(x)"),
 ("B9 key 1/sin(x) | sin^-1(x)", E("1/sin(x)"), "sin^-1(x)"),
 ("B10 key -4 | -2^2", N("-4"), "-2^2"),
 ("B11 key 4 | -2^2", N("4"), "-2^2"),
 ("B12 key 512 | 2^3^2", N("512"), "2^3^2"),
 ("B13 key 64 | 2^3^2", N("64"), "2^3^2"),
 ("B14 key 1/x | x^-1", E("1/x"), "x^-1"),
 ("B15 key 1/(x+1) | 1/x+1", E("1/(x+1)"), "1/x+1"),
 ("B16 key x*e^x | xe^x", E("x*e^x"), "xe^x"),
 ("B17 key x*e^x | x e^x", E("x*e^x"), "x e^x"),
 ("B18 key x*e^x | x*e^x", E("x*e^x"), "x*e^x"),
 ("B19 key 2*x^2 | 2x^2", E("2*x^2"), "2x^2"),
 ("B20 key 4*x^2 | (2x)^2", E("4*x^2"), "(2x)^2"),
 ("B21 key x^2 | x²", E("x^2"), "x²"),
 ("B22 key sqrt(2) | √2", N("sqrt(2)"), "√2"),
 ("B23 key pi | π", N("pi"), "π"),
 ("B24 key 6 | 2·3", N("6"), "2·3"),
 ("B25 key -3 | −3 (U+2212)", N("-3"), "−3"),
 ("B26 key 1000 | 1,000", N("1000"), "1,000"),
 ("B27 key 0.5 | 0,5", N("0.5"), "0,5"),
 ("B28 key 0.5 | 50%", N("0.5"), "50%"),
 ("B29 key 0.5 | .5", N("0.5"), ".5"),
 ("B30 key 12000 | 1.2e4", N("12000"), "1.2e4"),
 ("B31 key 12000 | 1.2*10^4", N("12000"), "1.2*10^4"),
 ("B32 key 12000 | 1.2x10^4", N("12000"), "1.2x10^4"),
 ("B33 key 12000 | 1.2×10^4", N("12000"), "1.2×10^4"),
 ("B34 key 2 | 4/2/1 ", N("2"), "4/2/1"),
 ("B35 key 8 | 16/2/1 (left assoc)", N("8"), "16/2/1"),
 ("B36 key 32 | 16/2*4 (left assoc)", N("32"), "16/2*4"),
 ("B37 key 2 | 16/2*4 (wrong assoc check)", N("2"), "16/2*4"),
 # --- C. numeric tolerance (default 0.1% relative) and approximation
 ("C1 key 1/3 | 0.333", N("1/3"), "0.333"),
 ("C2 key 1/3 | 0.3333", N("1/3"), "0.3333"),
 ("C3 key 1/3 | 0.33", N("1/3"), "0.33"),
 ("C4 key 2/3 | 0.667", N("2/3"), "0.667"),
 ("C5 key 2/3 | 0.67", N("2/3"), "0.67"),
 ("C6 key 2/3 | 0.66", N("2/3"), "0.66"),
 ("C7 key sqrt(2) | 1.414", N("sqrt(2)"), "1.414"),
 ("C8 key sqrt(2) | 1.41", N("sqrt(2)"), "1.41"),
 ("C9 key pi | 22/7", N("pi"), "22/7"),
 ("C10 key pi | 355/113", N("pi"), "355/113"),
 ("C11 key pi, tolerance 1e-9 | 355/113", N("pi", tolerance="1e-9"), "355/113"),
 ("C12 key 0.1 | 1/10", N("0.1"), "1/10"),
 ("C13 key 1/3 exact | 0.3333", N("1/3", exact=True), "0.3333"),
 ("C14 key 1/3 exact | 2/6", N("1/3", exact=True), "2/6"),
 ("C15 key 100 | 100.05", N("100"), "100.05"),
 ("C16 key 100 | 100.2", N("100"), "100.2"),
 # --- D. intervals / sets
 ("D1 interval (-inf,2] | x<=2", S("interval","(-inf, 2]"), "x <= 2"),
 ("D2 interval [1,3) U (3,5] | 1<=x<5 and x!=3", S("interval","[1, 3) U (3, 5]"), "1 <= x < 5 and x != 3"),
 ("D3 interval [1,3) U (3,5] | [1,3) ∪ (3,5]", S("interval","[1, 3) U (3, 5]"), "[1,3) ∪ (3,5]"),
 ("D4 interval (1,3) | 1<x<3", S("interval","(1, 3)"), "1 < x < 3"),
 ("D5 interval (1,3) | (1,3]", S("interval","(1, 3)"), "(1, 3]"),
 ("D6 interval (1,3) | (1.0000000001, 3)", S("interval","(1, 3)"), "(1.0000000001, 3)"),
 ("D7 interval [0,1] U [1,2] | [0,2]", S("interval","[0, 2]"), "[0,1] U [1,2]"),
 ("D8 interval (0,1) U (1,2) | (0,2)", S("interval","(0, 2)"), "(0,1) U (1,2)"),
 ("D9 set {1,2} | {2,1}", S("set","1, 2"), "{2, 1}"),
 # --- F. equations
 ("F1 eq y=2x+1 | y-2x=1", S("equation","y = 2*x + 1"), "y - 2x = 1"),
 ("F2 eq x^2+y^2=1 | y=sqrt(1-x^2)", S("equation","x^2 + y^2 = 1"), "y = sqrt(1-x^2)"),
 ("F3 eq y=x^2 | y/x^2=1", S("equation","y = x^2"), "y/x^2 = 1"),
 ("F4 eq y=x^2 | x^2=y", S("equation","y = x^2"), "x^2 = y"),
 ("F5 eq y=2x+1 | 2y=4x+2", S("equation","y = 2*x + 1"), "2y = 4x + 2"),
 ("F6 eq y=2x+1 | y=2x+1.0000001", S("equation","y = 2*x + 1"), "y = 2x + 1.0000001"),
 # --- N. no-go inputs and DoS probes (time shown)
 ("G1 1000 nested parens", E("x"), "(" * 1000 + "x" + ")" * 1000),
 ("G2 10k-char sum", E("x"), "+".join(["x"] * 3000)),
 ("G3 factorial(100000)", N("2"), "100000!"),
 ("G4 ((10^1000)^1000)^1000", N("2"), "((10^1000)^1000)^1000"),
 ("G5 10^1000", N("2"), "10^1000"),
 ("G6 sin(10^100)", N("2"), "sin(10^100)"),
 ("G7 x^x^x^x big", E("x"), "x^x^x^x"),
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
