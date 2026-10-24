"""Tasks that score networks instead of points.

A network maps an input vector to an output vector and may keep state
between calls. A task runs a batch of them in lockstep (see ``Policy``)
and returns one score and one solved flag per network.
"""

from .poles import DoublePole, SinglePole
from .policy import Policy, single
from .reference import LinearController
from .task import Scores, Task
from .tracked import TrackedTask
from .xor import Xor

__all__ = [
    "DoublePole",
    "LinearController",
    "Policy",
    "Scores",
    "SinglePole",
    "Task",
    "TrackedTask",
    "Xor",
    "single",
]
