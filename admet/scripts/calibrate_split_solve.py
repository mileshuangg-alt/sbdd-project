"""Work-limited calibration solve of the native split model (report only).

Implements D034 section 4 step 3 as amended by D034 Amendment 1 A2. It builds
the qualified native formulation (`equivalence.build_native_gurobi_model`) on
the real `split_input_v1` artifacts, runs one Gurobi solve under caller-given
calibration caps, and reports the incumbent trajectory against Gurobi work
units and wall time. It chooses no budget: Miles sets W_A, W_B and each safety
TimeLimit from the report.

The calibration caps are bounds on this run only. They are not W_A.

Usage (from the repository root, in the Gurobi environment, interactively on
gpu-dev1; never through Slurm):

    GRB_LICENSE_FILE=<gurobi.license_file from the config> \
    python -s -m admet.scripts.calibrate_split_solve \
        --config admet/data/splits/split_optimization_config.json \
        --stage stage_a --work-limit-cap <W> --time-limit-cap <T> \
        --soft-mem-limit-gb <G>

`--soft-mem-limit-gb` is Gurobi's SoftMemLimit in decimal gigabytes (10^9
bytes). It must lie below the RSS cap in the config; the harness cap is a hard
exit checked per sample, whereas SoftMemLimit asks Gurobi to stop cleanly and
may overshoot, so neither guarantees a clean exit.

While the solve runs, every new incumbent is appended to
`<output_root>/<stage>_calibration_inprogress/trajectory.jsonl` (fsynced) and
the Gurobi log is written beside it, so a hard abort leaves a progress record.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from admet.qualification.datasail_scaling import probe
from admet.qualification.native_quadratic import equivalence
from admet.scripts import measure_split_model_construction as measure


SCHEMA_VERSION = "admet_split_calibration.v1"
REPORT_FILENAME = "calibration_report.json"
LOG_FILENAME = "gurobi.log"
LICENSE_ENV_VAR = "GRB_LICENSE_FILE"
TRAJECTORY_FILENAME = "trajectory.jsonl"
BYTES_PER_GB = 10**9  # Gurobi's GB is decimal


def check_license_environment(config: Mapping, environ: Mapping[str, str]) -> str:
    """Halt unless GRB_LICENSE_FILE equals gurobi.license_file in the config.

    Without the variable gurobipy falls back to the size-limited restricted
    licence. The licence file itself is never opened here.
    """

    expected = config.get("gurobi", {}).get("license_file")
    if not expected:
        raise RuntimeError("gurobi.license_file is not set in the config")
    observed = environ.get(LICENSE_ENV_VAR)
    if not observed:
        raise RuntimeError(f"{LICENSE_ENV_VAR} is not set; expected {expected}")
    if observed != expected:
        raise RuntimeError(
            f"{LICENSE_ENV_VAR} is {observed}; the config requires {expected}"
        )
    return observed


def check_caps(work_limit_cap: float, time_limit_cap: float) -> None:
    for name, value in (
        ("work-limit-cap", work_limit_cap),
        ("time-limit-cap", time_limit_cap),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"--{name} must be a positive finite number, got {value}")


def check_soft_mem_limit(soft_mem_limit_gb: float, rss_cap_bytes: int) -> None:
    """SoftMemLimit (decimal GB) must be positive, finite and below the RSS cap."""

    if not math.isfinite(soft_mem_limit_gb) or soft_mem_limit_gb <= 0:
        raise ValueError(
            f"--soft-mem-limit-gb must be a positive finite number, got {soft_mem_limit_gb}"
        )
    if soft_mem_limit_gb * BYTES_PER_GB >= rss_cap_bytes:
        raise ValueError(
            f"--soft-mem-limit-gb {soft_mem_limit_gb} ({soft_mem_limit_gb * BYTES_PER_GB:.0f} "
            f"bytes) must be below the RSS cap of {rss_cap_bytes} bytes"
        )


def total_pair_weight(weights: np.ndarray, values: np.ndarray) -> float:
    """Sum over i<j of w_i w_j S_ij from the upper-triangle array (float64)."""

    count = int(weights.size)
    if values.ndim != 1 or values.size != count * (count - 1) // 2:
        raise ValueError(
            f"similarity array of size {values.size} does not match {count} families"
        )
    weights = weights.astype(np.float64)
    total = 0.0
    for i in range(count - 1):
        start = i * count - i * (i + 1) // 2
        length = count - i - 1
        total += float(weights[i] * np.dot(weights[i + 1 :], values[start : start + length]))
    return total


def l_cross_from_within(total_weight: float, within_objective: float) -> float:
    """L_cross = total pair weight - within-partition objective (D031 section 7)."""

    return total_weight - within_objective


class TrajectorySink:
    """Append-only JSON-lines progress record, fsynced after every line.

    The first line is a header. A failure while writing an event is kept in
    `write_error` and does not stop the solve; a failure writing the header
    raises, before any solve work starts. An existing file is never opened.
    """

    def __init__(self, path: Path, header: dict):
        self.path = path
        self.write_error: str | None = None
        self._handle = open(path, "x", encoding="utf-8")
        self._write({"record": "header", **header})

    def _write(self, record: dict) -> None:
        self._handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def append(self, event: dict) -> None:
        if self.write_error is not None:
            return
        try:
            self._write({"record": "incumbent", **event})
        except OSError as error:
            self.write_error = repr(error)

    def close(self) -> None:
        try:
            self._handle.close()
        except OSError as error:
            if self.write_error is None:
                self.write_error = repr(error)


class TrajectoryRecorder:
    """Gurobi callback that records each new incumbent.

    `codes` maps the callback names used here to Gurobi's integer codes
    (`GRB.Callback.MIPSOL`, `GRB.Callback.RUNTIME`, ...) so tests need no
    Gurobi. If a `sink` is given, each event is also persisted as it happens.
    """

    def __init__(
        self,
        total_weight: float,
        codes: Mapping[str, int],
        sink: TrajectorySink | None = None,
    ):
        self._total = total_weight
        self._codes = codes
        self._sink = sink
        self.events: list[dict] = []

    def __call__(self, model, where: int) -> None:
        if where != self._codes["MIPSOL"]:
            return
        within = model.cbGet(self._codes["MIPSOL_OBJ"])
        bound = model.cbGet(self._codes["MIPSOL_OBJBND"])
        event = {
            "runtime_seconds": model.cbGet(self._codes["RUNTIME"]),
            "work_units": model.cbGet(self._codes["WORK"]),
            "incumbent_within_objective": within,
            "incumbent_l_cross": l_cross_from_within(self._total, within),
            "best_bound_within_objective": bound,
            "best_bound_l_cross": l_cross_from_within(self._total, bound),
            "node_count": model.cbGet(self._codes["MIPSOL_NODCNT"]),
            "solution_count": model.cbGet(self._codes["MIPSOL_SOLCNT"]),
        }
        self.events.append(event)
        if self._sink is not None:
            self._sink.append(event)


def gurobi_codes(grb) -> dict[str, int]:
    return {
        "MIPSOL": grb.Callback.MIPSOL,
        "MIPSOL_OBJ": grb.Callback.MIPSOL_OBJ,
        "MIPSOL_OBJBND": grb.Callback.MIPSOL_OBJBND,
        "MIPSOL_NODCNT": grb.Callback.MIPSOL_NODCNT,
        "MIPSOL_SOLCNT": grb.Callback.MIPSOL_SOLCNT,
        "RUNTIME": grb.Callback.RUNTIME,
        "WORK": grb.Callback.WORK,
    }


def classify_stop(status: int, grb) -> str:
    """Name the stop reason; A2 requires reporting a TimeLimit stop."""

    if status == grb.OPTIMAL:
        return "optimal"
    if status == grb.TIME_LIMIT:
        return "time_limit_cap"
    work_limit = getattr(grb, "WORK_LIMIT", None)
    if work_limit is not None and status == work_limit:
        return "work_limit_cap"
    mem_limit = getattr(grb, "MEM_LIMIT", None)
    if mem_limit is not None and status == mem_limit:
        return "soft_mem_limit"
    return f"other_status_{status}"


def read_final_state(model, total_weight: float, error_types=(Exception,)) -> dict:
    """Incumbent and bound after the solve, whatever state it stopped in.

    With an incumbent: `final` holds incumbent, bound and gap. Without one:
    `final` is empty. The bound is read on its own and reported as unavailable
    (with the reason) if Gurobi cannot supply a finite value.
    """

    best_bound: dict
    bound = None
    try:
        candidate = model.ObjBound
    except error_types as error:
        best_bound = {"available": False, "reason": repr(error)}
    else:
        if math.isfinite(candidate):
            bound = candidate
            best_bound = {
                "available": True,
                "within_objective": bound,
                "l_cross": l_cross_from_within(total_weight, bound),
            }
        else:
            best_bound = {"available": False, "reason": f"non-finite bound {candidate}"}

    final: dict = {}
    if model.SolCount > 0:
        within = model.ObjVal
        final = {
            "incumbent_within_objective": within,
            "incumbent_l_cross": l_cross_from_within(total_weight, within),
        }
        if bound is not None:
            final["best_bound_within_objective"] = bound
            final["best_bound_l_cross"] = l_cross_from_within(total_weight, bound)
        try:
            gap = model.MIPGap
        except error_types:
            gap = None
        if gap is not None and math.isfinite(gap):
            final["mip_gap"] = gap
    return {"final": final, "best_bound": best_bound}


def nondefault_parameters(model) -> str:
    """Text of the .prm file Gurobi writes for non-default parameters."""

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "nondefault.prm"
        model.write(str(path))
        return path.read_text()


def load_stage_problem(config: dict, stage: str, repo_root: Path) -> dict:
    """Load and verify the split input and stage bounds (as the construction
    measurement does; that reviewed script is left unedited)."""

    stage_config = config["stages"].get(stage)
    if stage_config is None:
        raise ValueError(f"Stage {stage!r} is not configured")
    if stage_config["family_scope"] != "all":
        raise ValueError(
            f"Family scope {stage_config['family_scope']!r} is not supported yet"
        )

    endpoints = config["endpoints"]
    measure.check_endpoint_interface(endpoints)

    split_input = config["split_input"]
    input_dir = repo_root / split_input["directory"]
    input_hashes = measure.verify_split_input(input_dir, split_input["expected_sha256"])
    family_ids, weights, endpoint_counts = measure.load_families(
        input_dir / "families.csv", endpoints, split_input["family_count"]
    )
    values = np.load(input_dir / "family_similarity_upper.npy", mmap_mode="r")
    if values.dtype != np.float64 or values.size != split_input["similarity_length"]:
        raise ValueError(f"similarity array is {values.dtype} of size {values.size}")

    partition_names, lower_bounds, upper_bounds = measure.stage_bounds(
        family_ids,
        weights,
        endpoint_counts,
        stage_config["partitions"],
        config["epsilon"],
        config["delta"],
    )
    return {
        "stage_config": stage_config,
        "input_hashes": input_hashes,
        "family_ids": family_ids,
        "weights": weights,
        "endpoint_counts": endpoint_counts,
        "values": values,
        "partition_names": partition_names,
        "lower_bounds": lower_bounds,
        "upper_bounds": upper_bounds,
    }


def executed_code_hashes() -> dict:
    modules = {
        "admet.scripts.calibrate_split_solve": sys.modules[__name__],
        "admet.scripts.measure_split_model_construction": measure,
        "admet.qualification.native_quadratic.equivalence": equivalence,
        "admet.qualification.datasail_scaling.probe": probe,
    }
    return {
        name: {
            "path": str(Path(module.__file__).resolve()),
            "sha256": measure.sha256_file(Path(module.__file__).resolve()),
        }
        for name, module in modules.items()
    }


def write_report(
    output_dir: Path,
    report: dict,
    log_path: Path,
    trajectory_path: Path | None = None,
) -> dict[str, str]:
    """Write report, Gurobi log, optional trajectory file and checksums to a
    temporary sibling, then move the directory into place. Existing output is
    never overwritten."""

    if output_dir.exists():
        raise FileExistsError(f"{output_dir} exists; reports are not overwritten")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.partial-", dir=output_dir.parent)
    )
    try:
        (staging / REPORT_FILENAME).write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        (staging / LOG_FILENAME).write_bytes(log_path.read_bytes())
        names = [REPORT_FILENAME, LOG_FILENAME]
        if trajectory_path is not None:
            (staging / TRAJECTORY_FILENAME).write_bytes(trajectory_path.read_bytes())
            names.append(TRAJECTORY_FILENAME)
        digests = {name: measure.sha256_file(staging / name) for name in names}
        (staging / measure.CHECKSUMS_FILENAME).write_text(
            "".join(f"{digest}  {name}\n" for name, digest in digests.items())
        )
        staging.rename(output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return digests


def run_calibration(
    config_path: Path,
    stage: str,
    repo_root: Path,
    work_limit_cap: float,
    time_limit_cap: float,
    soft_mem_limit_gb: float,
    environ: Mapping[str, str] = os.environ,
) -> dict:
    check_caps(work_limit_cap, time_limit_cap)
    config = json.loads(config_path.read_text())
    license_file = check_license_environment(config, environ)

    calibration = config.get("calibration") or {}
    threads = calibration.get("threads")
    if not isinstance(threads, int) or isinstance(threads, bool) or threads < 1:
        raise RuntimeError("calibration.threads is not set to a positive integer")
    seed = config["gurobi"]["seed"]

    measurement = config["construction_measurement"]
    if not measurement.get("rss_cap_bytes"):
        raise RuntimeError("rss_cap_bytes is not set in the config")
    check_soft_mem_limit(soft_mem_limit_gb, measurement["rss_cap_bytes"])

    output_root = repo_root / calibration["output_root"]
    output_dir = output_root / f"{stage}_calibration"
    abort_path = output_root / f"{stage}_calibration_ABORTED.json"
    inprogress_dir = output_root / f"{stage}_calibration_inprogress"
    for path in (output_dir, abort_path, inprogress_dir):
        if path.exists():
            raise FileExistsError(f"{path} exists; it is not overwritten")

    problem = load_stage_problem(config, stage, repo_root)
    family_ids = problem["family_ids"]
    weights = problem["weights"]
    values = problem["values"]
    weight_array = np.array([weights[fid] for fid in family_ids], dtype=np.float64)
    total_weight = total_pair_weight(weight_array, values)
    nonzero_pairs = int(np.count_nonzero(values))

    import gurobipy as gp
    from gurobipy import GRB

    inprogress_dir.mkdir(parents=True)
    sink = TrajectorySink(
        inprogress_dir / TRAJECTORY_FILENAME,
        {
            "schema_version": SCHEMA_VERSION,
            "stage": stage,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "total_pair_weight": total_weight,
            "Seed": seed,
            "Threads": threads,
            "WorkLimit_cap": work_limit_cap,
            "TimeLimit_cap": time_limit_cap,
            "SoftMemLimit_gb": soft_mem_limit_gb,
            "rss_cap_bytes": measurement["rss_cap_bytes"],
        },
    )
    sampler = measure.RssSampler(
        measurement["rss_cap_bytes"], measurement["sample_interval_seconds"], abort_path
    )
    sampler.start()
    try:
        build_started = time.perf_counter()
        built = equivalence.build_native_gurobi_model(
            family_ids=family_ids,
            partition_names=problem["partition_names"],
            molecular_weights=weights,
            pka_counts=problem["endpoint_counts"]["pka_identities"],
            clearance_counts=problem["endpoint_counts"]["clearance_identities"],
            similarities=measure.UpperTriangleSimilarities(values, family_ids),
            lower_bounds=problem["lower_bounds"],
            upper_bounds=problem["upper_bounds"],
        )
        build_seconds = time.perf_counter() - build_started
        model = built["model"]

        expected = measure.expected_dimensions(
            len(family_ids),
            len(problem["partition_names"]),
            1 + len(config["endpoints"]),
            nonzero_pairs,
        )
        observed = {
            "binary_variables": model.NumBinVars,
            "linear_constraints": model.NumConstrs,
            "quadratic_terms": model.getObjective().size(),
        }
        for name, value in expected.items():
            if observed[name] != value:
                raise AssertionError(f"{name}: observed {observed[name]}, expected {value}")

        # The log lives in the in-progress directory so a hard abort keeps it;
        # it is also copied into the report directory.
        log_path = inprogress_dir / LOG_FILENAME
        model.Params.LogFile = str(log_path)
        model.Params.OutputFlag = 1
        model.Params.Seed = seed
        model.Params.Threads = threads
        model.Params.WorkLimit = work_limit_cap
        model.Params.TimeLimit = time_limit_cap
        model.Params.SoftMemLimit = soft_mem_limit_gb

        recorder = TrajectoryRecorder(total_weight, gurobi_codes(GRB), sink)
        solve_started = time.perf_counter()
        model.optimize(recorder)
        solve_seconds = time.perf_counter() - solve_started
    finally:
        sampler.stop()
        sink.close()

    status = model.Status
    state = read_final_state(model, total_weight, (gp.GurobiError, AttributeError))
    final = state["final"]

    stop_reason = classify_stop(status, GRB)
    report = {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "governing_decisions": config["governing_decisions"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "report_only_note": (
            "Calibration reports; Miles sets W_A and the safety TimeLimit "
            "(D034 Amendment 1 A2). The caps below bound this run only."
        ),
        "config_sha256": measure.sha256_file(config_path),
        "split_input_sha256": problem["input_hashes"],
        "executed_code_sha256": executed_code_hashes(),
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "gurobi": ".".join(str(part) for part in gp.gurobi.version()),
        },
        "host": measure.host_description(),
        "license_file_env": license_file,
        "parameters": {
            "Seed": seed,
            "Threads": threads,
            "WorkLimit_cap": work_limit_cap,
            "TimeLimit_cap": time_limit_cap,
            "SoftMemLimit_gb": soft_mem_limit_gb,
            "nondefault_prm": nondefault_parameters(model),
        },
        "dimensions": observed,
        "expected_dimensions": expected,
        "total_pair_weight": total_weight,
        "construction_seconds": build_seconds,
        "solve_wall_seconds": solve_seconds,
        "gurobi_runtime_seconds": model.Runtime,
        "gurobi_work_units": model.Work,
        "status": status,
        "stop_reason": stop_reason,
        "stopped_on_safety_time_limit": stop_reason == "time_limit_cap",
        "not_reproducible_note": (
            "A run that stops on the TimeLimit before its WorkLimit is reported "
            "as not reproducible (D034 Amendment 1 A2)."
            if stop_reason == "time_limit_cap"
            else None
        ),
        "stopped_on_soft_mem_limit": stop_reason == "soft_mem_limit",
        "soft_mem_limit_note": (
            "Gurobi stopped on SoftMemLimit: the run is partial and its stop point "
            "is memory-dependent, not work-deterministic, so it is not reproducible. "
            "Incumbent and bound are those held at the stop."
            if stop_reason == "soft_mem_limit"
            else None
        ),
        "soft_mem_limit_bytes": soft_mem_limit_gb * BYTES_PER_GB,
        "solution_count": model.SolCount,
        "node_count": model.NodeCount,
        "final": final,
        "best_bound": state["best_bound"],
        "trajectory_event": "each new incumbent (MIPSOL callback)",
        "trajectory": recorder.events,
        "trajectory_write_error": sink.write_error,
        "inprogress_directory": str(inprogress_dir),
        "peak_rss_bytes": max(sample["rss_bytes"] for sample in sampler.samples),
        "last_rss_bytes": sampler.samples[-1]["rss_bytes"],
        "rss_cap_bytes": measurement["rss_cap_bytes"],
        "rss_sample_count": len(sampler.samples),
    }

    checksums = write_report(output_dir, report, log_path, sink.path)
    return {"report": report, "output_sha256": checksums}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--work-limit-cap", required=True, type=float)
    parser.add_argument("--time-limit-cap", required=True, type=float)
    parser.add_argument("--soft-mem-limit-gb", required=True, type=float)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    result = run_calibration(
        args.config,
        args.stage,
        args.repo_root,
        args.work_limit_cap,
        args.time_limit_cap,
        args.soft_mem_limit_gb,
    )
    report = result["report"]
    print(
        json.dumps(
            {
                "status": report["status"],
                "stop_reason": report["stop_reason"],
                "stopped_on_safety_time_limit": report["stopped_on_safety_time_limit"],
                "stopped_on_soft_mem_limit": report["stopped_on_soft_mem_limit"],
                "solution_count": report["solution_count"],
                "gurobi_work_units": report["gurobi_work_units"],
                "solve_wall_seconds": report["solve_wall_seconds"],
                "final": report["final"],
                "incumbent_events": len(report["trajectory"]),
                "peak_rss_bytes": report["peak_rss_bytes"],
            },
            indent=2,
        )
    )
    for name, digest in result["output_sha256"].items():
        print(f"{digest}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
