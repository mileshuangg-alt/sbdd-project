import json

import pytest

import evaluation.stage6_d026_normalization_compatibility as compat


def _key(index):
    return f"{index:014d}-{index:010d}-A"


def _same_prefix_key(suffix):
    return f"ABCDEFGHIJKLMN-{suffix:010d}-A"


def _conflict_row(key, existing_smiles, new_smiles):
    return {
        "d026_inchikey": key,
        "existing_status": "representable",
        "existing_canonical_smiles": existing_smiles,
        "existing_failure_reason": "",
        "new_status": "representable",
        "new_canonical_smiles": new_smiles,
        "new_failure_reason": "",
    }


def _stock_source(keys_to_smiles):
    return {key: frozenset(smiles) for key, smiles in keys_to_smiles.items()}


def _mapped_normalizer(mapping):
    def normalize(smiles, rdkit_version):
        value = mapping.get(smiles, smiles)
        if value is None:
            return compat.NormalizationResult(smiles, "failure", None, "stub failure")
        return compat.NormalizationResult(
            smiles,
            "success",
            (rdkit_version, value),
            None,
        )

    return normalize


def _normalizers(mapping_a=None, mapping_b=None):
    return {
        "candidate_a": _mapped_normalizer(mapping_a or {}),
        "candidate_b": _mapped_normalizer(mapping_b or mapping_a or {}),
    }


def _small_report(conflict_rows, stock_source, normalizers=None, selected_key_count=None):
    if selected_key_count is None:
        selected_key_count = len(stock_source)
    return compat.build_report(
        conflict_rows=conflict_rows,
        d026_stock_record_count=sum(len(values) for values in stock_source.values()),
        d026_stock_distinct_keys=frozenset(stock_source),
        d026_stock_source_smiles_by_key=stock_source,
        conflict_file_path="conflicts.tsv",
        d026_stock_path="stock.tsv",
        conflict_file_sha256="c" * 64,
        d026_stock_sha256="d" * 64,
        utc_start_timestamp="2026-10-02T00:00:00Z",
        utc_end_timestamp="2026-10-02T00:00:01Z",
        selected_key_count=selected_key_count,
        rdkit_version="RDKit.TEST",
        normalizers=normalizers or _normalizers(),
    )


def test_full_27_character_d026_key_enforcement():
    with pytest.raises(ValueError, match="full 27-character"):
        compat.build_conflict_source_smiles_by_key(
            [_conflict_row("ABCDEFGHIJKLMN", "CCO", "OCC")]
        )

    with pytest.raises(ValueError, match="full 27-character"):
        compat.select_sampled_keys(["ABCDEFGHIJKLMN"], selected_key_count=1)


def test_evidence_groups_by_full_d026_key_not_first_14_characters():
    key_a = _same_prefix_key(1)
    key_b = _same_prefix_key(2)

    evidence = compat.build_conflict_source_smiles_by_key(
        [
            _conflict_row(key_a, "CCO", "OCC"),
            _conflict_row(key_b, "CCN", "NCC"),
        ]
    )

    assert sorted(evidence) == [key_a, key_b]
    assert evidence[key_a] == frozenset({"CCO", "OCC"})
    assert evidence[key_b] == frozenset({"CCN", "NCC"})


def test_row_order_invariance_for_report_accounting():
    rows = [
        _conflict_row(_key(1), "B", "A"),
        _conflict_row(_key(2), "D", "C"),
    ]
    stock_source = _stock_source({_key(1): {"A", "B"}, _key(2): {"C", "D"}})
    normalizers = _normalizers({"A": "X", "B": "X", "C": "Y", "D": "Z"})

    first = _small_report(rows, stock_source, normalizers)
    second = _small_report(list(reversed(rows)), stock_source, normalizers)

    assert first["candidates"] == second["candidates"]
    assert first["sampled_keys"] == second["sampled_keys"]
    assert first["candidate_selection"] == second["candidate_selection"]


def test_deterministic_sha256_key_sampling_matches_frozen_algorithm():
    keys = [_key(index) for index in range(8)]

    selected = compat.select_sampled_keys(reversed(keys), selected_key_count=4)

    expected = sorted(keys, key=lambda key: (compat.sampling_priority(key), key))[:4]
    assert selected == expected
    assert compat.sampling_priority(_key(1)) == compat.sampling_priority(_key(1))


def test_exact_20000_key_and_10000_pair_construction():
    keys = [_key(index) for index in range(20_000)]

    selected = compat.select_sampled_keys(keys, selected_key_count=20_000)
    pairs = compat.construct_adjacent_pairs_after_lexicographic_sort(selected)

    assert len(selected) == 20_000
    assert len(pairs) == 10_000


def test_adjacent_pairing_occurs_after_lexicographic_full_key_sorting():
    selected = [_key(4), _key(1), _key(3), _key(2)]

    assert compat.construct_adjacent_pairs_after_lexicographic_sort(selected) == [
        (_key(1), _key(2)),
        (_key(3), _key(4)),
    ]


def test_every_source_spelling_is_preserved_for_selected_key():
    report = _small_report(
        [_conflict_row(_key(1), "C", "C")],
        _stock_source({_key(1): {"B", "A"}, _key(2): {"D"}}),
        _normalizers({"A": "I1", "B": "I2", "D": "I3"}),
    )
    by_key = {entry["d026_inchikey"]: entry for entry in report["sampled_keys"]}

    assert by_key[_key(1)]["distinct_source_smiles_count"] == 2
    assert by_key[_key(1)]["source_smiles"] == ["A", "B"]
    assert by_key[_key(1)]["candidate_identity_sets"]["candidate_a"] == [
        {"rdkit_version": "RDKit.TEST", "canonical_isomeric_smiles": "I1"},
        {"rdkit_version": "RDKit.TEST", "canonical_isomeric_smiles": "I2"},
    ]


def test_false_merge_detection_uses_identity_set_intersections():
    results = compat.normalize_source_smiles_by_key(
        {_key(1): {"A", "B"}, _key(2): {"C"}, _key(3): {"D"}},
        _mapped_normalizer({"A": "X", "B": "Y", "C": "Y", "D": "Z"}),
        "RDKit.TEST",
    )

    failures = compat.detect_false_merge_pairs(results)

    assert failures == [
        {
            "d026_inchikey_a": _key(1),
            "d026_inchikey_b": _key(2),
            "intersecting_candidate_identities": [
                {"rdkit_version": "RDKit.TEST", "canonical_isomeric_smiles": "Y"}
            ],
        }
    ]


def test_false_split_detection_within_one_d026_key():
    results = compat.normalize_source_smiles_by_key(
        {_key(1): {"A", "B"}, _key(2): {"C", "D"}},
        _mapped_normalizer({"A": "X", "B": "X", "C": "Y", "D": "Z"}),
        "RDKit.TEST",
    )

    assert compat.detect_false_split_keys(results) == [_key(2)]


def test_candidate_a_normalization_pipeline(monkeypatch):
    calls = []

    class FakeChem:
        def MolFromSmiles(self, smiles):
            calls.append(("MolFromSmiles", smiles))
            return "mol"

        def MolToInchi(self, mol):
            calls.append(("MolToInchi", mol))
            return "InChI=1S/fake"

        def MolFromInchi(self, inchi):
            calls.append(("MolFromInchi", inchi))
            return "normalized"

        def MolToSmiles(self, mol, canonical, isomericSmiles):
            calls.append(("MolToSmiles", mol, canonical, isomericSmiles))
            return "canonical"

    monkeypatch.setattr(compat, "Chem", FakeChem())

    result = compat.candidate_a_normalize("input", "RDKit.TEST")

    assert calls == [
        ("MolFromSmiles", "input"),
        ("MolToInchi", "mol"),
        ("MolFromInchi", "InChI=1S/fake"),
        ("MolToSmiles", "normalized", True, True),
    ]
    assert result.identity == ("RDKit.TEST", "canonical")


def test_candidate_b_normalization_pipeline(monkeypatch):
    calls = []

    class FakeChem:
        def MolFromSmiles(self, smiles):
            calls.append(("MolFromSmiles", smiles))
            return "mol"

        def MolToSmiles(self, mol, canonical, isomericSmiles):
            calls.append(("MolToSmiles", mol, canonical, isomericSmiles))
            return "canonical"

    class FakeMolStandardize:
        def CleanupParameters(self):
            calls.append(("CleanupParameters",))
            return "params"

        def Cleanup(self, mol, params):
            calls.append(("Cleanup", mol, params))
            return "cleaned"

        def CanonicalTautomer(self, mol, params):
            calls.append(("CanonicalTautomer", mol, params))
            return "normalized"

    monkeypatch.setattr(compat, "Chem", FakeChem())
    monkeypatch.setattr(compat, "MolStandardize", FakeMolStandardize())

    result = compat.candidate_b_normalize("input", "RDKit.TEST")

    assert calls == [
        ("MolFromSmiles", "input"),
        ("CleanupParameters",),
        ("Cleanup", "mol", "params"),
        ("CanonicalTautomer", "cleaned", "params"),
        ("MolToSmiles", "normalized", True, True),
    ]
    assert result.identity == ("RDKit.TEST", "canonical")


def test_rdkit_version_is_recorded_in_candidate_identity_and_report():
    result = compat.candidate_a_normalize("CCO", "RDKit.VERSION.TEST")

    report = _small_report(
        [_conflict_row(_key(1), "CCO", "OCC")],
        _stock_source({_key(1): {"CCO"}, _key(2): {"CCN"}}),
        _normalizers({"CCO": "CCO", "OCC": "CCO", "CCN": "CCN"}),
    )

    assert result.identity[0] == "RDKit.VERSION.TEST"
    assert report["rdkit_version"] == "RDKit.TEST"
    assert "(RDKit version, canonical isomeric SMILES)" in report[
        "candidate_identity_statement"
    ]


def test_pass_fail_accounting():
    conflict_results = compat.normalize_source_smiles_by_key(
        {_key(1): {"A", "B"}, _key(2): {"C"}},
        _mapped_normalizer({"A": "X", "B": "Y", "C": "Y"}),
        "RDKit.TEST",
    )
    sample_results = compat.normalize_source_smiles_by_key(
        {_key(1): {"A"}, _key(2): {"C"}},
        _mapped_normalizer({"A": "X", "C": "Y"}),
        "RDKit.TEST",
    )

    report = compat.build_candidate_report(conflict_results, sample_results, [(_key(1), _key(2))])

    assert report["false_merge_count_conflicted"] == 1
    assert report["false_split_count_conflicted"] == 1
    assert report["false_merge_count_sample"] == 0
    assert report["conflicted_pass"] is False
    assert report["sample_pass"] is True
    assert report["overall_pass"] is False


def test_deterministic_report_structure_and_json_serialization(tmp_path):
    report = _small_report(
        [_conflict_row(_key(1), "A", "B")],
        _stock_source({_key(1): {"A"}, _key(2): {"C"}}),
        _normalizers({"A": "X", "B": "X", "C": "Y"}),
    )
    output = tmp_path / "report.json"

    compat.write_json_report(report, output)
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert list(loaded) == [
        "schema_version",
        "utc_start_timestamp",
        "utc_end_timestamp",
        "rdkit_version",
        "candidate_identity_statement",
        "candidate_definitions",
        "inputs",
        "sampling",
        "pass_criteria",
        "candidates",
        "candidate_selection",
        "sampled_keys",
        "sampled_pairs_with_detected_intersections",
    ]
    assert list(loaded["candidates"]) == ["candidate_a", "candidate_b"]


def test_rule_of_three_reporting_when_sample_has_zero_false_merges():
    report = _small_report(
        [_conflict_row(_key(1), "A", "A")],
        _stock_source({_key(1): {"A"}, _key(2): {"B"}}),
        _normalizers({"A": "X", "B": "Y"}),
    )

    bound = report["sampling"]["rule_of_three_upper_bound_when_zero_false_merges"]
    assert bound["formula"] == "3 / 10000"
    assert bound["value"] == pytest.approx(0.0003)
    assert bound["percent"] == pytest.approx(0.03)
    assert "not proof of zero false merges" in bound["statement"]


def test_no_representative_first_or_row_order_behavior():
    rows = [
        _conflict_row(_key(1), "FIRST", "SECOND"),
        _conflict_row(_key(2), "OTHER", "OTHER"),
    ]
    stock_source = _stock_source({_key(1): {"FIRST"}, _key(2): {"OTHER"}})
    normalizers = _normalizers({"FIRST": "X", "SECOND": "Y", "OTHER": "Z"})

    first = _small_report(rows, stock_source, normalizers)
    second = _small_report(list(reversed(rows)), stock_source, normalizers)

    assert first["candidates"]["candidate_a"]["false_split_count_conflicted"] == 1
    assert second["candidates"]["candidate_a"]["false_split_count_conflicted"] == 1
    assert first["candidates"] == second["candidates"]


def test_read_conflict_tsv_validates_exact_columns(tmp_path):
    path = tmp_path / "conflicts.tsv"
    path.write_text(
        "\t".join(compat.EXPECTED_CONFLICT_FIELDS)
        + "\n"
        + "\t".join([_key(1), "representable", "CCO", "", "representable", "OCC", ""])
        + "\n",
        encoding="utf-8",
    )

    assert compat.read_conflict_tsv(path) == [_conflict_row(_key(1), "CCO", "OCC")]


def test_stock_reader_collects_all_source_spellings_for_selected_key(tmp_path):
    path = tmp_path / "stock.tsv"
    header = sorted(compat.REQUIRED_D026_STOCK_FIELDS)

    def line(values):
        return "\t".join(values[field] for field in header)

    path.write_text(
        "\t".join(header)
        + "\n"
        + line(
            {
                "smiles": "CCO",
                "zinc_id": "ZINC1",
                "zinc_inchikey": "ZKEY1",
                "d026_inchikey": _key(1),
                "full_key_match": "True",
                "connectivity_match": "True",
                "source_file": "file",
                "source_line_number": "1",
            }
        )
        + "\n"
        + line(
            {
                "smiles": "OCC",
                "zinc_id": "ZINC2",
                "zinc_inchikey": "ZKEY2",
                "d026_inchikey": _key(1),
                "full_key_match": "True",
                "connectivity_match": "True",
                "source_file": "file",
                "source_line_number": "2",
            }
        )
        + "\n"
        + line(
            {
                "smiles": "CCN",
                "zinc_id": "ZINC3",
                "zinc_inchikey": "ZKEY3",
                "d026_inchikey": _key(2),
                "full_key_match": "True",
                "connectivity_match": "True",
                "source_file": "file",
                "source_line_number": "3",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    record_count, keys = compat.read_d026_stock_key_population(path)
    source = compat.collect_stock_source_smiles_for_keys(path, {_key(1)})

    assert record_count == 3
    assert keys == frozenset({_key(1), _key(2)})
    assert source == {_key(1): frozenset({"CCO", "OCC"})}
