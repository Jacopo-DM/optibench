"""The network interface and the XOR task."""

import numpy as np
import pytest
from numpy.typing import NDArray

from optibench.networks import Scores, Xor, single

PATTERNS = 4


def _sigmoid(z: NDArray[np.float64]) -> NDArray[np.float64]:
    return 1.0 / (1.0 + np.exp(-z))


def _xor_net(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """XOR as AND(OR, NAND).

    Returns
    -------
    numpy.ndarray
        The one output for the input vector ``x``.
    """
    hidden = _sigmoid(
        np.array([20.0 * (x[0] + x[1]) - 10.0, 30.0 - 20.0 * (x[0] + x[1])]),
    )
    return _sigmoid(np.array([20.0 * (hidden[0] + hidden[1]) - 30.0]))


class Batch:
    """A batch of ``n`` networks, each one a function of its inputs.

    A test double, behaviour first; it keeps the calls it receives.
    """

    def __init__(self, outputs: NDArray[np.float64] | None = None) -> None:
        self.outputs = outputs
        self.resets: list[int] = []
        self.calls = 0

    def reset(self, n: int) -> None:
        self.resets.append(n)

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        self.calls += 1
        if self.outputs is not None:
            return self.outputs
        return np.stack([_xor_net(row) for row in inputs])


def test_xor_sizes() -> None:
    assert (Xor().n_inputs, Xor().n_outputs) == (2, 1)


def test_hand_built_network_solves_xor() -> None:
    scores = Xor().evaluate(single(_xor_net))
    assert isinstance(scores, Scores)
    # The sigmoids saturate but never reach 0 or 1 exactly.
    assert scores.score == pytest.approx([16.0], abs=1e-2)
    assert scores.solved.tolist() == [True]


def test_batch_and_single_score_alike() -> None:
    batch = Batch()
    batched = Xor().evaluate(batch, n=3, trials=2)
    alone = Xor().evaluate(single(_xor_net), trials=2)
    np.testing.assert_allclose(batched.score, np.repeat(alone.score, 3))
    assert batched.solved.all()

    # One reset before each of the four patterns, in each trial.
    assert batch.resets == [3] * PATTERNS * 2
    assert batch.calls == PATTERNS * 2


def test_constant_network_is_not_solved() -> None:
    half = Xor().evaluate(Batch(np.full((2, 1), 0.5)), n=2)
    assert half.score == pytest.approx([4.0, 4.0])
    assert not half.solved.any()


def test_outputs_are_clipped_to_the_unit_interval() -> None:
    wild = Xor().evaluate(Batch(np.array([[5.0], [-5.0]])), n=2)
    assert wild.score == pytest.approx([4.0, 4.0])


def test_single_calls_its_reset_hook() -> None:
    resets: list[None] = []
    policy = single(_xor_net, reset=lambda: resets.append(None))
    Xor().evaluate(policy)
    assert len(resets) == PATTERNS


def test_single_refuses_a_batch() -> None:
    with pytest.raises(ValueError, match="one network"):
        single(_xor_net).reset(2)


def test_wrong_output_shape_is_refused() -> None:
    with pytest.raises(ValueError, match=r"shape \(2, 1\)"):
        Xor().evaluate(Batch(np.zeros((2, 2))), n=2)


def test_nan_output_is_refused() -> None:
    with pytest.raises(ValueError, match="NaN"):
        Xor().evaluate(Batch(np.array([[np.nan]])))


@pytest.mark.parametrize(("n", "trials"), [(0, 1), (1, 0)])
def test_sizes_must_be_positive(n: int, trials: int) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        Xor().evaluate(Batch(), n=n, trials=trials)
