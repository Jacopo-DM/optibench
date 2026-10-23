"""What a task scores: a batch of networks, and a wrapper for one."""

from collections.abc import Callable
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class Policy(Protocol):
    """A batch of ``n`` networks that a task runs in lockstep.

    A ``Protocol``, the standard's exception: any object with these two
    methods is a policy, a Rust batch included.
    """

    def reset(self, n: int) -> None:
        """Clear every network's recurrent state before a trial."""

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        """Map inputs shaped ``(n, n_in)`` to outputs ``(n, n_out)``."""
        ...


class Single:
    """One network, a function of one input vector, as a batch of one.

    Behaviour first and holding no record, the standard's exception.

    Parameters
    ----------
    network
        Maps an input vector ``(n_in,)`` to an output vector ``(n_out,)``.
    on_reset
        Called before every trial; clears the network's state.
    """

    def __init__(
        self,
        network: Callable[[NDArray[np.float64]], NDArray[np.float64]],
        on_reset: Callable[[], object] | None,
    ) -> None:
        self._network = network
        self._on_reset = on_reset

    def reset(self, n: int) -> None:
        """Clear the network's state.

        Raises
        ------
        ValueError
            If the task asks for more than one network.
        """
        if n != 1:
            msg = f"single() wraps one network, the task asked for {n}"
            raise ValueError(msg)
        if self._on_reset is not None:
            self._on_reset()

    def __call__(self, inputs: NDArray[np.float64]) -> NDArray[np.float64]:
        """Run the network on the batch's one row.

        Returns
        -------
        numpy.ndarray
            Its output as a batch of one, shaped ``(1, n_out)``.
        """
        return np.asarray(self._network(inputs[0]), dtype=np.float64)[None]


def single(
    network: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    reset: Callable[[], object] | None = None,
) -> Single:
    """Wrap one network as a policy, so ``task.evaluate`` can score it.

    Example: ``Xor().evaluate(single(net))``.

    Returns
    -------
    Single
        A policy of one network.
    """
    return Single(network, reset)
