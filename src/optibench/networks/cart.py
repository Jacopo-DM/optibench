"""A cart with one or two poles, simulated with RK4.

From Gomez, Schmidhuber and Miikkulainen (2008), Appendix A: Wieland's
equations for N poles on one cart, with friction.
"""

from typing import Self

import numpy as np
from numpy.typing import NDArray

from optibench.model import Model

from .compiled import compiled, compiled_parallel, rows


class Cart(Model):
    """The physical constants of the cart and its poles.

    Every default is the appendix's value. The single-pole table lists no
    friction, so the single pole uses the double pole's.

    Parameters
    ----------
    masses
        Mass of each pole (kg).
    half_lengths
        Half length of each pole (m).
    cart_mass
        Mass of the cart (kg).
    cart_friction
        Coefficient of friction of the cart on the track.
    hinge_friction
        Coefficient of friction of each pole's hinge.
    gravity
        Gravity (m/s^2), negative as the equations need it.
    dt
        Runge-Kutta step (s).
    substeps
        Runge-Kutta steps per network step (0.02 s in the papers).
    """

    masses: tuple[float, ...]
    half_lengths: tuple[float, ...]
    cart_mass: float = 1.0
    cart_friction: float = 0.0005
    hinge_friction: float = 0.000002
    gravity: float = -9.8
    dt: float = 0.01
    substeps: int = 2

    @classmethod
    def single(cls) -> Self:
        """Return the single-pole cart: one pole of 0.1 kg, 0.5 m half long.

        Returns
        -------
        Cart
            The appendix's single-pole system.
        """
        return cls(masses=(0.1,), half_lengths=(0.5,))

    @classmethod
    def double(cls) -> Self:
        """Return the double-pole cart: the long pole and a 0.01 kg one.

        Returns
        -------
        Cart
            The appendix's double-pole system.
        """
        return cls(masses=(0.1, 0.01), half_lengths=(0.5, 0.05))


@compiled
def _derivative(
    s: NDArray[np.float64],
    force: float,
    poles: NDArray[np.float64],
    cart: NDArray[np.float64],
    out: NDArray[np.float64],
) -> None:
    """Write the time derivative of one state ``s`` into ``out``.

    ``poles`` holds the masses in its first row and the half lengths in
    its second; ``cart`` holds the constants ``_constants`` lists.
    """
    masses, half = poles[0], poles[1]
    mass, mu_c, mu_p, g = cart[0], cart[1], cart[2], cart[3]
    pull = force - mu_c * np.sign(s[1])
    load = mass
    # The sines and cosines wait in ``out``'s pole slots until the second
    # loop needs them, so each is computed once.
    for j in range(len(masses)):
        th, thd = s[2 + 2 * j], s[3 + 2 * j]
        sin, cos = np.sin(th), np.cos(th)
        out[2 + 2 * j], out[3 + 2 * j] = sin, cos
        ml = masses[j] * half[j]
        pull += ml * thd * thd * sin + 0.75 * masses[j] * cos * (
            mu_p * thd / ml + g * sin
        )
        load += masses[j] * (1.0 - 0.75 * cos * cos)
    xdd = pull / load
    out[0], out[1] = s[1], xdd
    for j in range(len(masses)):
        sin, cos = out[2 + 2 * j], out[3 + 2 * j]
        thd = s[3 + 2 * j]
        ml = masses[j] * half[j]
        out[2 + 2 * j] = thd
        out[3 + 2 * j] = (
            -0.75 / half[j] * (xdd * cos + g * sin + mu_p * thd / ml)
        )


def _advance(
    states: NDArray[np.float64],
    forces: NDArray[np.float64],
    poles: NDArray[np.float64],
    cart: NDArray[np.float64],
) -> None:
    """Advance every state by one network step of RK4 steps, in place."""
    dt, substeps = cart[4], int(cart[5])
    n, width = states.shape
    work = np.empty((n, 5, width))
    for i in rows(n):
        s, k, trial = states[i], work[i, :4], work[i, 4]
        # Element loops, not array expressions: each of those would
        # allocate a temporary array per cart and step.
        for _ in range(substeps):
            _derivative(s, forces[i], poles, cart, k[0])
            for c in range(width):
                trial[c] = s[c] + dt / 2 * k[0, c]
            _derivative(trial, forces[i], poles, cart, k[1])
            for c in range(width):
                trial[c] = s[c] + dt / 2 * k[1, c]
            _derivative(trial, forces[i], poles, cart, k[2])
            for c in range(width):
                trial[c] = s[c] + dt * k[2, c]
            _derivative(trial, forces[i], poles, cart, k[3])
            for c in range(width):
                s[c] += dt / 6 * (k[0, c] + 2 * k[1, c] + 2 * k[2, c] + k[3, c])


_advance_serial = compiled(_advance)
_advance_parallel = compiled_parallel(_advance)

# Below this many carts, starting threads costs more than they save (85 us
# a step for one cart, measured 2026-10-24).
PARALLEL_FROM = 64


def _constants(cart: Cart) -> NDArray[np.float64]:
    """Pack the cart's scalars for the compiled code.

    Returns
    -------
    numpy.ndarray
        Cart mass, cart friction, hinge friction, gravity, dt and substeps.
    """
    return np.array(
        [
            cart.cart_mass,
            cart.cart_friction,
            cart.hinge_friction,
            cart.gravity,
            cart.dt,
            cart.substeps,
        ],
    )


def advance(
    states: NDArray[np.float64],
    forces: NDArray[np.float64],
    cart: Cart,
) -> None:
    """Advance each cart by one network step, in place.

    ``states`` is shaped ``(n, 2 + 2 * poles)``: x, x', then each pole's
    angle and angular velocity; ``forces`` is shaped ``(n,)`` in newtons.
    """
    poles = np.array([cart.masses, cart.half_lengths])
    kernel = (
        _advance_parallel if len(states) >= PARALLEL_FROM else _advance_serial
    )
    kernel(states, forces, poles, _constants(cart))
