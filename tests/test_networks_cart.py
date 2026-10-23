"""The cart-pole dynamics against Gomez et al. (2008), Appendix A."""

import os

import numpy as np
import pytest
from numpy.typing import NDArray

from optibench.networks.cart import PARALLEL_FROM, Cart, advance

G = -9.8
CART_MASS = 1.0
MU_C = 0.0005
MU_P = 0.000002
DT = 0.01


def _derivative(
    s: NDArray[np.float64],
    force: NDArray[np.float64],
    m: NDArray[np.float64],
    half: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Return the appendix's equations, written again over the batch.

    Returns
    -------
    numpy.ndarray
        The time derivative of every state, shaped like ``s``.
    """
    xd = s[:, 1]
    th, thd = s[:, 2::2], s[:, 3::2]
    sin, cos = np.sin(th), np.cos(th)
    ml = m * half
    f_eff = ml * thd**2 * sin + 0.75 * m * cos * (MU_P * thd / ml + G * sin)
    m_eff = m * (1 - 0.75 * cos**2)
    xdd = (force - MU_C * np.sign(xd) + f_eff.sum(1)) / (
        CART_MASS + m_eff.sum(1)
    )
    thdd = -0.75 / half * (xdd[:, None] * cos + G * sin + MU_P * thd / ml)
    out = np.empty_like(s)
    out[:, 0], out[:, 1] = xd, xdd
    out[:, 2::2], out[:, 3::2] = thd, thdd
    return out


def _rk4(
    s: NDArray[np.float64],
    force: NDArray[np.float64],
    m: NDArray[np.float64],
    half: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Take one classical Runge-Kutta step of ``DT``.

    Returns
    -------
    numpy.ndarray
        The states after the step.
    """
    k1 = _derivative(s, force, m, half)
    k2 = _derivative(s + DT / 2 * k1, force, m, half)
    k3 = _derivative(s + DT / 2 * k2, force, m, half)
    k4 = _derivative(s + DT * k3, force, m, half)
    return s + DT / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def test_tests_run_the_code_uncompiled() -> None:
    assert os.environ["NUMBA_DISABLE_JIT"] == "1"


@pytest.mark.parametrize("cart", [Cart.single(), Cart.double()])
def test_one_network_step_is_two_rk4_steps(cart: Cart) -> None:
    m, half = np.array(cart.masses), np.array(cart.half_lengths)
    rng = np.random.default_rng(1)
    state = rng.uniform(-0.3, 0.3, size=(6, 2 + 2 * len(m)))
    force = rng.uniform(-10, 10, size=6)
    expected = _rk4(_rk4(state, force, m, half), force, m, half)
    advance(state, force, cart)
    np.testing.assert_allclose(state, expected, rtol=1e-12, atol=1e-12)


def test_published_constants() -> None:
    single, double = Cart.single(), Cart.double()
    assert (single.masses, single.half_lengths) == ((0.1,), (0.5,))
    assert double.masses == (0.1, 0.01)
    assert double.half_lengths == (0.5, 0.05)


def test_a_pole_left_alone_falls() -> None:
    cart = Cart.single()
    start = 0.01
    state = np.array([[0.0, 0.0, start, 0.0]])
    for _ in range(50):
        advance(state, np.zeros(1), cart)
    assert state[0, 2] > start


def test_large_and_small_batches_step_alike() -> None:
    cart = Cart.double()
    rng = np.random.default_rng(2)
    many = rng.uniform(-0.3, 0.3, size=(PARALLEL_FROM, 6))
    force = rng.uniform(-10, 10, size=PARALLEL_FROM)
    one = many[:1].copy()
    advance(many, force, cart)
    advance(one, force[:1], cart)
    np.testing.assert_array_equal(many[:1], one)
