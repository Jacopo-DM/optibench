"""A linear controller that balances the poles: the tasks' known answer.

Its gains are the discrete linear-quadratic regulator of the cart's
equations linearised at rest, so it shows each pole task can be solved as
set up, as a published minimum does for a test function. Without the
velocities it estimates them from its last two observations, which makes
it a recurrent controller.
"""

import numpy as np
from numpy.typing import NDArray

from .cart import advance
from .poles import MAX_FORCE, Poles

STEP = 1e-6
ITERATIONS = 10_000


def _linearise(
    task: Poles,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return A and B of the network step around rest, by differences.

    Without the cart's friction: its sign term jumps at zero speed, so a
    small step in the speed would see the jump instead of the slope.

    Returns
    -------
    tuple of numpy.ndarray
        ``A`` shaped ``(w, w)`` and ``B`` shaped ``(w, 1)``.
    """
    cart = task.cart.model_copy(update={"cart_friction": 0.0})
    width = 2 + 2 * len(cart.masses)

    def step(state: NDArray[np.float64], force: float) -> NDArray[np.float64]:
        states = state[None].copy()
        advance(states, np.array([force]), cart)
        after: NDArray[np.float64] = states[0]
        return after

    rest = np.zeros(width)
    base = step(rest, 0.0)
    a = np.column_stack(
        [(step(rest + STEP * e, 0.0) - base) / STEP for e in np.eye(width)],
    )
    b = ((step(rest, STEP) - base) / STEP)[:, None]
    return a, b


def _gains(
    a: NDArray[np.float64],
    b: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Return the regulator's gains for unit state and force weights.

    Returns
    -------
    numpy.ndarray
        ``K`` shaped ``(1, w)``; the force is ``-K @ state``.
    """
    p = np.eye(len(a))
    for _ in range(ITERATIONS):
        k = np.linalg.solve(1.0 + b.T @ p @ b, b.T @ p @ a)
        p = np.eye(len(a)) + a.T @ p @ (a - b @ k)
    gains: NDArray[np.float64] = np.linalg.solve(1.0 + b.T @ p @ b, b.T @ p @ a)
    return gains


class LinearController:
    """The regulator as a policy for any number of copies of itself.

    Behaviour first: it keeps only the last observation between calls.

    Parameters
    ----------
    task
        The pole task to balance.
    """

    def __init__(self, task: Poles) -> None:
        self.task = task
        self.gains = _gains(*_linearise(task))

        # One network step, over which unseen velocities are differenced.
        self._dt = task.cart.dt * task.cart.substeps
        self._last: NDArray[np.float64] | None = None

    def reset(self, n: int) -> None:  # ruff: ignore[unused-method-argument]  # the Policy protocol passes n
        """Forget the last observation."""
        self._last = None

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        """Push against the state, estimating unseen velocities.

        Returns
        -------
        numpy.ndarray
            Forces in ``[-1, 1]``, shaped ``(n, 1)``.
        """
        scale = self.task.scale
        if self.task.velocities:
            state = inputs * scale
        else:
            seen = inputs * scale[::2]
            last = seen if self._last is None else self._last
            self._last = seen
            state = np.empty((len(inputs), len(scale)))
            state[:, ::2] = seen
            state[:, 1::2] = (seen - last) / self._dt
        push: NDArray[np.float64] = np.clip(
            -(state @ self.gains.T) / MAX_FORCE,
            -1.0,
            1.0,
        )
        return push
