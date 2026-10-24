"""Time the double pole on a batch of networks (goal network-core).

Run with ``uv run python -m optibench.scripts.pole_timing``. Each repeat
runs 1,000 copies of the linear reference from the published start for
100,000 network steps, so every cart balances to the end: the worst case.
The time is wall seconds, because the carts run on all cores, less the
time spent inside the policy, which is the caller's. Prints every repeat,
the median and the spread, and exits with status 1 if the median is over
the 35 s budget. Takes minutes; run nothing else meanwhile.
"""

import argparse
import statistics
import sys
import time
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from optibench.model import Model
from optibench.networks import DoublePole, LinearController

# No ``from __future__ import annotations`` here: ruff would then move this
# import, which pydantic needs at run time, under TYPE_CHECKING.
from optibench.scripts.common import Integer

NETWORKS = 1_000
STEPS = 100_000
REPEATS = 5
# The spec's 10 s was not reachable; the user, 2026-10-24, set the budget
# to the measured median plus its spread (28.2 + 6.4 s at load 4 to 11).
BUDGET = 35.0


class Arguments(Model):
    """The command-line arguments, parsed from their text."""

    networks: Integer = NETWORKS
    steps: Integer = STEPS
    repeats: Integer = REPEATS


def parse_arguments(argv: Sequence[str] | None = None) -> Arguments:
    """Read ``--networks``, ``--steps`` and ``--repeats``.

    Returns
    -------
    Arguments
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
    )
    parser.add_argument("--networks", default=NETWORKS)
    parser.add_argument("--steps", default=STEPS)
    parser.add_argument("--repeats", default=REPEATS)
    return Arguments.model_validate(vars(parser.parse_args(argv)))


class Timed:
    """A policy that adds up the time spent inside another one.

    Behaviour first and holding no record, the standard's exception.
    """

    def __init__(self, policy: LinearController) -> None:
        self.policy = policy
        self.seconds = 0.0

    def reset(self, n: int) -> None:
        """Reset the wrapped policy."""
        self.policy.reset(n)

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        """Call the wrapped policy and count its time.

        Returns
        -------
        numpy.ndarray
            The wrapped policy's outputs.
        """
        start = time.perf_counter()
        outputs = self.policy(inputs)
        self.seconds += time.perf_counter() - start
        return outputs


def time_poles(networks: int, steps: int) -> tuple[float, int]:
    """Run the reference on the double pole once.

    Returns
    -------
    tuple
        Seconds less the policy's own, and the fewest steps any cart
        balanced.
    """
    task = DoublePole(steps=steps)
    policy = Timed(LinearController(task))
    states = task.start(networks, np.random.default_rng(0), 0)
    policy.reset(networks)
    start = time.perf_counter()
    balanced = task.run(policy, states, steps)
    return time.perf_counter() - start - policy.seconds, int(balanced.min())


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point.

    Returns
    -------
    int
        0 if the median is within the budget, else 1.
    """
    args = parse_arguments(argv)

    # One untimed run compiles the cart code first.
    time_poles(args.networks, 1)
    times: list[float] = []
    for repeat in range(args.repeats):
        seconds, fewest = time_poles(args.networks, args.steps)
        times.append(seconds)
        print(f"repeat {repeat}: {seconds:.2f} s, every cart {fewest} steps")  # ruff: ignore[print]
    median = statistics.median(times)
    spread = max(times) - min(times)
    verdict = "within" if median <= BUDGET else "OVER"
    print(  # ruff: ignore[print]
        f"{args.networks} networks, {args.steps} steps: median {median:.2f}"
        f" s, spread {spread:.2f} s, {verdict} the {BUDGET:.0f} s budget",
    )
    return 0 if median <= BUDGET else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
