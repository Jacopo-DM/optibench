# CLAUDE.md

Read PLAN.md first in every session, then DESIGN.md for the approved spec and
the reasoning behind the code, CODEMAP.md for its structure, and
`src/optibench/README.md` before changing the package. If any of them
disagrees with the code, trust the code and fix the file.

## Commands

All commands run from the repo root with uv (Python 3.13).

| Purpose | Command |
|---------|---------|
| Install or rebuild the environment (numpy, pydantic, sympy, numba; dev group: pytest, pytest-cov, hypothesis, mypy, pyright, ty, ruff, pillow, pre-commit, nbclient, nbformat, ipykernel, coco-experiment, which has no Python 3.13 wheel and is compiled from its source archive with Xcode's compiler) | `uv sync` |
| Format | `uv run ruff format` |
| Lint (auto-fixes, unsafe fixes included: read the diff) | `uv run ruff check` |
| Lint as the Stop hook and CI do | `uv run ruff format --check && uv run ruff check --no-fix` |
| Type check (strict, no `Any`; the one the Stop hook runs) | `uv run mypy .` |
| Type check as the editor does (strict, `pyrightconfig.json`) | `uv run pyright` |
| Advisory type check (`ty.toml`; never blocks, 2 known numpy-stub findings in PLAN.md) | `uv run --locked ty check` |
| Tests, with 100% branch coverage over `src` and `tests` enforced by `pytest.ini`, under the 2 GB memory watchdog (about 2.5 min at load 4 to 8, most of it the formula test's sympy work and the 45 s compiled pole check in a child process; run one file with the command below while working) | `uv run pytest` |
| Run every pre-commit hook (the same checks through `uv run --locked`; `uv run pre-commit install` installs the pre-commit and pre-push hooks, and pre-push runs `tools/run_notebooks.py`, which finds no notebooks yet) | `uv run pre-commit run --all-files` |
| One test file quickly, no coverage | `uv run pytest tests/test_x.py -k name --no-cov` |
| Time every function on 100,000 points, spec criterion 2 (about 5 s; table, `__data__/timing.csv`, exit status 1 if any is over 0.1 s, except the stated exceptions in `src/optibench/scripts/timing.py`) | `uv run python -m optibench.scripts.timing [--points N] [--repeats K]` |
| Time the double pole on 1,000 reference networks for 100,000 steps, goal network-core (about 3 min; 5 repeats, median and spread, exit status 1 if the median is over 35 s; run nothing else meanwhile) | `uv run python -m optibench.scripts.pole_timing [--networks N] [--steps S] [--repeats K]` |
| Run the random-search baseline on every function, 10 seeds of 10,000 points (about 1 s; table, curves in `__data__/baseline/`) | `uv run python -m optibench.scripts.baseline [--budget N] [--seeds K]` |

`mypy.ini`, `ruff.toml`, `pytest.ini`, `pyrightconfig.json`, `ty.toml`,
`.pre-commit-config.yaml`, `.github/`, `.gitignore` (below its PROJECT
section), `tools/compress_images.py` and `tools/run_notebooks.py` are copies
of the user's templates in `~/Functions/_rsync/`: never edit them to get a
check through (the Stop hook compares them with the templates); refresh
them with `rsync-sync pull python` in a clean tree and read the diff (it
also copies `main.py`, which this library deletes). Approved
exceptions, both from Dependabot (the user, 2026-10-23 and 2026-10-24):
`ci.yml` keeps setup-uv v10.3.0 over the template's v9.0.0, and uv 0.13.4
(the uv-pre-commit `rev` in `.pre-commit-config.yaml` and `version` in
`ci.yml`, kept equal) over the template's 0.13.1; put those lines back
after a refresh.
The `.gitignore` ignores `.typings/` as the template does, but the `cocoex`
stub there stays tracked; a new file there needs `git add -f`.

Before every commit run format, lint, both type checks and the tests above.

## Rules

- Keep the four state files up to date at all times, in the same commit as
  the change that makes them stale: PLAN.md (state, remaining work, known
  problems), CODEMAP.md (modules, interfaces, line counts), DESIGN.md (spec,
  decisions, rejected approaches, results) and this file (commands, rules).
  Each fact lives in exactly one file.
- This library never imports `entwined` or any other optimiser code, and
  depends on numpy, pydantic, sympy (for `formula()`, approved
  2026-10-17) and numba (for the network simulations, approved
  2026-10-24) only at run time. numba is imported only in
  `networks/compiled.py`. A new run-time dependency needs the user's
  approval.
- Every function is written from its published formula, never from the
  SFU site's MATLAB or R code (GPL-2.0). Read the formula image on the
  function's SFU page (`<page>2.png` and so on) and the cited paper.
- BBOB functions are written from RR-6829's formulas, and their instances
  (the random generator, `x_opt`, `f_opt`, rotations) from COCO's BSD code;
  where COCO's code and the report differ, follow the code, say so in the
  class docstring, and add the function to the `cocoex` comparison in
  `tests/test_bbob.py` (every function, d = 2 to 40, instances 1, 2, 7, 15,
  100, to 1e-12, or 1e-9 where `RTOL` there says why). `cocoex` is a test
  reference only; never import it in
  `src`.
- Adding a function (spec criteria 1 to 7): a subclass of `Problem` (a
  frozen pydantic model; fields are keyword arguments; mark each
  `_evaluate`, `default_bounds`, `minimum` and `_check` with
  `@typing.override`) (or of `AnyDimension` when any `d` works, which
  supplies the `d` field) in the module of its SFU group under
  `src/optibench/functions/` (a function from another collection goes in
  that collection's modules, `classics_*.py`, with its `suite` set); every constant of the formula is a field with
  the published default (see DESIGN.md for which constants count);
  `name`, `group`, `url` and `references` as `ClassVar`s (shared references
  in `functions/references.py`); `dimension`, `default_bounds`, `minimum`
  and `_evaluate`; a `_check` for parameters that can be wrong (call
  `super()._check()` in an `AnyDimension`). Export it from
  `functions/__init__.py` (the registry reads that list) and from
  `optibench/__init__.py`. The tests in `tests/test_all_problems.py` then
  cover it automatically; add tests of its published constants, its
  published minimum and its parameter handling in the group's test file.
- A minimum that holds only for the published constants (found
  numerically, or published without a proof for other constants) goes in
  `functions/known_minima.py` with where it comes from, and the function
  returns
  `at_defaults(self, CONSTANT)`, which gives it only for the published
  constants and domain. Check a candidate with a grid over the whole domain,
  not only near the published point, and keep Newton steps inside the
  domain: the Eggholder's minimum is on the edge, and unconstrained steps
  left the box to a lower value.
- A minimum is only stated when it is certain: from a formula, from the
  literature, or found numerically from a published point (say which in
  `Minimum.source`, and give its accuracy in `Minimum.tolerance`).
- Evaluation is vectorised over the batch: no Python loop over points.
  A simulation that steps one network at a time loops in code compiled
  through `networks/compiled.py` instead; tests run it uncompiled
  (`NUMBA_DISABLE_JIT=1` in `tests/conftest.py`), so a change there is
  checked compiled too, by the child-process test in
  `tests/test_networks_poles.py`.
- Keep each file under 400 lines; split a group module before it grows past,
  alphabetically, naming the parts after their first and last function
  (`many_local_minima_bukin_to_gramacy.py`) or after what they share
  (`bbob_separable.py`).
- No abstraction without two real call sites today. Delete replaced code
  outright: no shims or old and new versions side by side.
- Put one blank line before every comment that introduces a block of code.
- Typed Python, pyright strict, numpy for data, one seeded
  `numpy.random.Generator` in tests.

## Ignore list (never read or edit these when working on features)

| Path | Hand-written or generated | Made by |
|------|---------------------------|---------|
| `.venv/` | generated | `uv sync` / `uv run` |
| `uv.lock` | generated | `uv add`, `uv lock`; never edit by hand |
| `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `.coverage` | generated | pytest, ruff, the interpreter, pytest-cov |
| `__data__/` | generated, git-ignored (`timing.csv`, `baseline/` curves, `plots/`) | `optibench.scripts.timing`, `optibench.scripts.baseline` |
| `src/optibench/py.typed` | hand-written, empty marker | n/a |
| `.typings/cocoex/__init__.pyi` | hand-written stub (only `Suite`) so pyright finds `cocoex`; mypy does not read it (`tests/test_bbob.py` casts instead) | n/a |

## Things that bite

- sympy can take the whole machine's memory. One BBOB f3 formula at d = 2
  whose piecewise conditions held another piecewise (T_asy testing the
  sign of T_osz; sympy rewrites that as an `ITE` condition) grew to 160 GB
  inside `lambdify` on 2026-10-18 before macOS killed it, with only exit
  status 137 to show. `evaluate_formula` now refuses such a formula with a
  ValueError; write the condition on the inner piecewise's own variable
  (`functions/bbob_symbolic.py` shows how). Every pytest run starts
  `tests/memory_guard.py` from `tests/conftest.py`, which stops the
  process with tracebacks (exit status 3) once its peak memory passes
  2 GB; the suite peaks near 200 MB. Any sympy experiment outside pytest
  starts the guard first: begin the script with `import sys;
  sys.path.insert(0, "tests"); import memory_guard; memory_guard.start()`
  and run it from the repo root. macOS ignores `ulimit -v` and
  `RLIMIT_AS`, so a hard limit is not available.
- Ruff's typing-only-import rules (TC001 to TC003) move an import that is
  used only in annotations under `if TYPE_CHECKING:` when the module has
  `from __future__ import annotations`. Pydantic reads field annotations
  at run time, so a model whose fields use such a type (`NDArray` in
  `problem.py`) then fails to build. Modules that declare model fields of
  imported types do not use the future import, so ruff keeps the import.
- Editing a state file with a Python `str.replace` script does nothing when
  the old text does not match exactly (a reflowed line, a word changed by an
  earlier edit), and raises no error. Put `assert old in text` before every
  replacement. Twice on 2026-10-16/17 a PLAN.md task list stayed stale this
  way until a later read caught it.
- Ruff's auto-fix (ISC004) wraps implicitly joined strings in a tuple in
  parentheses, which pushes lines past 80 characters; rewrap the strings by
  hand afterwards.
- `ruff format` can wrap a long `print(...)  # ruff: ignore[print]` so the
  comment no longer sits on the `print` line; the next `ruff check` then
  deletes the whole call (T201 is an unsafe fix). It removed the baseline
  table's header on 2026-10-17. Keep such lines under 80 characters, and read
  the diff after ruff.
- Ruff's auto-fix (`non-augmented-assignment`) rewrites `y = y * w` into
  `y *= w`, which changes the array in place. When `y` may be the same
  array as `w` or another live array (`power = w`, then a loop), that
  silently changes it: on 2026-10-17 it broke BBOB f16 (values off by up to
  170) until the COCO test caught it. Start such a loop from a new array
  (`power = w * w`) and read the diff after ruff.
- BBOB batch products go through `bbob_common.rotate` and `weighted`
  (`einsum`), never `@`: BLAS may sum one row in another order than a
  batch, and the functions that take powers or cosines of large arguments
  magnify that past the batch test's 1e-14. Matrices built from the
  rotations go through `bbob_common._dot` and `linear_map` (COCO's order),
  never `@`: BLAS sums differently on macOS and on Linux, which failed CI
  on f23.
