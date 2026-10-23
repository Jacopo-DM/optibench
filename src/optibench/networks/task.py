"""The base class of every network task, and the scores it returns."""

from abc import ABC, abstractmethod
from typing import Annotated

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pydantic import ConfigDict, PlainValidator

from optibench.model import Model

from .policy import Policy


def _floats(values: ArrayLike) -> NDArray[np.float64]:
    array = np.array(values, dtype=np.float64)
    array.flags.writeable = False
    return array


def _flags(values: ArrayLike) -> NDArray[np.bool_]:
    array = np.array(values, dtype=np.bool_)
    array.flags.writeable = False
    return array


class Scores(Model):
    """One score and one solved flag per network, over the trials.

    Parameters
    ----------
    score
        Each network's score, averaged over the trials, shaped ``(n,)``.
    solved
        Whether each network solved the task in every trial.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    score: Annotated[NDArray[np.float64], PlainValidator(_floats)]
    solved: Annotated[NDArray[np.bool_], PlainValidator(_flags)]


class Task(Model, ABC):
    """A task that scores a batch of networks.

    Subclasses are frozen pydantic models whose fields are the task's
    settings; ``_trial`` runs one trial of every network.
    """

    @property
    @abstractmethod
    def n_inputs(self) -> int:
        """Length of the input vector each network receives."""

    @property
    @abstractmethod
    def n_outputs(self) -> int:
        """Length of the output vector each network returns."""

    @abstractmethod
    def _trial(
        self,
        policy: Policy,
        n: int,
        rng: np.random.Generator,
        trial: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
        """Run trial number ``trial`` of every network.

        Returns
        -------
        tuple of numpy.ndarray
            Each network's score, and whether it solved the task.
        """

    def evaluate(
        self,
        policy: Policy,
        n: int = 1,
        seed: int = 0,
        trials: int = 1,
    ) -> Scores:
        """Score ``n`` networks over ``trials`` trials.

        The same seed gives the same start states, so a network's score
        repeats. The policy is reset before every trial.

        Returns
        -------
        Scores
            The mean score and whether every trial was solved.

        Raises
        ------
        ValueError
            If ``n`` or ``trials`` is below 1.
        """
        if n < 1 or trials < 1:
            msg = f"n and trials must be at least 1, got {n} and {trials}"
            raise ValueError(msg)
        rng = np.random.default_rng(seed)
        total = np.zeros(n)
        solved = np.ones(n, dtype=np.bool_)
        for trial in range(trials):
            policy.reset(n)
            score, done = self._trial(policy, n, rng, trial)
            total += score
            solved &= done
        return Scores(score=total / trials, solved=solved)

    def _act(
        self,
        policy: Policy,
        inputs: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Call the policy and check what it returns.

        Returns
        -------
        numpy.ndarray
            The outputs, shaped ``(n, n_outputs)``.

        Raises
        ------
        ValueError
            If the outputs have the wrong shape or hold NaN.
        """
        outputs = np.asarray(policy(inputs), dtype=np.float64)
        expected = (len(inputs), self.n_outputs)
        if outputs.shape != expected:
            got = outputs.shape
            msg = f"the policy must return shape {expected}, got {got}"
            raise ValueError(msg)
        if np.isnan(outputs).any():
            rows = np.flatnonzero(np.isnan(outputs).any(axis=1)).tolist()
            msg = f"the policy returned NaN for networks {rows}"
            raise ValueError(msg)
        return outputs
