# ADR-0003: Nothing typed by the user is ever evaluated as code

- Status: Accepted
- Date: 2026-11-01

## Context

Answers are typed math (MathLive gives LaTeX). The easy path, `sympy.sympify(text)` or
`parse_expr(text)`, runs Python `eval` on a string derived from user input. `lambdify`
`exec`s generated source in which symbol names appear verbatim.

## Decision

- Banned in our code (`core/`, `app/`, `scripts/`, `spike/`, specs): `eval`, `exec`,
  `compile`, `__import__`, `sympify` (any import path), `S(...)` calls (`S.Half` is fine),
  `parse_expr`, anything from `sympy.parsing`, `lambdify`.
- Enforced twice: ruff (`S102`, `S307`, `TID251` banned-api in `pyproject.toml`) and
  `tests/test_no_eval.py` (AST scan, with self-tests proving it catches each pattern).
- User text will be parsed by our own Lark grammar into SymPy objects built explicitly
  (`Symbol`, `Integer`, `Add`, ...). Never pass a `str` that came from the user into any
  SymPy function: most of them call `sympify` on their arguments.
- In the page: no `eval`, `new Function`, or string timers in `web/src` (same test), and
  the CSP has no `'unsafe-eval'` (ADR-0002), so the engine refuses them anyway.

## Consequences

- A runtime block of SymPy's string parser is not workable: `simplify` (via unit prefixes),
  definite `integrate` and `nsimplify` parse SymPy's own constant strings internally. The
  rule is therefore about what we pass in, guarded statically and by code review.
- Answer checking will also run in a worker process with a timeout (later milestone), so a
  pathological expression cannot hang the UI.
