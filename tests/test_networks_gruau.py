"""Gruau's damping score and solution test for the double pole."""

import numpy as np
import pytest
from numpy.typing import NDArray

from optibench.networks import DoublePole, LinearController
from optibench.networks import poles as poles_module
from optibench.networks.cart import advance
from optibench.networks.poles import GRUAU_STEPS, GRUAU_WINDOW

FULL_RUN = 0.1
LATE = 150


class Constant:
    """Every network outputs the same push; a test double."""

    def __init__(self, push: float) -> None:
        self.push = push

    def reset(self, n: int) -> None:
        """Nothing to clear."""

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.full((len(inputs), 1), self.push)


def _by_hand(task: DoublePole, push: float) -> tuple[int, float]:
    """Run one cart step by step and apply eq. 3 and 4 of Stanley (2002).

    Returns
    -------
    tuple
        Steps balanced, and the damping score.
    """
    state = task.start(1, np.random.default_rng(0), 0)
    offsets: list[float] = []
    limit = np.radians(task.failure_angle)
    # The papers' smallest push, 10/256 N, zero counting as positive.
    force = 10.0 * push if abs(push) >= 1 / 256 else 10.0 / 256
    # A constant push always ends off the track or with a fallen pole.
    while True:
        advance(state, np.array([force]), task.cart)
        if abs(state[0, 0]) > poles_module.TRACK or np.any(
            np.abs(state[0, 2::2]) > limit,
        ):
            break
        offsets.append(float(np.abs(state[0, :4] / task.scale[:4]).sum()))
    t = len(offsets)
    f2 = (
        0.0
        if t < GRUAU_WINDOW
        else min(1.0, 0.75 / sum(offsets[-GRUAU_WINDOW:]))
    )
    return t, 0.1 * t / GRUAU_STEPS + 0.9 * f2


@pytest.mark.parametrize("push", [0.0, 0.05])
def test_damping_score_follows_the_equations(push: float) -> None:
    task = DoublePole(velocities=False, gruau=True, start_angle=0.5)
    t, expected = _by_hand(task, push)
    scores = task.evaluate(Constant(push))
    assert scores.score[0] == pytest.approx(expected, rel=1e-12)
    assert not scores.solved[0]
    assert t < GRUAU_STEPS


def test_a_short_run_scores_only_its_length() -> None:
    task = DoublePole(gruau=True, start_angle=30.0)
    t, expected = _by_hand(task, 1.0)
    assert t < GRUAU_WINDOW
    assert task.evaluate(Constant(1.0)).score[0] == pytest.approx(expected)


def test_solution_needs_the_full_run_and_generalisation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # One start (all variables at the middle of their range), so the test
    # runs uncompiled in seconds.
    monkeypatch.setattr(poles_module, "GRID", (0.5,))
    monkeypatch.setattr(poles_module, "GENERALISE", 1)
    task = DoublePole(velocities=False, gruau=True, steps=2_000)
    reference = LinearController(task)
    assert task.generalisation(reference, 2).tolist() == [1, 1]
    scores = task.evaluate(reference, n=2)
    assert scores.solved.all()
    # A full run earns all of f1's 0.1, and damping on top.
    assert scores.score.min() > FULL_RUN

    monkeypatch.setattr(poles_module, "GENERALISE", 2)
    assert not task.evaluate(reference).solved[0]


class Recorder:
    """The reference for 150 steps, then a full push right.

    A test double; it keeps every input it sees.
    """

    def __init__(self, task: DoublePole) -> None:
        self.reference = LinearController(task)
        self.seen: list[NDArray[np.float64]] = []

    def reset(self, n: int) -> None:
        self.reference.reset(n)

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        self.seen.append(inputs[0].copy())
        if len(self.seen) <= LATE:
            return self.reference(inputs)
        return np.ones((len(inputs), 1))


def test_window_holds_only_balanced_steps() -> None:
    task = DoublePole(gruau=True)
    policy = Recorder(task)
    score = task.evaluate(policy).score[0]

    # Input i is the state after i steps, so the last balanced steps are
    # inputs t - 99 to t; the policy never sees the state it fell in.
    t = len(policy.seen) - 1
    assert GRUAU_WINDOW < t < GRUAU_STEPS
    window = np.abs(np.array(policy.seen[t - GRUAU_WINDOW + 1 : t + 1])[:, :4])
    f2 = min(1.0, 0.75 / window.sum())
    assert score == pytest.approx(0.1 * t / GRUAU_STEPS + 0.9 * f2, rel=1e-12)


def test_gruau_runs_one_trial_only() -> None:
    with pytest.raises(ValueError, match="one trial"):
        DoublePole(gruau=True).evaluate(Constant(0.0), trials=2)
