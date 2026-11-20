"""Mechanical tiny-fixture tests for the Stage-A calibration solve.

Gurobi and psutil are not installed on the Mac; the solve test runs only where
both are importable. None of this is pinned-runtime qualification.
"""

import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from admet.qualification.native_quadratic import equivalence
from admet.scripts import calibrate_split_solve as calibrate


LIVE_CONFIG = (
    Path(__file__).resolve().parents[1]
    / "admet"
    / "data"
    / "splits"
    / "split_optimization_config.json"
)
LICENSE = "/mnt/nfs/CX900004_DS117/private/gurobi/gurobi.lic"


def test_license_guard_requires_matching_environment_variable():
    config = {"gurobi": {"license_file": LICENSE}}
    assert calibrate.check_license_environment(config, {"GRB_LICENSE_FILE": LICENSE}) == LICENSE
    with pytest.raises(RuntimeError, match="is not set"):
        calibrate.check_license_environment(config, {})
    with pytest.raises(RuntimeError, match="requires"):
        calibrate.check_license_environment(config, {"GRB_LICENSE_FILE": "/other.lic"})
    with pytest.raises(RuntimeError, match="gurobi.license_file"):
        calibrate.check_license_environment({"gurobi": {}}, {"GRB_LICENSE_FILE": LICENSE})


def test_live_config_has_threads_and_license():
    config = json.loads(LIVE_CONFIG.read_text())
    assert config["calibration"]["threads"] == 32
    assert config["gurobi"]["license_file"] == LICENSE


@pytest.mark.parametrize("work,time", [(0, 10), (10, 0), (-1, 10), (float("inf"), 10), (10, float("nan"))])
def test_caps_must_be_positive_and_finite(work, time):
    with pytest.raises(ValueError):
        calibrate.check_caps(work, time)
    calibrate.check_caps(1.0, 1.0)


def test_total_pair_weight_matches_reference_leakage_identity():
    ids = ["0", "1", "2", "3"]
    weights = {"0": 3, "1": 2, "2": 1, "3": 4}
    values = np.array([0.4, 0.0, 0.2, 0.3, 0.1, 0.5], dtype=np.float64)
    similarities = dict(zip(itertools.combinations(ids, 2), values))
    total = calibrate.total_pair_weight(
        np.array([weights[i] for i in ids], dtype=np.float64), values
    )
    # Every family in its own partition: all pairs are cross-partition.
    everyone_apart = {fid: f"p{fid}" for fid in ids}
    assert total == pytest.approx(
        equivalence.reference_cross_partition_leakage(ids, weights, similarities, everyone_apart)
    )
    # L_cross = total - within, for an assignment with two partitions.
    assignment = {"0": "dev", "1": "dev", "2": "test", "3": "test"}
    within = sum(
        weights[a] * weights[b] * similarities[(a, b)]
        for a, b in itertools.combinations(ids, 2)
        if assignment[a] == assignment[b]
    )
    assert calibrate.l_cross_from_within(total, within) == pytest.approx(
        equivalence.reference_cross_partition_leakage(ids, weights, similarities, assignment)
    )


def test_total_pair_weight_rejects_wrong_length():
    with pytest.raises(ValueError):
        calibrate.total_pair_weight(np.ones(4), np.zeros(5))


class FakeModel:
    def __init__(self, values):
        self._values = values

    def cbGet(self, code):
        return self._values[code]


CODES = {
    "MIPSOL": 5,
    "MIPSOL_OBJ": 1,
    "MIPSOL_OBJBND": 2,
    "MIPSOL_NODCNT": 3,
    "MIPSOL_SOLCNT": 4,
    "RUNTIME": 6,
    "WORK": 7,
}


def test_recorder_records_only_incumbents_in_order():
    recorder = calibrate.TrajectoryRecorder(total_weight=100.0, codes=CODES)
    other = FakeModel({})
    recorder(other, where=999)  # not a MIPSOL event: no cbGet calls
    assert recorder.events == []

    for work, within in ((1.5, 40.0), (3.0, 55.0)):
        recorder(
            FakeModel({1: within, 2: 70.0, 3: 12, 4: 1, 6: work * 2, 7: work}),
            where=5,
        )
    assert [e["work_units"] for e in recorder.events] == [1.5, 3.0]
    assert recorder.events[1]["incumbent_l_cross"] == 45.0
    assert recorder.events[1]["best_bound_l_cross"] == 30.0
    assert recorder.events[0]["runtime_seconds"] == 3.0


def test_gurobi_codes_read_callback_constants_from_grb_callback():
    # Layout observed on gpu-dev1 (gurobipy 14.0.0, Session 017 section 17.25):
    # MIPSOL, RUNTIME, WORK and the MIPSOL_* codes are attributes of
    # GRB.Callback, not of GRB.
    class Grb:
        class Callback:
            MIPSOL = 5
            MIPSOL_OBJ = 1
            MIPSOL_OBJBND = 2
            MIPSOL_NODCNT = 3
            MIPSOL_SOLCNT = 4
            RUNTIME = 6
            WORK = 7

    assert calibrate.gurobi_codes(Grb) == CODES


def test_classify_stop_names_time_limit_and_unknown():
    class Grb:
        OPTIMAL = 2
        TIME_LIMIT = 9

    assert calibrate.classify_stop(2, Grb) == "optimal"
    assert calibrate.classify_stop(9, Grb) == "time_limit_cap"
    assert calibrate.classify_stop(17, Grb) == "other_status_17"
    Grb.WORK_LIMIT = 17
    assert calibrate.classify_stop(17, Grb) == "work_limit_cap"


def test_write_report_is_atomic_checksummed_and_not_overwritten(tmp_path):
    log = tmp_path / "in.log"
    log.write_text("gurobi log\n")
    out = tmp_path / "out" / "stage_a_calibration"
    digests = calibrate.write_report(out, {"a": 1}, log)
    assert set(digests) == {"calibration_report.json", "gurobi.log"}
    sums = (out / "SHA256SUMS.txt").read_text().splitlines()
    assert sums == [f"{digests[n]}  {n}" for n in digests]
    assert not list(out.parent.glob(".*partial-*"))
    with pytest.raises(FileExistsError):
        calibrate.write_report(out, {"a": 2}, log)


def test_run_refuses_before_any_work_without_license_env(tmp_path):
    config = json.loads(LIVE_CONFIG.read_text())
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    with pytest.raises(RuntimeError, match="is not set"):
        calibrate.run_calibration(path, "stage_a", tmp_path, 10.0, 60.0, environ={})
    assert not (tmp_path / "admet").exists()


def test_run_refuses_missing_threads(tmp_path):
    config = json.loads(LIVE_CONFIG.read_text())
    del config["calibration"]["threads"]
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    with pytest.raises(RuntimeError, match="threads"):
        calibrate.run_calibration(
            path, "stage_a", tmp_path, 10.0, 60.0, environ={"GRB_LICENSE_FILE": LICENSE}
        )


def test_run_refuses_existing_output(tmp_path):
    config = json.loads(LIVE_CONFIG.read_text())
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    out = tmp_path / config["calibration"]["output_root"] / "stage_a_calibration"
    out.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        calibrate.run_calibration(
            path, "stage_a", tmp_path, 10.0, 60.0, environ={"GRB_LICENSE_FILE": LICENSE}
        )


def test_tiny_calibration_solve_when_gurobi_is_available():
    gp = pytest.importorskip("gurobipy")
    pytest.importorskip("psutil")
    from gurobipy import GRB

    ids = ["0", "1", "2", "3"]
    weights = {"0": 3, "1": 2, "2": 1, "3": 4}
    values = np.array([0.4, 0.0, 0.2, 0.3, 0.1, 0.5], dtype=np.float64)
    similarities = dict(zip(itertools.combinations(ids, 2), values))
    zero = {fid: 0 for fid in ids}
    bounds_lo = {p: {"molecular_identities": 1, "pka_identities": 0, "clearance_identities": 0} for p in ("dev", "test")}
    bounds_hi = {p: {"molecular_identities": 10, "pka_identities": 0, "clearance_identities": 0} for p in ("dev", "test")}
    built = equivalence.build_native_gurobi_model(
        ids, ["dev", "test"], weights, zero, zero, similarities, bounds_lo, bounds_hi
    )
    model = built["model"]
    model.Params.OutputFlag = 0
    total = calibrate.total_pair_weight(
        np.array([weights[i] for i in ids], dtype=np.float64), values
    )
    recorder = calibrate.TrajectoryRecorder(total, calibrate.gurobi_codes(GRB))
    model.optimize(recorder)
    assert model.SolCount >= 1
    assert recorder.events
    assert recorder.events[-1]["incumbent_l_cross"] == pytest.approx(
        calibrate.l_cross_from_within(total, model.ObjVal)
    )
    assert "Seed" not in calibrate.nondefault_parameters(model)
