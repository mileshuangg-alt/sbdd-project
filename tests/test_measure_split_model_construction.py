"""Mechanical tiny-fixture tests for the split-model construction measurement.

Gurobi and psutil are not installed on the Mac; the model-build test runs only
where both are importable. None of this is pinned-runtime qualification.
"""

import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from admet.scripts import measure_split_model_construction as measure


LIVE_CONFIG = (
    Path(__file__).resolve().parents[1]
    / "admet"
    / "data"
    / "splits"
    / "split_optimization_config.json"
)


def _families_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["family_index", "family_key", "w", "pka_identities", "clearance_identities", "diagnostic_scaffold_keys"]
        )
        writer.writerows(rows)


# Six family pairs for four families; one pair has zero similarity, as
# 924,534 pairs do in the real split input.
FIXTURE_SIMILARITIES = np.array([0.4, 0.0, 0.2, 0.3, 0.1, 0.5], dtype=np.float64)

FAMILY_ROWS = [
    [0, "A", 3, 3, 0, ""],
    [1, "B", 2, 1, 1, ""],
    [2, "C", 1, 0, 1, ""],
    [3, "D", 4, 3, 1, ""],
]


def test_similarity_mapping_reads_documented_upper_triangle_order():
    ids = ["0", "1", "2", "3"]
    values = np.arange(6, dtype=np.float64) / 10.0
    mapping = measure.UpperTriangleSimilarities(values, ids)

    assert list(mapping) == list(itertools.combinations(ids, 2))
    assert [mapping[pair] for pair in mapping] == list(values)
    assert len(mapping) == 6
    assert ("0", "1") in mapping
    assert ("1", "0") not in mapping
    assert ("0", "0") not in mapping
    assert ("0", "9") not in mapping
    with pytest.raises(KeyError):
        mapping[("2", "1")]


def test_similarity_mapping_rejects_wrong_array_length():
    with pytest.raises(ValueError, match="does not match"):
        measure.UpperTriangleSimilarities(np.zeros(5), ["0", "1", "2", "3"])


def test_stage_bounds_follow_recorded_formulas_and_rounding():
    ids = ["0", "1", "2", "3"]
    weights = {"0": 3, "1": 2, "2": 1, "3": 4}
    counts = {
        "pka_identities": {"0": 3, "1": 1, "2": 0, "3": 3},
        "clearance_identities": {"0": 0, "1": 1, "2": 1, "3": 1},
    }

    names, lower, upper = measure.stage_bounds(
        ids, weights, counts, {"dev": 0.8, "test": 0.2}, 0.05, 0.05
    )

    assert names == ["dev", "test"]
    assert lower["dev"]["molecular_identities"] == int(0.8 * 0.95 * 10)
    assert lower["test"]["molecular_identities"] == int(0.2 * 0.95 * 10)
    assert lower["dev"]["pka_identities"] == pytest.approx(7 * 0.8 * 0.95)
    assert lower["test"]["clearance_identities"] == pytest.approx(3 * 0.2 * 0.95)
    assert lower["test"]["clearance_identities"] != int(lower["test"]["clearance_identities"])
    for name in names:
        assert upper[name] == {
            "molecular_identities": 10,
            "pka_identities": 7,
            "clearance_identities": 3,
        }


def test_expected_dimensions_count_only_nonzero_similarity_pairs():
    # Stage A on split_input_v1: 13,907,647 non-zero of 14,832,181 pairs
    # (Session 017 section 17.20); Gurobi stores 27,815,294 objective terms.
    dims = measure.expected_dimensions(5447, 2, 3, 13907647)
    assert dims == {
        "binary_variables": 10894,
        "linear_constraints": 5459,
        "quadratic_terms": 27815294,
    }


def test_endpoint_interface_is_checked():
    measure.check_endpoint_interface(["pka", "clearance"])
    with pytest.raises(ValueError, match="qualified native formulation"):
        measure.check_endpoint_interface(["clearance", "pka"])


def test_load_families_checks_order_and_count(tmp_path):
    path = tmp_path / "families.csv"
    _families_csv(path, FAMILY_ROWS)

    ids, weights, counts = measure.load_families(path, ["pka", "clearance"], 4)
    assert ids == ["0", "1", "2", "3"]
    assert weights == {"0": 3, "1": 2, "2": 1, "3": 4}
    assert counts["clearance_identities"]["3"] == 1

    with pytest.raises(ValueError, match="expected 5"):
        measure.load_families(path, ["pka", "clearance"], 5)

    _families_csv(path, [FAMILY_ROWS[1], FAMILY_ROWS[0]])
    with pytest.raises(ValueError, match="at position 0"):
        measure.load_families(path, ["pka", "clearance"], 2)


def _split_input_dir(tmp_path):
    directory = tmp_path / "split_input_v1"
    directory.mkdir()
    _families_csv(directory / "families.csv", FAMILY_ROWS)
    (directory / "memberships.csv").write_text("endpoint,identity\n")
    np.save(directory / "family_similarity_upper.npy", FIXTURE_SIMILARITIES)
    (directory / "run_metadata.json").write_text("{}\n")
    names = ["families.csv", "memberships.csv", "family_similarity_upper.npy", "run_metadata.json"]
    (directory / "SHA256SUMS.txt").write_text(
        "".join(f"{measure.sha256_file(directory / n)}  {n}\n" for n in names)
    )
    expected = {n: measure.sha256_file(directory / n) for n in measure.SPLIT_INPUT_FILES}
    return directory, expected


def test_verify_split_input_requires_recorded_hashes(tmp_path):
    directory, expected = _split_input_dir(tmp_path)

    assert measure.verify_split_input(directory, expected) == expected

    with pytest.raises(RuntimeError, match="not recorded yet"):
        measure.verify_split_input(directory, {**expected, "families.csv": None})

    with pytest.raises(ValueError, match="SHA-256 mismatch for memberships.csv"):
        measure.verify_split_input(directory, {**expected, "memberships.csv": "0" * 64})


def test_measurement_refuses_pending_config(tmp_path):
    config = json.loads(LIVE_CONFIG.read_text())
    config["construction_measurement"]["rss_cap_bytes"] = None
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))

    with pytest.raises(RuntimeError, match="rss_cap_bytes is not set"):
        measure.measure_construction(path, "stage_a", tmp_path)

    with pytest.raises(ValueError, match="not configured"):
        measure.measure_construction(path, "stage_b", tmp_path)


def test_similarity_mapping_repeat_lookup_reuses_offset():
    ids = ["0", "1", "2"]
    mapping = measure.UpperTriangleSimilarities(np.array([0.1, 0.2, 0.3]), ids)

    assert ("1", "2") in mapping
    assert mapping[("1", "2")] == 0.3
    assert mapping[("0", "2")] == 0.2
    assert mapping[("0", "1")] == 0.1


def test_measurement_refuses_existing_abort_report(tmp_path):
    config = json.loads(LIVE_CONFIG.read_text())
    config["construction_measurement"]["output_root"] = "out"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "stage_a_construction_ABORTED.json").write_text("{}")

    with pytest.raises(FileExistsError, match="earlier aborted run"):
        measure.measure_construction(path, "stage_a", tmp_path)


def test_rss_sampler_writes_abort_report_and_exits(tmp_path):
    readings = iter([10, 20, 500, 500])
    exits = []
    abort_path = tmp_path / "out" / "stage_a_construction_ABORTED.json"

    sampler = measure.RssSampler(
        cap_bytes=100,
        interval_seconds=0.001,
        abort_path=abort_path,
        rss_reader=lambda: next(readings),
        exit_function=exits.append,
    )
    sampler.start()
    sampler._thread.join(timeout=5)

    assert exits == [3]
    report = json.loads(abort_path.read_text())
    assert report["status"] == "aborted_rss_cap_exceeded"
    assert report["rss_cap_bytes"] == 100
    assert [s["rss_bytes"] for s in report["samples"]] == [10, 20, 500]


def test_rss_sampler_records_samples_without_abort(tmp_path):
    sampler = measure.RssSampler(
        cap_bytes=1000,
        interval_seconds=0.001,
        abort_path=tmp_path / "unused.json",
        rss_reader=lambda: 42,
        exit_function=lambda code: pytest.fail("unexpected abort"),
    )
    sampler.start()
    sampler.stop()

    assert sampler.samples and all(s["rss_bytes"] == 42 for s in sampler.samples)
    assert not (tmp_path / "unused.json").exists()


def test_host_description_reads_cpu_model_and_memory(tmp_path):
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text("processor\t: 0\nmodel name\t: Example CPU 9000\n")

    host = measure.host_description(total_memory=lambda: 123, cpuinfo_path=cpuinfo)

    assert host["cpu_model"] == "Example CPU 9000"
    assert host["total_memory_bytes"] == 123
    assert set(host) == {
        "hostname",
        "platform",
        "cpu_model",
        "logical_cpus",
        "total_memory_bytes",
    }


def test_report_is_not_overwritten(tmp_path):
    (tmp_path / "stage_a_construction").mkdir()
    with pytest.raises(FileExistsError):
        measure.write_report(tmp_path / "stage_a_construction", {})


def test_report_write_is_atomic_and_checksummed(tmp_path):
    output = tmp_path / "stage_a_construction"
    checksums = measure.write_report(output, {"ok": True})

    assert sorted(p.name for p in output.iterdir()) == [
        measure.CHECKSUMS_FILENAME,
        measure.REPORT_FILENAME,
    ]
    digest = hashlib.sha256((output / measure.REPORT_FILENAME).read_bytes()).hexdigest()
    assert checksums == {measure.REPORT_FILENAME: digest}
    assert not list(tmp_path.glob(".stage_a_construction.partial-*"))


def test_tiny_native_build_when_gurobi_is_available(tmp_path):
    pytest.importorskip("gurobipy")
    pytest.importorskip("psutil")

    directory, expected = _split_input_dir(tmp_path)
    config = {
        "governing_decisions": ["test"],
        "split_input": {
            "directory": str(directory.relative_to(tmp_path)),
            "family_count": 4,
            "similarity_length": 6,
            "expected_sha256": expected,
        },
        "endpoints": ["pka", "clearance"],
        "epsilon": 0.05,
        "delta": 0.05,
        "stages": {"stage_a": {"family_scope": "all", "partitions": {"dev": 0.8, "test": 0.2}}},
        "construction_measurement": {
            "rss_cap_bytes": 1 << 40,
            "sample_interval_seconds": 0.01,
            "output_root": "out",
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))

    result = measure.measure_construction(path, "stage_a", tmp_path)

    # Gurobi drops the one zero-similarity pair's terms from the objective:
    # 5 non-zero pairs x 2 partitions = 10 stored terms, not 12.
    assert result["report"]["dimensions"]["quadratic_terms"] == 10
    assert result["report"]["similarity_pairs"] == {
        "total": 6,
        "nonzero": 5,
        "zero": 1,
        "zero_pair_terms_note": result["report"]["similarity_pairs"]["zero_pair_terms_note"],
    }
    assert result["report"]["optimize_called"] is False
    assert result["report"]["solution_count"] == 0
