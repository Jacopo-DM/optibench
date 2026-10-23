"""Shared pytest setup: the memory watchdog and the Hypothesis profile."""

import os

import memory_guard
from hypothesis import settings

memory_guard.start()

# Coverage cannot see numba's compiled code, so tests run it as Python.
os.environ["NUMBA_DISABLE_JIT"] = "1"

settings.register_profile("default", deadline=None)
settings.register_profile("ci", deadline=None, derandomize=True)
settings.load_profile("ci" if os.environ.get("CI") else "default")
