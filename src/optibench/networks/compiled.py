"""The one import of numba: compiling a function, typed for the checkers.

Tests set ``NUMBA_DISABLE_JIT=1`` (``tests/conftest.py``), so the same code
runs as plain Python there and coverage sees it.
"""

from collections.abc import Callable

import numba


def compiled[**P, R](function: Callable[P, R]) -> Callable[P, R]:
    """Compile ``function`` with numba in nopython mode.

    Returns
    -------
    Callable
        The compiled function, with the same signature.
    """
    result: Callable[P, R] = numba.njit(cache=True)(function)
    return result


def compiled_parallel[**P, R](function: Callable[P, R]) -> Callable[P, R]:
    """Compile ``function`` like ``compiled``, its ``rows`` on all cores.

    Not cached on disk: numba names a cache entry after the function, so
    a parallel and a serial build of one function share it, and the
    parallel one then loaded the serial code (371 us a step for 1,000
    carts instead of 188, measured 2026-10-24). Compiling costs about a
    second once per process.

    Returns
    -------
    Callable
        The compiled function, with the same signature.
    """
    result: Callable[P, R] = numba.njit(parallel=True)(function)
    return result


# A loop over independent rows, split across cores in ``compiled_parallel``
# code; a plain ``range`` when the JIT is off.
rows: Callable[[int], range] = numba.prange
