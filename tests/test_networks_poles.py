"""The four pole-balancing tasks of Gomez et al. (2008)."""

import math
import os
import subprocess  # ruff: ignore[suspicious-subprocess-import]  # runs the package compiled
import sys

import numpy as np
import pytest
from numpy.typing import NDArray

from optibench.networks import DoublePole, LinearController, SinglePole
from optibench.networks.poles import START_SPREAD, Poles

# Every pole task, and a seed whose random starts the reference wins.
TASKS = [
    SinglePole(),
    SinglePole(velocities=False),
    DoublePole(),
    DoublePole(velocities=False),
]
SEED = 1
SHORT = 1_000
TRACK = 2.4


class Constant:
    """Every network outputs the same push; a test double."""

    def __init__(self, push: float) -> None:
        self.push = push

    def reset(self, n: int) -> None:
        """Nothing to clear."""

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.full((len(inputs), 1), self.push)


def test_sizes() -> None:
    assert [(t.n_inputs, t.n_outputs) for t in TASKS] == [
        (4, 1),
        (2, 1),
        (6, 1),
        (3, 1),
    ]


@pytest.mark.parametrize("task", TASKS)
def test_reference_balances_every_trial(task: Poles) -> None:
    short = task.model_copy(update={"steps": SHORT})
    scores = short.evaluate(LinearController(short), n=2, seed=SEED, trials=4)
    assert scores.score.tolist() == [SHORT, SHORT]
    assert scores.solved.all()


@pytest.mark.parametrize("task", TASKS)
def test_doing_nothing_fails(task: Poles) -> None:
    short = task.model_copy(update={"steps": SHORT})
    scores = short.evaluate(Constant(0.0))
    assert 0 < scores.score[0] < SHORT
    assert not scores.solved.any()


def test_trial_zero_is_the_published_start() -> None:
    start = DoublePole().start(2, np.random.default_rng(0), 0)
    np.testing.assert_array_equal(
        start,
        [[0, 0, math.radians(4), 0, 0, 0]] * 2,
    )
    assert SinglePole(start_angle=1.0).start(1, np.random.default_rng(0), 0)[
        0, 2
    ] == pytest.approx(math.radians(1))


def test_later_starts_repeat_and_stay_in_range() -> None:
    task = DoublePole()
    first = task.start(500, np.random.default_rng(3), 1)
    again = task.start(500, np.random.default_rng(3), 1)
    np.testing.assert_array_equal(first, again)
    spread = task.scale[:4] * START_SPREAD
    assert np.all(np.abs(first[:, :4]) <= spread)
    assert np.all(first[:, 4:] == 0)
    assert np.all(np.abs(first[:, :4]).max(axis=0) > spread * 0.9)


def test_observations_are_scaled() -> None:
    state = np.array([[1.2, 1.0, math.radians(18), 1.0, math.radians(-9), 2]])
    np.testing.assert_allclose(
        DoublePole().observe(state),
        [[0.5, 0.5, 0.5, 0.5, -0.25, 1.0]],
    )
    np.testing.assert_allclose(
        DoublePole(velocities=False).observe(state),
        [[0.5, 0.5, -0.25]],
    )


def test_pushes_are_clipped_and_never_zero() -> None:
    task = SinglePole(start_angle=0.0, steps=20)
    runs: list[NDArray[np.float64]] = []
    for push in (0.0, 1e-9, 1.0, 5.0, -1e-9):
        states = task.start(1, np.random.default_rng(0), 0)
        task.run(Constant(push), states, task.steps)
        runs.append(states)
    np.testing.assert_array_equal(runs[0], runs[1])
    np.testing.assert_array_equal(runs[2], runs[3])
    assert runs[4][0, 1] < 0 < runs[0][0, 1]


def test_a_cart_that_leaves_the_track_fails() -> None:
    task = SinglePole(start_angle=0.0, steps=SHORT)
    states = np.array([[TRACK - 0.01, 1.0, 0.0, 0.0]])
    assert task.run(Constant(0.0), states, task.steps)[0] == 0
    assert states[0, 0] > TRACK


def test_reference_balances_the_full_budget_compiled() -> None:
    """Run all four tasks for 100,000 steps with numba on.

    A child process, so pytest's uncompiled setting does not reach it.
    """
    code = (
        "from optibench.networks import DoublePole, LinearController, "
        "SinglePole\n"
        "for task in (SinglePole(), SinglePole(velocities=False), "
        "DoublePole(), DoublePole(velocities=False)):\n"
        "    s = task.evaluate(LinearController(task))\n"
        "    print(int(s.score[0]), bool(s.solved[0]))\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "NUMBA_DISABLE_JIT"}
    done = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]  # fixed arguments
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert done.stdout.split("\n")[:4] == ["100000 True"] * 4
