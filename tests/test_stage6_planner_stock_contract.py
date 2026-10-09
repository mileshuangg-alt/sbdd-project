import pytest

from evaluation.stage6_planner_stock_contract import (
    read_frozen_identity_record,
)


def _valid_row():
    return {
        "smiles": "C[C@H](O)C(=O)O",
        "zinc_id": "ZINC000000000001",
        "zinc_inchikey": "JVTAAEKCZFNVCJ-REOHCLBHSA-N",
        "d026_inchikey": "JVTAAEKCZFNVCJ-REOHCLBHSA-N",
        "full_key_match": "True",
        "connectivity_match": "True",
        "source_file": "example_source.txt",
        "source_line_number": "42",
    }


def test_read_frozen_identity_record_preserves_authoritative_fields_exactly():
    row = _valid_row()

    result = read_frozen_identity_record(row)

    assert result["smiles"] == row["smiles"]
    assert result["d026_inchikey"] == row["d026_inchikey"]
    assert result["zinc_id"] == row["zinc_id"]
    assert result["source_file"] == row["source_file"]
    assert result["source_line_number"] == row["source_line_number"]


def test_read_frozen_identity_record_does_not_replace_d026_identity_with_zinc_key():
    row = _valid_row()
    row["zinc_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"

    result = read_frozen_identity_record(row)

    assert result["d026_inchikey"] == "JVTAAEKCZFNVCJ-REOHCLBHSA-N"
    assert result["zinc_inchikey"] == "AAAAAAAAAAAAAA-BBBBBBBBBB-C"


def test_read_frozen_identity_record_preserves_smiles_without_normalization():
    row = _valid_row()
    row["smiles"] = "C[C@@H](O)C(=O)O"

    result = read_frozen_identity_record(row)

    assert result["smiles"] == "C[C@@H](O)C(=O)O"


def test_read_frozen_identity_record_rejects_missing_required_field():
    row = _valid_row()
    del row["d026_inchikey"]

    with pytest.raises(
        ValueError,
        match="missing required frozen-source field",
    ):
        read_frozen_identity_record(row)


@pytest.mark.parametrize(
    "bad_key",
    [
        "",
        "NOT_AN_INCHIKEY",
        "JVTAAEKCZFNVCJ",
        "jvtaaekczfnvcj-reohclbhsa-n",
    ],
)
def test_read_frozen_identity_record_rejects_invalid_d026_key(bad_key):
    row = _valid_row()
    row["d026_inchikey"] = bad_key

    with pytest.raises(ValueError):
        read_frozen_identity_record(row)


@pytest.mark.parametrize("bad_smiles", ["", None])
def test_read_frozen_identity_record_rejects_empty_or_non_string_smiles(
    bad_smiles,
):
    row = _valid_row()
    row["smiles"] = bad_smiles

    with pytest.raises(
        ValueError,
        match="SMILES must be a non-empty string",
    ):
        read_frozen_identity_record(row)


def test_measure_d026_identity_inventory_counts_all_unique_records():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
    )

    rows = []

    for key in (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
    ):
        row = _valid_row()
        row["d026_inchikey"] = key
        rows.append(row)

    connection = sqlite3.connect(":memory:")
    result = measure_d026_identity_inventory(rows, connection)

    assert result == {
        "total_records": 3,
        "unique_d026_keys": 3,
        "duplicate_rows": 0,
        "duplicate_d026_keys": 0,
    }


def test_measure_d026_identity_inventory_counts_repeated_authoritative_key():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
    )

    row_a = _valid_row()

    row_b = _valid_row()
    row_b["zinc_id"] = "ZINC000000000002"

    row_c = _valid_row()
    row_c["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"

    connection = sqlite3.connect(":memory:")
    result = measure_d026_identity_inventory(
        [row_a, row_b, row_c],
        connection,
    )

    assert result == {
        "total_records": 3,
        "unique_d026_keys": 2,
        "duplicate_rows": 1,
        "duplicate_d026_keys": 1,
    }


def test_measure_d026_identity_inventory_distinguishes_duplicate_rows_from_duplicate_keys():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
    )

    rows = []

    for zinc_id in (
        "ZINC000000000001",
        "ZINC000000000002",
        "ZINC000000000003",
    ):
        row = _valid_row()
        row["zinc_id"] = zinc_id
        rows.append(row)

    other = _valid_row()
    other["zinc_id"] = "ZINC000000000004"
    other["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    rows.append(other)

    connection = sqlite3.connect(":memory:")
    result = measure_d026_identity_inventory(rows, connection)

    assert result == {
        "total_records": 4,
        "unique_d026_keys": 2,
        "duplicate_rows": 2,
        "duplicate_d026_keys": 1,
    }


def test_measure_d026_identity_inventory_ignores_historical_zinc_key_for_identity():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
    )

    row_a = _valid_row()

    row_b = _valid_row()
    row_b["zinc_id"] = "ZINC000000000002"
    row_b["zinc_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"

    connection = sqlite3.connect(":memory:")
    result = measure_d026_identity_inventory(
        [row_a, row_b],
        connection,
    )

    assert result == {
        "total_records": 2,
        "unique_d026_keys": 1,
        "duplicate_rows": 1,
        "duplicate_d026_keys": 1,
    }


def test_write_d026_duplicate_identity_report_is_complete_and_deterministic(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
        write_d026_duplicate_identity_report,
    )

    rows = []

    for key, count in (
        ("FFFFFFFFFFFFFF-GGGGGGGGGG-H", 2),
        ("AAAAAAAAAAAAAA-BBBBBBBBBB-C", 3),
        ("CCCCCCCCCCCCCC-DDDDDDDDDD-E", 1),
    ):
        for index in range(count):
            row = _valid_row()
            row["d026_inchikey"] = key
            row["zinc_id"] = f"ZINC{key[:4]}{index}"
            rows.append(row)

    connection = sqlite3.connect(":memory:")
    measure_d026_identity_inventory(rows, connection)

    output_path = tmp_path / "duplicate_d026_identities.tsv"

    result = write_d026_duplicate_identity_report(
        connection,
        output_path,
    )

    assert result == {
        "duplicate_d026_keys": 2,
        "represented_source_rows": 5,
    }

    assert output_path.read_text() == (
        "d026_inchikey\toccurrence_count\n"
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\t3\n"
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H\t2\n"
    )


def test_write_d026_duplicate_identity_report_writes_header_only_when_unique(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
        write_d026_duplicate_identity_report,
    )

    rows = []

    for key in (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
    ):
        row = _valid_row()
        row["d026_inchikey"] = key
        rows.append(row)

    connection = sqlite3.connect(":memory:")
    measure_d026_identity_inventory(rows, connection)

    output_path = tmp_path / "duplicate_d026_identities.tsv"

    result = write_d026_duplicate_identity_report(
        connection,
        output_path,
    )

    assert result == {
        "duplicate_d026_keys": 0,
        "represented_source_rows": 0,
    }

    assert output_path.read_text() == (
        "d026_inchikey\toccurrence_count\n"
    )


def test_write_aizynthfinder_d026_key_stock_is_unique_and_deterministic(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
        write_aizynthfinder_d026_key_stock,
    )

    rows = []

    for key in (
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
    ):
        row = _valid_row()
        row["d026_inchikey"] = key
        rows.append(row)

    connection = sqlite3.connect(":memory:")
    inventory = measure_d026_identity_inventory(rows, connection)

    output_path = tmp_path / "aizynthfinder_d026_stock.txt"

    result = write_aizynthfinder_d026_key_stock(
        connection,
        output_path,
    )

    assert inventory == {
        "total_records": 4,
        "unique_d026_keys": 3,
        "duplicate_rows": 1,
        "duplicate_d026_keys": 1,
    }

    assert result == {
        "stock_keys_written": 3,
    }

    assert output_path.read_text() == (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\n"
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E\n"
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H\n"
    )


def test_write_aizynthfinder_d026_key_stock_preserves_full_stereo_sensitive_keys(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_d026_identity_inventory,
        write_aizynthfinder_d026_key_stock,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"

    connection = sqlite3.connect(":memory:")
    measure_d026_identity_inventory(
        [row_a, row_b],
        connection,
    )

    output_path = tmp_path / "aizynthfinder_d026_stock.txt"

    result = write_aizynthfinder_d026_key_stock(
        connection,
        output_path,
    )

    assert result == {
        "stock_keys_written": 2,
    }

    assert output_path.read_text() == (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\n"
        "AAAAAAAAAAAAAA-CCCCCCCCCC-D\n"
    )


def test_compute_d026_identity_set_sha256_is_order_and_multiplicity_invariant():
    import hashlib
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        compute_d026_identity_set_sha256,
        measure_d026_identity_inventory,
    )

    rows = []

    for key in (
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
    ):
        row = _valid_row()
        row["d026_inchikey"] = key
        rows.append(row)

    connection = sqlite3.connect(":memory:")
    measure_d026_identity_inventory(rows, connection)

    result = compute_d026_identity_set_sha256(connection)

    expected_serialization = (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\n"
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E\n"
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H\n"
    ).encode("utf-8")

    assert result == {
        "identity_count": 3,
        "identity_set_sha256": hashlib.sha256(
            expected_serialization
        ).hexdigest(),
    }


def test_compute_d026_identity_set_sha256_preserves_full_key_distinctions():
    import hashlib
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        compute_d026_identity_set_sha256,
        measure_d026_identity_inventory,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"

    connection = sqlite3.connect(":memory:")
    measure_d026_identity_inventory(
        [row_b, row_a],
        connection,
    )

    result = compute_d026_identity_set_sha256(connection)

    expected_serialization = (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\n"
        "AAAAAAAAAAAAAA-CCCCCCCCCC-D\n"
    ).encode("utf-8")

    assert result == {
        "identity_count": 2,
        "identity_set_sha256": hashlib.sha256(
            expected_serialization
        ).hexdigest(),
    }


def test_make_askcos_representation_result_records_success_without_redefining_identity():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTABLE,
        make_askcos_representation_result,
    )

    row = _valid_row()

    result = make_askcos_representation_result(
        row,
        status=ASKCOS_STATUS_REPRESENTABLE,
        canonical_smiles="C[C@H](O)C(=O)O",
    )

    assert result == {
        "d026_inchikey": row["d026_inchikey"],
        "source_smiles": row["smiles"],
        "askcos_status": "representable",
        "canonical_smiles": "C[C@H](O)C(=O)O",
        "representation_failure_reason": None,
    }


def test_make_askcos_representation_result_records_documented_failure():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        make_askcos_representation_result,
    )

    row = _valid_row()

    result = make_askcos_representation_result(
        row,
        status=ASKCOS_STATUS_REPRESENTATION_FAILURE,
        failure_reason="ASKCOS_PARSE_FAILURE",
    )

    assert result == {
        "d026_inchikey": row["d026_inchikey"],
        "source_smiles": row["smiles"],
        "askcos_status": "representation_failure",
        "canonical_smiles": None,
        "representation_failure_reason": "ASKCOS_PARSE_FAILURE",
    }


def test_make_askcos_representation_result_rejects_ambiguous_success_failure_state():
    import pytest

    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTABLE,
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        make_askcos_representation_result,
    )

    row = _valid_row()

    with pytest.raises(
        ValueError,
        match="requires non-empty canonical SMILES",
    ):
        make_askcos_representation_result(
            row,
            status=ASKCOS_STATUS_REPRESENTABLE,
        )

    with pytest.raises(
        ValueError,
        match="cannot carry canonical SMILES",
    ):
        make_askcos_representation_result(
            row,
            status=ASKCOS_STATUS_REPRESENTATION_FAILURE,
            canonical_smiles="CCO",
            failure_reason="FAILURE",
        )


def test_make_askcos_representation_result_reserves_collision_for_dataset_pass():
    import pytest

    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED,
        make_askcos_representation_result,
    )

    row = _valid_row()

    with pytest.raises(
        ValueError,
        match="dataset-level collision pass",
    ):
        make_askcos_representation_result(
            row,
            status=ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED,
            canonical_smiles="CCO",
        )


def test_canonicalize_askcos_smiles_canonicalizes_without_removing_stereo():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTABLE,
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "OC[C@H](C)N"

    result = canonicalize_askcos_smiles(row)

    assert result["d026_inchikey"] == row["d026_inchikey"]
    assert result["source_smiles"] == row["smiles"]
    assert result["askcos_status"] == ASKCOS_STATUS_REPRESENTABLE
    assert result["canonical_smiles"] != ""
    assert "@" in result["canonical_smiles"]
    assert result["representation_failure_reason"] is None


def test_canonicalize_askcos_smiles_is_input_order_invariant():
    from rdkit import Chem

    from evaluation.stage6_planner_stock_contract import (
        canonicalize_askcos_smiles,
    )

    row_a = _valid_row()
    row_a["smiles"] = "C1=CC=CC=C1O"

    row_b = _valid_row()
    row_b["smiles"] = "Oc1ccccc1"

    result_a = canonicalize_askcos_smiles(row_a)
    result_b = canonicalize_askcos_smiles(row_b)

    assert result_a["askcos_status"] == "representable"
    assert result_b["askcos_status"] == "representable"
    assert result_a["canonical_smiles"] == result_b["canonical_smiles"]

    assert Chem.MolFromSmiles(
        result_a["canonical_smiles"]
    ) is not None


def test_canonicalize_askcos_smiles_rejects_multiple_components_without_fragment_selection():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "CCO.CN"

    result = canonicalize_askcos_smiles(row)

    assert result == {
        "d026_inchikey": row["d026_inchikey"],
        "source_smiles": "CCO.CN",
        "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
        "canonical_smiles": None,
        "representation_failure_reason": "ASKCOS_MULTIPLE_COMPONENTS:2",
    }


def test_canonicalize_askcos_smiles_records_parse_failure_without_substitution():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "C1("

    result = canonicalize_askcos_smiles(row)

    assert result["d026_inchikey"] == row["d026_inchikey"]
    assert result["source_smiles"] == "C1("
    assert result["askcos_status"] == ASKCOS_STATUS_REPRESENTATION_FAILURE
    assert result["canonical_smiles"] is None
    assert result["representation_failure_reason"] == "ASKCOS_PARSE_FAILURE"


def test_canonicalize_askcos_smiles_does_not_strip_component_as_identity_normalization():
    from evaluation.stage6_planner_stock_contract import (
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "[Na+].[O-]C(=O)C"

    result = canonicalize_askcos_smiles(row)

    assert result["askcos_status"] == "representation_failure"
    assert result["canonical_smiles"] is None
    assert result["source_smiles"] == "[Na+].[O-]C(=O)C"


def test_canonicalize_askcos_smiles_preserves_authoritative_d026_identity():
    from evaluation.stage6_planner_stock_contract import (
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row["zinc_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"

    result = canonicalize_askcos_smiles(row)

    assert result["d026_inchikey"] == (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    )
    assert result["d026_inchikey"] != row["zinc_inchikey"]


def test_canonicalize_askcos_smiles_canonicalizes_without_removing_stereo():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTABLE,
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "OC[C@H](C)N"

    result = canonicalize_askcos_smiles(row)

    assert result["d026_inchikey"] == row["d026_inchikey"]
    assert result["source_smiles"] == row["smiles"]
    assert result["askcos_status"] == ASKCOS_STATUS_REPRESENTABLE
    assert result["canonical_smiles"] != ""
    assert "@" in result["canonical_smiles"]
    assert result["representation_failure_reason"] is None


def test_canonicalize_askcos_smiles_is_input_order_invariant():
    from rdkit import Chem

    from evaluation.stage6_planner_stock_contract import (
        canonicalize_askcos_smiles,
    )

    row_a = _valid_row()
    row_a["smiles"] = "C1=CC=CC=C1O"

    row_b = _valid_row()
    row_b["smiles"] = "Oc1ccccc1"

    result_a = canonicalize_askcos_smiles(row_a)
    result_b = canonicalize_askcos_smiles(row_b)

    assert result_a["askcos_status"] == "representable"
    assert result_b["askcos_status"] == "representable"
    assert result_a["canonical_smiles"] == result_b["canonical_smiles"]

    assert Chem.MolFromSmiles(
        result_a["canonical_smiles"]
    ) is not None


def test_canonicalize_askcos_smiles_rejects_multiple_components_without_fragment_selection():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "CCO.CN"

    result = canonicalize_askcos_smiles(row)

    assert result == {
        "d026_inchikey": row["d026_inchikey"],
        "source_smiles": "CCO.CN",
        "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
        "canonical_smiles": None,
        "representation_failure_reason": "ASKCOS_MULTIPLE_COMPONENTS:2",
    }


def test_canonicalize_askcos_smiles_records_parse_failure_without_substitution():
    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "C1("

    result = canonicalize_askcos_smiles(row)

    assert result["d026_inchikey"] == row["d026_inchikey"]
    assert result["source_smiles"] == "C1("
    assert result["askcos_status"] == ASKCOS_STATUS_REPRESENTATION_FAILURE
    assert result["canonical_smiles"] is None
    assert result["representation_failure_reason"] == "ASKCOS_PARSE_FAILURE"


def test_canonicalize_askcos_smiles_does_not_strip_component_as_identity_normalization():
    from evaluation.stage6_planner_stock_contract import (
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["smiles"] = "[Na+].[O-]C(=O)C"

    result = canonicalize_askcos_smiles(row)

    assert result["askcos_status"] == "representation_failure"
    assert result["canonical_smiles"] is None
    assert result["source_smiles"] == "[Na+].[O-]C(=O)C"


def test_canonicalize_askcos_smiles_preserves_authoritative_d026_identity():
    from evaluation.stage6_planner_stock_contract import (
        canonicalize_askcos_smiles,
    )

    row = _valid_row()
    row["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row["zinc_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"

    result = canonicalize_askcos_smiles(row)

    assert result["d026_inchikey"] == (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    )
    assert result["d026_inchikey"] != row["zinc_inchikey"]


def test_measure_askcos_canonical_collisions_detects_distinct_d026_keys(
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "OCC"

    row_c = _valid_row()
    row_c["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    row_c["smiles"] = "CCN"

    connection = sqlite3.connect(":memory:")

    result = measure_askcos_canonical_collisions(
        [row_a, row_b, row_c],
        connection,
    )

    assert result == {
        "total_source_records": 3,
        "representable_source_records": 3,
        "representation_failure_records": 0,
        "distinct_representable_d026_keys": 3,
        "collision_canonical_smiles": 1,
        "collision_d026_keys": 2,
    }


def test_measure_askcos_canonical_collisions_does_not_call_same_key_duplicate_a_collision():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_b["zinc_id"] = "ZINC000000000002"
    row_b["smiles"] = "OCC"

    connection = sqlite3.connect(":memory:")

    result = measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    assert result == {
        "total_source_records": 2,
        "representable_source_records": 2,
        "representation_failure_records": 0,
        "distinct_representable_d026_keys": 1,
        "collision_canonical_smiles": 0,
        "collision_d026_keys": 0,
    }


def test_measure_askcos_canonical_collisions_excludes_representation_failures():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "CCO.CN"

    connection = sqlite3.connect(":memory:")

    result = measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    assert result == {
        "total_source_records": 2,
        "representable_source_records": 1,
        "representation_failure_records": 1,
        "distinct_representable_d026_keys": 1,
        "collision_canonical_smiles": 0,
        "collision_d026_keys": 0,
    }


def test_measure_askcos_canonical_collisions_separates_distinct_canonical_smiles():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "CCN"

    connection = sqlite3.connect(":memory:")

    result = measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    assert result == {
        "total_source_records": 2,
        "representable_source_records": 2,
        "representation_failure_records": 0,
        "distinct_representable_d026_keys": 2,
        "collision_canonical_smiles": 0,
        "collision_d026_keys": 0,
    }


def test_measure_askcos_canonical_collisions_does_not_use_connectivity_prefix_as_identity():
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"
    row_b["smiles"] = "CCN"

    connection = sqlite3.connect(":memory:")

    result = measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    assert result["distinct_representable_d026_keys"] == 2
    assert result["collision_d026_keys"] == 0


def test_write_askcos_collision_exclusion_report_is_complete_and_deterministic(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_collision_exclusion_report,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    row_a["smiles"] = "CCN"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_b["smiles"] = "CCO"

    row_c = _valid_row()
    row_c["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_c["smiles"] = "OCC"

    row_d = _valid_row()
    row_d["d026_inchikey"] = "HHHHHHHHHHHHHH-IIIIIIIIII-J"
    row_d["smiles"] = "CCN"

    connection = sqlite3.connect(":memory:")

    measure_askcos_canonical_collisions(
        [row_a, row_b, row_c, row_d],
        connection,
    )

    output_path = tmp_path / "askcos_collision_exclusions.tsv"

    result = write_askcos_collision_exclusion_report(
        connection,
        output_path,
    )

    assert result == {
        "collision_canonical_smiles": 2,
        "collision_d026_keys": 4,
    }

    assert output_path.read_text() == (
        "canonical_smiles\td026_inchikey\n"
        "CCN\tFFFFFFFFFFFFFF-GGGGGGGGGG-H\n"
        "CCN\tHHHHHHHHHHHHHH-IIIIIIIIII-J\n"
        "CCO\tAAAAAAAAAAAAAA-BBBBBBBBBB-C\n"
        "CCO\tCCCCCCCCCCCCCC-DDDDDDDDDD-E\n"
    )


def test_write_askcos_collision_exclusion_report_is_header_only_without_collisions(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_collision_exclusion_report,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "CCN"

    connection = sqlite3.connect(":memory:")

    measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    output_path = tmp_path / "askcos_collision_exclusions.tsv"

    result = write_askcos_collision_exclusion_report(
        connection,
        output_path,
    )

    assert result == {
        "collision_canonical_smiles": 0,
        "collision_d026_keys": 0,
    }

    assert output_path.read_text() == (
        "canonical_smiles\td026_inchikey\n"
    )


def test_write_askcos_collision_exclusion_report_does_not_include_representation_failures(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_collision_exclusion_report,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "CCO.CN"

    connection = sqlite3.connect(":memory:")

    measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    output_path = tmp_path / "askcos_collision_exclusions.tsv"

    result = write_askcos_collision_exclusion_report(
        connection,
        output_path,
    )

    assert result == {
        "collision_canonical_smiles": 0,
        "collision_d026_keys": 0,
    }

    assert output_path.read_text() == (
        "canonical_smiles\td026_inchikey\n"
    )


def test_write_askcos_qualified_stock_excludes_entire_collision_group(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_qualified_stock,
    )

    collision_a = _valid_row()
    collision_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    collision_a["smiles"] = "CCO"

    collision_b = _valid_row()
    collision_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    collision_b["smiles"] = "OCC"

    qualified = _valid_row()
    qualified["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    qualified["smiles"] = "CCN"

    connection = sqlite3.connect(":memory:")

    collision_result = measure_askcos_canonical_collisions(
        [collision_a, collision_b, qualified],
        connection,
    )

    assert collision_result["collision_canonical_smiles"] == 1
    assert collision_result["collision_d026_keys"] == 2

    output_path = tmp_path / "askcos_qualified_stock.tsv"

    result = write_askcos_qualified_stock(
        connection,
        output_path,
    )

    assert result == {
        "qualified_d026_keys": 1,
        "qualified_canonical_smiles": 1,
    }

    assert output_path.read_text() == (
        "d026_inchikey\tcanonical_smiles\n"
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H\tCCN\n"
    )


def test_write_askcos_qualified_stock_is_deterministically_sorted(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_qualified_stock,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    row_a["smiles"] = "CCN"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_b["smiles"] = "CCO"

    row_c = _valid_row()
    row_c["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_c["smiles"] = "CCCl"

    connection = sqlite3.connect(":memory:")

    measure_askcos_canonical_collisions(
        [row_a, row_b, row_c],
        connection,
    )

    output_path = tmp_path / "askcos_qualified_stock.tsv"

    result = write_askcos_qualified_stock(
        connection,
        output_path,
    )

    assert result == {
        "qualified_d026_keys": 3,
        "qualified_canonical_smiles": 3,
    }

    assert output_path.read_text() == (
        "d026_inchikey\tcanonical_smiles\n"
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\tCCO\n"
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E\tCCCl\n"
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H\tCCN\n"
    )


def test_write_askcos_qualified_stock_has_no_entries_when_all_are_collisions(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_qualified_stock,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "OCC"

    connection = sqlite3.connect(":memory:")

    measure_askcos_canonical_collisions(
        [row_a, row_b],
        connection,
    )

    output_path = tmp_path / "askcos_qualified_stock.tsv"

    result = write_askcos_qualified_stock(
        connection,
        output_path,
    )

    assert result == {
        "qualified_d026_keys": 0,
        "qualified_canonical_smiles": 0,
    }

    assert output_path.read_text() == (
        "d026_inchikey\tcanonical_smiles\n"
    )


def test_write_askcos_qualified_stock_never_converts_representation_failure_into_stock(
    tmp_path,
):
    import sqlite3

    from evaluation.stage6_planner_stock_contract import (
        measure_askcos_canonical_collisions,
        write_askcos_qualified_stock,
    )

    representable = _valid_row()
    representable["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    representable["smiles"] = "CCO"

    failure = _valid_row()
    failure["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    failure["smiles"] = "CCO.CN"

    connection = sqlite3.connect(":memory:")

    result_measurement = measure_askcos_canonical_collisions(
        [representable, failure],
        connection,
    )

    assert result_measurement == {
        "total_source_records": 2,
        "representable_source_records": 1,
        "representation_failure_records": 1,
        "distinct_representable_d026_keys": 1,
        "collision_canonical_smiles": 0,
        "collision_d026_keys": 0,
    }

    output_path = tmp_path / "askcos_qualified_stock.tsv"

    result = write_askcos_qualified_stock(
        connection,
        output_path,
    )

    assert result == {
        "qualified_d026_keys": 1,
        "qualified_canonical_smiles": 1,
    }

    assert "CCCCCCCCCCCCCC-DDDDDDDDDD-E" not in (
        output_path.read_text()
    )


def test_build_askcos_identity_accounting_forms_complete_partition():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
    )

    collision_a = _valid_row()
    collision_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    collision_a["smiles"] = "CCO"

    collision_b = _valid_row()
    collision_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    collision_b["smiles"] = "OCC"

    failure = _valid_row()
    failure["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    failure["smiles"] = "CCO.CN"

    qualified = _valid_row()
    qualified["d026_inchikey"] = "HHHHHHHHHHHHHH-IIIIIIIIII-J"
    qualified["smiles"] = "CCN"

    records, summary = build_askcos_identity_accounting(
        [collision_a, collision_b, failure, qualified]
    )

    assert summary == {
        "unique_frozen_d026_keys": 4,
        "representation_failure_keys": 1,
        "canonical_collision_excluded_keys": 2,
        "qualified_keys": 1,
    }

    assert [
        record["d026_inchikey"]
        for record in records
    ] == [
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
        "HHHHHHHHHHHHHH-IIIIIIIIII-J",
    ]

    status_by_key = {
        record["d026_inchikey"]: record["askcos_status"]
        for record in records
    }

    assert status_by_key == {
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C":
            "canonical_collision_excluded",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E":
            "canonical_collision_excluded",
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H":
            "representation_failure",
        "HHHHHHHHHHHHHH-IIIIIIIIII-J":
            "qualified",
    }


def test_build_askcos_identity_accounting_collapses_source_duplicates():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_b["zinc_id"] = "ZINC000000000002"
    row_b["smiles"] = "OCC"

    row_c = _valid_row()
    row_c["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_c["smiles"] = "CCN"

    records, summary = build_askcos_identity_accounting(
        [row_a, row_b, row_c]
    )

    assert summary == {
        "unique_frozen_d026_keys": 2,
        "representation_failure_keys": 0,
        "canonical_collision_excluded_keys": 0,
        "qualified_keys": 2,
    }

    assert len(records) == 2
    assert {
        record["d026_inchikey"]
        for record in records
    } == {
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
    }


def test_build_askcos_identity_accounting_never_classifies_failure_as_collision():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
    )

    failure_a = _valid_row()
    failure_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    failure_a["smiles"] = "CCO.CN"

    failure_b = _valid_row()
    failure_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    failure_b["smiles"] = "CCO.CN"

    records, summary = build_askcos_identity_accounting(
        [failure_a, failure_b]
    )

    assert summary == {
        "unique_frozen_d026_keys": 2,
        "representation_failure_keys": 2,
        "canonical_collision_excluded_keys": 0,
        "qualified_keys": 0,
    }

    assert all(
        record["askcos_status"] == "representation_failure"
        for record in records
    )


def test_build_askcos_identity_accounting_preserves_full_d026_identity():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"
    row_b["smiles"] = "CCN"

    records, summary = build_askcos_identity_accounting(
        [row_a, row_b]
    )

    assert summary["unique_frozen_d026_keys"] == 2
    assert summary["qualified_keys"] == 2

    assert {
        record["d026_inchikey"]
        for record in records
    } == {
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        "AAAAAAAAAAAAAA-CCCCCCCCCC-D",
    }


def test_write_askcos_identity_accounting_report_is_complete_and_deterministic(
    tmp_path,
):
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
        write_askcos_identity_accounting_report,
    )

    collision_a = _valid_row()
    collision_a["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    collision_a["smiles"] = "CCO"

    collision_b = _valid_row()
    collision_b["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    collision_b["smiles"] = "OCC"

    failure = _valid_row()
    failure["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    failure["smiles"] = "CCO.CN"

    qualified = _valid_row()
    qualified["d026_inchikey"] = "HHHHHHHHHHHHHH-IIIIIIIIII-J"
    qualified["smiles"] = "CCN"

    accounting_records, _ = build_askcos_identity_accounting(
        [collision_a, collision_b, failure, qualified]
    )

    output_path = tmp_path / "askcos_identity_accounting.tsv"

    result = write_askcos_identity_accounting_report(
        accounting_records,
        output_path,
    )

    assert result == {
        "total_d026_keys": 4,
        "representation_failure_keys": 1,
        "canonical_collision_excluded_keys": 2,
        "qualified_keys": 1,
    }

    assert output_path.read_text() == (
        "d026_inchikey\taskcos_status\tcanonical_smiles\t"
        "representation_failure_reason\n"
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\t"
        "canonical_collision_excluded\tCCO\t\n"
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E\t"
        "canonical_collision_excluded\tCCO\t\n"
        "FFFFFFFFFFFFFF-GGGGGGGGGG-H\t"
        "representation_failure\t\t"
        "ASKCOS_MULTIPLE_COMPONENTS:2\n"
        "HHHHHHHHHHHHHH-IIIIIIIIII-J\t"
        "qualified\tCCN\t\n"
    )


def test_write_askcos_identity_accounting_report_rejects_duplicate_keys(
    tmp_path,
):
    import pytest

    from evaluation.stage6_planner_stock_contract import (
        write_askcos_identity_accounting_report,
    )

    duplicate_records = [
        {
            "d026_inchikey": "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "askcos_status": "qualified",
            "canonical_smiles": "CCO",
            "representation_failure_reason": None,
        },
        {
            "d026_inchikey": "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "askcos_status": "qualified",
            "canonical_smiles": "CCO",
            "representation_failure_reason": None,
        },
    ]

    with pytest.raises(
        ValueError,
        match="duplicate D026 key",
    ):
        write_askcos_identity_accounting_report(
            duplicate_records,
            tmp_path / "accounting.tsv",
        )


def test_write_askcos_identity_accounting_report_rejects_invalid_failure_row(
    tmp_path,
):
    import pytest

    from evaluation.stage6_planner_stock_contract import (
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        write_askcos_identity_accounting_report,
    )

    invalid_record = [
        {
            "d026_inchikey": "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
            "canonical_smiles": "CCO",
            "representation_failure_reason": None,
        }
    ]

    with pytest.raises(
        ValueError,
        match="representation failure cannot contain canonical SMILES",
    ):
        write_askcos_identity_accounting_report(
            invalid_record,
            tmp_path / "accounting.tsv",
        )


def test_compute_askcos_identity_sets_and_proof_passes_for_equal_representable_sets():
    import hashlib

    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
        compute_askcos_identity_sets_and_proof,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "CCN"

    failure = _valid_row()
    failure["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    failure["smiles"] = "CCO.CN"

    accounting_records, summary = build_askcos_identity_accounting(
        [row_a, row_b, failure]
    )

    assert summary == {
        "unique_frozen_d026_keys": 3,
        "representation_failure_keys": 1,
        "canonical_collision_excluded_keys": 0,
        "qualified_keys": 2,
    }

    result = compute_askcos_identity_sets_and_proof(
        accounting_records,
        [
            "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
            "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
        ],
    )

    expected_representable = (
        "AAAAAAAAAAAAAA-BBBBBBBBBB-C\n"
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E\n"
    ).encode("utf-8")

    assert result["frozen_count"] == 3
    assert result["representation_failure_count"] == 1
    assert result["collision_excluded_count"] == 0
    assert result["qualified_count"] == 2
    assert result["representable_count"] == 2
    assert result["aizynthfinder_count"] == 2

    assert result["aizynthfinder_only_count"] == 0
    assert result["representable_only_count"] == 0

    assert result["representable_set_equality_pass"] is True

    assert result["representable_set_sha256"] == hashlib.sha256(
        expected_representable
    ).hexdigest()

    assert result["aizynthfinder_set_sha256"] == (
        result["representable_set_sha256"]
    )


def test_compute_askcos_identity_sets_and_proof_treats_collision_exclusions_as_representable(
):
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
        compute_askcos_identity_sets_and_proof,
    )

    collision_a = _valid_row()
    collision_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    collision_a["smiles"] = "CCO"

    collision_b = _valid_row()
    collision_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    collision_b["smiles"] = "OCC"

    qualified = _valid_row()
    qualified["d026_inchikey"] = "FFFFFFFFFFFFFF-GGGGGGGGGG-H"
    qualified["smiles"] = "CCN"

    accounting_records, _ = build_askcos_identity_accounting(
        [collision_a, collision_b, qualified]
    )

    result = compute_askcos_identity_sets_and_proof(
        accounting_records,
        [
            "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
            "FFFFFFFFFFFFFF-GGGGGGGGGG-H",
        ],
    )

    assert result["frozen_count"] == 3
    assert result["collision_excluded_count"] == 2
    assert result["qualified_count"] == 1
    assert result["representable_count"] == 3

    assert result["representable_set_equality_pass"] is True


def test_compute_askcos_identity_sets_and_proof_fails_on_missing_representable_key():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
        compute_askcos_identity_sets_and_proof,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    row_b["smiles"] = "CCN"

    accounting_records, _ = build_askcos_identity_accounting(
        [row_a, row_b]
    )

    result = compute_askcos_identity_sets_and_proof(
        accounting_records,
        ["AAAAAAAAAAAAAA-BBBBBBBBBB-C"],
    )

    assert result["representable_set_equality_pass"] is False
    assert result["aizynthfinder_only_count"] == 0
    assert result["representable_only_count"] == 1
    assert result["representable_only_keys"] == [
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    ]


def test_compute_askcos_identity_sets_and_proof_fails_on_extra_aizynthfinder_key():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
        compute_askcos_identity_sets_and_proof,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    accounting_records, _ = build_askcos_identity_accounting(
        [row_a]
    )

    result = compute_askcos_identity_sets_and_proof(
        accounting_records,
        [
            "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "CCCCCCCCCCCCCC-DDDDDDDDDD-E",
        ],
    )

    assert result["representable_set_equality_pass"] is False
    assert result["aizynthfinder_only_count"] == 1
    assert result["representable_only_count"] == 0
    assert result["aizynthfinder_only_keys"] == [
        "CCCCCCCCCCCCCC-DDDDDDDDDD-E"
    ]


def test_compute_askcos_identity_sets_and_proof_never_uses_connectivity_prefix_as_identity():
    from evaluation.stage6_planner_stock_contract import (
        build_askcos_identity_accounting,
        compute_askcos_identity_sets_and_proof,
    )

    row_a = _valid_row()
    row_a["d026_inchikey"] = "AAAAAAAAAAAAAA-BBBBBBBBBB-C"
    row_a["smiles"] = "CCO"

    row_b = _valid_row()
    row_b["d026_inchikey"] = "AAAAAAAAAAAAAA-CCCCCCCCCC-D"
    row_b["smiles"] = "CCN"

    accounting_records, _ = build_askcos_identity_accounting(
        [row_a, row_b]
    )

    result = compute_askcos_identity_sets_and_proof(
        accounting_records,
        [
            "AAAAAAAAAAAAAA-BBBBBBBBBB-C",
            "AAAAAAAAAAAAAA-CCCCCCCCCC-D",
        ],
    )

    assert result["representable_count"] == 2
    assert result["aizynthfinder_count"] == 2
    assert result["representable_set_equality_pass"] is True
