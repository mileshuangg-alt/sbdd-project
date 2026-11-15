"""Measure construction of the native split model without solving it.

Implements D034 section 4 step 2 (Stage A); the stage argument lets the same
script serve the Stage-B measurement of D034 Amendment 1 A3 once a frozen
Stage-A partition exists. It builds the qualified native formulation
(`equivalence.build_native_gurobi_model`) on the real `split_input_v1`
artifacts and records wall time and peak RSS. It never calls `optimize()`.

Usage (from the repository root, in the Gurobi environment):

    python -s -m admet.scripts.measure_split_model_construction \
        --config admet/data/splits/split_optimization_config.json \
        --stage stage_a
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from admet.qualification.datasail_scaling import probe
from admet.qualification.native_quadratic import equivalence


SCHEMA_VERSION = "admet_split_model_construction.v1"
REPORT_FILENAME = "construction_report.json"
CHECKSUMS_FILENAME = "SHA256SUMS.txt"
SPLIT_INPUT_FILES = (
    "families.csv",
    "memberships.csv",
    "family_similarity_upper.npy",
    "run_metadata.json",
    "SHA256SUMS.txt",
)
MOLECULAR_METRIC = "molecular_identities"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def endpoint_metric(endpoint: str) -> str:
    return f"{endpoint}_identities"


def check_endpoint_interface(endpoints: list[str]) -> None:
    """The qualified native interface names exactly these endpoint metrics."""

    expected = ("pka_identities", "clearance_identities")
    observed = tuple(endpoint_metric(name) for name in endpoints)
    if observed != expected:
        raise ValueError(
            f"Config endpoints map to metrics {observed}; the qualified native "
            f"formulation requires {expected}"
        )


def verify_split_input(directory: Path, expected: Mapping[str, str | None]) -> dict[str, str]:
    """Halt unless every split-input file matches its recorded SHA-256."""

    missing = [name for name in SPLIT_INPUT_FILES if not expected.get(name)]
    if missing:
        raise RuntimeError(
            "Expected split-input hashes are not recorded yet for: "
            + ", ".join(missing)
        )

    observed: dict[str, str] = {}
    for name in SPLIT_INPUT_FILES:
        digest = sha256_file(directory / name)
        if digest != expected[name]:
            raise ValueError(
                f"SHA-256 mismatch for {name}: observed {digest}, "
                f"recorded {expected[name]}"
            )
        observed[name] = digest

    for line in (directory / "SHA256SUMS.txt").read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        if observed.get(name.strip()) != digest:
            raise ValueError(f"{name.strip()} does not match SHA256SUMS.txt")

    return observed


def load_families(
    path: Path, endpoints: list[str], expected_count: int
) -> tuple[list[str], dict[str, int], dict[str, dict[str, int]]]:
    """Read family ids, weights and endpoint identity counts."""

    family_ids: list[str] = []
    weights: dict[str, int] = {}
    counts: dict[str, dict[str, int]] = {endpoint_metric(e): {} for e in endpoints}

    with path.open(newline="") as handle:
        for position, row in enumerate(csv.DictReader(handle)):
            family_id = row["family_index"]
            if int(family_id) != position:
                raise ValueError(
                    f"families.csv family_index {family_id} at position {position}"
                )
            family_ids.append(family_id)
            weights[family_id] = int(row["w"])
            for endpoint in endpoints:
                metric = endpoint_metric(endpoint)
                counts[metric][family_id] = int(row[metric])

    if len(family_ids) != expected_count:
        raise ValueError(
            f"families.csv has {len(family_ids)} families, expected {expected_count}"
        )
    return family_ids, weights, counts


class UpperTriangleSimilarities(Mapping):
    """Read-only S_ij lookup over the builder's upper-triangle array.

    Keys are (family_id_i, family_id_j) with i < j in family order, the order
    in which the native formulation enumerates pairs. Values are read from the
    (memory-mapped) array; no per-pair dictionary is built.
    """

    def __init__(self, values: np.ndarray, family_ids: list[str]):
        family_count = len(family_ids)
        if values.ndim != 1 or values.size != family_count * (family_count - 1) // 2:
            raise ValueError(
                f"similarity array of size {values.size} does not match "
                f"{family_count} families"
            )
        self._values = values
        self._family_ids = list(family_ids)
        self._position = {fid: index for index, fid in enumerate(family_ids)}
        self._count = family_count
        self._last_key = None
        self._last_offset = -1

    def _offset(self, key) -> int:
        # The native builder checks `pair in mapping` and then reads
        # `mapping[pair]`; reuse the offset computed for the same key.
        if key == self._last_key:
            return self._last_offset
        try:
            left, right = key
            i = self._position[left]
            j = self._position[right]
        except (TypeError, ValueError, KeyError):
            raise KeyError(key) from None
        if i >= j:
            raise KeyError(key)
        offset = i * self._count - i * (i + 1) // 2 + (j - i - 1)
        self._last_key = key
        self._last_offset = offset
        return offset

    def __getitem__(self, key) -> float:
        return float(self._values[self._offset(key)])

    def __contains__(self, key) -> bool:
        try:
            self._offset(key)
        except KeyError:
            return False
        return True

    def __len__(self) -> int:
        return int(self._values.size)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        for i in range(self._count):
            for j in range(i + 1, self._count):
                yield (self._family_ids[i], self._family_ids[j])


def stage_bounds(
    family_ids: list[str],
    weights: Mapping[str, int],
    endpoint_counts: Mapping[str, Mapping[str, int]],
    partitions: Mapping[str, float],
    epsilon: float,
    delta: float,
) -> tuple[list[str], dict, dict]:
    """D031 section 4 lower bounds and section 5 stage-total upper bounds.

    Lower bounds use the recorded functions in datasail_scaling/probe.py:
    the molecular bound is truncated by int(); endpoint bounds are not rounded.
    """

    partition_names = list(partitions)
    splits = [partitions[name] for name in partition_names]
    metrics = list(endpoint_counts)

    total_identities = sum(weights[fid] for fid in family_ids)
    molecular_lower = probe.compute_limits(epsilon, total_identities, splits)

    s_matrix = np.array(
        [[endpoint_counts[m][fid] for m in metrics] for fid in family_ids],
        dtype=float,
    )
    endpoint_lower = probe.stratification_lower_bounds(s_matrix, splits, delta)
    endpoint_totals = {
        m: int(sum(endpoint_counts[m][fid] for fid in family_ids)) for m in metrics
    }

    lower_bounds: dict[str, dict[str, float]] = {}
    upper_bounds: dict[str, dict[str, int]] = {}
    for p, name in enumerate(partition_names):
        lower_bounds[name] = {MOLECULAR_METRIC: molecular_lower[p]}
        upper_bounds[name] = {MOLECULAR_METRIC: total_identities}
        for e, metric in enumerate(metrics):
            lower_bounds[name][metric] = float(endpoint_lower[p][e])
            upper_bounds[name][metric] = endpoint_totals[metric]

    return partition_names, lower_bounds, upper_bounds


def expected_dimensions(
    family_count: int,
    partition_count: int,
    metric_count: int,
    nonzero_similarity_pairs: int,
) -> dict:
    """Expected native-model dimensions.

    Gurobi keeps zero-coefficient terms in a QuadExpr but drops them when the
    expression is set as the model objective (Session 017 section 17.20). A
    family pair with S_ij = 0 has coefficient w_i w_j S_ij = 0, so the stored
    objective holds one term per partition for each non-zero pair only. The
    objective is mathematically unchanged.
    """

    return {
        "binary_variables": family_count * partition_count,
        "linear_constraints": family_count + 2 * metric_count * partition_count,
        "quadratic_terms": nonzero_similarity_pairs * partition_count,
    }


def _psutil_total_memory() -> int:
    import psutil

    return psutil.virtual_memory().total


def _psutil_rss_reader():
    import psutil

    process = psutil.Process(os.getpid())
    return lambda: process.memory_info().rss


def host_description(
    total_memory=_psutil_total_memory, cpuinfo_path: Path = Path("/proc/cpuinfo")
) -> dict:
    cpu_model = platform.processor()
    if cpuinfo_path.exists():
        for line in cpuinfo_path.read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break

    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "cpu_model": cpu_model,
        "logical_cpus": os.cpu_count(),
        "total_memory_bytes": total_memory(),
    }


def executed_code_hashes() -> dict:
    modules = {
        "admet.scripts.measure_split_model_construction": sys.modules[__name__],
        "admet.qualification.native_quadratic.equivalence": equivalence,
        "admet.qualification.datasail_scaling.probe": probe,
    }
    return {
        name: {
            "path": str(Path(module.__file__).resolve()),
            "sha256": sha256_file(Path(module.__file__).resolve()),
        }
        for name, module in modules.items()
    }


class RssSampler:
    """Sample this process's RSS; on exceeding the cap, report and exit.

    Mirrors the sampling loop of
    `admet.qualification.native_quadratic.construction_probe.measure_native_construction`
    (left unedited because it is qualified code); a change to one should be
    reviewed against the other.

    The cap is checked only at each sample, so it is not a hard limit: memory
    can exceed it between samples before the process exits.
    """

    def __init__(
        self,
        cap_bytes: int,
        interval_seconds: float,
        abort_path: Path,
        rss_reader=None,
        exit_function=os._exit,
    ):
        self._read_rss = rss_reader or _psutil_rss_reader()
        self._exit = exit_function
        self._cap = cap_bytes
        self._interval = interval_seconds
        self._abort_path = abort_path
        self._stop = threading.Event()
        self._start = time.perf_counter()
        self.samples: list[dict] = []
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            rss = self._read_rss()
            sample = {"t_seconds": time.perf_counter() - self._start, "rss_bytes": rss}
            self.samples.append(sample)
            if rss > self._cap:
                self._abort_path.parent.mkdir(parents=True, exist_ok=True)
                self._abort_path.write_text(
                    json.dumps(
                        {
                            "status": "aborted_rss_cap_exceeded",
                            "rss_cap_bytes": self._cap,
                            "sample_interval_seconds": self._interval,
                            "created_utc": datetime.now(timezone.utc).isoformat(),
                            "samples": self.samples,
                        },
                        indent=2,
                    )
                    + "\n"
                )
                self._exit(3)
                return
            self._stop.wait(self._interval)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join()
        self.samples.append(
            {
                "t_seconds": time.perf_counter() - self._start,
                "rss_bytes": self._read_rss(),
            }
        )


def write_report(output_dir: Path, report: dict) -> dict[str, str]:
    """Write the report to a temporary sibling and move it into place."""

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
        digest = sha256_file(staging / REPORT_FILENAME)
        (staging / CHECKSUMS_FILENAME).write_text(f"{digest}  {REPORT_FILENAME}\n")
        staging.rename(output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {REPORT_FILENAME: digest}


def measure_construction(config_path: Path, stage: str, repo_root: Path) -> dict:
    config = json.loads(config_path.read_text())
    stage_config = config["stages"].get(stage)
    if stage_config is None:
        raise ValueError(f"Stage {stage!r} is not configured")
    if stage_config["family_scope"] != "all":
        raise ValueError(
            f"Family scope {stage_config['family_scope']!r} is not supported yet"
        )

    measurement = config["construction_measurement"]
    if not measurement.get("rss_cap_bytes"):
        raise RuntimeError("rss_cap_bytes is not set in the config")

    output_dir = repo_root / measurement["output_root"] / f"{stage}_construction"
    if output_dir.exists():
        raise FileExistsError(f"{output_dir} exists; reports are not overwritten")
    abort_path = (
        repo_root / measurement["output_root"] / f"{stage}_construction_ABORTED.json"
    )
    if abort_path.exists():
        raise FileExistsError(
            f"{abort_path} exists from an earlier aborted run; it is not overwritten"
        )

    endpoints = config["endpoints"]
    check_endpoint_interface(endpoints)

    split_input = config["split_input"]
    input_dir = repo_root / split_input["directory"]
    input_hashes = verify_split_input(input_dir, split_input["expected_sha256"])

    family_ids, weights, endpoint_counts = load_families(
        input_dir / "families.csv", endpoints, split_input["family_count"]
    )
    values = np.load(input_dir / "family_similarity_upper.npy", mmap_mode="r")
    if values.dtype != np.float64 or values.size != split_input["similarity_length"]:
        raise ValueError(
            f"similarity array is {values.dtype} of size {values.size}"
        )
    similarities = UpperTriangleSimilarities(values, family_ids)
    nonzero_similarity_pairs = int(np.count_nonzero(values))
    zero_similarity_pairs = int(values.size) - nonzero_similarity_pairs

    partition_names, lower_bounds, upper_bounds = stage_bounds(
        family_ids,
        weights,
        endpoint_counts,
        stage_config["partitions"],
        config["epsilon"],
        config["delta"],
    )

    sampler = RssSampler(
        measurement["rss_cap_bytes"],
        measurement["sample_interval_seconds"],
        abort_path,
    )
    sampler.start()
    started = time.perf_counter()
    try:
        built = equivalence.build_native_gurobi_model(
            family_ids=family_ids,
            partition_names=partition_names,
            molecular_weights=weights,
            pka_counts=endpoint_counts["pka_identities"],
            clearance_counts=endpoint_counts["clearance_identities"],
            similarities=similarities,
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
        )
    finally:
        elapsed = time.perf_counter() - started
        sampler.stop()

    model = built["model"]
    observed = {
        "binary_variables": model.NumBinVars,
        "variables": model.NumVars,
        "linear_constraints": model.NumConstrs,
        "quadratic_terms": model.getObjective().size(),
    }
    expected = expected_dimensions(
        len(family_ids),
        len(partition_names),
        1 + len(endpoints),
        nonzero_similarity_pairs,
    )
    for name, value in expected.items():
        if observed[name] != value:
            raise AssertionError(f"{name}: observed {observed[name]}, expected {value}")
    if observed["variables"] != expected["binary_variables"]:
        raise AssertionError("non-binary variables present in the model")
    if model.SolCount != 0:
        raise AssertionError("construction-only measurement produced a solution")

    import gurobipy

    report = {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "governing_decisions": config["governing_decisions"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "optimize_called": False,
        "config_sha256": sha256_file(config_path),
        "split_input_sha256": input_hashes,
        "executed_code_sha256": executed_code_hashes(),
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "gurobi": ".".join(str(part) for part in gurobipy.gurobi.version()),
        },
        "host": host_description(),
        "partitions": stage_config["partitions"],
        "epsilon": config["epsilon"],
        "delta": config["delta"],
        "lower_bounds": lower_bounds,
        "upper_bounds": upper_bounds,
        "dimensions": observed,
        "expected_dimensions": expected,
        "similarity_pairs": {
            "total": int(values.size),
            "nonzero": nonzero_similarity_pairs,
            "zero": zero_similarity_pairs,
            "zero_pair_terms_note": (
                "Gurobi does not store zero-coefficient objective terms; zero-"
                "similarity pairs contribute 0 to L_cross in every assignment"
            ),
        },
        "solution_count": model.SolCount,
        "construction_seconds": elapsed,
        "peak_rss_bytes": max(sample["rss_bytes"] for sample in sampler.samples),
        "rss_cap_bytes": measurement["rss_cap_bytes"],
        "rss_cap_enforcement": (
            "checked at each sample every "
            f"{measurement['sample_interval_seconds']} s; not a hard limit"
        ),
        "rss_samples": sampler.samples,
    }
    checksums = write_report(output_dir, report)
    return {"report": report, "output_sha256": checksums}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    result = measure_construction(args.config, args.stage, args.repo_root)
    report = result["report"]
    print(json.dumps(
        {
            "dimensions": report["dimensions"],
            "similarity_pairs": report["similarity_pairs"],
            "construction_seconds": report["construction_seconds"],
            "peak_rss_bytes": report["peak_rss_bytes"],
            "host": report["host"],
        },
        indent=2,
    ))
    for name, digest in result["output_sha256"].items():
        print(f"{digest}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
