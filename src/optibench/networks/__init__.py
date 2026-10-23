"""Tasks that score networks instead of points.

A network maps an input vector to an output vector and may keep state
between calls. A task runs a batch of them in lockstep (see ``Policy``)
and returns one score and one solved flag per network.
"""

from .policy import Policy, single
from .task import Scores, Task
from .xor import Xor

__all__ = ["Policy", "Scores", "Task", "Xor", "single"]
