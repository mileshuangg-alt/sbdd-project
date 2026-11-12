#!/usr/bin/env python3
"""Synthetic-only DataSAIL v1.2.4 S1 scaling probe.

This probe intentionally does not import DataSAIL or read project data. It
reproduces the pinned DataSAIL ``solve_c1()`` CVXPY formulation against
deterministic synthetic families, then measures construction,
canonicalization for SCIP, and SCIP solve as separate phases.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.metadata
import json
import math
import multiprocessing as mp
import os
import platform
import signal
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np


DATASAIL_VERSION = "1.2.4"
DATASAIL_COMMIT = "a212606c4ad9d847ff94365545392958c2aab7f5"
FORMULATION_PROVENANCE = {
    "source": "DataSAIL solve_c1",
    "version": DATASAIL_VERSION,
    "commit": DATASAIL_COMMIT,
    "datasail_import_required": False,
}
CVXPY_VERSION = "1.5.3"
PYTHON_VERSION = "3.12"
SCIP_VERSION_POLICY = "<=9.1"
PYSCIPOPT_VERSION = "5.1.1"

DEFAULT_LADDER = (100, 500, 1000, 2000, 3000, 5446)
AUTHORIZED_CHARACTERIZATION_SCENARIOS = (100,)
STAGE_B_SCENARIO = 4357
STAGE_A_SPLIT_NAMES = ("dev", "test")
STAGE_A_SPLITS = (0.8, 0.2)
STAGE_B_SPLIT_NAMES = ("fold0", "fold1", "fold2", "fold3", "fold4")
STAGE_B_SPLITS = (0.2, 0.2, 0.2, 0.2, 0.2)
CLASSES = ("pKa", "clearance")
DELTA = 0.05
EPSILON = 0.05

SOLVER_OPTIMIZATION_LIMIT_SECONDS = 1800
SOLVE_EXTERNAL_PROCESS_CAP_SECONDS = SOLVER_OPTIMIZATION_LIMIT_SECONDS + 60
PHASE_CAPS_SECONDS = {"construction": 600.0, "canonicalization": 600.0, "solve": float(SOLVE_EXTERNAL_PROCESS_CAP_SECONDS)}
RSS_CAP_BYTES = int(204.8 * 1024**3)
SCIP_PARAMS = {
    "limits/time": SOLVER_OPTIMIZATION_LIMIT_SECONDS,
    "display/verblevel": 2,
    "lp/threads": 14,
    "parallel/maxnthreads": 14,
}


@dataclass(frozen=True)
class SyntheticFixture:
    clusters: list[str]
    weights: list[float]
    s_matrix: np.ndarray
    similarities: np.ndarray
    endpoint_counts: dict[str, list[int]]
    classes: tuple[str, ...]


@dataclass(frozen=True)
class SplitPlan:
    stage: str
    names: tuple[str, ...]
    ratios: tuple[float, ...]


@dataclass
class PhaseMonitor:
    name: str
    cap_seconds: float
    rss_cap_bytes: int = RSS_CAP_BYTES
    sample_seconds: float = 0.25
    start_time: float = 0.0
    elapsed_seconds: float = 0.0
    peak_rss_bytes: int = 0
    samples: list[dict[str, float | int]] | None = None
    stop_reason: str | None = None
    _stop_event: threading.Event | None = None
    _thread: threading.Thread | None = None

    def __enter__(self) -> "PhaseMonitor":
        self.samples = []
        self._stop_event = threading.Event()
        self.start_time = time.monotonic()
        self._sample()
        self._thread = threading.Thread(target=self._run, name=f"rss-{self.name}", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._sample()
        self.elapsed_seconds = time.monotonic() - self.start_time
        if self.peak_rss_bytes > self.rss_cap_bytes and self.stop_reason is None:
            self.stop_reason = "rss_cap_exceeded"
        if self.elapsed_seconds > self.cap_seconds and self.stop_reason is None:
            self.stop_reason = "phase_cap_exceeded"

    def _run(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.wait(self.sample_seconds):
            self._sample()

    def _sample(self) -> None:
        rss = current_rss_bytes()
        self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
        if self.samples is not None:
            self.samples.append({"t_seconds": time.monotonic() - self.start_time, "rss_bytes": rss})

    def as_record(self) -> dict[str, Any]:
        record = {
            "phase": self.name,
            "cap_seconds": self.cap_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "peak_rss_bytes": self.peak_rss_bytes,
            "rss_cap_bytes": self.rss_cap_bytes,
            "stop_reason": self.stop_reason,
            "samples": self.samples or [],
        }
        if self.name == "solve":
            record["solver_optimization_limit_seconds"] = SOLVER_OPTIMIZATION_LIMIT_SECONDS
            record["external_process_cap_seconds"] = SOLVE_EXTERNAL_PROCESS_CAP_SECONDS
        return record


class PhaseTimeoutError(TimeoutError):
    pass


@contextlib.contextmanager
def phase_alarm(seconds: float) -> Iterator[None]:
    def _raise_timeout(signum: int, frame: Any) -> None:
        raise PhaseTimeoutError(f"phase exceeded {seconds} seconds")

    if not hasattr(signal, "SIGALRM") or threading.current_thread() is not threading.main_thread():
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, _raise_timeout)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def current_rss_bytes() -> int:
    """Return current RSS, not lifetime high-water RSS."""
    return process_current_rss_bytes(os.getpid())


def process_current_rss_bytes(pid: int) -> int:
    status_path = Path(f"/proc/{pid}/status")
    if status_path.exists():
        for line in status_path.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    statm_path = Path(f"/proc/{pid}/statm")
    if statm_path.exists():
        pages = int(statm_path.read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE")
    completed = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], check=True, capture_output=True, text=True)
    return int(completed.stdout.strip()) * 1024


def deterministic_fixture(n_families: int) -> SyntheticFixture:
    if n_families <= 0:
        raise ValueError("n_families must be positive")
    clusters = [f"synthetic_family_{i:05d}" for i in range(n_families)]
    weights = [float(1 + ((i * 37 + 11) % 9)) for i in range(n_families)]

    pka = [1 + ((i * 17 + 3) % 5) for i in range(n_families)]
    clearance = [1 + ((i * 19 + 7) % 4) for i in range(n_families)]
    s_matrix = np.asarray(list(zip(pka, clearance)), dtype=float)

    idx = np.arange(n_families, dtype=np.int64)
    diff = np.abs(idx[:, None] - idx[None, :])
    mod = ((idx[:, None] * 31 + idx[None, :] * 17 + 13) % 100).astype(float) / 1000.0
    similarities = 1.0 / (1.0 + diff.astype(float)) + mod
    similarities = (similarities + similarities.T) / 2.0
    np.fill_diagonal(similarities, 1.0)

    return SyntheticFixture(
        clusters=clusters,
        weights=weights,
        s_matrix=s_matrix,
        similarities=similarities,
        endpoint_counts={"pKa": pka, "clearance": clearance},
        classes=CLASSES,
    )


def compute_limits(epsilon: float, total: int | float, splits: list[float] | tuple[float, ...]) -> list[int]:
    """Pinned DataSAIL v1.2.4 lower-bound semantics."""
    return [int(split * (1 - epsilon) * total) for split in splits]


def stratification_lower_bounds(s_matrix: np.ndarray, splits: list[float] | tuple[float, ...], delta: float) -> np.ndarray:
    """Pinned DataSAIL v1.2.4 numeric stratification lower-bound semantics."""
    c = np.sum(s_matrix, axis=0)
    return np.array([[c[e] * split * (1 - delta) for e in range(s_matrix.shape[1])] for split in splits])


def assert_numeric_counts_preserved(fixture: SyntheticFixture, expected_classes: tuple[str, ...] = CLASSES) -> None:
    if fixture.classes != expected_classes:
        raise AssertionError(f"class ordering changed: {fixture.classes!r} != {expected_classes!r}")
    expected = np.asarray([fixture.endpoint_counts[name] for name in expected_classes], dtype=float).T
    if not np.array_equal(fixture.s_matrix, expected):
        raise AssertionError("numeric endpoint counts changed before constraint construction")


def build_pinned_solve_c1_problem(
    clusters: list[str],
    weights: list[float],
    s_matrix: np.ndarray | None,
    similarities: np.ndarray | None,
    distances: np.ndarray | None,
    delta: float,
    epsilon: float,
    splits: list[float] | tuple[float, ...],
    expected_endpoint_counts: dict[str, list[int]] | None = None,
    expected_classes: tuple[str, ...] = CLASSES,
) -> tuple[Any, Any, dict[str, Any]]:
    """Build the pinned uncoarsened DataSAIL v1.2.4 ``solve_c1()`` problem.

    The CVXPY expression below mirrors commit
    a212606c4ad9d847ff94365545392958c2aab7f5 and intentionally keeps the
    original pairwise objective form instead of algebraically simplifying it.
    """
    import cvxpy

    if s_matrix is not None and expected_endpoint_counts is not None:
        assert_numeric_counts_preserved(
            SyntheticFixture(
                clusters,
                weights,
                np.asarray(s_matrix),
                np.zeros((len(clusters), len(clusters))),
                expected_endpoint_counts,
                expected_classes,
            )
        )

    min_lim = compute_limits(epsilon, sum(weights), splits)

    x = cvxpy.Variable((len(splits), len(clusters)), boolean=True)  # 19

    constraints = [cvxpy.sum(x, axis=0) == np.ones((len(clusters)))]  # 16

    for s, lim in enumerate(min_lim):
        constraints.append(lim <= cvxpy.sum(cvxpy.multiply(x[s], weights)))  # 17

    if s_matrix is not None:
        constraints.append((x @ s_matrix) >= stratification_lower_bounds(s_matrix, splits, delta))

    intra_weights = similarities if similarities is not None else np.max(distances) - distances

    # Because of different weights tmp != len(clusters) * (len(clusters) - 1) / 2
    tmp = [[weights[e1] * weights[e2] * intra_weights[e1, e2] * cvxpy.max(
        cvxpy.vstack([x[s, e1] - x[s, e2] for s in range(len(splits))])
    ) for e2 in range(e1 + 1, len(clusters))] for e1 in range(len(clusters))]  # 15

    loss = cvxpy.sum([t for tmp_list in tmp for t in tmp_list])
    problem = cvxpy.Problem(cvxpy.Minimize(loss), constraints)
    dimensions = formulation_dimensions(problem, len(clusters), len(splits), s_matrix)
    dimensions["pair_terms"] = pair_term_count(len(clusters))
    return problem, x, dimensions


def pair_term_count(n_families: int) -> int:
    return n_families * (n_families - 1) // 2


def formulation_dimensions(problem: Any, n_families: int, n_splits: int, s_matrix: np.ndarray | None) -> dict[str, int]:
    variables = sum(math.prod(v.shape) for v in problem.variables())
    constraints = sum(math.prod(c.shape) for c in problem.constraints)
    return {
        "families": n_families,
        "splits": n_splits,
        "classes": 0 if s_matrix is None else int(s_matrix.shape[1]),
        "boolean_assignment_variables": n_families * n_splits,
        "cvxpy_variables": int(variables),
        "cvxpy_constraint_entries": int(constraints),
    }


def small_objective_reference(weights: list[float], similarities: np.ndarray, assignment: list[int], n_splits: int) -> float:
    total = 0.0
    for e1 in range(len(weights)):
        for e2 in range(e1 + 1, len(weights)):
            stacked = [int(assignment[e1] == s) - int(assignment[e2] == s) for s in range(n_splits)]
            total += weights[e1] * weights[e2] * float(similarities[e1, e2]) * max(stacked)
    return total


def split_plan_for_scenario(n_families: int) -> SplitPlan:
    if n_families == STAGE_B_SCENARIO:
        return SplitPlan("B5", STAGE_B_SPLIT_NAMES, STAGE_B_SPLITS)
    return SplitPlan("A", STAGE_A_SPLIT_NAMES, STAGE_A_SPLITS)


def default_scenarios(include_stage_b: bool = False) -> list[int]:
    if include_stage_b:
        raise ValueError("Stage-B is not authorized for this P0 characterization")
    scenarios = list(AUTHORIZED_CHARACTERIZATION_SCENARIOS)
    return scenarios


def validate_authorized_scenarios(scenarios: list[int]) -> None:
    unauthorized = [scenario for scenario in scenarios if scenario not in AUTHORIZED_CHARACTERIZATION_SCENARIOS]
    if unauthorized:
        raise ValueError(f"only P0 N=100 characterization is authorized; refused scenarios: {unauthorized}")


def ensure_empty_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def dependency_metadata() -> dict[str, Any]:
    records: dict[str, Any] = {
        "python": platform.python_version(),
        "python_major_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_target": PYTHON_VERSION,
        "datasail_target_version": DATASAIL_VERSION,
        "datasail_target_commit": DATASAIL_COMMIT,
        "formulation_provenance": FORMULATION_PROVENANCE,
        "cvxpy_target_version": CVXPY_VERSION,
        "pyscipopt_target_version": PYSCIPOPT_VERSION,
        "scip_version_policy": SCIP_VERSION_POLICY,
        "scip_actual_version": observed_scip_version(),
    }
    for package in ("cvxpy", "pyscipopt", "numpy"):
        try:
            records[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            records[package] = None
    return records


def observed_scip_version() -> str | None:
    try:
        import pyscipopt
    except Exception:
        return None
    for attr in ("scip_version", "getTechVersion", "getVersion"):
        candidate = getattr(pyscipopt, attr, None)
        if callable(candidate):
            try:
                return str(candidate())
            except Exception:
                pass
        elif candidate is not None:
            return str(candidate)
    model_type = getattr(pyscipopt, "Model", None)
    if model_type is None:
        return None
    try:
        model = model_type()
    except Exception:
        return None
    for attr in ("getTechVersion", "getVersion", "version"):
        candidate = getattr(model, attr, None)
        if callable(candidate):
            try:
                return str(candidate())
            except Exception:
                pass
        elif candidate is not None:
            return str(candidate)
    return None


def version_tuple(version: str) -> tuple[int, ...]:
    parts = []
    for token in version.replace("-", ".").split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        if digits:
            parts.append(int(digits))
        elif parts:
            break
    return tuple(parts)


def validate_runtime_dependencies() -> None:
    import cvxpy

    validate_formulation_provenance()
    if f"{sys.version_info.major}.{sys.version_info.minor}" != PYTHON_VERSION:
        raise RuntimeError(f"Python {PYTHON_VERSION} required, found {platform.python_version()}")
    if cvxpy.__version__ != CVXPY_VERSION:
        raise RuntimeError(f"CVXPY {CVXPY_VERSION} required, found {cvxpy.__version__}")
    if "SCIP" not in cvxpy.installed_solvers():
        raise RuntimeError("CVXPY SCIP solver is unavailable; install pinned PySCIPOpt/SCIP in the container")
    try:
        pyscipopt_version = importlib.metadata.version("pyscipopt")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError("PySCIPOpt is unavailable") from exc
    if pyscipopt_version != PYSCIPOPT_VERSION:
        raise RuntimeError(f"PySCIPOpt {PYSCIPOPT_VERSION} required, found {pyscipopt_version}")
    scip_version = observed_scip_version()
    if scip_version is None:
        raise RuntimeError("SCIP actual version is unavailable from PySCIPOpt")
    if version_tuple(scip_version)[:2] > (9, 1):
        raise RuntimeError(f"SCIP {SCIP_VERSION_POLICY} required, found {scip_version}")


def validate_formulation_provenance() -> None:
    if FORMULATION_PROVENANCE["version"] != "1.2.4":
        raise RuntimeError(f"unexpected DataSAIL formulation version: {FORMULATION_PROVENANCE['version']}")
    if FORMULATION_PROVENANCE["commit"] != "a212606c4ad9d847ff94365545392958c2aab7f5":
        raise RuntimeError(f"unexpected DataSAIL formulation commit: {FORMULATION_PROVENANCE['commit']}")
    if FORMULATION_PROVENANCE["datasail_import_required"] is not False:
        raise RuntimeError("probe must remain independent of importing DataSAIL")


def run_scenario(n_families: int, output_dir: Path) -> dict[str, Any]:
    scenario_dir = output_dir / f"scenario_{n_families}"
    ensure_empty_output_dir(scenario_dir)
    process = mp.Process(target=_scenario_worker, args=(n_families, output_dir), name=f"datasail-scenario-{n_families}")
    process.start()
    watchdog = monitor_scenario_process(process, scenario_dir)
    watchdog["exitcode"] = process.exitcode
    result_path = scenario_dir / "result.json"
    if watchdog["stop_reason"]:
        process.join(timeout=10.0)
        if process.is_alive():
            kill_process_group(process.pid)
            process.join(timeout=10.0)
    else:
        process.join()
    watchdog["exitcode"] = process.exitcode
    if result_path.exists() and watchdog["stop_reason"] != "rss_cap_exceeded":
        result = json.loads(result_path.read_text())
    else:
        result = {
            "scenario": n_families,
            "stage": split_plan_for_scenario(n_families).stage,
            "stage_b_explicit": n_families == STAGE_B_SCENARIO,
            "solver_optimization_limit_seconds": SOLVER_OPTIMIZATION_LIMIT_SECONDS,
            "solve_external_process_cap_seconds": SOLVE_EXTERNAL_PROCESS_CAP_SECONDS,
            "status": "failed",
            "stop_reason": watchdog["stop_reason"] or f"scenario_process_exit_{process.exitcode}",
            "error": "scenario process terminated by external watchdog" if watchdog["stop_reason"] else "scenario process exited without result artifact",
            "phases": [],
        }
        write_json(result_path, result)
    result["external_watchdog"] = watchdog
    write_json(result_path, result)
    return result


def _scenario_worker(n_families: int, output_dir: Path) -> None:
    with contextlib.suppress(OSError):
        os.setsid()
    result = run_scenario_in_process(n_families, output_dir)
    if result.get("stop_reason") == "rss_cap_exceeded":
        raise SystemExit(1)


def monitor_scenario_process(process: mp.Process, scenario_dir: Path) -> dict[str, Any]:
    samples: list[dict[str, float | int]] = []
    start = time.monotonic()
    peak = 0
    stop_reason = None
    stop_detail: dict[str, Any] = {}
    pid = process.pid
    if pid is None:
        return {"samples": samples, "peak_rss_bytes": peak, "rss_cap_bytes": RSS_CAP_BYTES, "stop_reason": "missing_pid"}
    while process.is_alive():
        try:
            rss = process_current_rss_bytes(pid)
        except Exception:
            break
        peak = max(peak, rss)
        samples.append({"t_seconds": time.monotonic() - start, "rss_bytes": rss})
        if rss > RSS_CAP_BYTES:
            stop_reason = "rss_cap_exceeded"
            write_json(
                scenario_dir / "watchdog_stop.json",
                {"pid": pid, "rss_bytes": rss, "rss_cap_bytes": RSS_CAP_BYTES, "stop_reason": stop_reason},
            )
            terminate_process_group(pid)
            break
        phase_state = read_phase_state(scenario_dir)
        if phase_state.get("phase") == "solve":
            elapsed = time.time() - float(phase_state["started_at_epoch"])
            external_cap = float(phase_state.get("external_process_cap_seconds", SOLVE_EXTERNAL_PROCESS_CAP_SECONDS))
            if elapsed > external_cap:
                stop_reason = "solve_external_process_cap_exceeded"
                stop_detail = {
                    "phase": "solve",
                    "elapsed_seconds": elapsed,
                    "solver_optimization_limit_seconds": SOLVER_OPTIMIZATION_LIMIT_SECONDS,
                    "external_process_cap_seconds": external_cap,
                }
                write_json(
                    scenario_dir / "watchdog_stop.json",
                    {"pid": pid, "rss_bytes": rss, "rss_cap_bytes": RSS_CAP_BYTES, "stop_reason": stop_reason, **stop_detail},
                )
                terminate_process_group(pid)
                break
        time.sleep(0.25)
    return {
        "pid": pid,
        "samples": samples,
        "peak_rss_bytes": peak,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "stop_reason": stop_reason,
        **stop_detail,
    }


def phase_state_path(scenario_dir: Path) -> Path:
    return scenario_dir / "phase_state.json"


def write_phase_state(scenario_dir: Path, phase: str) -> None:
    payload: dict[str, Any] = {"phase": phase, "started_at_epoch": time.time()}
    if phase == "solve":
        payload["solver_optimization_limit_seconds"] = SOLVER_OPTIMIZATION_LIMIT_SECONDS
        payload["external_process_cap_seconds"] = SOLVE_EXTERNAL_PROCESS_CAP_SECONDS
    write_json(phase_state_path(scenario_dir), payload)


def clear_phase_state(scenario_dir: Path) -> None:
    with contextlib.suppress(FileNotFoundError):
        phase_state_path(scenario_dir).unlink()


def read_phase_state(scenario_dir: Path) -> dict[str, Any]:
    path = phase_state_path(scenario_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def terminate_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        with contextlib.suppress(OSError):
            os.kill(pid, signal.SIGTERM)


def kill_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        with contextlib.suppress(OSError):
            os.kill(pid, signal.SIGKILL)


def collect_solver_statistics(problem: Any) -> dict[str, Any]:
    stats: dict[str, Any] = {"cvxpy_status": getattr(problem, "status", None)}
    solver_stats = getattr(problem, "solver_stats", None)
    if solver_stats is None:
        return {key: value for key, value in stats.items() if value is not None}

    exposed_fields = {
        "solve_time": "solving_time_seconds",
        "setup_time": "setup_time_seconds",
    }
    for source_name, target_name in exposed_fields.items():
        value = getattr(solver_stats, source_name, None)
        if value is not None:
            stats[target_name] = value

    extra_stats = getattr(solver_stats, "extra_stats", None)
    if extra_stats is not None:
        for target_name, source_names in {
            "status": ("status", "scip_status", "solver_status"),
            "solving_time_seconds": ("solving_time", "solving_time_seconds", "solve_time", "time"),
            "primal_bound": ("primal_bound", "primalbound", "primal"),
            "dual_bound": ("dual_bound", "dualbound", "dual"),
            "gap": ("gap", "mip_gap", "relative_gap"),
            "solution_count": ("solution_count", "n_solutions", "nsols", "sols"),
            "node_count": ("node_count", "nodes", "nnodes"),
        }.items():
            value = first_exposed_value(extra_stats, source_names)
            if value is not None:
                stats[target_name] = value

    return {key: normalize_stat_value(value) for key, value in stats.items() if value is not None}


def first_exposed_value(source: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        if isinstance(source, dict) and name in source:
            return source[name]
        if hasattr(source, name):
            value = getattr(source, name)
            return value() if callable(value) else value
    return None


def normalize_stat_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


@contextlib.contextmanager
def instrument_native_scip_statistics(stats_sink: dict[str, Any]) -> Iterator[None]:
    """Capture PySCIPOpt model statistics at CVXPY's SCIP ``_solve`` seam.

    CVXPY 1.5.3 keeps the PySCIPOpt ``Model`` local to ``solve_via_data`` and
    discards it after ``_solve`` returns. This wrapper preserves the original
    solve behavior and records native statistics immediately after that return.
    """
    from cvxpy.reductions.solvers.conic_solvers.scip_conif import SCIP

    original_solve = SCIP._solve

    def wrapped_solve(self: Any, model: Any, variables: list[Any], constraints: list[Any], data: dict[str, Any], dims: dict[str, Any]) -> dict[str, Any]:
        try:
            solution = original_solve(self, model, variables, constraints, data, dims)
        except Exception:
            stats_sink.clear()
            stats_sink.update(capture_native_scip_statistics(model))
            raise
        stats_sink.clear()
        stats_sink.update(capture_native_scip_statistics(model))
        return solution

    SCIP._solve = wrapped_solve
    try:
        yield
    finally:
        SCIP._solve = original_solve


def capture_native_scip_statistics(model: Any) -> dict[str, Any]:
    best_solution = safe_model_call(model, "getBestSol")
    has_best_solution = best_solution is not None
    return {
        "status": safe_model_call(model, "getStatus"),
        "solving_time_seconds": safe_model_call(model, "getSolvingTime"),
        "primal_bound": safe_model_call(model, "getPrimalbound"),
        "dual_bound": safe_model_call(model, "getDualbound"),
        "gap": safe_model_call(model, "getGap"),
        "solution_count": safe_model_call(model, "getNSols"),
        "node_count": safe_model_call(model, "getNNodes"),
        "has_best_solution": has_best_solution,
        "objective_value": safe_model_call(model, "getObjVal") if has_best_solution else None,
    }


def safe_model_call(model: Any, method_name: str) -> Any:
    method = getattr(model, method_name, None)
    if method is None:
        return None
    try:
        return normalize_stat_value(method())
    except Exception:
        return None


def run_scenario_in_process(n_families: int, output_dir: Path) -> dict[str, Any]:
    import cvxpy

    split_plan = split_plan_for_scenario(n_families)
    fixture = deterministic_fixture(n_families)
    assert_numeric_counts_preserved(fixture)
    scenario_dir = output_dir / f"scenario_{n_families}"
    phase_records: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "scenario": n_families,
        "stage": split_plan.stage,
        "stage_b_explicit": n_families == STAGE_B_SCENARIO,
        "split_names": list(split_plan.names),
        "splits": list(split_plan.ratios),
        "solver_optimization_limit_seconds": SOLVER_OPTIMIZATION_LIMIT_SECONDS,
        "solve_external_process_cap_seconds": SOLVE_EXTERNAL_PROCESS_CAP_SECONDS,
        "status": "started",
        "stop_reason": None,
        "phases": phase_records,
    }

    problem = None
    x = None
    try:
        with PhaseMonitor("construction", PHASE_CAPS_SECONDS["construction"]) as monitor:
            with phase_alarm(PHASE_CAPS_SECONDS["construction"]):
                problem, x, dimensions = build_pinned_solve_c1_problem(
                    clusters=fixture.clusters,
                    weights=fixture.weights,
                    s_matrix=fixture.s_matrix,
                    similarities=fixture.similarities,
                    distances=None,
                    delta=DELTA,
                    epsilon=EPSILON,
                    splits=split_plan.ratios,
                    expected_endpoint_counts=fixture.endpoint_counts,
                    expected_classes=fixture.classes,
                )
                result["dimensions"] = dimensions
        phase_records.append(monitor.as_record())
        if monitor.stop_reason:
            raise RuntimeError(monitor.stop_reason)

        with PhaseMonitor("canonicalization", PHASE_CAPS_SECONDS["canonicalization"]) as monitor:
            with phase_alarm(PHASE_CAPS_SECONDS["canonicalization"]):
                assert problem is not None
                data, chain, inverse_data = problem.get_problem_data(cvxpy.SCIP)
                result["canonicalization"] = {
                    "data_keys": sorted(str(k) for k in data.keys()),
                    "reductions": [type(reduction).__name__ for reduction in chain.reductions],
                    "inverse_data_count": len(inverse_data),
                }
        phase_records.append(monitor.as_record())
        if monitor.stop_reason:
            raise RuntimeError(monitor.stop_reason)

        log_file = scenario_dir / "scip.log"
        native_scip_statistics: dict[str, Any] = {}
        with PhaseMonitor("solve", PHASE_CAPS_SECONDS["solve"]) as monitor:
            write_phase_state(scenario_dir, "solve")
            try:
                assert problem is not None
                with log_file.open("w") as log_handle, contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
                    with instrument_native_scip_statistics(native_scip_statistics):
                        problem.solve(
                            solver=cvxpy.SCIP,
                            qcp=True,
                            verbose=True,
                            scip_params=SCIP_PARAMS,
                        )
            finally:
                clear_phase_state(scenario_dir)
        phase_records.append(monitor.as_record())
        if monitor.stop_reason:
            raise RuntimeError(monitor.stop_reason)

        result.update({"status": "completed", "solver_status": problem.status, "objective_value": problem.value})
        result["solver_statistics"] = collect_solver_statistics(problem)
        result["native_scip_statistics"] = native_scip_statistics
        if problem.status in {"user_limit", "infeasible", "infeasible_inaccurate", "unbounded", "unbounded_inaccurate"}:
            result["stop_reason"] = f"solver_status_{problem.status}"
        result["overall_peak_rss_bytes"] = max((phase["peak_rss_bytes"] for phase in phase_records), default=0)
    except PhaseTimeoutError as exc:
        result.update({"status": "failed", "stop_reason": "phase_timeout", "error": str(exc)})
    except Exception as exc:
        result.update({"status": "failed", "stop_reason": result.get("stop_reason") or type(exc).__name__, "error": str(exc)})
        result["traceback"] = traceback.format_exc()

    write_json(scenario_dir / "result.json", result)
    return result


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_hash_manifest(output_dir: Path) -> None:
    rows = []
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(output_dir)}")
    (output_dir / "SHA256SUMS").write_text("\n".join(rows) + ("\n" if rows else ""))


def write_results_csv(output_dir: Path, results: list[dict[str, Any]]) -> None:
    with (output_dir / "results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario",
                "status",
                "stop_reason",
                "solver_status",
                "objective_value",
                "solver_optimization_limit_seconds",
                "solve_external_process_cap_seconds",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow({key: result.get(key) for key in writer.fieldnames})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--scenarios", nargs="+", type=int, default=list(AUTHORIZED_CHARACTERIZATION_SCENARIOS))
    parser.add_argument("--include-stage-b", action="store_true", help="append explicit 4,357-family Stage-B scenario")
    parser.add_argument("--allow-unpinned-runtime", action="store_true", help="record but do not fail on local dependency drift")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_empty_output_dir(args.output_dir)
    scenarios = list(args.scenarios)
    if args.include_stage_b and STAGE_B_SCENARIO not in scenarios:
        scenarios.append(STAGE_B_SCENARIO)
    validate_authorized_scenarios(scenarios)
    metadata = {
        "probe": "datasail_v1_2_4_s1_scaling_session016",
        "synthetic_only": True,
        "default_ladder": list(DEFAULT_LADDER),
        "authorized_characterization_scenarios": list(AUTHORIZED_CHARACTERIZATION_SCENARIOS),
        "stage_b_scenario": STAGE_B_SCENARIO,
        "scenarios": scenarios,
        "stage_a": {"splits": list(STAGE_A_SPLITS), "split_names": list(STAGE_A_SPLIT_NAMES)},
        "stage_b": {"splits": list(STAGE_B_SPLITS), "split_names": list(STAGE_B_SPLIT_NAMES)},
        "classes": list(CLASSES),
        "delta": DELTA,
        "epsilon": EPSILON,
        "phase_caps_seconds": PHASE_CAPS_SECONDS,
        "solver_optimization_limit_seconds": SOLVER_OPTIMIZATION_LIMIT_SECONDS,
        "solve_external_process_cap_seconds": SOLVE_EXTERNAL_PROCESS_CAP_SECONDS,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "scip_params": SCIP_PARAMS,
        "dependencies": dependency_metadata(),
        "cwd": os.getcwd(),
    }
    write_json(args.output_dir / "metadata.json", metadata)
    if not args.allow_unpinned_runtime:
        validate_runtime_dependencies()

    results = []
    exit_code = 0
    for scenario in scenarios:
        result = run_scenario(scenario, args.output_dir)
        results.append(result)
        if result.get("status") != "completed" or result.get("stop_reason"):
            exit_code = 1
            break
    write_results_csv(args.output_dir, results)
    write_json(args.output_dir / "results.json", results)
    write_hash_manifest(args.output_dir)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
