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
        --stage stage_a --work-limit-cap <W> --time-limit-cap <T>
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


class TrajectoryRecorder:
    """Gurobi callback that records each new incumbent.

    `codes` maps the callback names used here to Gurobi's integer codes
    (`GRB.MIPSOL`, `GRB.Callback.RUNTIME`, ...) so tests need no Gurobi.
    """

    def __init__(self, total_weight: float, codes: Mapping[str, int]):
        self._total = total_weight
        self._codes = codes
        self.events: list[dict] = []

    def __call__(self, model, where: int) -> None:
        if where != self._codes["MIPSOL"]:
            return
        within = model.cbGet(self._codes["MIPSOL_OBJ"])
        bound = model.cbGet(self._codes["MIPSOL_OBJBND"])
        self.events.append(
            {
                "runtime_seconds": model.cbGet(self._codes["RUNTIME"]),
                "work_units": model.cbGet(self._codes["WORK"]),
                "incumbent_within_objective": within,
                "incumbent_l_cross": l_cross_from_within(self._total, within),
                "best_bound_within_objective": bound,
                "best_bound_l_cross": l_cross_from_within(self._total, bound),
                "node_count": model.cbGet(self._codes["MIPSOL_NODCNT"]),
                "solution_count": model.cbGet(self._codes["MIPSOL_SOLCNT"]),
            }
        )


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
    return f"other_status_{status}"


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


def write_report(output_dir: Path, report: dict, log_path: Path) -> dict[str, str]:
    """Write report, Gurobi log and checksums to a temporary sibling, then move
    the directory into place. Existing output is never overwritten."""

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
        digests = {
            name: measure.sha256_file(staging / name)
            for name in (REPORT_FILENAME, LOG_FILENAME)
        }
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

    output_root = repo_root / calibration["output_root"]
    output_dir = output_root / f"{stage}_calibration"
    abort_path = output_root / f"{stage}_calibration_ABORTED.json"
    for path in (output_dir, abort_path):
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

        # The log is written into a temporary location and moved with the report.
        log_dir = Path(tempfile.mkdtemp(prefix="calibration_log_"))
        log_path = log_dir / LOG_FILENAME
        model.Params.LogFile = str(log_path)
        model.Params.OutputFlag = 1
        model.Params.Seed = seed
        model.Params.Threads = threads
        model.Params.WorkLimit = work_limit_cap
        model.Params.TimeLimit = time_limit_cap

        recorder = TrajectoryRecorder(total_weight, gurobi_codes(GRB))
        solve_started = time.perf_counter()
        model.optimize(recorder)
        solve_seconds = time.perf_counter() - solve_started
    finally:
        sampler.stop()

    status = model.Status
    has_solution = model.SolCount > 0
    final = {}
    if has_solution:
        within = model.ObjVal
        bound = model.ObjBound
        final = {
            "incumbent_within_objective": within,
            "incumbent_l_cross": l_cross_from_within(total_weight, within),
            "best_bound_within_objective": bound,
            "best_bound_l_cross": l_cross_from_within(total_weight, bound),
            "mip_gap": model.MIPGap,
        }

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
        "solution_count": model.SolCount,
        "node_count": model.NodeCount,
        "final": final,
        "trajectory_event": "each new incumbent (MIPSOL callback)",
        "trajectory": recorder.events,
        "peak_rss_bytes": max(sample["rss_bytes"] for sample in sampler.samples),
        "rss_cap_bytes": measurement["rss_cap_bytes"],
        "rss_sample_count": len(sampler.samples),
    }

    checksums = write_report(output_dir, report, log_path)
    return {"report": report, "output_sha256": checksums}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--work-limit-cap", required=True, type=float)
    parser.add_argument("--time-limit-cap", required=True, type=float)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    result = run_calibration(
        args.config, args.stage, args.repo_root, args.work_limit_cap, args.time_limit_cap
    )
    report = result["report"]
    print(
        json.dumps(
            {
                "status": report["status"],
                "stop_reason": report["stop_reason"],
                "stopped_on_safety_time_limit": report["stopped_on_safety_time_limit"],
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
