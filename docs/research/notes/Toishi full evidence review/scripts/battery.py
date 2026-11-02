import sys, time
sys.path.insert(0, "/home/claude/toishi")
from core.grader import AnswerSpec, grade

def S(t, a, **kw):
    return AnswerSpec(answer_type=t, answer=a, **kw)

cases = [
 # (label, spec, student)
 ("STACK#1061 inequality var rename: key (1,inf), student 't > 1'", S("interval","(1, inf)"), "t > 1"),
 ("  same, student 'x > 1'", S("interval","(1, inf)"), "x > 1"),
 ("STACK#107 sigfig floor: 0.1667 m, 4 s.f., student 0.1667 m", S("quantity","0.1667 m", sig_figs=4), "0.1667 m"),
 ("  student 0.1666 m", S("quantity","0.1667 m", sig_figs=4), "0.1666 m"),
 ("  student 0.167 m (3 s.f.)", S("quantity","0.1667 m", sig_figs=4), "0.167 m"),
 ("  student 1.667e-1 m", S("quantity","0.1667 m", sig_figs=4), "1.667e-1 m"),
 ("  student 0.16670 m (5 s.f.)", S("quantity","0.1667 m", sig_figs=4), "0.16670 m"),
 ("large: key 10^100, student 10^100+1", S("number","10^100"), "10^100+1"),
 ("large: key 10^100, student 1e100", S("number","10^100"), "1e100"),
 ("large: key 10^100, student 10^100+10^50", S("number","10^100"), "10^100+10^50"),
 ("tiny: key 0, student 10^(-30)", S("number","0"), "10^(-30)"),
 ("tiny: key 0, student 0.0000001", S("number","0"), "0.0000001"),
 ("pi: student 355/113", S("number","pi"), "355/113"),
 ("pi: student 3.14159265", S("number","pi"), "3.14159265"),
 ("pi: student 3.14 (0.05% off)", S("number","pi"), "3.14"),
 ("pi: student 3.1", S("number","pi"), "3.1"),
 ("hole: key x+1, student (x^2-1)/(x-1)", S("expression","x+1"), "(x^2-1)/(x-1)"),
 ("hole: key (x^2-1)/(x-1), student x+1", S("expression","(x^2-1)/(x-1)"), "x+1"),
 ("hole: key (x^2-1)/(x-1), student (x+1)(x-1)/(x-1)", S("expression","(x^2-1)/(x-1)"), "(x+1)*(x-1)/(x-1)"),
 ("ln|x|: key 2*ln(abs(x)), student ln(x^2)", S("expression","2*ln(abs(x))"), "ln(x^2)"),
 ("ln: key 2*ln(x) (no domain), student ln(x^2)", S("expression","2*ln(x)"), "ln(x^2)"),
 ("ln: key 2*ln(x) domain x>0, student ln(x^2)", S("expression","2*ln(x)", domain="x > 0"), "ln(x^2)"),
 ("sqrt(x^2): key abs(x), student sqrt(x^2)", S("expression","abs(x)"), "sqrt(x^2)"),
 ("sqrt(x^2): key x, student sqrt(x^2)", S("expression","x"), "sqrt(x^2)"),
 ("cuberoot: key root(x,3), student x^(1/3)", S("expression","root(x,3)"), "x^(1/3)"),
 ("cuberoot: key x^(1/3) domain x>0, student root(x,3)", S("expression","x^(1/3)", domain="x > 0"), "root(x,3)"),
 ("9^9^9 as number", S("number","2"), "9^9^9"),
 ("equation: key x=4, student sqrt(x)=2", S("equation","x = 4"), "sqrt(x)=2"),
 ("equation: key y=2x+1, student 2x-y+1=0", S("equation","y = 2*x + 1"), "2x - y + 1 = 0"),
 ("atan sum: key pi/2 domain x>0, student atan(x)+atan(1/x)", S("expression","pi/2", domain="x > 0", vars=("x",)), "atan(x)+atan(1/x)"),
 ("atan sum: key pi/2 no domain, student atan(x)+atan(1/x)", S("expression","pi/2", vars=("x",)), "atan(x)+atan(1/x)"),
 ("trig: key 1, student sin(x)^2+cos(x)^2", S("expression","1", vars=("x",)), "sin(x)^2+cos(x)^2"),
 ("trig: key 1, student sec(x)^2-tan(x)^2", S("expression","1", vars=("x",)), "sec(x)^2-tan(x)^2"),
 ("antideriv: key ln(abs(x))+C (of 1/x), student ln(x)", S("antiderivative","ln(abs(x)) + C"), "ln(x)"),
 ("antideriv: key ln(abs(x))+C, student ln(abs(x))", S("antiderivative","ln(abs(x)) + C"), "ln(abs(x))"),
 ("antideriv: key ln(abs(x))+C, student ln(x^2)/2 + 7", S("antiderivative","ln(abs(x)) + C"), "ln(x^2)/2 + 7"),
 ("antideriv: key ln(x)+C domain x>0, student ln(x)", S("antiderivative","ln(x) + C", domain="x > 0"), "ln(x)"),
 ("units: key 9.8 m/s^2 sf2, student 980 cm/s^2", S("quantity","9.8 m/s^2", sig_figs=2), "980 cm/s^2"),
 ("units: student 9.8 m/s", S("quantity","9.8 m/s^2", sig_figs=2), "9.8 m/s"),
 ("units: student 9.8 (no unit)", S("quantity","9.8 m/s^2", sig_figs=2), "9.8"),
 ("units: student 9.80 m/s^2 (3 sf)", S("quantity","9.8 m/s^2", sig_figs=2), "9.80 m/s^2"),
 ("units: student 9.81 m/s^2", S("quantity","9.8 m/s^2", sig_figs=2), "9.81 m/s^2"),
 ("units temp: key 20 degC", S("quantity","20 degC", sig_figs=2), "293 K"),
 ("units case: key 5 mS vs ms", S("quantity","5 mS", sig_figs=1), "5 ms"),
 ("interval: [0,2] vs 0<=x<=2", S("interval","[0, 2]"), "0 <= x <= 2"),
 ("interval: [0,2] vs (0,2)", S("interval","[0, 2]"), "(0, 2)"),
 ("interval: (-inf,0)U(0,inf) vs x<0 or x>0", S("interval","(-inf, 0) U (0, inf)"), "x < 0 or x > 0"),
 ("interval: (-inf,0)U(0,inf) vs (-inf, inf)", S("interval","(-inf, 0) U (0, inf)"), "(-inf, inf)"),
 ("set order: -1,0,1 vs 1,0,-1", S("set","-1, 0, 1"), "1, 0, -1"),
 ("set dup: -1,0,1 vs -1,0,1,1", S("set","-1, 0, 1"), "-1, 0, 1, 1"),
 ("lowest-terms: 1/3 form lowest-terms, student 2/6", S("number","1/3", form="lowest-terms"), "2/6"),
 ("lowest-terms: student 0.3333", S("number","1/3", form="lowest-terms"), "0.3333"),
 ("exact: sqrt(2)/2 exact, student 0.7071", S("number","sqrt(2)/2", exact=True), "0.7071"),
 ("cardano: key 2, student (sqrt(108)+10)^(1/3)-(sqrt(108)-10)^(1/3)", S("number","2"), "(sqrt(108)+10)^(1/3)-(sqrt(108)-10)^(1/3)"),
 ("junk: DROP TABLE", S("expression","x"), "x; import os"),
 ("junk: dunder", S("expression","x"), "x.__class__"),
 ("junk: sinx", S("expression","sin(x)"), "sinx"),
 ("junk: e^2x", S("expression","e^(2*x)"), "e^2x"),
]

w = max(len(c[0]) for c in cases)
for label, spec, student in cases:
    t0 = time.perf_counter()
    try:
        r = grade(student, spec, "text")
        dt = (time.perf_counter()-t0)*1000
        msg = (r.message or "")[:70].replace("\n"," ")
        print(f"{label:<{w}} -> {r.status.value:<11} {dt:6.0f} ms  {msg}")
    except Exception as e:
        print(f"{label:<{w}} -> EXC {type(e).__name__}: {str(e)[:80]}")
