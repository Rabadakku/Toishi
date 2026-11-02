"""Independent pure-Python FSRS-6 reference (transcribed from fsrs-rs v6.6.2 src/model.rs)
used to produce and cross-check numeric test vectors."""
import math

W = [0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666,
     0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542]
S_MIN, S_MAX, D_MIN, D_MAX = 0.001, 36500.0, 1.0, 10.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def factor(w):
    return 0.9 ** (-1.0 / w[20]) - 1.0


def retrievability(w, t, s):
    return (1.0 + factor(w) * t / s) ** (-w[20])


def interval(w, s, r):
    return s / factor(w) * (r ** (-1.0 / w[20]) - 1.0)


def s0(w, g):
    return w[g - 1]


def d0(w, g):
    return w[4] - math.exp(w[5] * (g - 1)) + 1.0


def next_d(w, d, g):
    delta = -w[6] * (g - 3)
    d1 = d + (10.0 - d) * delta / 9.0          # linear damping
    d2 = w[7] * d0(w, 4) + (1.0 - w[7]) * d1   # mean reversion toward D0(4)
    return clamp(d2, D_MIN, D_MAX)


def s_success(w, s, d, r, g):
    hard = w[15] if g == 2 else 1.0
    easy = w[16] if g == 4 else 1.0
    return s * (math.exp(w[8]) * (11.0 - d) * s ** (-w[9]) * (math.exp((1.0 - r) * w[10]) - 1.0) * hard * easy + 1.0)


def s_fail(w, s, d, r):
    long_term = w[11] * d ** (-w[12]) * ((s + 1.0) ** w[13] - 1.0) * math.exp((1.0 - r) * w[14])
    short_cap = s / math.exp(w[17] * w[18])
    return min(long_term, short_cap)


def s_short(w, s, g):
    sinc = math.exp(w[17] * (g - 3 + w[18])) * s ** (-w[19])
    return s * (max(sinc, 1.0) if g >= 2 else sinc)


def step(w, state, g, delta_t):
    """state=None for first review. delta_t is an integer number of Anki days."""
    if state is None:
        return clamp(s0(w, g), S_MIN, S_MAX), clamp(d0(w, g), D_MIN, D_MAX)
    s, d = clamp(state[0], S_MIN, S_MAX), clamp(state[1], D_MIN, D_MAX)
    r = retrievability(w, delta_t, s)
    if delta_t == 0:
        ns = s_short(w, s, g)
    elif g == 1:
        ns = s_fail(w, s, d, r)
    else:
        ns = s_success(w, s, d, r, g)
    return clamp(ns, S_MIN, S_MAX), next_d(w, d, g)


def replay(w, reviews):
    """reviews = [(rating, delta_t), ...] first has delta_t 0."""
    state = None
    for g, dt in reviews:
        state = step(w, state, g, dt)
    return state


def logloss(preds, labels, weights=None):
    weights = weights or [1.0] * len(preds)
    tot = sum(-(y * math.log(p) + (1 - y) * math.log(1 - p)) * w for p, y, w in zip(preds, labels, weights))
    return tot / sum(weights)


def recency_weights(n):
    length = max(n - 1.0, 1.0)
    return [0.25 + 0.75 * (i / length) ** 3 for i in range(n)]


def bins(delta_t, long_term_cnt_before, lapses):
    # fsrs-rs dataset.rs r_matrix_index (note: delta_t bin is x100 and rounded to int)
    dt = round(2.48 * 3.62 ** math.floor(math.log(delta_t, 3.62)) * 100) if delta_t > 0 else None
    length = long_term_cnt_before + 1.0
    lb = round(1.99 * 1.89 ** math.floor(math.log(length, 1.89)))
    if lapses == 0:
        return dt, lb, 0
    return dt, lb, round(1.65 * 1.73 ** math.floor(math.log(lapses, 1.73)))
