"""Counting evaluations of a network task."""

import numpy as np
import pytest
from numpy.typing import NDArray

from optibench.networks import TrackedTask, Xor


class Constant:
    """A batch whose networks each output a fixed value.

    A test double, behaviour first.
    """

    def __init__(self, values: list[float]) -> None:
        self.values = np.array(values)[:, None]

    def reset(self, n: int) -> None:
        """Nothing to clear."""

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        return self.values[: len(inputs)]


class Exact:
    """A batch that answers XOR exactly; a test double."""

    def reset(self, n: int) -> None:
        """Nothing to clear."""

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.not_equal(inputs[:, :1], inputs[:, 1:]).astype(np.float64)


def test_a_fresh_tracker_is_empty() -> None:
    tracked = TrackedTask(Xor())
    assert tracked.evaluations == 0
    assert tracked.best_score == -np.inf
    assert tracked.solved_at is None
    assert tracked.curve.shape == (0, 2)


def test_counts_one_evaluation_per_network_per_trial() -> None:
    tracked = TrackedTask(Xor())
    scores = tracked.evaluate(Constant([0.5, 0.0]), n=2, trials=3)
    assert scores.score.tolist() == [4.0, 4.0]
    assert tracked.evaluations == 2 * 3
    assert tracked.best_score == pytest.approx(4.0)
    assert tracked.solved_at is None


def test_keeps_the_best_and_the_first_solution() -> None:
    tracked = TrackedTask(Xor())
    tracked.evaluate(Constant([0.5, 0.5, 0.5]), n=3)
    tracked.evaluate(Exact(), n=2, trials=2)
    tracked.evaluate(Exact(), n=1)

    # The first exact network finished its two trials at 3 + 2.
    assert tracked.solved_at == 3 + 2
    assert tracked.best_score == pytest.approx(16.0)
    np.testing.assert_array_equal(
        tracked.curve,
        [[3.0, 4.0], [7.0, 16.0], [8.0, 16.0]],
    )
