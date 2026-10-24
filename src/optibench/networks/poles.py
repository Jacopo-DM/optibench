"""Balancing one or two poles on a cart, with or without velocities.

The four tasks of Gomez, Schmidhuber and Miikkulainen (2008, section 5.3),
on the cart of ``cart.py``.
"""

import itertools
import math
from abc import abstractmethod
from typing import override

import numpy as np
from numpy.typing import NDArray

from .cart import Cart, advance
from .policy import Policy
from .task import Task

TRACK = 2.4
MAX_FORCE = 10.0

# The papers' smallest push, so a network cannot hold the poles still by
# pushing with exactly zero.
MIN_FORCE = MAX_FORCE / 256

# Gruau, Whitley and Pyeatt (1996, section 3): cart speeds of 1.5 m/s
# and pole speeds of 115 deg/s map to an input of 1, as do the track's end
# and the failure angle.
SPEED_SCALE = 1.5
SPIN_SCALE = math.radians(115)

# Later trials start within this fraction of each input scale (the user,
# 2026-10-24); at half, even the linear reference lost 30% of double-pole
# starts.
START_SPREAD = 0.25

# Gruau, Whitley and Pyeatt (1996), as Stanley and Miikkulainen (2002,
# section 4.3.3) state it: the damping score over 1,000 steps, its window
# of 100, and the solution test of 625 starts, 200 of which must balance.
GRUAU_STEPS = 1_000
GRUAU_WINDOW = 100
GRID = (0.05, 0.25, 0.5, 0.75, 0.95)
GENERALISE = 200

# The intervals of the 625 starts for x, x', theta_1 and theta_1' (Gruau
# et al. 1996, section 4.3); the second pole always starts upright.
INTERVALS = np.array([2.16, 1.35, math.radians(3.6), math.radians(8.6)])


class Poles(Task):
    """The shared simulation of ``SinglePole`` and ``DoublePole``.

    Each network step observes the state, asks every network for a force
    in ``[-1, 1]`` (clipped, times 10 N, at least 10/256 N in size) and
    advances its cart by 0.02 s. A cart fails when it leaves the track
    (+-2.4 m) or a pole passes the failure angle. The score is the
    number of network steps balanced, out of ``steps``; solved when all
    of them are.

    Trial 0 starts from the published state: the cart at rest in the
    middle, the first pole at ``start_angle``, any second pole upright.
    Later trials draw x, x', the first angle and its velocity uniformly
    within a quarter of each one's input scale, from the seed.

    Parameters
    ----------
    velocities
        Whether the networks see the velocities (the Markovian task) or
        only the cart's position and the angles.
    start_angle
        The first pole's angle at the start of trial 0, in degrees.
    steps
        The budget of network steps.
    """

    velocities: bool = True
    start_angle: float = 4.0
    steps: int = 100_000

    @property
    @abstractmethod
    def cart(self) -> Cart:
        """The cart and its poles."""

    @property
    @abstractmethod
    def failure_angle(self) -> float:
        """The angle past which a pole has fallen, in degrees."""

    @property
    @override
    def n_inputs(self) -> int:
        poles = len(self.cart.masses)
        return 2 + 2 * poles if self.velocities else 1 + poles

    @property
    @override
    def n_outputs(self) -> int:
        return 1

    @property
    def scale(self) -> NDArray[np.float64]:
        """What each state variable is divided by to form an input."""
        limit = math.radians(self.failure_angle)
        poles = [limit, SPIN_SCALE] * len(self.cart.masses)
        return np.array([TRACK, SPEED_SCALE, *poles])

    def start(
        self,
        n: int,
        rng: np.random.Generator,
        trial: int,
    ) -> NDArray[np.float64]:
        """Return the start state of every cart in trial ``trial``.

        Returns
        -------
        numpy.ndarray
            States shaped ``(n, 2 + 2 * poles)``.
        """
        states = np.zeros((n, len(self.scale)))
        if trial == 0:
            states[:, 2] = math.radians(self.start_angle)
        else:
            spread = self.scale[:4] * START_SPREAD
            states[:, :4] = rng.uniform(-spread, spread, size=(n, 4))
        return states

    def observe(self, states: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return what the networks see of each state.

        Returns
        -------
        numpy.ndarray
            Inputs shaped ``(n, n_inputs)``.
        """
        scaled = states / self.scale
        return scaled if self.velocities else scaled[:, ::2]

    def run(
        self,
        policy: Policy,
        states: NDArray[np.float64],
        steps: int,
        offsets: NDArray[np.float64] | None = None,
    ) -> NDArray[np.int64]:
        """Run every cart from ``states`` for up to ``steps`` network steps.

        ``states`` is advanced in place; a failed cart stays as it fell.
        ``offsets``, shaped ``(window, n)``, receives the sum of each live
        cart's first four inputs in absolute value (x, x', theta_1,
        theta_1', each scaled as an input) after every step, step
        ``i`` in row ``i % window``, so it ends holding each cart's last
        ``window`` balanced steps.

        Returns
        -------
        numpy.ndarray
            The steps each cart balanced, shaped ``(n,)``.
        """
        n = len(states)
        balanced = np.zeros(n, dtype=np.int64)
        alive = np.ones(n, dtype=np.bool_)
        limit = math.radians(self.failure_angle)
        for step in range(steps):
            push = np.clip(self._act(policy, self.observe(states))[:, 0], -1, 1)
            force = MAX_FORCE * push
            small = np.abs(force) < MIN_FORCE
            force[small] = np.where(force[small] < 0, -MIN_FORCE, MIN_FORCE)
            live = np.flatnonzero(alive)
            moving = states[live]
            advance(moving, force[live], self.cart)
            states[live] = moving
            if offsets is not None:
                offsets[step % len(offsets), live] = np.abs(
                    moving[:, :4] / self.scale[:4],
                ).sum(axis=1)
            alive[live] = (np.abs(moving[:, 0]) <= TRACK) & np.all(
                np.abs(moving[:, 2::2]) <= limit,
                axis=1,
            )
            balanced += alive
            if not alive.any():
                break
        return balanced

    @override
    def _trial(
        self,
        policy: Policy,
        n: int,
        rng: np.random.Generator,
        trial: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
        balanced = self.run(policy, self.start(n, rng, trial), self.steps)
        return balanced.astype(np.float64), balanced == self.steps


class SinglePole(Poles):
    """One pole (0.1 kg, half length 0.5 m) on a cart; fails at 12 deg."""

    @property
    @override
    def cart(self) -> Cart:
        return Cart.single()

    @property
    @override
    def failure_angle(self) -> float:
        return 12.0


class DoublePole(Poles):
    """Two poles (half lengths 0.5 m and 0.05 m) on one cart.

    A pole fails at 36 deg. With ``gruau``, the score is Gruau's damping
    score instead, ``0.1 * t / 1000 + 0.9 * f2`` over 1,000 steps, where
    ``t`` is the steps balanced and ``f2`` is 0 below 100 steps, else
    0.75 over the sum of ``|x| + |x'| + |theta_1| + |theta_1'|`` across
    the last 100 balanced steps, each scaled as an input, and at most 1
    (Gruau et al. 1996, section 4.1; Stanley and Miikkulainen 2002 state
    neither the scaling nor the cap); and
    solved means Gruau's solution test: ``steps`` balanced from the start
    and at least 200 of the 625 starts of ``generalisation``. The test
    runs only when some network balanced all 1,000 steps.

    Parameters
    ----------
    gruau
        Score and solve the task as Gruau et al. (1996) did.
    """

    gruau: bool = False

    @property
    @override
    def cart(self) -> Cart:
        return Cart.double()

    @property
    @override
    def failure_angle(self) -> float:
        return 36.0

    def generalisation(self, policy: Policy, n: int) -> NDArray[np.int64]:
        """Count the starts of Gruau's 625 that each network balances.

        Each of x, x', the first angle and its velocity takes 0.05, 0.25,
        0.5, 0.75 and 0.95 of its interval in ``INTERVALS`` (Gruau et al.
        1996, section 4.3: +-2.16 m, +-1.35 m/s, +-3.6 deg, +-8.6 deg/s),
        so x takes -1.944, -1.08, 0, 1.08 and 1.944 m; every start runs
        1,000 steps.

        Returns
        -------
        numpy.ndarray
            How many of the 625 starts each network balanced, ``(n,)``.
        """
        wins = np.zeros(n, dtype=np.int64)
        for start in itertools.product(GRID, repeat=4):
            states = np.zeros((n, len(self.scale)))
            states[:, :4] = INTERVALS * (2 * np.array(start) - 1)
            policy.reset(n)
            wins += self.run(policy, states, GRUAU_STEPS) == GRUAU_STEPS
        return wins

    @override
    def _trial(
        self,
        policy: Policy,
        n: int,
        rng: np.random.Generator,
        trial: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
        if not self.gruau:
            return super()._trial(policy, n, rng, trial)
        start = self.start(n, rng, trial)
        offsets = np.zeros((GRUAU_WINDOW, n))
        balanced = self.run(policy, start.copy(), GRUAU_STEPS, offsets)
        damping = np.zeros(n)
        long = balanced >= GRUAU_WINDOW
        damping[long] = np.minimum(1.0, 0.75 / offsets[:, long].sum(axis=0))
        score = 0.1 * balanced / GRUAU_STEPS + 0.9 * damping
        solved = np.zeros(n, dtype=np.bool_)
        if np.any(balanced == GRUAU_STEPS):
            policy.reset(n)
            full = self.run(policy, start, self.steps) == self.steps
            solved = full & (self.generalisation(policy, n) >= GENERALISE)
        return score, solved
