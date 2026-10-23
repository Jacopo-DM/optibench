"""Counting evaluations while a neuroevolution method runs."""

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, PrivateAttr

from optibench.model import Model

from .policy import Policy
from .task import Scores, Task


class TrackedTask(Model):
    """Wraps a task to count evaluations and keep the first solution.

    Call ``evaluate`` as on the task. One evaluation is one network in one
    trial. After every call, ``curve`` gains one row ``(evaluations so
    far, best score so far)``; higher scores are better.

    A mutable model, the standard's exception for a record that must
    change: it counts as it goes.

    Parameters
    ----------
    task
        The task to evaluate.
    """

    model_config = ConfigDict(frozen=False)

    task: Task
    evaluations: int = 0
    best_score: float = -np.inf
    solved_at: int | None = None
    _curve: list[tuple[float, float]] = PrivateAttr(
        default_factory=list[tuple[float, float]],
    )

    def __init__(self, task: Task) -> None:
        # BaseModel's own __init__: the one type checkers synthesise for
        # Model has no fields, so it would refuse ``task``.
        BaseModel.__init__(self, task=task)

    def evaluate(
        self,
        policy: Policy,
        n: int = 1,
        seed: int = 0,
        trials: int = 1,
    ) -> Scores:
        """Score ``n`` networks and record them.

        ``solved_at`` is the evaluation count once the first solving
        network's trials are done, counting the networks of a batch in
        order.

        Returns
        -------
        Scores
            The task's scores.
        """
        scores = self.task.evaluate(policy, n, seed, trials)
        if self.solved_at is None and scores.solved.any():
            first = int(np.argmax(scores.solved))
            self.solved_at = self.evaluations + (first + 1) * trials
        self.evaluations += n * trials
        self.best_score = max(self.best_score, float(scores.score.max()))
        self._curve.append((self.evaluations, self.best_score))
        return scores

    @property
    def curve(self) -> NDArray[np.float64]:
        """Rows of (evaluations, best score so far), one per call."""
        return np.array(self._curve, dtype=np.float64).reshape(-1, 2)
