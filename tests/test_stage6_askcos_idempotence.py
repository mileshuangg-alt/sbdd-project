import json

import evaluation.stage6_askcos_idempotence as diagnostic


def _key(index):
    return f"AAAAAAAAAAAA{index:02d}-BBBBBBBBBB-C"


def _row(key, existing_smiles, new_smiles, existing_status="representable", new_status="representable"):
    return {
        "d026_inchikey": key,
        "existing_status": existing_status,
        "existing_canonical_smiles": existing_smiles,
        "existing_failure_reason": "",
        "new_status": new_status,
        "new_canonical_smiles": new_smiles,
        "new_failure_reason": "",
    }


def _stub_canonicalizer(source_record):
    smiles = source_record["smiles"]
    if smiles == "FAIL":
        return {
            "d026_inchikey": source_record["d026_inchikey"],
            "source_smiles": smiles,
            "askcos_status": "representation_failure",
            "canonical_smiles": None,
            "representation_failure_reason": "STUB_FAILURE",
        }
    if smiles in {"CCO", "OCC"}:
        canonical_smiles = "CCO"
    else:
        canonical_smiles = smiles
    return {
        "d026_inchikey": source_record["d026_inchikey"],
        "source_smiles": smiles,
        "askcos_status": "representable",
        "canonical_smiles": canonical_smiles,
        "representation_failure_reason": None,
    }


def test_build_evidence_map_groups_by_full_d026_key():
    rows = [
        _row(_key(1), "CCO", "OCC"),
        _row(_key(1), "N", "CCO", new_status="canonical_collision_excluded"),
        _row(_key(2), "CCC", "CCC"),
    ]

    evidence = diagnostic.build_evidence_map(rows)

    assert sorted(evidence) == [_key(1), _key(2)]
    assert evidence[_key(1)]["observed_askcos_smiles"] == frozenset(
        {"CCO", "OCC", "N"}
    )
    assert evidence[_key(1)]["observed_statuses"] == frozenset(
        {"representable", "canonical_collision_excluded"}
    )


def test_select_keys_for_analysis_samples_deterministically():
    rows = []
    for index in range(10):
        rows.append(_row(_key(index), f"C{index}", f"N{index}"))
    rows.append(_row(_key(99), "A", "B"))
    rows.append(_row(_key(99), "C", "A"))
    evidence = diagnostic.build_evidence_map(rows)

    first = diagnostic.select_keys_for_analysis(evidence, sample_size=4, seed=20261001)
    second = diagnostic.select_keys_for_analysis(evidence, sample_size=4, seed=20261001)

    assert first == second
    assert first["high_multiplicity_keys"] == [_key(99)]
    assert len(first["sampled_keys"]) == 4
    assert _key(99) not in first["sampled_keys"]
    assert first["selected_keys"] == sorted(
        first["high_multiplicity_keys"] + first["sampled_keys"]
    )


def test_row_order_does_not_change_evidence_map():
    rows = [
        _row(_key(1), "CCO", "OCC"),
        _row(_key(2), "CCC", "N"),
        _row(_key(1), "N", "CCO"),
    ]

    assert diagnostic.build_evidence_map(rows) == diagnostic.build_evidence_map(
        list(reversed(rows))
    )


def test_build_report_marks_idempotent_and_non_idempotent_cases():
    rows = [
        _row(_key(1), "CCO", "OCC"),
        _row(_key(2), "CCC", "NNN"),
        _row(_key(3), "CCO", "FAIL"),
    ]

    report = diagnostic.build_report(
        rows,
        sample_size=3,
        seed=20261001,
        canonicalizer=_stub_canonicalizer,
    )

    by_key = {
        key_report["d026_inchikey"]: key_report
        for key_report in report["keys"]
    }

    assert by_key[_key(1)]["idempotent"] is True
    assert by_key[_key(1)]["distinct_recanonicalized_outputs"] == ["CCO"]
    assert by_key[_key(2)]["idempotent"] is False
    assert by_key[_key(2)]["distinct_recanonicalized_output_count"] == 2
    assert by_key[_key(3)]["idempotent"] is False
    assert by_key[_key(3)]["representation_failures"] == [
        {
            "observed_askcos_smiles": "FAIL",
            "askcos_status": "representation_failure",
            "representation_failure_reason": "STUB_FAILURE",
        }
    ]
    assert report["aggregate"] == {
        "total_conflicted_keys": 3,
        "keys_with_at_least_3_spellings": 0,
        "random_sample_size": 3,
        "sampled_keys": 3,
        "selected_keys": 3,
        "idempotent_keys": 1,
        "non_idempotent_keys": 2,
        "idempotence_fraction": 1 / 3,
    }


def test_write_json_report_has_deterministic_structure(tmp_path):
    report = diagnostic.build_report(
        [_row(_key(1), "OCC", "CCO")],
        sample_size=1,
        seed=20261001,
        canonicalizer=_stub_canonicalizer,
    )
    output_path = tmp_path / "report.json"

    diagnostic.write_json_report(report, output_path)

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert list(loaded) == [
        "aggregate",
        "keys",
        "non_convergent_examples",
        "parameters",
        "selection",
    ]
    assert loaded["parameters"] == {
        "max_non_convergent_examples": 20,
        "requested_random_sample_size": 1,
        "sample_seed": 20261001,
    }
    assert loaded["keys"][0]["observed_askcos_smiles"] == ["CCO", "OCC"]


def test_read_conflict_tsv_validates_exact_columns(tmp_path):
    path = tmp_path / "conflicts.tsv"
    path.write_text(
        "\t".join(diagnostic.EXPECTED_CONFLICT_FIELDS)
        + "\n"
        + "\t".join(
            [
                _key(1),
                "representable",
                "CCO",
                "",
                "representable",
                "OCC",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert diagnostic.read_conflict_tsv(path) == [
        _row(_key(1), "CCO", "OCC")
    ]
