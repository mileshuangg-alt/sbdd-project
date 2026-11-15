"""Mechanical tiny-fixture tests for the ADMET split-input builder.

These run on any RDKit version and are not pinned-runtime qualification.
"""

import csv
import hashlib
import itertools
import json

import numpy as np
import pytest

from admet.scripts import build_split_input as builder
from evaluation.novelty import calculate_tanimoto


def _identity(endpoint, identity, smiles, family_key):
    return builder.SplitIdentity(endpoint, identity, smiles, family_key)


FIXTURE = [
    _identity("pka", "1", "CCO", "A"),
    _identity("pka", "2", "CCN", "A"),
    _identity("clearance", "C1", "c1ccccc1O", "B"),
    _identity("pka", "3", "c1ccccc1N", "C"),
    _identity("clearance", "C2", "CC(=O)O", "C"),
    _identity("clearance", "C3", "CCCC", "C"),
]


def test_weighted_family_similarity_equals_molecular_pair_sum():
    fingerprints = builder.fingerprint_split_identities(FIXTURE)
    families = builder.build_families(FIXTURE)

    for left, right in itertools.combinations(families, 2):
        s_ij = builder.family_mean_similarity(
            list(left.members), list(right.members), fingerprints
        )
        brute_force = sum(
            calculate_tanimoto(
                fingerprints[(a.endpoint, a.identity)],
                fingerprints[(b.endpoint, b.identity)],
            )
            for a in left.members
            for b in right.members
        )
        assert left.weight * right.weight * s_ij == pytest.approx(brute_force)


def test_family_fields_and_ordering():
    families = builder.build_families(FIXTURE)

    assert [f.family_key for f in families] == ["A", "B", "C"]
    assert [f.family_index for f in families] == [0, 1, 2]
    assert [f.weight for f in families] == [2, 1, 3]
    assert [f.endpoint_count("pka") for f in families] == [2, 0, 1]
    assert [f.endpoint_count("clearance") for f in families] == [0, 1, 2]


def test_complete_similarities_fill_upper_triangle_in_documented_order():
    fingerprints = builder.fingerprint_split_identities(FIXTURE)
    families = builder.build_families(FIXTURE)

    similarities = builder.complete_family_similarities(families, fingerprints)

    assert similarities.dtype == np.float64
    assert similarities.size == builder.upper_triangle_length(3) == 3
    for i, j in itertools.combinations(range(3), 2):
        expected = builder.family_mean_similarity(
            list(families[i].members), list(families[j].members), fingerprints
        )
        assert similarities[builder.upper_triangle_index(i, j, 3)] == expected


def test_upper_triangle_index_is_a_bijection():
    count = 7
    positions = [
        builder.upper_triangle_index(i, j, count)
        for i, j in itertools.combinations(range(count), 2)
    ]
    assert positions == list(range(builder.upper_triangle_length(count)))


def test_parse_failure_halts():
    bad = [_identity("pka", "1", "not_a_smiles", "A")]
    with pytest.raises(ValueError, match="failed sanitized RDKit parsing"):
        builder.fingerprint_split_identities(bad)


def test_duplicate_identity_halts():
    duplicated = [FIXTURE[0], FIXTURE[0]]
    with pytest.raises(ValueError, match="Duplicate split identity"):
        builder.fingerprint_split_identities(duplicated)


def _write_csv(path, header, rows):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_loader_keeps_only_identity_and_smiles(tmp_path):
    path = tmp_path / "pka.csv"
    _write_csv(
        path,
        ["unique_ID", "smiles", "side", "step", "pka"],
        [["7", "CCO", "acid", "1", "15.9"], ["7", "CCO", "base", "1", "-2.0"]],
    )

    loaded = builder.load_source_identities(
        path, endpoint="pka", identity_column="unique_ID", smiles_column="smiles"
    )

    assert loaded == [builder.SourceIdentity("pka", "7", "CCO")]
    assert set(vars(loaded[0])) == {"endpoint", "identity", "source_smiles"}


def test_loader_halts_on_conflicting_smiles_for_one_identity(tmp_path):
    path = tmp_path / "pka.csv"
    _write_csv(
        path,
        ["unique_ID", "smiles", "pka"],
        [["7", "CCO", "15.9"], ["7", "OCC", "15.9"]],
    )

    with pytest.raises(ValueError, match="2 distinct source-recorded SMILES"):
        builder.load_source_identities(
            path, endpoint="pka", identity_column="unique_ID", smiles_column="smiles"
        )


def test_manifest_mismatch_halts(tmp_path):
    data = tmp_path / "pka.csv"
    data.write_text("unique_ID,smiles\n1,CCO\n")
    good = hashlib.sha256(data.read_bytes()).hexdigest()

    manifest = tmp_path / "MANIFEST.sha256"
    manifest.write_text(f"{good}  pka.csv\n")
    assert builder.verify_inputs_against_manifest([data], manifest) == {
        str(data): good
    }

    manifest.write_text(f"{'0' * 64}  pka.csv\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        builder.verify_inputs_against_manifest([data], manifest)


def test_expected_count_mismatch_halts():
    builder.check_expected_counts({"distinct_family_keys": 5447}, {"distinct_family_keys": 5447})
    with pytest.raises(ValueError, match="distinct_family_keys"):
        builder.check_expected_counts(
            {"distinct_family_keys": 5446}, {"distinct_family_keys": 5447}
        )


def test_grouping_failure_halts():
    sources = [builder.SourceIdentity("clearance", "X", "CC.CN")]
    with pytest.raises(ValueError, match="grouping failure"):
        builder.group_identities(sources)


def test_loader_halts_on_short_or_blank_row(tmp_path):
    path = tmp_path / "pka.csv"
    path.write_text("unique_ID,smiles,pka\n7,CCO,15.9\n\n")

    with pytest.raises(ValueError, match="line 3: expected 3 fields, found 0"):
        builder.load_source_identities(
            path, endpoint="pka", identity_column="unique_ID", smiles_column="smiles"
        )


def test_manifest_rejects_input_outside_manifest_directory(tmp_path):
    prepared = tmp_path / "prepared"
    elsewhere = tmp_path / "elsewhere"
    prepared.mkdir()
    elsewhere.mkdir()
    (prepared / "pka.csv").write_text("unique_ID,smiles\n1,CCO\n")
    (elsewhere / "pka.csv").write_text("unique_ID,smiles\n1,CCO\n")
    digest = hashlib.sha256((prepared / "pka.csv").read_bytes()).hexdigest()
    manifest = prepared / "MANIFEST.sha256"
    manifest.write_text(f"{digest}  pka.csv\n")

    with pytest.raises(ValueError, match="not in the manifest directory"):
        builder.verify_inputs_against_manifest([elsewhere / "pka.csv"], manifest)


def test_outputs_are_not_overwritten(tmp_path):
    (tmp_path / "existing.txt").write_text("frozen")
    with pytest.raises(FileExistsError):
        builder.write_outputs(tmp_path, [], [], {}, np.empty(0), {})


def test_failed_write_leaves_no_partial_output(tmp_path, monkeypatch):
    output_dir = tmp_path / "split_input_v1"

    def failing_save(*args, **kwargs):
        raise OSError("simulated disk quota")

    monkeypatch.setattr(builder.np, "save", failing_save)
    with pytest.raises(OSError, match="simulated disk quota"):
        builder.write_outputs(output_dir, [], [], {}, np.empty(0), {})

    assert not output_dir.exists()
    assert list(tmp_path.iterdir()) == []


def _fixture_repo(tmp_path):
    prepared = tmp_path / "admet" / "data" / "prepared"
    prepared.mkdir(parents=True)
    _write_csv(
        prepared / "pka.csv",
        ["unique_ID", "smiles", "side", "step", "pka"],
        [
            ["1", "CCO", "acid", "1", "15.9"],
            ["1", "CCO", "base", "1", "-2.0"],
            ["2", "CCO.Cl", "acid", "1", "15.9"],
            ["3", "Oc1ccccc1", "acid", "1", "10.0"],
        ],
    )
    _write_csv(
        prepared / "clearance.csv",
        ["molecule_chembl_id", "smiles", "clearance"],
        [["C1", "Oc1ccccc1", "3.0"], ["C2", "CCCC", "9.0"]],
    )
    (prepared / "MANIFEST.sha256").write_text(
        "".join(
            f"{hashlib.sha256((prepared / name).read_bytes()).hexdigest()}  {name}\n"
            for name in ("pka.csv", "clearance.csv")
        )
    )
    config = {
        "schema_version": "test",
        "governing_decisions": ["D031", "D032", "D033"],
        "authoritative_rdkit_version": builder.rdBase.rdkitVersion,
        "prepared_manifest": "admet/data/prepared/MANIFEST.sha256",
        "endpoints": [
            {
                "endpoint": "pka",
                "path": "admet/data/prepared/pka.csv",
                "identity_column": "unique_ID",
                "smiles_column": "smiles",
            },
            {
                "endpoint": "clearance",
                "path": "admet/data/prepared/clearance.csv",
                "identity_column": "molecule_chembl_id",
                "smiles_column": "smiles",
            },
        ],
        "expected_counts": {
            "endpoint_identities": {"pka": 3, "clearance": 2},
            "endpoint_qualified_identities": 5,
            "successfully_grouped": 5,
            "grouping_failures": 0,
            "distinct_family_keys": 3,
            "distinct_scaffold_keys": 1,
        },
        "output_dir": "out/split_input",
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


def test_end_to_end_fixture_build(tmp_path, monkeypatch):
    monkeypatch.setattr(
        builder.alias_grouping, "assert_authoritative_rdkit_runtime", lambda: None
    )
    config_path = _fixture_repo(tmp_path)

    summary = builder.build_split_input(config_path, tmp_path)

    output_dir = tmp_path / "out" / "split_input"
    assert sorted(p.name for p in output_dir.iterdir()) == sorted(
        [
            builder.FAMILIES_FILENAME,
            builder.MEMBERSHIPS_FILENAME,
            builder.SIMILARITY_FILENAME,
            builder.METADATA_FILENAME,
            builder.CHECKSUMS_FILENAME,
        ]
    )

    for line in (output_dir / builder.CHECKSUMS_FILENAME).read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        assert hashlib.sha256((output_dir / name).read_bytes()).hexdigest() == digest

    with (output_dir / builder.FAMILIES_FILENAME).open() as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == [
        "family_index",
        "family_key",
        "w",
        "pka_identities",
        "clearance_identities",
        "diagnostic_scaffold_keys",
    ]
    assert sum(int(r["w"]) for r in rows) == 5
    assert sum(int(r["pka_identities"]) for r in rows) == 3
    assert sum(int(r["clearance_identities"]) for r in rows) == 2

    similarities = np.load(output_dir / builder.SIMILARITY_FILENAME)
    assert similarities.shape == (3,)

    with (output_dir / builder.MEMBERSHIPS_FILENAME).open() as handle:
        memberships = list(csv.DictReader(handle))
    assert "pka" not in memberships[0] and "clearance" not in memberships[0]
    assert {m["source_smiles"] for m in memberships} >= {"CCO.Cl"}

    metadata = json.loads((output_dir / builder.METADATA_FILENAME).read_text())
    assert metadata["observed_counts"] == summary["metadata"]["observed_counts"]
    code_hashes = metadata["executed_code_sha256"]
    assert code_hashes["evaluation.novelty"]["sha256"] == hashlib.sha256(
        open(builder.novelty.__file__, "rb").read()
    ).hexdigest()
    assert not list((tmp_path / "out").glob(".split_input.partial-*"))
