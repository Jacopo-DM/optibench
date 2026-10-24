# DESIGN.md

Reasoning and reference that stays true after a task is done: the approved
specs, decisions with their reasons, rejected approaches, results and
gotchas.

## Specs

### Approved spec (the user, 2026-10-16)

The user's request, made in the `entwined` repo (named `ailigment` until 2026-10-24) on 2026-10-16: "a separate
benchmarking library which lets me test optimisation algorithms like the
CGP", based on the optimisation pages of the Virtual Library of Simulation
Experiments (https://www.sfu.ca/~ssurjano/, Surjanovic and Bingham, Simon
Fraser University), "totally distinct from the library we are working on,
but we should use this benchmark lib for CGP". The user approved the spec and
task list below on 2026-10-16 and chose the MIT license. The user's own words
on parameters: every constant in a formula must be editable, "for example
y = 2*x*x where x is the input to the function, 2 should be a parameter".

Users and use case: the user, testing optimisation algorithms (CGP-based ones
from `entwined`, and any other) on standard test functions with known
answers, and changing the functions' constants to make variants.

Acceptance criteria, each testable:
1. All 49 functions of the SFU optimisation pages exist, each written from
   its published formula (not the site's GPL code), each citing the SFU page
   and its primary reference in its docstring.
2. One call evaluates a batch: `problem(x)` takes an `(n, d)` float array and
   returns an `(n,)` float64 array, with no Python loop over points. Budget:
   100,000 points (d = 10 where d is free) in under 0.1 s on this machine
   (CPU time, min of 5), checked by a timing script, not a test.
3. Every constant in a formula is a keyword argument with the published
   value as default, and the defaults are tested against the published
   values. Example: `Ackley(d=10, a=20.0, b=0.2, c=2*pi)`; Shekel's `beta`
   vector and `C` matrix and Langermann's `m`, `c` and `A` are arrays.
   Arguments are checked on construction (shapes that do not fit `d` raise
   `ValueError`).
4. Each problem knows its domain (`bounds`, an `(d, 2)` array; the usual
   domain by default, overridable) and its global minimum: the value and
   every known minimiser (Branin has three, Holder Table four, Shubert 18).
   Where the minimum depends on the parameters, it is given as a formula of
   them when one is known; otherwise it is known only at the defaults, and
   `minimum` is `None` for other values.
5. Seven pages state no global minimum (Gramacy and Lee 2012, Langermann,
   Schaffer N. 4, Power Sum, De Jong N. 5, Forrester et al. 2008, Hartmann
   4-D). Their minimum is taken from the literature where it gives one, else
   found by a dense search, and marked with its source and accuracy.
6. Tests for every function: the value at each listed minimiser equals the
   minimum (to 1e-6 relative, or the stated accuracy); 10,000 random points
   in the domain are never below it; the batch result equals evaluating the
   points one at a time; a wrong shape raises `ValueError`.
7. Metadata on each problem: name, SFU group, dimension (fixed, or free with
   a smallest d), references, and the page URL. A registry lists and builds
   them: `optibench.names(group=None)`, `optibench.make(name, **params)`.
8. An evaluation counter for running optimisers: `Tracked(problem)` counts
   evaluated points, keeps the best value and point so far, and records the
   best-so-far curve (evaluations, best) that a caller can save as CSV. It is
   the only state in the library; problems themselves are pure.
9. It never imports `entwined`, and depends on numpy only at run time.
   (Changed 2026-10-17 with module `python-standard`, which the user
   approved: pydantic too, for the records the Python standard requires;
   `entwined` already depends on it.)

Non-goals for the first version: the emulation, integration and uncertainty
pages; shifted, rotated or noisy variants (CEC style); constrained or
multi-objective problems; plotting; GPU arrays; the optimisers themselves
(beyond a random-search baseline); and the `entwined` adapters, which live
in `entwined/benchmarks/` and get their own specs.

Constraints: a separate uv project at
`/Users/jmdm/Documents/projects/code/4xx_dual_pc/optibench` (named
`optbench` until 2026-10-23), private GitHub repo
`Jacopo-DM/optibench`; Python >=3.13 (same interpreter as `entwined`,
which pulls it in); numpy; dev tools as in
`entwined` (ruff, pyright strict, pytest); its own four state files and
module READMEs; feature branches and the user-level git rules.

Architecture:
- `src/optibench/problem.py`: `Problem`, the base class. Subclasses are frozen
  pydantic models whose fields are the parameters, so `Rastrigin(d=5, a=12.0)`
  needs no hand-written constructor and `problem.replace(a=12.0)` makes a
  checked variant.
  It provides `__call__` (shape check, then the subclass's `_evaluate`),
  `bounds`, `minimum` (a `Minimum`: value, minimisers, source) and metadata.
- `src/optibench/functions/`: one file per SFU group (`many_local_minima.py`,
  `bowl.py`, `plate.py`, `valley.py`, `steep.py`, `other.py`), each under
  400 lines.
- `src/optibench/registry.py`: `names`, `make`.
- `src/optibench/tracking.py`: `Tracked`.
- Rejected: porting the GPL-2.0 R code (ties the license; the user chose
  formulas); one plain function per problem plus a metadata table (the
  parameters, bounds and minimum would live in three places); depending on an
  existing Python collection of test functions (the user asked for an
  own library with every constant editable, and their licences and accuracy
  would need checking function by function).

Task list (approved 2026-10-16 with the spec):
- Tier 1, walking skeleton: create the repo and toolchain, the four state
  files, `Problem`, `Minimum`, the registry, `Tracked`, and three functions
  that span the cases (Sphere: free d, closed-form minimum; Branin: fixed
  d, three minimisers, six parameters; Shekel: array parameters), with the
  tests of criterion 6. Then the private GitHub repo (needs the user's
  say-so to create and push).
- Tier 2, one commit per group, largest value first: many local minima (16),
  bowl-shaped (9 with the three Bohachevsky functions), valley-shaped (4),
  plate-shaped (5), steep ridges (3), other (12). Then a random-search
  baseline and a timing script for criterion 2.
- Tier 3, not built: the non-goals above.

### Approved spec: bbob and classics (the user, 2026-10-17)

The user reviewed other collections of test functions on 2026-10-17 (see
"Other sources of test functions" below) and approved these two modules.
`bbob` replaces the first version's non-goal "shifted, rotated or noisy
variants" for the BBOB noiseless suite only; the rest of that non-goal
stands.

Answers to the questions asked with the specs:
- BBOB instances reproduce COCO's exactly (its random generator and
  instance-to-seed rule, read from COCO's BSD-3-Clause code), so results
  compare with published COCO data. Own numpy seeds were rejected: the
  numbers would match nothing published.
- Tests check BBOB values against COCO's Python package, added as a
  dev-only dependency; run time stays numpy and pydantic only. Hand-copied values were
  rejected as too thin a check.

#### Module `bbob` (build): the 24 noiseless COCO/BBOB functions

Goal: the BBOB 2009 noiseless suite in optibench, so optimisers (CGP-evolved
ones included) can be compared with published COCO results.

Acceptance criteria, each testable:
1. f1 to f24, written from the formulas of Hansen, Finck, Ros and Auger
   (2009), "Real-Parameter Black-Box Optimization Benchmarking 2009:
   Noiseless Functions Definitions", INRIA RR-6829, in their five groups:
   separable (f1 sphere, f2 ellipsoidal, f3 Rastrigin, f4 Buche-Rastrigin,
   f5 linear slope); low or moderate conditioning (f6 attractive sector,
   f7 step ellipsoidal, f8 Rosenbrock, f9 rotated Rosenbrock); high
   conditioning and unimodal (f10 ellipsoidal, f11 discus, f12 bent cigar,
   f13 sharp ridge, f14 different powers); multimodal with adequate global
   structure (f15 Rastrigin, f16 Weierstrass, f17 Schaffers F7, f18
   ill-conditioned Schaffers F7, f19 composite Griewank-Rosenbrock);
   multimodal with weak global structure (f20 Schwefel, f21 Gallagher 101
   peaks, f22 Gallagher 21 peaks, f23 Katsuura, f24 Lunacek bi-Rastrigin).
2. A problem is built from `(d, instance)`: the instance fixes `x_opt`,
   `f_opt` and the rotation matrices, so the same arguments always give the
   same function. Any `d >= 2`; domain [-5, 5]^d.
3. Every constant of a formula is a field, as spec criterion 3 says
   (conditioning 10^6, the asymmetry beta, the Weierstrass and Katsuura
   constants, Gallagher's peak count and so on).
4. The shared transformations (T_osz, T_asy, the diagonal Lambda^alpha, the
   boundary penalty f_pen, the seeded rotations) are one helper each; each
   has several real call sites.
5. Each problem knows its minimum `f_opt` and minimiser (`x_opt` for most;
   from the definitions for f5, f20, f21 and f22).
6. The existing criterion-6 tests run on every BBOB problem; values match
   COCO's Python package at fixed points.
7. 100,000 points at d = 10 in under 0.1 s, as criterion 2.

Non-goals: the noisy suite, bbob-biobj, large-scale, mixed-integer and
constrained suites; COCO's experiment runner and post-processing.

Architecture: a new module area `functions/bbob_*.py` (split by group to
stay under 400 lines) and `functions/bbob_transforms.py` (built as
`functions/bbob_common.py`, see Decisions). A new class
variable `suite` (`"sfu"`, `"bbob"`, `"classic"`) beside `group`, with BBOB's
five groups as their own `Group` values, and `names(group=None, suite=None)`.
Names like `bbob_f01_sphere`.

Tiers: Tier 1, the instance machinery and transforms plus f1 to f5, with
the reference check. Tier 2, one commit per group: f6 to f9, f10 to f14,
f15 to f19, f20 to f24. Tier 3: the non-goals.

Source: RR-6829, the PDF at
https://inria.hal.science/inria-00362633/document (573,076 bytes; download
approved 2026-10-17), and COCO's code for the instance generation.

#### Module `classics` (build): ten well-known functions not on the SFU pages

Each from its formula in Jamil and Yang (2013) and Gavana's AMPGO pages,
with every constant a field, its minimum and the criterion-6 tests:
Himmelblau (2-D, four minimisers, 0), Bird (2-D, two minimisers,
-106.7645), Alpine N. 2 (any d, -2.808^d at x_i = 7.917; it replaced
Alpine N. 1, see Decisions), Salomon (any d, 0 at the origin), Schwefel 2.21 (any d, max of |x_i|, 0), Schwefel 2.22 (any d, sum
plus product of |x_i|, 0), Qing (any d, 0 at x_i = +-sqrt(i)), Happy Cat
(any d, 0 at x = -1), Whitley (any d, 0 at x = 1), Deceptive (any d, -1 at
the alpha vector). `suite = "classic"`, and each in the SFU shape group that
fits it. One commit; the minima are checked numerically as for SFU.


### Approved spec: formula (the user, 2026-10-17)

Kind: build (new behaviour). Goal: every optibench problem returns its
formula as a sympy expression. Users: `entwined`'s `optbench-symreg`,
which checks whether an evolved formula equals the true one exactly, and
anyone who wants a function's closed form (sympy can print or simplify
it). The user chose to keep the formulas here rather than in `entwined`,
so they stay next to the functions and change with their parameters.

Acceptance criteria:

1. `Problem.formula()` returns a sympy expression in the variables
   `optibench.variables(d)`, named `x1` to `xd` as the SFU pages write them
   (column j of the points is `x(j+1)`; the user's choice over `x0`), for
   every one of the 83 problems. Example: `Booth().formula()` prints
   `(x1 + 2*x2 - 7)**2 + (2*x1 + x2 - 5)**2`.
2. It equals the numpy value: for every problem with default parameters
   (any-d problems at d = 1 to 6 where allowed, BBOB at d = 2 to 6 and
   instances 1 to 5), the formula turned into a numpy function with
   `sympy.lambdify` matches `problem(x)` at the 26 points the BBOB test
   already uses (20 in the domain, 5 outside, the optimum), to the
   relative tolerances of `tests/test_bbob.py` (1e-12, and 1e-9 for f16
   to f19 and f23), absolute 1e-10. (Amended by the user, 2026-10-18: a
   BBOB value is compared with `f_opt` subtracted from both sides, so the
   tolerance is relative to the function's own size. f19 at d = 5,
   instance 4, at a point outside the domain, has a core of 58.55 and
   f_opt -58.48; the formula's error of 4e-10 is 7e-12 of the core but
   5.5e-9 of the 0.074 left after the offset. The user first kept all
   25 (d, instance) pairs per BBOB function on my estimate of 3 to 5
   minutes; measured at 9 to 9.5 minutes, the user chose a sample on
   2026-10-18: every d at instance 1, and every instance at d = 3, 9 of
   the 25 pairs. The instance changes only `x_opt`, `f_opt` and the
   rotations, not the code path.)
3. It follows the parameters: a problem built with changed constants
   (for example `make("ackley", a=10.0)`) gives a formula that matches its
   own values, tested on one problem per file.
4. sympy is a required dependency of optibench (the user's choice over an
   optional extra: simpler, and no missing-extra path to handle).
5. The standard holds: mypy strict with no `Any`, pyright strict, ruff,
   100% branch coverage, no change to the template configs. sympy has no
   type information (1.14 ships no `py.typed`), so one module,
   `optibench/symbolic.py`, reaches it through typed Protocols with a
   `cast`, as the standard's untyped-library pattern does, and nothing
   else imports sympy. (`untyped_calls_exclude` in `mypy.ini` is the
   standard's other route, but that file is a template copy.)

Non-goals: simplifying the formulas, LaTeX or other printing APIs,
symbolic gradients, evaluating through sympy instead of numpy, formulas
for dimensions beyond what each problem allows.

Dependency: sympy 1.14.0 from PyPI (wheel about 6.3 MB) with mpmath 1.3.0
(about 0.5 MB), in `[project].dependencies`; the user accepted it for this
purpose in `entwined`'s spec and chose a required dependency here.

Architecture: `symbolic.py` (the typed sympy facade: symbols, the
operations the formulas use, `lambdify`); `formula()` on each problem
class next to its `_evaluate`, written from the same fields; a symbolic
twin of the BBOB transforms (T_osz, T_asy, Lambda, the rotations as
number matrices, f_pen) in `bbob_common.py`. Rejected: generating the
formulas by tracing the numpy code (fragile for the piecewise and rounding
transforms), and one table of formulas apart from the classes (would drift
from the parameters).

Estimated size: about 83 formulas and a facade, roughly 1500 lines with
tests; the BBOB transforms are the largest part.

### Approved spec: network-core (the user, 2026-10-24)

Users: `multineat` (and any neuroevolution caller) scores a population of
networks on XOR and on pole balancing, and reports evaluations to solve
over 20 seeds. A network is anything that maps a batch of input vectors to
a batch of output vectors and can reset its recurrent state.

Interface (the user, 2026-10-24: batched, one callable wrapped):

- `optibench.networks.Policy`, a `Protocol`: `reset(n)` before each trial,
  and `__call__(inputs)` from `(n, n_in)` to `(n, n_out)` floats.
  `single(fn, reset=None)` wraps one plain callable (one vector in, one
  out) as a batch of one.
- `Task`, a frozen pydantic base like `Problem`: `n_inputs`, `n_outputs`,
  `evaluate(policy, n, seed=0, trials=1) -> Scores`. Trials run one after
  another with `reset(n)` before each; the same seed gives the same start
  states. `Scores` holds `score` and `solved`, each shaped `(n,)`, the
  score averaged over trials and its natural sign kept.
- `TrackedTask(task)`: counts evaluations (one per network per trial),
  keeps the best score so far and the evaluation at which `solved` was
  first true, like `Tracked` for problems.

Tasks:

- `Xor`: inputs (0, 0), (0, 1), (1, 0), (1, 1), no bias (the caller adds
  one). Score (4 - sum of absolute errors)^2, 16 when perfect; solved when
  all four outputs fall on the correct side of 0.5.
- `SinglePole` and `DoublePole`, each with `velocities: bool`, from Gomez,
  Schmidhuber and Miikkulainen (2008, Appendix A: Wieland's equations for
  N poles on one cart, with friction). Track +-2.4 m; failure angle 12 deg
  (one pole) or 36 deg (two); cart 1.0 kg; poles 0.1 kg with half length
  0.5 m, and for the second pole 0.01 kg and 0.05 m; friction 0.0005 (cart)
  and 0.000002 (hinges), used for the single pole too because the paper's
  single-pole table lists none; g = -9.8 m/s^2, the sign the equations
  need. RK4 with 0.01 s; one network step is 0.02 s (two RK4 steps).
  `start_angle` is a field, default 4 deg from Gomez (NEAT's paper used
  1 deg; the user, 2026-10-24); the second pole starts vertical. Inputs:
  x / 2.4, x' / 1.5 m/s, each angle / its failure angle, each angular
  velocity / 115 deg/s, from Gruau, Whitley and Pyeatt (1996, section 3;
  the user, 2026-10-24, replacing optibench's own 2 and 2, chosen before
  the paper was found); without velocities only x and the angles. Output: one value in -1..1
  (clipped), force = 10 N times it, and at least 10/256 N in magnitude
  as in the papers (the user, 2026-10-24: -1..1). Score = network steps
  balanced, budget 100,000; solved = the full budget. Trial 0 starts
  from the published state; later trials draw x, x', the first angle and
  its velocity uniformly from the seed within a quarter of each input
  scale (the user, 2026-10-24, changed from half: at half the linear
  reference lost 30% of double-pole starts, at a quarter 2%, at a tenth
  none).
- `DoublePole(gruau=True)` gives Gruau, Whitley and Pyeatt's (1996,
  section 4.1) damping score over 1,000 steps, F = 0.1 t/1000 + 0.9 f2,
  with f2 = 0.75 over the sum of the four scaled inputs of the cart and
  the long pole in absolute value across the last 100 steps, capped at 1
  (Stanley and Miikkulainen 2002, eq. 3 and 4, state neither the scaling
  nor the cap), and their solution test: 100,000 steps from the start
  state and at least 200 of 625 start states balanced for 1,000 steps,
  each of x, x', the first angle and its velocity at 0.05, 0.25, 0.5,
  0.75 and 0.95 of +-2.16 m, +-1.35 m/s, +-3.6 deg and +-8.6 deg/s
  (section 4.3), the second pole upright. The test runs only when a
  network balanced all 1,000 steps, as Gruau ran it only on champions,
  and `gruau` takes one trial only (Gruau's protocol: one run from the
  published start).

Speed (the user, 2026-10-24: keep 10 s, add numba; then, measured, a
budget of 35 s): the cart simulation is compiled with numba (run-time
dependency, 43 MB on macOS with llvmlite), on all cores from 64 carts.
1,000 networks on 100,000 double-pole steps, every one balancing to the
end, take at most 35 s on this Mac, excluding the policy's own time,
checked by `scripts.pole_timing`. The 10 s target was not met (Results).
Tests run the same code uncompiled (`NUMBA_DISABLE_JIT=1`, set in
`tests/conftest.py`) so coverage sees it.

Proof (the user, 2026-10-24: reference solutions; the controller is
`networks.LinearController`, in the package because `scripts.pole_timing`
needs it too): one network step
equals two hand-computed RK4 steps of the appendix equations to 1e-12; a
hand-built 2-2-1 network solves XOR; a linear state-feedback controller
(gains from the linearised equations) balances both velocity variants
for 100,000 steps; a recurrent controller that differences its last two
observations to estimate the velocities balances both variants without
them.

Non-goals: the novelty archive, a population or any optimiser, rendering,
gym compatibility. The 83 functions and their tests do not change.

Rejected: tasks as a kind of `Problem` (its contract is points in, values
out, no state, and recurrent networks break it); one network per call
(50 million Python calls per generation; the user chose batched); Euler
integration (the papers use RK4); plain numpy (about 80 s for the worst
case above; the user chose numba).

Sources: Gomez et al. (2008) and Stanley and Miikkulainen (2002),
downloaded with approval on 2026-10-24; Gruau et al. (1996), supplied by
the user as PostScript the same day. None is kept in the repo.

## Decisions

- Name (2026-10-23, the user's request): the library was renamed from
  `optbench` to `optibench`, the import name too, because a package
  installed under one name and imported under another misleads readers,
  and `entwined` was its only user. The local folder was renamed too, with
  its per-folder Claude state (skill runs, audit record, project folder).
  One old name stays on purpose: `entwined`'s goal `optbench-symreg`,
  which belongs to that repo. Moving the folder breaks two things that
  hold its absolute path: `.venv` (rebuild it: delete it, then
  `uv sync --locked`) and `.git/hooks/pre-commit`, whose `INSTALL_PYTHON`
  line named the old `.venv`, so the first commit failed with "`pre-commit`
  not found" until `uv run --locked pre-commit install` rewrote it. The
  per-folder Claude state is keyed by the path too:
  `~/.claude/state/skill-runs.json` keys, the audit record in
  `~/.claude/state/audits/` and the folder in `~/.claude/projects/`. The
  Legion's clone moved to `~/projects/optibench` the same day (origin
  `git@github.com:Jacopo-DM/optibench.git`; it has no `.venv`).

- Module `formula` (2026-10-17): sympy is reached only through
  `symbolic.py`, typed as Protocols behind one `cast` of the imported
  module, because sympy 1.14 has no type information and `mypy.ini` is a
  template copy that cannot list it in `untyped_calls_exclude`. The facade
  imports sympy on first use (`import optibench` stays at about 0.3 s; the
  first formula pays about 1 s). `Expr` is a Protocol with only the
  arithmetic the formulas use, and the facade grows a function only when a
  formula needs it (F1 needed `cos` and `absolute`, not `sin`). sympy's
  `pi` is used where the numpy code uses `math.pi`, so the formula is
  exact; `lambdify` turns it back into the same float. The same holds for
  `exp(1)` (Ackley's `e`) and `sqrt(i)` (Griewank). A caller comparing a
  formula with one built from float constants (entwined's exact match)
  must turn these exact constants into floats first, or `pi - 3.14159`
  never simplifies to 0. A function that
  takes any arguments is typed as a Protocol with `*columns`, since
  `Callable[..., object]` counts as an explicit `Any` under
  `disallow_any_explicit`. Formula tests select problems by (suite, group),
  since the classics share the SFU shape groups.
- BBOB formulas f15 to f24 (F8, 2026-10-18). Katsuura's numpy code
  doubles a running fraction 32 times; written that way each step holds
  the last one twice, so the printed code would hold 2^32 copies of z.
  The formula writes each step as `frac(2^j z)` on its own, the same
  number because multiplying a float by a power of 2 is exact. Gallagher's
  peaks use the same expanded quadratic as `_evaluate` (`[t^2, t]` times
  the weights, plus a constant), so the rounding stays close at 1e-12.
  Every problem has a formula after F8, so `formula()` became abstract in
  F8, not F9: the "no formula yet" path could no longer be covered.
  Rejected, with the numbers: `lambdify(cse=True)`, which names repeated
  subexpressions once; it cut Weierstrass at d = 6 from 3.2 s to 1.5 s
  but took Gallagher 101 from 2.1 s to 35 s.
- BBOB formulas (F6, 2026-10-18): the symbolic twins of the transforms
  live in `functions/bbob_symbolic.py`, not in `bbob_common.py` as the
  spec says, because `bbob_common.py` was at 386 lines. Each twin returns
  one expression per coordinate, so a `formula()` reads like its
  `_evaluate`. T_osz keeps the sign of its input, so a transform after it
  (T_asy, f4's skew) tests the shifted coordinate itself and each
  coordinate is one three-piece piecewise (`oscillate_pieces`,
  `oscillate_asymmetric`). Rejected, with the numbers: composing the
  twins as written (`asymmetric(oscillate(x))`), whose condition
  `T_osz(x) > 0` sympy turned into an `ITE`; `lambdify` on f3 at d = 2
  then grew to 160 GB before macOS killed it. `evaluate_formula` refuses
  that shape since, and every pytest run has a 2 GB memory watchdog
  (CLAUDE.md, things that bite). numpy evaluates every piece of a
  piecewise, so `evaluate_formula` silences divide and invalid warnings
  from the pieces not chosen (log(0) at the optimum, log of a negative).
- `memory_guard.watch` takes its limit as an argument (2026-10-18). It
  used to read the module's `LIMIT` on every check, so the test that
  patched `LIMIT` to 0 could, if the running guard woke during that test,
  make the guard call the patched `stop` and end its thread for the rest
  of the run. entwined's `benchmarks.memory_guard` was written this way
  from the start.
- Adding the formulas took `bowl.py` to 426 lines and
  `many_local_minima_any_d.py` past 400, so they were split by the size
  rule in CLAUDE.md: `bowl_sphere_to_bohachevsky.py` and
  `bowl_perm_to_trid.py`; `many_local_minima_ackley_to_langermann.py` and
  `many_local_minima_levy_to_schwefel.py` (`constant_point`, which both
  halves use, moved to `problem.py`).

- Written from the published formulas, not ported: the site's MATLAB and R
  code is GPL-2.0 (each file header says "version 2.0 of the License"), and
  a port would tie this library to that license. The formulas are images on
  each page; they were read from the images and the cited papers.
- MIT license (the user, 2026-10-16): short and permissive, fits a benchmark
  library others may copy or cite.
- Python >=3.13 and numpy and pydantic only at run time: `entwined` (Python 3.13, see its
  CLAUDE.md for why) pulls this library in, so the floors must not exceed its
  own.
- Problems are frozen models (frozen dataclasses until 2026-10-17, pydantic
  since, see "Python standard" below): their fields are the constants with
  the published defaults, so `Branin(s=5.0)` and `problem.replace(s=5.0)`
  give variants without hand-written constructors, and a problem is
  immutable and pure. Metadata (`name`, `group`, `url`, `references`) are
  class variables. Array constants (Shekel's `beta` and `c`) are tuples so
  the model stays hashable and frozen; they are turned into arrays when
  evaluating.
- One shape for input: `(n, d)` in, `(n,)` out. A single point is
  `x[None]`; refusing `(d,)` avoids silently treating a batch of 1-D points
  as one point.
- The minimum follows the parameters where a formula gives it (Sphere at the
  origin for every d; Branin `s t` at odd multiples of pi), and is otherwise
  known only at the published constants and the default domain (Shekel).
  `Problem.uses_default_domain` says whether a published minimum still
  applies. A minimiser outside a narrowed domain is dropped, and with none
  left the minimum is `None`.
- Shekel's published minimiser (4, 4, 4, 4) is rounded: the true minimisers
  were found by Newton steps from it (gradient below 1e-13) and are stored to
  full precision with their source; the values agree with the published
  -10.1532, -10.4029 and -10.5364 (m = 5, 7, 10) to their four decimals.
  Shekel's `m` selects the first `m` wells, so the three published variants
  are one class.
- Shekel computes distances from differences, not from the expansion
  `|x|^2 - 2 x.c + |c|^2`, which cancels and loses about 1e-13 near the
  minimum.
- `Tracked` is the only stateful object: it wraps a problem to count
  evaluations and record the best-so-far curve, so problems stay pure and an
  optimiser needs no changes to be measured.

- Which constants are parameters: every number in a formula that sets a
  scale, weight, frequency, shift, offset, exponent or count, named after
  what it does (`Bukin6(scale, curvature, slope, shift)`), or after the
  letter the literature uses (`Ackley(a, b, c)`). Not parameters: pi and e
  where they are part of the formula's structure (except where the
  literature makes them one, such as Ackley's `c = 2 pi`), the square in a
  squared distance, and the 1 in terms like `1 + cos(...)` that keep a term
  non-negative. Applied from the "many local minima" group on (2026-10-16).
- `AnyDimension` (a `Problem` with a `d` field, default 2, and its check)
  for the functions defined for any number of variables; it replaced the
  per-class `d` handling once six classes needed it. `Problem.contains`
  replaced two copies of the same domain check.
- Minima the literature does not give exactly are found once, offline, and
  stored with how they were found (`functions/known_minima.py`, named
  `numerical_minima.py` until the valley group): a grid
  over the whole default domain, then Newton steps with central differences
  from the best grid points. They hold only at the published constants and
  domain (`at_defaults`); a changed constant gives `None`, never a guess.
  The scripts were in a session scratch folder; the method is the record.
- Several published minima are rounded or slightly off, and the stored
  values are the true ones: Shekel (see above); Cross-in-Tray at
  (+-1.349407, +-1.349407), not 1.3491; the Schwefel function's published
  offset 418.9829 rounds the true peak 418.98288727..., so its minimum is
  about 1.27e-5 per dimension, not 0. The SFU values are kept in the tests
  at their printed precision.
- The Eggholder's minimum lies on the domain's edge (x1 = 512); outside the
  box the function goes lower (-976.9 at about (522, 413)), so it was found
  along the edge.
- Langermann takes its dimension from its centre matrix `a` (published for
  d = 2 only), not from a `d` field: other dimensions need other centres.
  Its minimum with the SFU constants, -4.1558 at (2.7934, 1.5972), comes
  from a grid over the whole domain; other collections quote other values
  (such as -5.1621), which must come from other constants or another form
  of the formula, so they do not apply here.

- Bowl-shaped group (2026-10-16): every minimum follows from a formula, so
  each holds for changed constants where the formula's conditions hold
  (non-negative weights, the minimiser inside the domain). The three
  Bohachevsky functions share a private base `_Bohachevsky`; each is its own
  registered problem, as on the SFU page. Perm 0, d, beta takes `beta = 10`
  from the default stated in the SFU page's code header, because the page
  itself gives none (only that stated default was read, not the code). The
  Trid minimum for any `shift`: the function is a convex quadratic, and
  replacing `x` by `shift x` scales it by `shift^2`, so the published minimum
  (`shift = 1`) scales by `shift^2` and its minimiser by `shift`.
- Perm 0, d, beta builds the powers `x_j^i` by repeated multiplication
  (`cumprod`) instead of calling power for each entry: 126 ms down to 43 ms
  for 100,000 points at d = 10, which brought it under the spec's 100 ms
  budget. The results differ from `x ** i` only in the last bits.

- Valley-shaped group (2026-10-16): `functions/numerical_minima.py` became
  `known_minima.py` (`KnownMinimum`), because the Three-Hump Camel's
  minimum (0 at the origin) is published and confirmed by a grid but not
  proven for other constants, and it belongs with the numerically found
  ones: both hold only at the published constants. `formula_minimum` moved
  to `problem.py` once two group modules used it. Dixon-Price has two
  minimisers for d >= 2, the published all-positive one and the same with
  `x_d` negated; flipping an earlier coordinate is not a minimiser, because
  it appears unsquared in the next term (a first version listed `2^(d-1)`
  sign flips; its test caught the error). Rosenbrock's minimum follows `b`
  only where every term can vanish: `(b, ..., b, b^2)` needs `b` equal to 0
  or 1 unless d = 2. The SFU page's rescaled Rosenbrock (Picheny et al.) is
  a variant and is not included.

- Plate-shaped group (2026-10-16): no search was needed. Booth's minimum
  solves its two linear equations for any `weight` other than +-1 (then the
  equations are dependent). Matyas is bounded below only while
  `a >= |b| / 2`. McCormick separates in `u = x1 + x2` and `v = x1 - x2`
  into `sin(u) + u / 2 + (v - 1)^2 + offset - 1`, so its minimum is
  `offset - 1 - sqrt(3) / 2 - pi / 3` at `u = -2 pi / 3`, `v = 1` (checked
  by a grid with step 0.001); other `a` and `b` are not covered because the
  minimum can move onto the domain's edge. The SFU page gives no minimum for
  Power Sum, but its published `b` holds the power sums of (1, 2, 2, 3), so
  the minimum is 0, and by Newton's identities the minimisers are exactly
  the 12 orderings of that vector (2,000,000 random points found nothing
  lower). Power Sum takes its dimension from `b` and builds its powers with
  `cumprod`, like Perm 0.

- Steep group (2026-10-16): Easom's minimum is -1 at `(centre, centre)`
  whenever `centre` is a multiple of pi, because `f >= -exp(-r^2) >= -1`.
  Michalewicz is a sum of independent one-variable terms, so its minimum is
  computed when asked, for any `d`, `m` and domain, by minimising each term
  on its own interval (a grid of 20,000 points per unit length, then Newton
  steps that must stay in the best grid cell); it reproduces the SFU
  values -1.8013, -4.687658 and -9.66015 for d = 2, 5 and 10 and takes about
  13 ms for d = 10. Its power `sin(...)^(2 m)` is computed as
  `(sin(...)^2)^m`, equal wherever the first is defined, so a non-integer
  `m` does not give NaN. De Jong N. 5 has no published minimum; a grid over
  the whole domain puts it at 0.998003837794 near (-32, -32) (the drops are
  weighted by their index, so the two coordinates differ slightly). Its
  drop centres `a` are a parameter, defaulting to the published 5 by 5 grid.

- "Other" group (2026-10-17): split into three modules
  (`other_beale_to_goldstein_price.py`, `other_hartmann.py`,
  `other_perm_to_styblinski_tang.py`), and Branin and Shekel moved there
  from `other.py`. Beale's minimum follows `c` when its three brackets can
  vanish together (the first two fix `x2 = c_2 / c_1 - 1`,
  `x1 = c_1 / (1 - x2)`, and the third must then hold). Colville's is 0 at
  (1, 1, 1, 1) while `c >= |e| / 2`. Goldstein-Price's polynomial
  coefficients are two parameter tuples (`p`, `q`, one entry per term of
  `(1, x1, x1^2, x2, x1 x2, x2^2)`) plus the two offsets, rather than twelve
  separate fields. The Hartmann functions share a base `_Hartmann`; 4-D uses
  the first four columns of the 6-D constants, rescaled as Picheny et al.
  give it. Their minima and Forrester's came from a search (200,000 random
  points, Newton from the 25 best distinct ones); Hartmann 3-D and 6-D match
  the published -3.86278 and -3.32237, and Hartmann 4-D (none published) is
  -3.13449. Perm d, beta takes `beta = 0.5` from the default stated in the
  SFU page's code header. Styblinski-Tang is separable and its minimum is
  exact for any constants and domain (the roots of a cubic per coordinate):
  -39.1661657 per dimension, so the SFU page's -39.16599 is 1.7e-4 too high.
  Powell needs `d` to be a multiple of 4, so `tests/test_all_problems.py`
  checks free-dimension functions at d = 8 (it was 5).

- Classics (2026-10-17): ten functions in
  `functions/classics_alpine_to_himmelblau.py` and
  `functions/classics_qing_to_whitley.py`, with `suite = "classic"`. The
  class variable `suite` (default `"sfu"` on `Problem`) tells the collections
  apart, and `names(group, suite)` filters by both; `group` stays the shape
  group, so each classic takes the SFU group that fits it: many local minima
  (Alpine N. 2, Bird, Salomon, Whitley), bowl (Schwefel 2.21 and 2.22,
  convex), valley (Happy Cat, a groove around |x|^2 = d), other (Deceptive,
  Himmelblau, Qing).
- Alpine N. 1 was swapped for Alpine N. 2 (the user, 2026-10-17). Alpine
  N. 1's terms |x_i (sin x_i + 0.1)| vanish at 0 and at the seven roots of
  sin x = -0.1 in [-10, 10], so it has 8^d minimisers, about 1.07 billion at
  d = 10, and criterion 4 (every minimiser listed) cannot hold. Alpine N. 2
  is written as a minimisation, -prod sqrt(x_i) sin(x_i) on [0, 10]^d, with
  one minimiser. Qing keeps all 2^d minimisers, built only when `minimum` is
  read (80 kB at d = 10, 168 MB at d = 20).
- Deceptive: Gavana's page formula leaves out the `+ 1` and `+ 4/5` of the
  last two pieces of g, so g would jump at alpha_i and at (1 + 4 alpha_i)/5;
  SciPy's benchmark code (BSD, "based on his code") has them and says the
  page is wrong, and so does optibench. alpha_i defaults to i / (d + 1), as
  in that code; beta = 2. Outside [0, 1] the end pieces continue as lines.
- Happy Cat's formula is Beyer and Finck's (PPSN 2012) as the soobench R
  package states it, alpha = 1/8; its domain [-100, 100]^d is the CEC 2014
  one (the paper sets none). Himmelblau's domain is Wikipedia's [-5, 5]^2
  (Gavana uses [-6, 6] and gives a wrong minimiser, [0, 0], where f = 170).
- Whitley is a stated exception to spec criterion 2 (the user, 2026-10-17):
  it has d^2 terms per point, so at d = 10 a batch of 100,000 points needs
  10 million cosines, which alone take 70 to 90 ms; it measures about 125
  ms. `src/optibench/scripts/timing.py` lists it in `EXCEPTIONS`, marks it "over budget,
  stated exception" and still exits 0. Changing the budget to scale with
  the terms per point, or leaving the script failing, were the rejected
  options.
- BBOB Tier 1 (2026-10-17): f1 to f5 in `functions/bbob_separable.py`,
  the generator and transforms in `functions/bbob_common.py` (first named
  `bbob_transforms.py`; renamed when f6 to f9 made it also hold the base
  class `BbobProblem` and `rastrigin`, each used by two group modules). Each
  problem takes `d` (at least 2: the formulas divide by d - 1) and
  `instance`; `x_opt` and `f_opt` are derived from them, cached per (seed,
  d), and are not fields. Instance k uses COCO's seed function + 10000 k,
  so every instance number gives COCO's instance, the workshop's 1 to 15
  and beyond. COCO's generator is ported line for line (a Park-Miller
  sequence through a 32-entry shuffle table, 40 warm-up steps, Box-Muller
  for normals), in a Python loop: at most 2 d^2 numbers per instance, made
  once.
- Where COCO's code and RR-6829 differ, optibench follows the code, so
  values match published COCO data: f4's `x_opt` takes the absolute value
  in every even coordinate (0-based) and comes from f3's seed (so f3 and f4
  share `f_opt` and the odd coordinates of `x_opt`); f_opt of f4 and f18 use
  the seeds of f3 and f17. f5's `x_opt` is the corner 5 sign(u) of COCO's
  random point u, and z_i stays at x_opt_i once x_i x_opt_i >= 25.
- COCO's constants are fields: f2 `conditioning` 1e6; f3 `conditioning` 10,
  `beta` 0.2, `a` 10; f4 `conditioning` 10, `skew` 10, `a` 10, `penalty`
  100; f5 `conditioning` 100 (slopes 1 to 10). The 0.049, 10, 7.9, 5.5 and
  3.1 inside T_osz are fixed, being part of the transform's definition, as
  is f5's boundary at 5^2.
- BBOB f6 to f9 (2026-10-17) in `functions/bbob_moderate.py`. COCO's
  rotation `R` comes from the instance's seed and `Q` from the seed plus
  1,000,000; both are Gram-Schmidt on a column-filled d by d matrix of
  `gauss` numbers, cached per (seed, d). f9 uses only `R`, and its `x_opt`
  is `R^T 1 / (2 max(1, sqrt(d) / 8))`, not a random point; f8's `x_opt`
  is 0.75 times COCO's random point. f7 rounds where `|z_hat_i| > 0.5`
  (COCO's code; the report has no absolute value) with halves rounding up,
  as COCO's `floor(x + 0.5)`.
- f7 reaches its minimum on a plateau (z_hat_1 = 0 and every other
  |z_hat_i| < 0.05 after rounding), a continuum that criterion 4 cannot
  list; `minimum.points` holds `x_opt` only, and the class docstring
  describes the plateau. `tests/test_bbob.py` checks a plateau point.
- BBOB f10 to f14 (2026-10-17) in `functions/bbob_high_conditioning.py`.
  RR-6829 calls the single rotation of f10, f11, f12 and f14 `R`, but
  COCO builds it from the seed plus 1,000,000, which is `q` here; the base
  `BbobRotated` (moved to `bbob_common.py` when a second module needed it)
  names the rotations by seed, not by the report's letters. As in COCO's
  code but not the report, f12's `x_opt` also comes from the seed plus
  1,000,000. f14's exponent spread (4) is the field `spread`.
- Batch products of points with a matrix go through `bbob_common.rotate`
  and `weighted` (`einsum`) since f15 to f19, not `@`: BLAS may sum one row
  in another order than 20, and f14's powers up to 6 and f16's and f19's
  cosines of large arguments magnified that last-bit difference past the
  batch test's 1e-14 (f10 to f14 had briefly loosened that test to 1e-13;
  it is back at 1e-14). einsum costs about 2 ms more per 100,000 points at
  d = 10.
- The rotations and the combined matrices are summed in COCO's order
  (2026-10-17, branch `coco-order`): `rotation`'s Gram-Schmidt adds each
  dot product for k from 0 up (`_dot`, a `cumsum`), and `linear_map`
  builds `q diag(scaling) r` as COCO's k loop does, both instead of `@`.
  CI on Linux failed f23 at d = 20, instance 100, by 3.3e-9 relative
  (tolerance 1e-9): `@` goes to BLAS, which is Accelerate on macOS and
  OpenBLAS on Linux, and their last bits differ. The rotation was the
  main source: a plain-Python copy of COCO's z changed f23 by only 4e-12
  relative, while the ordered Gram-Schmidt cut the worst f23 gap on macOS
  from 7.0e-10 to 3.8e-11. Both run once per instance (`rotation` is
  cached) or once per call on a d by d matrix, so they cost no measurable
  time.
- BBOB f15 to f19 (2026-10-17) in `functions/bbob_multimodal_adequate.py`.
  Here the report's `R` is COCO's `q` and its `Q` is `r`. f18 is f17 with
  conditioning 1000 and f17's seeds for its instance and `f_opt` (COCO's
  `rseed_17`). f16's minimum is reached wherever every `z_i` is an
  integer (the report: "non-unique global optimum"); like f7's plateau,
  `minimum` lists `x_opt` only. f19's true minimiser is
  `r^T 1 / (2 max(1, sqrt(d) / 8))`; COCO reports `r^T 1 / 2`, which is
  the same for d <= 64.
- f16 computes `cos(2 pi b^k u)` as the real part of `w^(b^k)` with
  `w = exp(2 pi i u)`, raising to the power `b` each term (b - 1 complex
  products) instead of 12 cosines per coordinate: 46 against 105 ms for the
  sum alone, the whole function 145 to about 93 ms. It needs an integer
  `b` (the field is now `int`, at least 2), which the published 3 is.
  Repeated products multiply the angle's rounding error by `b` per term,
  as the direct cosine does; the values stay within 1.5e-10 of COCO. The
  real triple-angle formula `4c^3 - 3c` was rejected: it multiplies
  errors by up to 9 per term (9^11 is 3e10) and timed 50 ms.
- BBOB f20 to f24 (2026-10-17) in `functions/bbob_multimodal_weak.py`
  (split by name range in F8, at 492 lines with the formulas),
  which completes the suite (24 functions). f20's `x_opt` is
  `+-4.2096874637 / 2` with signs from COCO's uniform numbers (below 0.5
  is negative), and its value at `x_opt` is `f_opt` plus 0.01 times the
  offset minus the peak of `z sin(sqrt|z|)` at z = 420.96874637 (about
  1e-15). f24's `x_opt` is `+-1.25` with signs from COCO's normal numbers;
  COCO first draws a random point and then overwrites it.
- Gallagher (f21, f22): COCO draws the peaks' condition numbers, each
  peak's coordinate permutation (seed + 1000 p) and the centres from its
  generator, sorting uniform numbers into permutations (`argsort`; ties
  have probability 0). The first centre, before rotation, is `x_opt`. The
  squared distances to all peaks are one `einsum` of `[t^2, t]` with
  precomputed weights, and `max_p h_p exp(-a_p)` is
  `exp(max_p (log h_p - a_p))`, one exp per point. BLAS for that product
  timed 23 against 84 ms, but differed by 2e-12 between a batch and one
  point; einsum keeps the batch test at 1e-14 and f21 at 72 ms.
- Katsuura (f23): `|2^j z - round(2^j z)|` for j = 1 to 32 is computed by
  doubling the fractional part of z, which is exact in binary floating
  point, and gives COCO's literal formula bit for bit on the same z.
- `tests/test_bbob.py` compares with COCO to a relative 1e-12, and 1e-9
  for f16 to f19 and f23 (2^j z up to j = 32, with |z| up to about 100;
  worst 7e-10 before the rotations were summed in COCO's order, 3.8e-11
  after): optibench and COCO sum in different orders, and those
  four take sines and cosines of large arguments (2 pi 3^11 z in f16, t up
  to about 1e5 in f19). Measured worst cases, all 30 (d, instance) pairs,
  before that change:
  f16 1.5e-10, f17 4.9e-11, f18 3.9e-12, f19 6.5e-10; every other function
  at most 1.4e-12 (after it: results table). Matching COCO bit for bit
  would mean copying its summation order everywhere and the compiler's
  fused multiply-adds (clang on Apple silicon fuses `a += b * c` by
  default), so it was not tried; the rotations alone were enough.
- `coco-experiment` 2.8.2 (BSD-3-Clause) is a dev dependency, used only by
  `tests/test_bbob.py` (the user approved it and the 3.9 MB source
  download, 2026-10-17). PyPI has no Python 3.13 wheel for it, so `uv sync`
  compiles it. Its suite object serves only the instances it is built with,
  so the test builds it with `instances: 1,2,7,15,100` (the default
  `instance_indices` are indices into the current year's list, not
  instance numbers).
- Bird's minimum, -106.7645367492647 (Newton on the exact gradient), is
  3e-8 below Gavana's published -106.7645367198034.

- The random-search baseline (2026-10-17) is `optibench.random_search`, in the
  package rather than in a script, because the `entwined` adapters will
  import it as the result to beat. It is not an optimiser library: one
  function, uniform points through `Tracked`, so `Tracked` stays the only
  state. Points come in batches of 1,000 (one `Tracked` curve row each) and
  the last batch is cut so the budget is exact.
- The timing and baseline runners are scripts in `src/optibench/scripts/`
  (run with `python -m optibench.scripts.<name>`, tested by
  `tests/test_scripts.py`). Until 2026-10-17 they were a top-level
  `scripts/` package outside `optibench`; the Python standard's `pytest.ini`
  (`pythonpath = src`, coverage over `src` and `tests`) moved them in (see
  "Python standard"). The package itself never imports them. They write to `__data__/` (git-ignored),
  as in `entwined`. The scripts draw no plots, because matplotlib would be a
  new dependency; the charts so far were drawn with `entwined`'s
  environment from the CSVs. The script lived in a session scratch folder,
  so redo it when needed: run from this repo with
  `PYTHONPATH=.:src ../entwined/.venv/bin/python <script>`, read
  `__data__/timing.csv` into a horizontal bar chart (one bar per
  `name (d=..)`, a dashed line at the 100 ms budget), and for each
  `scripts.common.every_problem()` take the last row of the 10 curves
  `__data__/baseline/<name>_seed<s>.csv`, subtract `problem.minimum.value`,
  clip at 1e-12 and draw a horizontal box plot on a log x axis, sorted by
  the median; save both to `__data__/plots/timing.png` and
  `__data__/plots/baseline_gap.png` (figure about 8 by 19 inches for 83
  functions).

- Python standard, module `python-standard` (kind: change; spec and nine
  tasks approved by the user on 2026-10-17). Goal: optibench passes the
  user's Python standard (`~/.claude/standards/python/core.md`) with the
  template configs unchanged and every value bit for bit the same.
  Non-goals: a Sphinx docs site (the user's `/zz-09-python-docs` prompt),
  any speed-up, the `entwined` migration. The user's answers to its four
  design questions (each the recommended option):
  - Variants come from a `problem.replace(**changes)` method that rebuilds
    the model through validation, because pydantic's `model_copy(update=...)`
    skips the checks (`model_copy(update={"d": 0})` would give a broken
    problem silently) and the constructor form
    `Branin(**{**p.model_dump(), "s": 5.0})` is long.
    `dataclasses.replace` did run the checks, so `replace` keeps that.
  - `domain` is stored as a tuple of `(low, high)` float pairs, whatever
    array-like the caller passes, so problems stay hashable and `==`
    between them works (`known_minima` compares a problem with its
    published default). A numpy array field would make `==` raise.
    `bounds` still returns the float64 array.
  - `Minimum.points` is a read-only float64 array, so the frozen record is
    frozen in fact; it matches the read-only cached `x_opt` and rotations
    of BBOB, and `problem(minimum.points)` is unchanged.
  - pre-commit and CI come in the same module; CI compiles cocoex from
    source (no Python 3.13 wheel), about a minute per run.
  - Mine, under the standard's "packaging is yours": `scripts/` moves into
    the package as `optibench.scripts`, because the template's
    `pythonpath = src` and `--cov=src` must not change and the tests import
    the scripts; they have no import-time side effects. Overrides that
    ignore `self` take `@typing.override`, which ruff's `no-self-use`
    honours, instead of suppression comments. `Tracked` becomes a mutable
    model (`frozen=False`), the standard's exception for records that must
    change. Pyright stays in the dev group as a check, since the standard
    counts its editor errors as real and a session sees no editor.
  - Found while doing it: the generated `__init__` is typed with the
    stored field type, so type checkers want `domain` as a tuple of tuples
    (tests pass tuples; arrays and lists still work at run time and
    through `model_validate`). A flat tuple where a matrix belongs
    (`Shekel(c=(1.0, 2.0))`) is now refused by pydantic's type check with
    its own message, not by the function's "c must be a matrix" check; an
    empty tuple still reaches that check. Errors raised in
    `model_post_init` reach the caller as `pydantic.ValidationError`, a
    `ValueError` subclass, with the original message inside.
  - Pyright types `BaseModel.__hash__` as `None` (pydantic adds it to
    frozen models at run time), so a model cannot be a `functools.cache`
    key without a type error; Gallagher's peak cache is keyed on the f21 or
    f22 class instead. `Tracked(problem)` stays positional by calling
    `BaseModel.__init__` directly, because the `__init__` type checkers
    synthesise for `Model` has no fields. `cocoex` has no stubs: the tests
    `cast` its `Suite` to a `Protocol` (mypy) and `.typings/cocoex` holds a
    minimal stub (pyright), with no config change.
- Python compliance pass (`/zz-08-python-compliance`, branch
  `python-compliance`, 2026-10-23; the user's answers): refresh the
  template files now; add nbclient, nbformat and ipykernel as dev
  dependencies so the template's `tools/run_notebooks.py` type-checks and
  its pre-push hook runs, though there are no notebooks yet; take the
  template's `.typings/` ignore line and keep the tracked `cocoex` stub;
  keep setup-uv v10.3.0 in `ci.yml` over the template's v9.0.0 (CLAUDE.md);
  parse the scripts' flags with a pydantic `Arguments` model (no range
  limits added; the flags accept what `int()` accepts, as with argparse's
  `type=int`, and text it refuses now raises `ValidationError` instead of
  argparse's usage error; see Gotchas), and make `timing.py`'s rows
  `Timing` records; add the Hypothesis profile and boundary tests for
  `make` and both scripts' arguments; add the `.vscode/` template files.

### Other sources of test functions (reviewed 2026-10-17)

The user shared a list of other collections on 2026-10-17. What each offers
optibench, and what was decided:

| Source | What it is | Decision |
|--------|------------|----------|
| COCO / BBOB (Hansen, Finck, Ros and Auger, 2009, INRIA RR-6829; https://github.com/numbbo/coco, BSD-3-Clause) | 24 noiseless functions in 5 groups, each a base function with seeded shifts, rotations and conditioning (no data files); the standard for comparing continuous optimisers, with published results for hundreds of algorithms | proposed as a new spec module (PLAN.md); it changes the non-goal "shifted, rotated or noisy variants", so it needs approval |
| AMPGO test functions (Gavana, https://infinity77.net/global_optimization/test_functions.html; already cited as `GAVANA`) | 18 one-dimensional and about 184 multivariate functions with difficulty ratings | source for a short list of missing classics (PLAN.md); not imported wholesale, most add little beyond the 49 |
| Wikipedia, "Test functions for optimization" (already cited as `WIKIPEDIA`) | formulas, domains and plots of about 25 single-objective functions, plus constrained and multi-objective ones | every single-objective one is in optibench except Himmelblau; the constrained and multi-objective ones are non-goals |
| Jamil and Yang (2013), "A literature survey of benchmark functions for global optimisation problems", Int. J. Math. Modelling and Numerical Optimisation 4(2) | 175 functions with formulas, domains and minima | primary reference for the missing classics |
| Opfunu (Python, numpy) and the CEC competition suites | about 200 functions including every CEC suite | not used: CEC needs per-suite shift and rotation data files (a download each, licences vary); a non-goal unless CEC comparisons are wanted |
| TestFunctions (R package, Collin Erickson) | mostly emulation functions (borehole and others) from SFU's non-optimisation pages | not used: emulation pages are a non-goal |
| Arnold Neumaier, Global Optimization test problems (https://arnold-neumaier.at/glopt/test.html) | an index of links to constrained and unconstrained suites | reference only |
| PLATO benchmarks (Mittelmann, https://plato.asu.edu/bench.html) | timings of optimisation software, not test functions | reference only |

## Rejected approaches

- fastmath for the compiled cart (2026-10-24): chosen by the user on my
  report that it halved the time, but that halving came from the
  parallel kernel, which a stale cache had made serial in the other
  runs. Measured fairly: 188 us a step exact, 190 with fastmath, for
  1,000 carts. It also lets results differ between machines, so the user
  dropped it.

- Porting the GPL-2.0 R code: see Decisions.
- Applying the matrix to a batch in COCO's order (a loop over j adding
  `x[:, j] * matrix[:, j]`) and summing the penalty with `cumsum`
  (2026-10-17, branch `coco-order`): the loop made f16 33% slower (99 to
  132 ms per 100,000 points at d = 10) and f23 29% slower, over the 0.1 s
  budget, and the `cumsum` penalty made f07, f22 and f24 12% to 28%
  slower. Both went back to `einsum`; the ordered rotations alone already
  cut the gap to COCO (Decisions).
- One plain function per problem plus a metadata table: the parameters,
  bounds and minimum would live in three places.
- Depending on an existing Python collection of test functions: the user
  asked for an own library with every constant editable, and the licences
  and accuracy of those collections would need checking function by function.
- Replacing BBOB's module-level `functools.cache` helpers with
  `cached_property` on the models (`python-standard`, 2026-10-17): no
  behaviour or speed gain, and the module cache is shared by every
  instance with the same seed, which is what BBOB wants.
- A `check_dimension` helper and an `as_array` helper in `problem.py`
  (Tier 1): each had one real call site, so the checks stay inline until a
  second one exists.
- Renaming only the distribution (installed as `optibench`, imported as
  `optbench`) or only the GitHub repo (2026-10-23): the two names would
  mislead every reader for a saving of about an hour; see Decisions, Name.
- Keeping the local folder as `optbench` after the rename (2026-10-23,
  first plan): it spared moving the per-folder Claude state, but the user
  wanted nothing left under the old name, so the folder moved too.

## Results

| What | Measure | Result | Notes |
|------|---------|--------|-------|
| Formulas F9: criterion 3 (`tests/test_formula.py`, `CHANGED`: one problem per function file with changed constants; a check that every file is in it) | formula against numpy, and against the default formula | all 20 match their numpy values and print differently from the defaults; Ackley's default formula on a = 10 would be off by 100% | suite 2005 tests in 4 min 2 s at load 25 (110 s at load 3 to 6 before F9, 21 cases added); timing script 0 of 83 over 100 ms |
| BBOB formula sampling (`tests/test_formula.py`: every d at instance 1, every instance at d = 3; the user's choice, 2026-10-18) | suite time | 9 min 27 s to 1 min 50 s (load 3 to 6), 2368 to 1984 tests; peak 353 to 292 MB; the slowest case is Gallagher 101 at d = 6, 10 s under coverage |
| Formulas F8: BBOB f15 to f24; `formula()` abstract (`tests/test_formula.py` over every registered problem; BBOB values compared with `f_opt` subtracted) | formula against numpy | all 250 new problem variants equal (1e-12, 1e-9 for f16 to f19 and f23; atol 1e-10) | suite 2368 tests in 9 min 0 s and 9 min 27 s (two runs, load 5 to 10), against 39 s after F7; peak 353 to 371 MB. Without coverage the new cases take 137 s (Gallagher 101: 61 s, Katsuura 26 s, Weierstrass 22 s); under coverage one Gallagher 101 case at d = 6 takes 12 to 54 s. Timing script 0 of 83 over 100 ms |
| Formulas F7: BBOB f6 to f14 (`tests/test_formula.py`, as F6) | formula against numpy | all 225 new problem variants equal to rtol 1e-12, atol 1e-10; f6's T_osz of a sum of squares tests the bare `sum z_i^2 > 0`, which holds no piecewise | suite 2119 tests: 39 s against F6's 14 s, back to back at load 5; building f7 at d = 6 took 1.0 s until `maximum` built `Max` unevaluated (0.09 s; sympy compared the arguments symbolically); timing script 0 of 83 over 100 ms (3 over at load 8 from another session's browser tests, none of them touched) |
| Formulas F6: BBOB f1 to f5 and the transform twins (`tests/test_formula.py`, d = 2 to 6 at instances 1 to 5) | formula against numpy | all 125 new problem variants equal to rtol 1e-12, atol 1e-10 | suite 1894 tests, 14.3 s with coverage (about 200 MB peak); timing script 0 of 83 over 100 ms |
| Formulas F5: the 10 classics (`tests/test_formula.py`, as F4, suite "classic" added) | formula against numpy | all 50 new problem variants equal to rtol 1e-12, atol 1e-10; the facade gains `maximum` (Schwefel 2.21) and `piecewise` (Deceptive's four pieces, chosen in `numpy.select`'s order); Alpine N. 2 is NaN below 0 on both sides, which counts as equal | suite 1765 tests, 6.8 s with coverage; timing script 0 of 83 over 100 ms (Whitley 131 ms at d = 10, the stated exception) |
| Formulas F4: other (12) (`tests/test_formula.py`, as F1; any-d problems at each d that `replace` accepts, so Powell only at d = 4) | formula against numpy | all 22 new problem variants equal to rtol 1e-12, atol 1e-10; Hartmann and Shekel carry their constant matrices as float numbers | suite 1715 tests, 7.6 s with coverage |
| Formulas F3: many local minima (16) (`tests/test_formula.py`, as F1) | formula against numpy | all 41 new problem variants equal to rtol 1e-12, atol 1e-10 | suite 1693 tests, 9.4 s without coverage at load average 21; the first formula test pays sympy's import (3.3 s under that load), every other formula test under 0.05 s |
| Formulas F2: plate (5), steep (3) and valley (4) (`tests/test_formula.py`, as F1) | formula against numpy | all 32 new problem variants equal to rtol 1e-12, atol 1e-10; Booth prints as `(x1 + 2.0*x2 - 7.0)**2 + (2.0*x1 + x2 - 5.0)**2` | suite 1652 tests, about 6 s |
| Formulas F1: the 9 bowl functions (`tests/test_formula.py`, d = 1 to 6, 26 points each, 2026-10-17) | formula against numpy | all 42 problem variants equal to rtol 1e-12, atol 1e-10 | suite 1578 to 1620 tests, about 5 s either way |
| network-core review (2026-10-24, a fresh-eyes read of the branch) | defects found and fixed | Gruau's window held the failing step (0.036980 instead of 0.037773 for a cart balanced 154 steps); `steps=0` counted every network solved; `gruau` reran the 625 starts in every trial; the parallel kernel was never run compiled in a test; infinite outputs were clipped silently; the reference hard-coded its step | each fixed in its own commit, 961983e to dcd3571, with a test first |
| network-core N6, double-pole speed (`scripts.pole_timing`, 1,000 reference networks, 100,000 steps, 5 runs, wall time less the policy's, 2026-10-24) | seconds | serial: median 37.5 s, spread 0.5 s (load 4 to 5); parallel, after the cache fix: median 28.2 s, spread 6.4 s (load 4 rising to 11); kernel alone 188 us a step parallel, 363 to 426 us serial | the 10 s target is not met: each cart step needs 16 sines and cosines, and the policy is called from Python every step; the budget is 35 s (the user) |
| network-core N5, Gruau's score and test (2026-10-24) | the damping score against eq. 3 and 4 worked by hand; the reference on the 625 starts, compiled | equal to 1e-12; the reference without velocities wins 535 of 625 on Gruau's ranges (167 on the full input scales, the spec's fallback before the paper was found; Gruau reports 569 on average with velocities) and passes the solution test | the compiled child test now takes about 45 s at load 8 |
| network-core N4, pole tasks (2026-10-24) | the linear reference (discrete LQR of the linearised cart, unit weights; velocities differenced from the last two observations when unseen) | 100,000 steps from the published start in all four variants, compiled, about 3 s each at n = 1; 4 random trials of 1,000 steps won at seed 1 in all four; at seed 0 one double-pole start is lost; a constant zero push fails every variant | 14 tests; the 100,000-step check runs in a child process with numba on (13 s) |
| network-core N3, cart dynamics (2026-10-24) | one network step against an independent RK4 of Gomez et al. (2008) Appendix A; speed of the compiled step | equal to 1e-12 for one and two poles; double pole compiled, 1 thread 477 ns per cart-step, 8 threads 241 ns at load 12; one cart 1.8 us a step (serial kernel), where the parallel one cost 85 us | 1,000 networks on 100,000 steps: about 48 s on one core, 24 s at load 12 on 8; under 10 s needs about 5 free cores (N6 measures it) |
| network-core N2, `TrackedTask` (2026-10-24) | acceptance tests | one evaluation per network per trial; best score and the first solving evaluation (5 after a batch of 3 and a solving batch of 2 over 2 trials) kept across calls | 3 tests, 100% branch coverage |
| network-core N1, XOR (2026-10-24) | acceptance tests | a hand-built 2-2-1 sigmoid network scores 15.9985 of 16 and is solved; a batch of 3 and `single` score alike over 2 trials; constant 0.5 scores 4, not solved; wrong shapes and NaN refused | 11 tests, 100% branch coverage of `networks/` |
| Python compliance (`python-compliance`, 2026-10-23) | checks after | `/zz-08-python-compliance` 13 of 22 checks met before, 22 after; 2009 tests, 100% coverage; ruff, mypy and pyright clean; ty 2 advisory findings, as before | `timing` 0 of 83 over budget (Whitley 135 ms, the stated exception); baseline and timing give the same table and CSV columns as before |
| Python standard (`python-standard`, template configs, 2026-10-17) | errors before, after | mypy strict 33 to 0; ruff with the template rules 70 to 0 (30 no-self-use, 23 banned-api, 17 magic values); pyright 0 to 0; coverage 100% of `src` and `scripts` to 100% of branches over `src` and `tests` | every value, bound and minimum of 254 problem variants bit-identical before and after (scratch pin); timing 1261 ms in all before, 1270 after (three runs each, minimum per function), median ratio 1.000 |
| Batch speed, Tier 1 functions (100,000 points, CPU time, min of 5, Apple silicon under load, 2026-10-16) | ms per call | Sphere (d = 10) 0.5; Branin 1.6; Shekel (m = 10) 7.3 | spec criterion 2 asks for under 100 ms |
| Batch speed, "many local minima" group (100,000 points, d = 10 where free, CPU time, min of 5, load average 5 to 9, 2026-10-16) | ms per call | Ackley 11.0; Bukin N. 6 0.3; Cross-in-Tray 2.9; Drop-Wave 1.5; Eggholder 2.0; Gramacy and Lee 1.8; Griewank 10.4; Holder Table 2.1; Langermann 13.2; Levy 13.0; Levy N. 13 2.8; Rastrigin 9.8; Schaffer N. 2 1.1; Schaffer N. 4 1.7; Schwefel 9.6; Shubert 14.5 | all under the 100 ms budget |
| Batch speed, bowl-shaped group (100,000 points, d = 10 where free, CPU time, min of 5, load average 7 to 10, 2026-10-16) | ms per call | Bohachevsky 1 1.9, 2 2.0, 3 1.1; Perm 0, d, beta 43.1 (126.3 with `x ** i`); Rotated Hyper-Ellipsoid 1.6; Sphere 0.4; Sum of Different Powers 9.4; Sum Squares 1.7; Trid 2.8 | all under the 100 ms budget |
| Batch speed, valley-shaped group (100,000 points, d = 10 where free, CPU time, min of 5, load average 4 to 9, 2026-10-16) | ms per call | Dixon-Price 2.9; Rosenbrock 2.9; Six-Hump Camel 1.5; Three-Hump Camel 0.3 | all under the 100 ms budget |
| Batch speed, plate-shaped group (100,000 points, d = 10 where free, CPU time, min of 5, load average 11 to 20, 2026-10-16) | ms per call | Booth 0.3; Matyas 0.2; McCormick 1.0; Power Sum (d = 4) 8.9; Zakharov 2.8 | all under the 100 ms budget |
| Batch speed, steep group (100,000 points, d = 10 where free, CPU time, min of 5, load average 3 to 9, 2026-10-16) | ms per call | De Jong N. 5 53.5; Easom 2.0; Michalewicz 25.2 | all under the 100 ms budget; De Jong pays for a float power over 25 drops |
| Batch speed, "other" group (100,000 points, d = 10 where free, Powell d = 8, CPU time, min of 5, load average 3 to 7, 2026-10-17) | ms per call | Beale 1.7; Branin 1.0; Colville 0.7; Forrester 0.9; Goldstein-Price 0.7; Hartmann 3-D 8.5, 4-D 10.7, 6-D 9.9; Perm d, beta 42.3; Powell 6.3; Shekel 6.8; Styblinski-Tang 13.1 | all under the 100 ms budget; every one of the 49 functions now meets spec criterion 2 |
| Batch speed, all 49 by `scripts.timing` (100,000 points, d = 10 where free, Powell d = 8, CPU time, min of 5, load average 6 to 13, 2026-10-17) | ms per call | fastest Matyas 0.2; median 2.7 (Zakharov); slowest Michalewicz 26.1, Perm d, beta 42.5, Perm 0 43.0, De Jong N. 5 54.5 | 0 of 49 over the 100 ms budget; the per-group rows above agree within 1 ms |
| Batch speed, the ten classics by `scripts.timing` (100,000 points, d = 10 where free, CPU time, min of 5, load average about 7, 2026-10-17) | ms per call | Himmelblau 0.3; Salomon 1.3; Schwefel 2.21 1.4; Qing 1.7; Schwefel 2.22 1.8; Happy Cat 2.1; Bird 4.7; Alpine N. 2 10.8; Deceptive 20.8; Whitley 128.4 | Whitley is over the 100 ms budget: it has d^2 = 100 terms per point, and the 10 million cosines alone take 70 to 90 ms; an in-place rewrite saved 3% (noise), so it was not kept |
| BBOB f1 to f5 against `cocoex` 2.8.2 (2026-10-17) | max relative difference | at most 1e-12 at 26 points each (20 in the domain, 5 outside, `x_opt`) for d = 2, 3, 5, 10, 20, 40 and instances 1, 2, 7, 15, 100 | 150 combinations, all pass |
| Batch speed, BBOB f1 to f5 by `scripts.timing` (100,000 points, d = 10, CPU time, min of 5, load average about 7, 2026-10-17) | ms per call | f1 0.9; f5 4.0; f2 34.4; f4 45.3; f3 51.4 | all under the 100 ms budget; T_osz (a log, an exp and two sines per coordinate) is most of f2 to f4 |
| BBOB f6 to f9 against `cocoex` 2.8.2 (2026-10-17) | max relative difference | at most 1e-12, same points, dimensions and instances as f1 to f5 | 120 combinations, all pass on the first run |
| Batch speed, BBOB f6 to f9 by `scripts.timing` (as f1 to f5, load average 5 to 10, 2026-10-17) | ms per call | f8 4.4; f9 4.9; f6 8.4; f7 10.3 | all under budget |
| BBOB f10 to f14 against `cocoex` 2.8.2 (2026-10-17) | max relative difference | at most 1e-12, same points, dimensions and instances as f1 to f5 | 150 combinations, all pass on the first run |
| Batch speed, BBOB f10 to f14 by `scripts.timing` (as f1 to f5, load average 4 to 7, 2026-10-17) | ms per call | f13 3.3; f14 10.7; f12 13.9; f10 35.5; f11 35.5 | all under budget; T_osz again is most of f10 and f11 |
| BBOB f15 to f19 against `cocoex` 2.8.2 (2026-10-17) | max relative difference | f15 1.2e-13; f16 1.5e-10; f17 4.9e-11; f18 3.9e-12; f19 6.5e-10 | 150 combinations; tolerance 1e-9 for f16 to f19 (see Decisions) |
| Batch speed, BBOB f15 to f19 by `scripts.timing` (as f1 to f5, load average about 4, 2026-10-17) | ms per call | f19 14.6; f17 37.1; f18 37.0; f15 60.0; f16 92.6 (145 with 12 cosines per coordinate) | all under budget; f16 is close to it: T_osz and the rotations take 37 ms of it |
| BBOB f20 to f24 against `cocoex` 2.8.2 (2026-10-17) | max relative difference | f20 4.7e-16; f21 9.0e-14; f22 3.4e-15; f23 7.0e-10; f24 2.5e-12 | 150 combinations; all 24 BBOB functions now match COCO |
| BBOB f1 to f24 against `cocoex` 2.8.2 after the rotations were summed in COCO's order (macOS, 2026-10-17, branch `coco-order`) | max relative difference | f16 1.7e-11; f19 1.8e-10; f23 3.8e-11 (was 7.0e-10); every other function at most 2.2e-13 | timing unchanged: interleaved with the old code, min of 3 rounds, every BBOB function within 0.98x to 1.03x; f16 103 ms in both under load |
| Batch speed, BBOB f20 to f24 by `scripts.timing` (as f1 to f5, load average 2 to 3, 2026-10-17) | ms per call | f20 15.8; f24 17.4; f22 24.1; f21 71.7; f23 78.9 | all under budget; 0 of 83 functions over it (Whitley excepted) |
| Random-search baseline, BBOB f20 to f24 by `scripts.baseline` (as f1 to f5) | median final value (f_opt) | f20 -242.3 (-546.5); f21 55.93 (40.78); f22 -979.9 (-1000); f23 8.556 (6.87); f24 220.1 (102.61) | |
| Random-search baseline, BBOB f15 to f19 by `scripts.baseline` (as f1 to f5) | median final value (f_opt) | f15 1135 (1000); f16 82.18 (71.35); f17 -12.19 (-16.94); f18 0.66 (-16.94); f19 -95.60 (-102.55) | |
| Random-search baseline, BBOB f10 to f14 by `scripts.baseline` (as f1 to f5) | median final value (f_opt) | f10 67282 (-54.94); f11 136.9 (76.27); f12 1.13e7 (-621.11); f13 662.3 (29.97); f14 -46.88 (-52.35) | |
| Random-search baseline, BBOB f6 to f9 by `scripts.baseline` (as f1 to f5) | median final value (f_opt) | f6 156.9 (35.9); f7 146.8 (92.94); f8 3131 (149.15); f9 2695 (123.83) | |
| Random-search baseline, BBOB f1 to f5 by `scripts.baseline` (instance 1, d = 10, 10 seeds of 10,000 points) | median final value (f_opt) | f1 92.29 (79.48); f2 62435 (-209.88); f3 -339.4 (-462.09); f4 -290.2 (-462.09); f5 47.19 (-9.21) | |
| Random-search baseline, the ten classics by `scripts.baseline` (as the row below) | median final value (minimum) | Alpine N. 2 -1563 (-30491); Bird -106.59 (-106.76); Deceptive -0.494 (-1); Happy Cat 250 (0); Himmelblau 0.026 (0); Qing 3.3e9 (0); Salomon 7.8 (0); Schwefel 2.21 37 (0); Schwefel 2.22 1.7e8 (0); Whitley 2.6e6 (0) | |
| Random-search baseline, all 49 by `scripts.baseline` (10 seeds of 10,000 points, d = 10 where free, Powell d = 8, 2026-10-17) | median final value minus the minimum | 1-D: about 1e-6 (Forrester, Gramacy and Lee); 2-D: 1e-4 to 10 (Cross-in-Tray 3e-4, Branin 4e-3, Eggholder 16); d = 10: Sphere 13, Rastrigin 72, Rosenbrock 1.1e4, Perm 0 2e14, Perm d, beta 2e15 | the reference an optimiser must beat at the same budget; Michalewicz d = 10 reaches -4.8 of -9.66, Shekel -3.2 of -10.54 |

## Gotchas

- numba's disk cache (`cache=True`) names an entry after the function and
  its line, so two builds of one function (serial and parallel) share
  it, and the parallel dispatcher loaded the serial code: 371 us a step
  instead of 188. The cache is also keyed to the function's own file, so
  changing a decorator in `compiled.py` left stale code in use. The
  parallel build is not cached; after changing compile options, delete
  `src/optibench/networks/__pycache__/*.nb[ci]` (2026-10-24).

- The cart's Coulomb friction (`0.0005 * sign(x')`) jumps at zero speed,
  so linearising the cart by finite differences at rest with friction on
  gives nonsense (A[0, 1] came out 0.0037 instead of 0.02) and a regulator
  that fails in 8 steps. `networks/reference.py` linearises with the
  cart's friction off (2026-10-24).

- Pydantic's lax integer parsing takes integral decimal text (`"5.0"`,
  `"0.0"`), which `int()` and argparse's `type=int` refuse. Flags parsed
  into a model therefore go through `scripts/common.Integer`, which calls
  `int()`; a Hypothesis test found `"0.0"` only after about 20,000
  examples, so it is pinned with `@example` (2026-10-23).
- `git commit` with pre-commit stashes unstaged files for the hook run and
  restores them after. A test run going in the background at that moment
  sees the files without the unstaged edits, so commit only after a
  background run has finished (2026-10-23).
