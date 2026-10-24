"""Balancing one or two poles on a cart, with or without velocities.

The four tasks of Gomez, Schmidhuber and Miikkulainen (2008, section 5.3),
on the cart of ``cart.py``.
"""

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

# optibench's own scales: the papers say only "scaled to [-1, 1]".
SPEED_SCALE = 2.0
SPIN_SCALE = 2.0

# Later trials start within this fraction of each input scale (the user,
# 2026-10-24); at half, even the linear reference lost 30% of double-pole
# starts.
START_SPREAD = 0.25


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
    ) -> NDArray[np.int64]:
        """Run every cart from ``states`` for up to ``steps`` network steps.

        ``states`` is advanced in place; a failed cart stays as it fell.

        Returns
        -------
        numpy.ndarray
            The steps each cart balanced, shaped ``(n,)``.
        """
        n = len(states)
        balanced = np.zeros(n, dtype=np.int64)
        alive = np.ones(n, dtype=np.bool_)
        limit = math.radians(self.failure_angle)
        for _ in range(steps):
            push = np.clip(self._act(policy, self.observe(states))[:, 0], -1, 1)
            force = MAX_FORCE * push
            small = np.abs(force) < MIN_FORCE
            force[small] = np.where(force[small] < 0, -MIN_FORCE, MIN_FORCE)
            live = np.flatnonzero(alive)
            moving = states[live]
            advance(moving, force[live], self.cart)
            states[live] = moving
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

    A pole fails at 36 deg.
    """

    @property
    @override
    def cart(self) -> Cart:
        return Cart.double()

    @property
    @override
    def failure_angle(self) -> float:
        return 36.0
