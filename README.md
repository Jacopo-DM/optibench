<div align="center">

<a id="optibench"></a>

# <img src="docs/logo.svg" alt="optibench logo: a ball resting at the bottom of a ring, with a fading trail, on a cobalt tile" width="160"><br>optibench

Test functions for optimisation algorithms, from the SFU Virtual Library of Simulation Experiments

[![CI][ci-shield]][ci-url]
[![License][license-shield]][license-url]
[![Last commit][commit-shield]][commit-url]

[![Python][tool-python-shield]][tool-python-url]
[![uv][tool-uv-shield]][tool-uv-url]
[![NumPy][tool-numpy-shield]][tool-numpy-url]
[![Pydantic][tool-pydantic-shield]][tool-pydantic-url]
[![SymPy][tool-sympy-shield]][tool-sympy-url]
[![Numba][tool-numba-shield]][tool-numba-url]

[Report a bug][issues-url]

</div>

## Installation

Install it from GitHub:

```bash
uv add git+https://github.com/Jacopo-DM/optibench
```

## Usage

```python
import numpy as np
import optibench

branin = optibench.make("branin")  # or optibench.Branin()
x = np.array([[np.pi, 2.275], [0.0, 0.0]])  # points shaped (n, d)
branin(x)  # values shaped (n,)
branin.minimum.value  # 0.3978873577...
optibench.Branin(s=5.0, t=0.2).minimum.value  # 1.0: the minimum follows s and t

tracked = optibench.Tracked(optibench.Sphere(d=10))
tracked(np.random.default_rng(0).uniform(-5.12, 5.12, size=(100, 10)))
tracked.evaluations, tracked.best_value, tracked.curve

# The baseline any optimiser should beat: 10,000 uniform random points.
run = optibench.random_search(branin, 10_000, np.random.default_rng(0))
run.best_value, run.best_point, run.curve
```

`optibench.names()` lists the functions: the 49 of the SFU pages
(`optibench.names(suite="sfu")`), ten well-known ones not on them
(`suite="classic"`: Alpine N. 2, Bird, Deceptive, Happy Cat, Himmelblau,
Qing, Salomon, Schwefel 2.21 and 2.22, Whitley), and the COCO/BBOB
noiseless suite (`suite="bbob"`, all 24 functions), whose instances equal
COCO's: `optibench.BbobRastrigin(d=10, instance=3)` is COCO's f3, instance
3, in 10-D. `optibench.names(group)`
lists those of one shape group.

## Overview

Test functions for optimisation algorithms, written from the formulas on the
optimisation pages of the Virtual Library of Simulation Experiments by Sonja
Surjanovic and Derek Bingham (Simon Fraser University,
https://www.sfu.ca/~ssurjano/optimization.html). Every function evaluates a
batch of points in one call, takes its constants as keyword arguments with
the published values as defaults, and knows its domain and global minimum.

## Formulas

Every problem returns its function as a sympy expression in the variables
`x1` to `xd`, built from the same constants as its numpy code, and
`optibench.evaluate_formula` turns one back into values:

```python
booth = optibench.make("booth")
booth.formula()  # (x1 + 2.0*x2 - 7.0)**2 + (2.0*x1 + x2 - 5.0)**2
x = np.array([[1.0, 3.0], [0.0, 0.0]])
optibench.evaluate_formula(booth.formula(), x)  # [0., 74.], as booth(x)
optibench.make("ackley", d=2, a=10.0).formula()  # follows the changed a
```

sympy is a required dependency. Its printer runs out of memory on a
piecewise expression nested inside another one's condition, so
`evaluate_formula` refuses that shape with a ValueError.

## Documentation

There are no built docs yet. Each class's docstring gives its formula,
constants and sources; `CODEMAP.md` lists the modules and their
interfaces, and `DESIGN.md` the decisions and the measured results.

## License

MIT license; see [`LICENSE`](LICENSE).

[ci-shield]: https://img.shields.io/github/actions/workflow/status/Jacopo-DM/optibench/ci.yml?branch=main&label=CI
[ci-url]: https://github.com/Jacopo-DM/optibench/actions/workflows/ci.yml
[license-shield]: https://img.shields.io/github/license/Jacopo-DM/optibench
[license-url]: LICENSE
[commit-shield]: https://img.shields.io/github/last-commit/Jacopo-DM/optibench
[commit-url]: https://github.com/Jacopo-DM/optibench/commits
[tool-python-shield]: https://img.shields.io/badge/Python-3.13%2B-3776AB?style=for-the-badge&logo=python&logoColor=white
[tool-python-url]: https://www.python.org/
[tool-uv-shield]: https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white
[tool-uv-url]: https://docs.astral.sh/uv/
[tool-numpy-shield]: https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white
[tool-numpy-url]: https://numpy.org/
[tool-pydantic-shield]: https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white
[tool-pydantic-url]: https://docs.pydantic.dev/
[tool-sympy-shield]: https://img.shields.io/badge/SymPy-3B5526?style=for-the-badge&logo=sympy&logoColor=white
[tool-sympy-url]: https://www.sympy.org/
[tool-numba-shield]: https://img.shields.io/badge/Numba-00A3E0?style=for-the-badge&logo=numba&logoColor=white
[tool-numba-url]: https://numba.pydata.org/
[issues-url]: https://github.com/Jacopo-DM/optibench/issues
