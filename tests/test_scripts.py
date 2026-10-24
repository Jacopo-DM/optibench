"""The command-line scripts, on small budgets in a temporary folder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from hypothesis import example, given
from hypothesis import strategies as st
from pydantic import ValidationError

import optibench
from optibench import Sphere
from optibench.scripts import baseline, common, pole_timing, timing

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    folder = tmp_path / "__data__"
    monkeypatch.setattr(timing, "DATA", folder)
    monkeypatch.setattr(baseline, "DATA", folder)
    return folder


def test_every_problem_sets_free_dimensions() -> None:
    problems = common.every_problem()
    assert [p.name for p in problems] == optibench.names()
    dimensions = {p.name: p.dimension for p in problems}
    assert dimensions["ackley"] == common.D
    assert dimensions["powell"] == 4 * (common.D // 4)
    assert dimensions["branin"] == optibench.Branin().dimension


def test_time_problem_is_positive() -> None:
    assert timing.time_problem(Sphere(d=3), 1_000, 2) >= 0


def test_timing_writes_a_table(data: Path) -> None:
    assert timing.main(["--points", "100", "--repeats", "1"]) == 0
    lines = (data / "timing.csv").read_text().splitlines()
    assert lines[0] == "name,d,seconds"
    assert len(lines) == 1 + len(optibench.names())


def test_timing_fails_when_over_budget(
    data: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(timing, "BUDGET", -1.0)
    assert timing.main(["--points", "10", "--repeats", "1"]) == 1
    assert (data / "timing.csv").exists()


def test_timing_excuses_the_stated_exceptions(
    data: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(timing, "BUDGET", -1.0)
    monkeypatch.setattr(timing, "EXCEPTIONS", frozenset(optibench.names()))
    assert timing.main(["--points", "10", "--repeats", "1"]) == 0
    assert (data / "timing.csv").exists()


def test_baseline_writes_one_curve_per_seed(data: Path) -> None:
    budget = 50
    baseline.main(["--budget", str(budget), "--seeds", "2"])
    curves = sorted((data / "baseline").glob("*.csv"))
    assert len(curves) == 2 * len(optibench.names())
    curve = np.loadtxt(
        data / "baseline" / "sphere_seed1.csv",
        delimiter=",",
        skiprows=1,
        ndmin=2,
    )
    assert curve[-1, 0] == budget


@given(st.text(), st.text())
@example("100", "2")
@example("0.0", "1")
def test_timing_arguments_parse_or_raise_validation_error(
    points: str,
    repeats: str,
) -> None:
    """Any text parses to arguments or raises ValidationError."""
    try:
        args = timing.parse_arguments(
            [f"--points={points}", f"--repeats={repeats}"],
        )
    except ValidationError:
        return
    assert (args.points, args.repeats) == (int(points), int(repeats))


@given(st.text(), st.text())
@example("50", "2")
@example("5.0", "1")
def test_baseline_arguments_parse_or_raise_validation_error(
    budget: str,
    seeds: str,
) -> None:
    """Any text parses to arguments or raises ValidationError."""
    try:
        args = baseline.parse_arguments(
            [f"--budget={budget}", f"--seeds={seeds}"],
        )
    except ValidationError:
        return
    assert (args.budget, args.seeds) == (int(budget), int(seeds))


def test_arguments_default_without_flags() -> None:
    assert timing.parse_arguments([]) == timing.Arguments()
    assert baseline.parse_arguments([]) == baseline.Arguments()


def test_pole_timing_reports_and_meets_a_budget(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert pole_timing.main(["--networks", "3", "--steps", "20"]) == 0
    out = capsys.readouterr().out
    assert "every cart 20 steps" in out
    assert "within the 35 s budget" in out


def test_pole_timing_fails_over_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pole_timing, "BUDGET", -1.0)
    argv = ["--networks", "2", "--steps", "5", "--repeats", "1"]
    assert pole_timing.main(argv) == 1


@given(st.text(), st.text(), st.text())
@example("1000", "100000", "5")
@example("2.0", "1", "1")
def test_pole_timing_arguments_parse_or_raise_validation_error(
    networks: str,
    steps: str,
    repeats: str,
) -> None:
    """Any text parses to arguments or raises ValidationError."""
    try:
        args = pole_timing.parse_arguments(
            [
                f"--networks={networks}",
                f"--steps={steps}",
                f"--repeats={repeats}",
            ],
        )
    except ValidationError:
        return
    assert (args.networks, args.steps, args.repeats) == (
        int(networks),
        int(steps),
        int(repeats),
    )
