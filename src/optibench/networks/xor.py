"""Exclusive or, the smallest task that needs a hidden unit."""

from typing import override

import numpy as np
from numpy.typing import NDArray

from .policy import Policy
from .task import Task

PATTERNS = np.array([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
TARGETS = np.array([0.0, 1.0, 1.0, 0.0])
THRESHOLD = 0.5


class Xor(Task):
    """XOR on the four patterns of two binary inputs.

    Each pattern is shown once, with the networks reset before it. The
    score is ``(4 - sum of absolute errors) ** 2``, 16 when perfect, as in
    Stanley and Miikkulainen (2002); outputs are clipped to ``[0, 1]``
    first, so an output past either end costs no more than a wrong one.
    Solved when every output is on the target's side of 0.5. No bias
    input: a caller that wants one adds it.
    """

    @property
    @override
    def n_inputs(self) -> int:
        return 2

    @property
    @override
    def n_outputs(self) -> int:
        return 1

    @override
    def _trial(
        self,
        policy: Policy,
        n: int,
        rng: np.random.Generator,
        trial: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
        error = np.zeros(n)
        solved = np.ones(n, dtype=np.bool_)
        for index, (pattern, target) in enumerate(
            zip(PATTERNS, TARGETS, strict=True),
        ):
            # ``evaluate`` has reset them before the first pattern.
            if index:
                policy.reset(n)
            out = self._act(policy, np.tile(pattern, (n, 1)))[:, 0]
            error += np.abs(np.clip(out, 0.0, 1.0) - target)
            solved &= (out > THRESHOLD) == (target > THRESHOLD)
        return (len(TARGETS) - error) ** 2, solved
