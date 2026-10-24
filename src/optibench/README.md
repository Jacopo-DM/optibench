# optibench (package)

The test functions, the `Problem` base class, the registry, `Tracked`,
the random-search baseline, and `networks/`: tasks that score batches of
networks instead of points.

Interface: see [CODEMAP.md](../../CODEMAP.md). Spec and reasons: see
[DESIGN.md](../../DESIGN.md).

## Assumes

- Callers pass points shaped `(n, d)`; one point is `x[None]`.
- A network task calls a policy with inputs `(n, n_in)` and expects
  outputs `(n, n_out)`; one network is wrapped with `networks.single`.
- A problem is pure: same points, same values; only `Tracked` keeps state.

## Must never depend on

- `entwined` or any other optimiser code.
- Any run-time library except numpy, pydantic, sympy and numba (numba
  only through `networks/compiled.py`).
- The SFU site's GPL-2.0 MATLAB and R code (see DESIGN.md).
