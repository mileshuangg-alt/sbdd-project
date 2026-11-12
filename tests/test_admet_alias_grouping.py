import pytest

from admet.scripts import alias_grouping as aliases


def _record(identity, scaffold_key=None, family_key=None, failures=()):
    return {
        "id": identity,
        "alias_grouping": {
            "scaffold_key": scaffold_key,
            "family_key": family_key,
            "failures": failures,
        },
    }


def _assignments(records):
    return {
        assignment["identity"]: assignment
        for assignment in aliases.construct_alias_connected_components(records)
    }


def test_source_smiles_is_preserved_and_largest_fragment_is_selected():
    record = {"id": "example", "smiles": "CCO.CCCCCC"}

    output = aliases.add_alias_grouping_fields(record)

    assert output["smiles"] == "CCO.CCCCCC"
    assert output["alias_grouping"]["source_smiles"] == "CCO.CCCCCC"
    assert output["alias_grouping"]["largest_fragment_smiles"] == "CCCCCC"
    assert output["alias_grouping"]["largest_fragment_heavy_atom_count"] == 6
    assert output["alias_grouping"]["fragment_heavy_atom_counts"] == (3, 6)


def test_equal_largest_fragment_ties_are_failures():
    result = aliases.build_alias_grouping_result("CC.CN")

    assert result.failures == (aliases.FRAGMENT_AMBIGUITY,)
    assert result.largest_fragment_heavy_atom_count == 2
    assert result.fragment_heavy_atom_counts == (2, 2)
    assert result.scaffold_key is None
    assert result.family_key is None


def test_parse_failures_are_reported_without_keys():
    result = aliases.build_alias_grouping_result("not-a-valid-smiles")

    assert result.failures == (aliases.PARSE_FAILURE,)
    assert result.largest_fragment_smiles is None
    assert result.scaffold_key is None
    assert result.family_key is None


def test_empty_fragment_result_is_no_fragments_not_parse_failure(monkeypatch):
    monkeypatch.setattr(aliases.Chem, "GetMolFrags", lambda *_args, **_kwargs: ())

    result = aliases.build_alias_grouping_result("CCO")

    assert result.failures == (aliases.NO_FRAGMENTS,)


def test_typed_bemis_murcko_scaffold_is_stereo_insensitive_not_generic():
    first = aliases.build_alias_grouping_result("C[C@H](O)c1ccccc1")
    second = aliases.build_alias_grouping_result("C[C@@H](O)c1ccccc1")
    pyridine = aliases.build_alias_grouping_result("c1ccncc1")

    assert first.scaffold_key == "c1ccccc1"
    assert second.scaffold_key == first.scaffold_key
    assert pyridine.scaffold_key == "c1ccncc1"
    assert pyridine.scaffold_key != first.scaffold_key


def test_ring_free_molecules_have_no_scaffold_key_without_failure():
    result = aliases.build_alias_grouping_result("CCO")

    assert result.scaffold_key is None
    assert result.family_key == "CCO"
    assert result.failures == ()
    assert result.notes == (aliases.RING_FREE_NO_SCAFFOLD,)


def test_conservative_family_key_removes_stereo_uncharges_and_canonicalizes_tautomers():
    first_stereo = aliases.build_alias_grouping_result("F[C@H](Cl)Br")
    second_stereo = aliases.build_alias_grouping_result("F[C@@H](Cl)Br")
    acetate = aliases.build_alias_grouping_result("CC(=O)[O-]")
    acetic_acid = aliases.build_alias_grouping_result("CC(=O)O")
    keto = aliases.build_alias_grouping_result("CC(=O)C")
    enol = aliases.build_alias_grouping_result("C=C(O)C")

    assert first_stereo.family_key == second_stereo.family_key == "FC(Cl)Br"
    assert acetate.family_key == acetic_acid.family_key == "CC(=O)O"
    assert keto.family_key == enol.family_key == "CC(C)=O"


def test_key_generation_failures_are_reported(monkeypatch):
    def fail_scaffold(_mol):
        return None, aliases.SCAFFOLD_KEY_FAILURE

    def fail_family(_mol):
        return None, aliases.FAMILY_KEY_FAILURE

    monkeypatch.setattr(aliases, "make_typed_bemis_murcko_scaffold_key", fail_scaffold)
    monkeypatch.setattr(aliases, "make_conservative_family_key", fail_family)

    result = aliases.build_alias_grouping_result("c1ccccc1")

    assert result.failures == (
        aliases.SCAFFOLD_KEY_FAILURE,
        aliases.FAMILY_KEY_FAILURE,
    )
    assert result.scaffold_key is None
    assert result.family_key is None


def test_grouping_uses_only_successful_existing_alias_keys():
    records = [
        aliases.add_alias_grouping_fields({"id": "a", "smiles": "CC(=O)C"}),
        aliases.add_alias_grouping_fields({"id": "b", "smiles": "C=C(O)C"}),
        aliases.add_alias_grouping_fields({"id": "failed", "smiles": "CC.CN"}),
        aliases.add_alias_grouping_fields({"id": "no-scaffold", "smiles": "CCO"}),
    ]

    family_groups = aliases.group_records_by_alias_key(records, key_field="family_key")
    scaffold_groups = aliases.group_records_by_alias_key(records, key_field="scaffold_key")

    assert [record["id"] for record in family_groups["CC(C)=O"]] == ["a", "b"]
    assert "failed" not in [record["id"] for group in family_groups.values() for record in group]
    assert scaffold_groups == {}


def test_grouping_rejects_non_frozen_key_names():
    with pytest.raises(ValueError, match="key_field"):
        aliases.group_records_by_alias_key([], key_field="largest_fragment_smiles")


def test_same_scaffold_joins_records():
    assignments = _assignments(
        [
            _record("a", scaffold_key="scaffold", family_key="family-a"),
            _record("b", scaffold_key="scaffold", family_key="family-b"),
        ]
    )

    assert assignments["a"]["component_members"] == ("a", "b")
    assert assignments["b"]["component_id"] == assignments["a"]["component_id"]


def test_same_family_joins_records():
    assignments = _assignments(
        [
            _record("a", scaffold_key="scaffold-a", family_key="family"),
            _record("b", scaffold_key="scaffold-b", family_key="family"),
        ]
    )

    assert assignments["a"]["component_members"] == ("a", "b")
    assert assignments["b"]["component_id"] == assignments["a"]["component_id"]


def test_components_are_transitive_across_scaffold_and_family_keys():
    assignments = _assignments(
        [
            _record("a", scaffold_key="shared-scaffold", family_key="family-a"),
            _record("b", scaffold_key="shared-scaffold", family_key="shared-family"),
            _record("c", scaffold_key="scaffold-c", family_key="shared-family"),
        ]
    )

    assert assignments["a"]["component_members"] == ("a", "b", "c")
    assert assignments["b"]["component_id"] == assignments["a"]["component_id"]
    assert assignments["c"]["component_id"] == assignments["a"]["component_id"]


def test_unrelated_records_remain_separate_singleton_components():
    assignments = _assignments(
        [
            _record("a", scaffold_key="scaffold-a", family_key="family-a"),
            _record("b", scaffold_key="scaffold-b", family_key="family-b"),
        ]
    )

    assert assignments["a"]["component_members"] == ("a",)
    assert assignments["b"]["component_members"] == ("b",)
    assert assignments["a"]["component_id"] != assignments["b"]["component_id"]


def test_null_keys_never_connect_records():
    assignments = _assignments(
        [
            _record("a", scaffold_key=None, family_key=None),
            _record("b", scaffold_key=None, family_key=None),
        ]
    )

    assert assignments["a"]["component_members"] == ("a",)
    assert assignments["b"]["component_members"] == ("b",)
    assert assignments["a"]["component_id"] != assignments["b"]["component_id"]


def test_failure_records_do_not_participate_in_alias_components():
    assignments = _assignments(
        [
            _record("a", scaffold_key="scaffold", family_key="family"),
            _record(
                "failed",
                scaffold_key="scaffold",
                family_key="family",
                failures=(aliases.SCAFFOLD_KEY_FAILURE,),
            ),
        ]
    )

    assert assignments["a"]["component_members"] == ("a",)
    assert assignments["failed"]["component_id"] is None
    assert assignments["failed"]["component_members"] == ()
    assert assignments["failed"]["grouping_failure"] == aliases.SCAFFOLD_KEY_FAILURE


def test_component_assignment_is_deterministic_under_input_order_permutation():
    records = [
        _record("c", scaffold_key="scaffold-c", family_key="shared-family"),
        _record("a", scaffold_key="shared-scaffold", family_key="family-a"),
        _record("d", scaffold_key="scaffold-d", family_key="family-d"),
        _record("b", scaffold_key="shared-scaffold", family_key="shared-family"),
        _record("failed", failures=(aliases.FRAGMENT_AMBIGUITY,)),
    ]

    first = aliases.construct_alias_connected_components(records)
    second = aliases.construct_alias_connected_components(list(reversed(records)))

    assert first == second
    assert _assignments(records)["a"]["component_members"] == ("a", "b", "c")


def test_production_artifact_generation_requires_authoritative_rdkit(monkeypatch):
    monkeypatch.setattr(aliases.rdBase, "rdkitVersion", "NOT.2023.09.6")

    with pytest.raises(RuntimeError, match="require RDKit 2023.09.6"):
        aliases.add_alias_grouping_fields_for_artifact({"smiles": "CCO"})


def test_non_authoritative_runtime_is_reported_without_claiming_authority(monkeypatch):
    monkeypatch.setattr(aliases.rdBase, "rdkitVersion", "NOT.2023.09.6")

    output = aliases.add_alias_grouping_fields({"smiles": "CCO"})

    assert output["alias_grouping"]["rdkit_version"] == "NOT.2023.09.6"
    assert output["alias_grouping"]["authoritative_rdkit_behavior"] == "2023.09.6"
    assert output["alias_grouping"]["is_authoritative_rdkit_runtime"] is False
