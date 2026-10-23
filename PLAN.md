# PLAN.md

## Goals

A library of optimisation test functions with known answers, built from the
optimisation pages of the SFU Virtual Library of Simulation Experiments, for
testing optimisation algorithms (CGP-based ones from `ailigment`, and any
other). The approved specs are in DESIGN.md, the task list below.

Network tasks, asked for by `multineat` (2026-10-24): tasks that score a
network (a function from an input vector to an output vector, with state
for recurrent ones) instead of a point. All four are new behaviour, numpy
only, written from the papers, with fixed seeds; done in this order.
Every task takes a seed and a trial count (the same seed gives the same
start states, so a network's score repeats), has a solved test, and
returns its natural reward, negative where the physics gives one.

- `network-core` (approved 2026-10-24): optibench scores a batch of
  networks through one batched interface (inputs `(n_nets, n_in)` to
  outputs `(n_nets, n_out)`, a `reset`, and a wrapper for one plain
  callable) on XOR and on single and double pole balancing, each with
  and without velocities, with Gruau's damping score and the 625-start
  generalisation test for double pole without velocities; and a
  `Tracked`-style counter that records evaluations, the best score so far
  and the evaluation at which the task was first solved, so a caller can
  report evaluations to solve over 20 seeds. Success: one
  simulator step equals a hand-computed step of the published equations to
  1e-12; a hand-built 2-2-1 network solves XOR; a linear controller
  balances both velocity variants for the full budget (100,000 steps for
  double pole); a recurrent reference controller that differences its last
  two observations balances both variants without velocities; 1,000
  networks on 100,000 double-pole steps run in under 10 s on this Mac.
- `network-fit` (approved 2026-10-24): fit-a-function for any
  registered problem (inputs scaled to -1..1, targets to 0..1, score =
  squared error / variance of the sample, so 0 is perfect and 1 is the
  mean's score) and image match on procedurally drawn targets (a smiley,
  rings, a checkerboard), as a point (a 100 x 100 image is a 10,000-d
  problem) and as a network drawing intensity from (x, y, distance from
  centre). Success: the exact function scores 0 and the mean 1 on every
  registered problem; the image problems pass `tests/test_all_problems.py`
  with their minimum 0 at the target; a network that returns the target
  scores 0.
- `network-pendulum` (approved 2026-10-24): pendulum swing-up, score =
  time upright averaged over 15 fixed start states per seed. Success: one
  step equals the published equation to 1e-12; an energy-pumping
  controller that hands over to a linear one swings up and holds in all 15
  trials; a network that outputs 0 scores 0.
- `network-maze` (approved 2026-10-24): a deceptive maze for novelty
  search, returning the score (10,000 minus the closest distance to the
  goal) and a behaviour (the robot's final position); the novelty archive
  stays the caller's. Instances: Lehman and Stanley's medium and hard maps,
  from their paper only (the user, 2026-10-24: papers only; MultiNEAT's
  `NoveltySearch.py` layout is read afterwards as a check, as `cocoex` is
  for BBOB, and any difference is reported). Success: walls stop the
  robot in tests; a scripted route reaches the goal; a controller that
  steers straight at the goal ends in the dead end, which shows the maze
  is deceptive.
- `network-ballkeeper` (approved 2026-10-24): ball keeping (no
  paper; MultiNEAT's `ball_keeper.py` was the only source): a floor and
  three walls under gravity, an agent that runs and jumps when grounded,
  a ball dropped with a random x and x velocity, elastic circle-circle and
  circle-wall collisions in numpy, with constants of optibench's own from
  the equations (the user, 2026-10-24: papers only), then checked against
  the old example's numbers afterwards. Score = steps until the ball touches the floor, capped at
  15,000, averaged over 20 starts; solved at 10,000. Success: a ball
  alone keeps its energy through 100 bounces to 1e-9; a scripted agent
  that stays under the ball and jumps on time reaches 10,000 steps; an
  agent that stands still scores the ball's first fall time.

## Current state (2026-10-24)

- Tier 1 (walking skeleton) done and on `main` (4133d55; `main` had no
  commits, so the branch `tier1-skeleton` simply became `main`).
- Private GitHub repo `Jacopo-DM/optibench` created and `main` pushed
  (2026-10-16, the user's say-so).
- Made public on 2026-10-18 (the user's choice), so ailigment's CI can
  install optibench as a git dependency without credentials.
- Tier 2, the functions: all six SFU groups are done, 49 functions, on
  `main` and pushed (ced98e3, 2026-10-17): 500 tests, coverage 100%, ruff and
  pyright clean, and every function evaluates 100,000 points in under 55 ms.
  Every feature branch so far was merged and deleted on the user's say-so;
  the working tree is clean.
- Tier 2 is complete (2026-10-17): `optibench.random_search` (the baseline)
  and the timing and baseline scripts (now `src/optibench/scripts/`);
  results in DESIGN.md.
  All 49 functions are under the 100 ms budget. On `main` and pushed
  (2026-10-17); the branch `tier2-baseline` was deleted.
- `classics` done (2026-10-17, branch `classics`): ten functions, 605
  tests, coverage 100%, ruff and pyright clean. Whitley is over the speed
  budget at d = 10, a stated exception (the user, 2026-10-17; DESIGN.md).
- `bbob` complete (2026-10-17, five commits, one per group, each merged
  and its branch deleted on the user's say-so): all 24 functions equal to
  `cocoex` (1e-9 for f16 to f19 and f23, 1e-12 for the rest; DESIGN.md
  results); 83 functions in all, 1578 tests, 100% branch coverage over
  `src` and `tests`; ruff, mypy strict and pyright strict clean.
- Git (2026-10-18): `main` holds the `formula` spec and task list
  (5a6efef to 4df5b43, from `spec-formula`) and was pushed at 4df5b43 (the
  user's say-so); `spec-formula` was deleted (the user's say-so). Module `formula` (569f452 to 0cea41b, then 690f912) was
  fast-forwarded into `main`, pushed at 690f912 and `formula` deleted
  (the user's say-so, 2026-10-18); CI passed on Linux (2005 tests, 100%
  coverage, 2 min 15 s for the tests). `main` was pushed again up to
  6cac15e (2026-10-19; CI passed). Earlier: `main` was pushed (de53338, 2026-10-17,
  the user's say-so). Every push to `main` from f33326f to fb9bd7e
  failed f23 on Linux by 3.3e-9 relative; summing the rotations in COCO's
  order (DESIGN.md Decisions) fixed it, and CI passed on de53338 (1578
  tests, 100% coverage).
  Dependabot's PR #1 (setup-uv 9.0.0 to 10.3.0) was merged by rebase on
  2026-10-17 (2aea30c, the user's say-so), so `ci.yml` now pins a newer
  setup-uv than the user's template.
- `ailigment` does not use this library yet; its adapters are separate
  modules in that repo (see its PLAN.md).
- Module `formula` done (2026-10-18): all 83 problems have `formula()`,
  abstract on `Problem` (results, decisions and the amended spec in
  DESIGN.md). 2005 tests, 100% coverage; the suite takes about 2 min at
  load 4 to 6 (4 min at load 25).
- Renamed from `optbench` to `optibench` (2026-10-23, the user's request):
  distribution and import name (a705f51). The GitHub repo is now
  `Jacopo-DM/optibench` (the old URL redirects), `origin` points at it,
  and `main` was pushed at a705f51 (the user's say-so). The local folder
  is now `1xx_projects/optibench` too, with its `.venv` rebuilt.
- Audit (`/zz-11-audit`, 2026-10-23): a fresh clone installs, passes 2005
  tests at 100% coverage and builds a wheel with `py.typed`; the README
  example runs; gitleaks finds nothing. Its shortfalls are tasks 4 to 6
  below. The housekeeping after it (61a6f30 to ea00dd8: CLAUDE.md copies of
  global rules out, this file's tasks, CODEMAP.md's top-level folders,
  virtualenv 21.14.13 for four advisories) is merged into `main` and pushed
  at ea00dd8 (the user's say-so); CI passed on it.
- Compliance pass (task 4) merged into `main`, pushed at 693876d (the
  user's say-so, 2026-10-23); CI passed on it. Dependabot's PR #2 (the
  uv-pre-commit hook 0.13.1 to 0.13.4) gained a commit setting CI's uv to
  0.13.4 too (2026-10-24, the user's go-ahead); CI passed and it was
  merged by rebase (af12724).

Next step: `ailigment` moves its pin (690f912, still the package
`optbench`), its dependency name and its imports to `optibench` at 693876d;
a separate session in that repo started on it on 2026-10-24. That is work in
the `ailigment` repo (226 uses in 18 files on 2026-10-23): `pyproject.toml`
lines 49 and 54, the imports, the old folder path in its PLAN.md:382, and
names of its own that hold the old word (`src/benchmarks/optbench_symreg.py`
and `optbench_table.py`, `tests/test_optbench_symreg.py` and
`test_optbench_table.py`, `tests/functional/symreg.ipynb`, the goal
`optbench-symreg`); whether those get renamed is the user's call. It was on
branch `cgp-engine` that day, so check it for other work first. After that,
`ailigment`'s goal `optbench-symreg`, task S1 (its PLAN.md).
No optibench module is open.

## Baseline (2026-10-23, at 693876d)

Every check in CLAUDE.md passes; the counts are in DESIGN.md's Results,
row "Python compliance". `pytest` takes 1 min 50 s at load 4 to 6.

## Tasks (approved modules, 2026-10-17)

The user approved both specs (now in DESIGN.md, "Approved spec: bbob and
classics") and their task lists on 2026-10-17, with the order: classics,
then BBOB, then the `ailigment` adapters. Downloading RR-6829 (573,076
bytes, from https://inria.hal.science/inria-00362633/document) and adding
COCO's Python package as a dev-only dependency are approved too.

1. done, CI green (2026-10-17, de53338): module `python-standard` (approved
   2026-10-17, commits ae6f494 to the pre-commit and CI commit on branch
   `python-standard`, merged into `main`). The spec, the user's four
   answers and what the work found are in DESIGN.md ("Python standard"
   under Decisions, the results row, the rejected approach).

2. done (2026-10-17): the same migration for `ailigment` (its PLAN.md).
3. done (2026-10-18, 569f452 to 0cea41b): module `formula` (spec
   in DESIGN.md, "Approved spec: formula"), asked for by `ailigment`'s
   approved goal `optbench-symreg` (its DESIGN.md). Pushed at 690f912.
4. done (2026-10-23, branch `python-compliance`, e2b3b49 to 6635487):
   `/zz-08-python-compliance` passes all 22 checks; the user's decisions
   are in DESIGN.md ("Python compliance pass").
5. done (2026-10-24, branch `state-layout`): the state-file layout of
   `/zz-01-project-setup`: Goals, Baseline and Tasks sections in PLAN.md
   (Constraints dropped: its dependency rule was a stale copy of
   CLAUDE.md's, its Python version a copy of DESIGN.md's decision); Specs
   and Gotchas in DESIGN.md.
6. open (the user, 2026-10-23: yes, later): a Sphinx docs site on GitHub
   Pages with `/zz-09-python-docs`.

## Open questions

None.

## Known problems

- BBOB f16 takes about 93 ms per 100,000 points at d = 10, close to the
  0.1 s budget; under heavier load it may cross it (103 ms on 2026-10-17
  with another test suite running, old and new code alike). On 2026-10-18,
  at load 8 from another session's browser tests, f21 (108 ms), f23
  (134 ms) and f16 (147 ms) were over too, with no change to their code;
  rerun at lower load, all 83 passed. T_osz (shared by seven
  BBOB functions) and the rotations are 37 ms of that; speeding up T_osz
  would help them all.
- `uv run --locked ty check` (advisory) reports 2 `not-iterable` errors,
  at `functions/other_perm_to_styblinski_tang.py:320` and
  `functions/steep.py:205`: unpacking `(low, high)` from rows of
  `self.bounds`, which ty types as `float64`. numpy's stubs cause it;
  mypy and pyright pass those lines. Left as they are (2026-10-23).
- Power Sum's recommended b vector is given for d = 4 only (other b give
  other dimensions, with an unknown minimum). Langermann's constants are for
  d = 2; other dimensions work when the caller passes `a`
  (and its minimum is then unknown).
- Functions whose minimum was found numerically (or is published without a
  proof for other constants) know it only at the
  published constants; any changed constant gives `minimum is None`. A
  caller who wants the minimum of a variant must search for it.
