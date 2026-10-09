import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import evaluation.stage6_planner_stock_build as build
from evaluation.stage6_planner_stock_build import (
    EXPECTED_SOURCE_FIELDS,
    run_stage6_planner_stock_build,
)


def _write_frozen_source(path):
    rows = [
        {
            "smiles": "CCO",
            "zinc_id": "ZINC000000000001",
            "zinc_inchikey": "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "d026_inchikey": "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "full_key_match": "True",
            "connectivity_match": "True",
            "source_file": "fixture.tsv",
            "source_line_number": "1",
        },
        {
            "smiles": "OCC",
            "zinc_id": "ZINC000000000002",
            "zinc_inchikey": "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
            "d026_inchikey": "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
            "full_key_match": "True",
            "connectivity_match": "True",
            "source_file": "fixture.tsv",
            "source_line_number": "2",
        },
        {
            "smiles": "CCO.CN",
            "zinc_id": "ZINC000000000003",
            "zinc_inchikey": "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
            "d026_inchikey": "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
            "full_key_match": "True",
            "connectivity_match": "True",
            "source_file": "fixture.tsv",
            "source_line_number": "3",
        },
        {
            "smiles": "CCN",
            "zinc_id": "ZINC000000000004",
            "zinc_inchikey": "HHHHHHHHHHHHHH-IIIIIIIIII-J",
            "d026_inchikey": "HHHHHHHHHHHHHH-IIIIIIIIII-J",
            "full_key_match": "True",
            "connectivity_match": "True",
            "source_file": "fixture.tsv",
            "source_line_number": "4",
        },
    ]

    path.write_text(
        "\t".join(EXPECTED_SOURCE_FIELDS)
        + "\n"
        + "".join(
            "\t".join(row[field] for field in EXPECTED_SOURCE_FIELDS)
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def test_stage6_planner_stock_build_uses_local_workspace_then_publishes(
    tmp_path,
):
    source_path = tmp_path / "frozen_source.tsv"
    local_work_dir = tmp_path / "local_work"
    output_dir = tmp_path / "final_output"
    _write_frozen_source(source_path)

    assert not output_dir.exists()

    result = run_stage6_planner_stock_build(
        source_path,
        output_dir,
        expected_source_records=4,
        local_work_dir=local_work_dir,
        _progress_interval_records=2,
    )

    assert result == {
        "source_record_count": 4,
        "unique_frozen_d026_keys": 4,
        "source_duplicate_rows": 0,
        "representation_failure_keys": 1,
        "collision_excluded_keys": 2,
        "qualified_keys": 1,
        "representable_keys": 3,
        "aizynthfinder_keys": 4,
        "representable_set_equality_pass": True,
        "output_dir": str(output_dir.resolve()),
        "local_workspace": result["local_workspace"],
    }

    local_workspace = Path(result["local_workspace"])
    assert local_workspace.parent == local_work_dir.resolve()
    assert (local_workspace / "planner_stock_build.sqlite").is_file()
    assert not (output_dir / "planner_stock_build.sqlite").exists()

    assert (output_dir / "manifest.json").is_file()
    assert (output_dir / "proof.json").is_file()
    assert (output_dir / "askcos_qualified_stock.tsv").is_file()

    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["local_workspace"] == str(local_workspace)
    assert manifest["progress_log"] == str(
        local_workspace / "progress.log"
    )
    assert manifest["final_output_dir"] == str(output_dir.resolve())

    progress_log = (local_workspace / "progress.log").read_text()
    assert "run_started" in progress_log
    assert "source_progress source_rows_processed=2" in progress_log
    assert "source_progress source_rows_processed=4" in progress_log
    assert "run_completed" in progress_log


def test_stage6_planner_stock_build_requires_local_work_dir(tmp_path):
    with pytest.raises(ValueError, match="local_work_dir is required"):
        run_stage6_planner_stock_build(
            tmp_path / "missing.tsv",
            tmp_path / "final_output",
        )


def test_stage6_planner_stock_build_failure_leaves_local_diagnostics_only(
    tmp_path,
):
    local_work_dir = tmp_path / "local_work"
    output_dir = tmp_path / "final_output"

    with pytest.raises(FileNotFoundError):
        run_stage6_planner_stock_build(
            tmp_path / "missing_source.tsv",
            output_dir,
            local_work_dir=local_work_dir,
        )

    assert not (output_dir / "manifest.json").exists()
    assert not (output_dir / "proof.json").exists()

    workspaces = list(local_work_dir.iterdir())
    assert len(workspaces) == 1
    assert workspaces[0].is_dir()
    assert (workspaces[0] / "planner_stock_build.sqlite").is_file()
    progress_log = (workspaces[0] / "progress.log").read_text()
    assert "run_failed exception_type=FileNotFoundError" in progress_log
    assert "Traceback" in progress_log


def test_stage6_planner_stock_build_injected_exception_logs_diagnostics(
    tmp_path,
    monkeypatch,
):
    source_path = tmp_path / "frozen_source.tsv"
    local_work_dir = tmp_path / "local_work"
    output_dir = tmp_path / "final_output"
    _write_frozen_source(source_path)

    def fail_canonicalization(source_record):
        raise RuntimeError("injected driver failure")

    monkeypatch.setattr(
        build,
        "canonicalize_askcos_smiles",
        fail_canonicalization,
    )

    with pytest.raises(RuntimeError, match="injected driver failure"):
        run_stage6_planner_stock_build(
            source_path,
            output_dir,
            local_work_dir=local_work_dir,
        )

    assert not (output_dir / "manifest.json").exists()
    assert not (output_dir / "proof.json").exists()

    workspaces = list(local_work_dir.iterdir())
    assert len(workspaces) == 1
    progress_log = (workspaces[0] / "progress.log").read_text()
    assert "run_failed exception_type=RuntimeError" in progress_log
    assert "injected driver failure" in progress_log
    assert (workspaces[0] / "planner_stock_build.sqlite").is_file()


def test_stage6_planner_stock_build_uncaught_failure_exits_nonzero(
    tmp_path,
):
    local_work_dir = tmp_path / "local_work"
    output_dir = tmp_path / "final_output"
    source_path = tmp_path / "missing_source.tsv"

    command = (
        "from evaluation.stage6_planner_stock_build import "
        "run_stage6_planner_stock_build; "
        "run_stage6_planner_stock_build(" 
        f"{str(source_path)!r}, "
        f"{str(output_dir)!r}, "
        f"local_work_dir={str(local_work_dir)!r})"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.getcwd()

    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=os.getcwd(),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not (output_dir / "manifest.json").exists()
    assert not (output_dir / "proof.json").exists()

    workspaces = list(local_work_dir.iterdir())
    assert len(workspaces) == 1
    progress_log = (workspaces[0] / "progress.log").read_text()
    assert "run_failed exception_type=FileNotFoundError" in progress_log
