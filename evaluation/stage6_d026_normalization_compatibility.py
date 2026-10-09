"""D029 D026-normalization compatibility experiment.

This module implements the preregistered local analysis only. It compares
candidate normalized identities against the frozen D026 full-InChIKey identity
relation without choosing row-order-dependent representative spellings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize as MolStandardize


EXPECTED_CONFLICT_FIELDS = (
    "d026_inchikey",
    "existing_status",
    "existing_canonical_smiles",
    "existing_failure_reason",
    "new_status",
    "new_canonical_smiles",
    "new_failure_reason",
)

REQUIRED_D026_STOCK_FIELDS = frozenset(
    {
        "smiles",
        "zinc_id",
        "zinc_inchikey",
        "d026_inchikey",
        "full_key_match",
        "connectivity_match",
        "source_file",
        "source_line_number",
    }
)

SCHEMA_VERSION = "stage6_d026_normalization_compatibility.v1"
SAMPLING_SEED = "20261002"
SAMPLING_SERIALIZATION = 'SHA256(b"20261002\\t" + full_D026_key.encode("utf-8"))'
DEFAULT_SELECTED_KEY_COUNT = 20_000
RULE_OF_THREE_PAIR_COUNT = 10_000
RULE_OF_THREE_UPPER_BOUND = 3 / RULE_OF_THREE_PAIR_COUNT
MAX_FAILURE_EXAMPLES = 20

CandidateIdentity = tuple[str, str]


@dataclass(frozen=True)
class NormalizationResult:
    source_smiles: str
    status: str
    identity: CandidateIdentity | None
    failure_reason: str | None


@dataclass(frozen=True)
class KeyCandidateResult:
    d026_inchikey: str
    source_smiles: tuple[str, ...]
    identities: frozenset[CandidateIdentity]
    normalization_results: tuple[NormalizationResult, ...]


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_full_d026_key(d026_inchikey: str) -> None:
    if len(d026_inchikey) != 27:
        raise ValueError(
            "D026 identity authority is the full 27-character InChIKey; "
            f"got {d026_inchikey!r}"
        )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_conflict_tsv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        if fieldnames != EXPECTED_CONFLICT_FIELDS:
            raise ValueError(
                "unexpected conflict TSV columns: "
                f"expected {EXPECTED_CONFLICT_FIELDS!r}, got {fieldnames!r}"
            )
        rows = [dict(row) for row in reader]
    for row in rows:
        validate_full_d026_key(row["d026_inchikey"])
    return rows


def build_conflict_source_smiles_by_key(
    rows: Iterable[Mapping[str, str]],
) -> dict[str, frozenset[str]]:
    source_smiles_by_key: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        d026_inchikey = row["d026_inchikey"]
        validate_full_d026_key(d026_inchikey)
        for field in ("existing_canonical_smiles", "new_canonical_smiles"):
            smiles = row[field]
            if smiles:
                source_smiles_by_key[d026_inchikey].add(smiles)
    return {
        key: frozenset(source_smiles_by_key[key])
        for key in sorted(source_smiles_by_key)
    }


def read_d026_stock_key_population(path: str | Path) -> tuple[int, frozenset[str]]:
    record_count = 0
    keys: set[str] = set()
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = set(reader.fieldnames or ())
        missing = sorted(REQUIRED_D026_STOCK_FIELDS.difference(fieldnames))
        if missing:
            raise ValueError(f"D026 stock TSV missing required columns: {missing!r}")
        for row in reader:
            record_count += 1
            d026_inchikey = row["d026_inchikey"]
            validate_full_d026_key(d026_inchikey)
            keys.add(d026_inchikey)
    return record_count, frozenset(keys)


def collect_stock_source_smiles_for_keys(
    path: str | Path,
    selected_keys: Iterable[str],
) -> dict[str, frozenset[str]]:
    selected_key_set = set(selected_keys)
    for key in selected_key_set:
        validate_full_d026_key(key)

    source_smiles_by_key = {key: set() for key in selected_key_set}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = set(reader.fieldnames or ())
        missing = sorted(REQUIRED_D026_STOCK_FIELDS.difference(fieldnames))
        if missing:
            raise ValueError(f"D026 stock TSV missing required columns: {missing!r}")
        for row in reader:
            d026_inchikey = row["d026_inchikey"]
            if d026_inchikey in source_smiles_by_key and row["smiles"]:
                source_smiles_by_key[d026_inchikey].add(row["smiles"])

    missing_source = sorted(
        key for key, source_smiles in source_smiles_by_key.items() if not source_smiles
    )
    if missing_source:
        raise ValueError(
            "selected D026 keys have no source SMILES in stock TSV: "
            f"{missing_source[:5]!r}"
        )
    return {
        key: frozenset(source_smiles_by_key[key])
        for key in sorted(source_smiles_by_key)
    }


def sampling_priority(full_d026_key: str) -> str:
    validate_full_d026_key(full_d026_key)
    payload = b"20261002\t" + full_d026_key.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def select_sampled_keys(
    distinct_full_d026_keys: Iterable[str],
    selected_key_count: int = DEFAULT_SELECTED_KEY_COUNT,
) -> list[str]:
    keys = sorted(set(distinct_full_d026_keys))
    for key in keys:
        validate_full_d026_key(key)
    if len(keys) < selected_key_count:
        raise ValueError(
            f"need at least {selected_key_count} distinct full D026 keys; got {len(keys)}"
        )
    prioritized = sorted(keys, key=lambda key: (sampling_priority(key), key))
    return prioritized[:selected_key_count]


def construct_adjacent_pairs_after_lexicographic_sort(
    selected_keys: Iterable[str],
) -> list[tuple[str, str]]:
    keys = sorted(selected_keys)
    if len(keys) % 2 != 0:
        raise ValueError(f"selected-key count must be even; got {len(keys)}")
    return [(keys[index], keys[index + 1]) for index in range(0, len(keys), 2)]


def _successful_identity(rdkit_version: str, canonical_smiles: str) -> CandidateIdentity:
    return (rdkit_version, canonical_smiles)


def candidate_a_normalize(smiles: str, rdkit_version: str | None = None) -> NormalizationResult:
    """Candidate A: SMILES -> standard InChI -> RDKit mol -> canonical isomeric SMILES."""

    if rdkit_version is None:
        rdkit_version = rdBase.rdkitVersion
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return NormalizationResult(smiles, "failure", None, "MolFromSmiles returned None")
    inchi = Chem.MolToInchi(mol)
    if not inchi:
        return NormalizationResult(smiles, "failure", None, "MolToInchi returned empty InChI")
    normalized_molecule = Chem.MolFromInchi(inchi)
    if normalized_molecule is None:
        return NormalizationResult(smiles, "failure", None, "MolFromInchi returned None")
    canonical_smiles = Chem.MolToSmiles(
        normalized_molecule,
        canonical=True,
        isomericSmiles=True,
    )
    return NormalizationResult(
        smiles,
        "success",
        _successful_identity(rdkit_version, canonical_smiles),
        None,
    )


def candidate_b_normalize(smiles: str, rdkit_version: str | None = None) -> NormalizationResult:
    """Candidate B: RDKit MolStandardize cleanup plus canonical tautomer."""

    if rdkit_version is None:
        rdkit_version = rdBase.rdkitVersion
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return NormalizationResult(smiles, "failure", None, "MolFromSmiles returned None")
    params = MolStandardize.CleanupParameters()
    cleaned = MolStandardize.Cleanup(mol, params)
    normalized_molecule = MolStandardize.CanonicalTautomer(cleaned, params)
    canonical_smiles = Chem.MolToSmiles(
        normalized_molecule,
        canonical=True,
        isomericSmiles=True,
    )
    return NormalizationResult(
        smiles,
        "success",
        _successful_identity(rdkit_version, canonical_smiles),
        None,
    )


def normalize_source_smiles_by_key(
    source_smiles_by_key: Mapping[str, Iterable[str]],
    normalizer: Callable[[str, str | None], NormalizationResult],
    rdkit_version: str,
) -> dict[str, KeyCandidateResult]:
    results = {}
    for d026_inchikey in sorted(source_smiles_by_key):
        validate_full_d026_key(d026_inchikey)
        source_smiles = tuple(sorted(set(source_smiles_by_key[d026_inchikey])))
        normalization_results = tuple(
            normalizer(smiles, rdkit_version) for smiles in source_smiles
        )
        identities = frozenset(
            result.identity
            for result in normalization_results
            if result.status == "success" and result.identity is not None
        )
        results[d026_inchikey] = KeyCandidateResult(
            d026_inchikey=d026_inchikey,
            source_smiles=source_smiles,
            identities=identities,
            normalization_results=normalization_results,
        )
    return results


def detect_false_split_keys(
    key_results: Mapping[str, KeyCandidateResult],
) -> list[str]:
    return sorted(
        key for key, result in key_results.items() if len(result.identities) > 1
    )


def detect_false_merge_pairs(
    key_results: Mapping[str, KeyCandidateResult],
) -> list[dict[str, Any]]:
    identity_to_keys: dict[CandidateIdentity, set[str]] = defaultdict(set)
    for key, result in key_results.items():
        for identity in result.identities:
            identity_to_keys[identity].add(key)

    pair_to_intersections: dict[tuple[str, str], set[CandidateIdentity]] = defaultdict(set)
    for identity in sorted(identity_to_keys):
        keys = sorted(identity_to_keys[identity])
        for key_a, key_b in combinations(keys, 2):
            pair_to_intersections[(key_a, key_b)].add(identity)

    return [
        {
            "d026_inchikey_a": key_a,
            "d026_inchikey_b": key_b,
            "intersecting_candidate_identities": identities_to_json(
                pair_to_intersections[(key_a, key_b)]
            ),
        }
        for key_a, key_b in sorted(pair_to_intersections)
    ]


def detect_false_merge_pairs_for_sample(
    key_results: Mapping[str, KeyCandidateResult],
    sampled_pairs: Sequence[tuple[str, str]],
) -> list[dict[str, Any]]:
    failures = []
    for key_a, key_b in sampled_pairs:
        intersection = set(key_results[key_a].identities).intersection(
            key_results[key_b].identities
        )
        if intersection:
            failures.append(
                {
                    "d026_inchikey_a": key_a,
                    "d026_inchikey_b": key_b,
                    "intersecting_candidate_identities": identities_to_json(intersection),
                }
            )
    return failures


def identities_to_json(identities: Iterable[CandidateIdentity]) -> list[dict[str, str]]:
    return [
        {
            "rdkit_version": rdkit_version,
            "canonical_isomeric_smiles": canonical_smiles,
        }
        for rdkit_version, canonical_smiles in sorted(identities)
    ]


def normalization_results_to_json(
    results: Iterable[NormalizationResult],
) -> list[dict[str, Any]]:
    serialized = []
    for result in sorted(results, key=lambda item: item.source_smiles):
        serialized.append(
            {
                "source_smiles": result.source_smiles,
                "status": result.status,
                "candidate_identity": identities_to_json([result.identity])[0]
                if result.identity is not None
                else None,
                "failure_reason": result.failure_reason,
            }
        )
    return serialized


def key_result_to_json(result: KeyCandidateResult) -> dict[str, Any]:
    return {
        "d026_inchikey": result.d026_inchikey,
        "distinct_source_smiles_count": len(result.source_smiles),
        "source_smiles": list(result.source_smiles),
        "candidate_identity_set": identities_to_json(result.identities),
        "normalization_results": normalization_results_to_json(
            result.normalization_results
        ),
    }


def build_candidate_report(
    conflict_results: Mapping[str, KeyCandidateResult],
    sample_results: Mapping[str, KeyCandidateResult],
    sampled_pairs: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    false_split_keys = detect_false_split_keys(conflict_results)
    false_merge_pairs_conflicted = detect_false_merge_pairs(conflict_results)
    false_merge_pairs_sample = detect_false_merge_pairs_for_sample(
        sample_results,
        sampled_pairs,
    )
    conflicted_pass = not false_split_keys and not false_merge_pairs_conflicted
    sample_pass = not false_merge_pairs_sample
    return {
        "false_merge_count_conflicted": len(false_merge_pairs_conflicted),
        "false_split_count_conflicted": len(false_split_keys),
        "false_merge_count_sample": len(false_merge_pairs_sample),
        "conflicted_pass": conflicted_pass,
        "sample_pass": sample_pass,
        "overall_pass": conflicted_pass and sample_pass,
        "representative_failure_examples": {
            "false_merges_conflicted": false_merge_pairs_conflicted[
                :MAX_FAILURE_EXAMPLES
            ],
            "false_splits_conflicted": [
                key_result_to_json(conflict_results[key])
                for key in false_split_keys[:MAX_FAILURE_EXAMPLES]
            ],
            "false_merges_sample": false_merge_pairs_sample[:MAX_FAILURE_EXAMPLES],
        },
    }


def candidate_selection(candidate_reports: Mapping[str, Mapping[str, Any]]) -> str:
    candidate_a_passes = bool(candidate_reports["candidate_a"]["overall_pass"])
    candidate_b_passes = bool(candidate_reports["candidate_b"]["overall_pass"])
    if candidate_a_passes and candidate_b_passes:
        return "candidate_a_inchi_consistent_treatment"
    if candidate_a_passes:
        return "candidate_a_inchi_consistent_treatment"
    if candidate_b_passes:
        return "candidate_b_rdkit_molstandardize_canonical_tautomer_treatment"
    return "STOP_AND_REDESIGN"


def build_report(
    *,
    conflict_rows: Iterable[Mapping[str, str]],
    d026_stock_record_count: int,
    d026_stock_distinct_keys: Iterable[str],
    d026_stock_source_smiles_by_key: Mapping[str, Iterable[str]],
    conflict_file_path: str,
    d026_stock_path: str,
    conflict_file_sha256: str,
    d026_stock_sha256: str,
    utc_start_timestamp: str,
    utc_end_timestamp: str,
    selected_key_count: int = DEFAULT_SELECTED_KEY_COUNT,
    rdkit_version: str | None = None,
    normalizers: Mapping[str, Callable[[str, str | None], NormalizationResult]] | None = None,
) -> dict[str, Any]:
    if rdkit_version is None:
        rdkit_version = rdBase.rdkitVersion
    if normalizers is None:
        normalizers = {
            "candidate_a": candidate_a_normalize,
            "candidate_b": candidate_b_normalize,
        }

    conflict_source_smiles_by_key = build_conflict_source_smiles_by_key(conflict_rows)
    selected_keys = select_sampled_keys(
        d026_stock_distinct_keys,
        selected_key_count=selected_key_count,
    )
    sampled_pairs = construct_adjacent_pairs_after_lexicographic_sort(selected_keys)
    selected_source_smiles_by_key = {
        key: frozenset(d026_stock_source_smiles_by_key[key]) for key in sorted(selected_keys)
    }

    conflict_results_by_candidate = {
        name: normalize_source_smiles_by_key(
            conflict_source_smiles_by_key,
            normalizer,
            rdkit_version,
        )
        for name, normalizer in normalizers.items()
    }
    sample_results_by_candidate = {
        name: normalize_source_smiles_by_key(
            selected_source_smiles_by_key,
            normalizer,
            rdkit_version,
        )
        for name, normalizer in normalizers.items()
    }
    candidate_reports = {
        name: build_candidate_report(
            conflict_results_by_candidate[name],
            sample_results_by_candidate[name],
            sampled_pairs,
        )
        for name in ("candidate_a", "candidate_b")
    }

    sample_false_merges_zero = all(
        report["false_merge_count_sample"] == 0 for report in candidate_reports.values()
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "utc_start_timestamp": utc_start_timestamp,
        "utc_end_timestamp": utc_end_timestamp,
        "rdkit_version": rdkit_version,
        "candidate_identity_statement": (
            "candidate identity is (RDKit version, canonical isomeric SMILES)"
        ),
        "candidate_definitions": {
            "candidate_a": {
                "name": "InChI-consistent treatment",
                "pipeline": [
                    "frozen source SMILES",
                    "RDKit MolFromSmiles",
                    "Standard InChI via MolToInchi() with no non-standard options",
                    "RDKit MolFromInchi(Standard InChI)",
                    "MolToSmiles(normalized_molecule, canonical=True, isomericSmiles=True)",
                ],
            },
            "candidate_b": {
                "name": "RDKit MolStandardize canonical-tautomer treatment",
                "pipeline": [
                    "frozen source SMILES",
                    "RDKit MolFromSmiles",
                    "MolStandardize.CleanupParameters() runtime defaults",
                    "MolStandardize.cleanup(mol, params)",
                    "MolStandardize.canonicalTautomer(cleaned, params)",
                    "MolToSmiles(normalized_molecule, canonical=True, isomericSmiles=True)",
                ],
            },
        },
        "inputs": {
            "conflict_file_path": conflict_file_path,
            "d026_stock_path": d026_stock_path,
            "conflict_file_sha256": conflict_file_sha256,
            "d026_stock_sha256": d026_stock_sha256,
            "d026_stock_record_count": d026_stock_record_count,
            "total_conflicted_key_count": len(conflict_source_smiles_by_key),
        },
        "sampling": {
            "sampling_seed": SAMPLING_SEED,
            "exact_sha256_sampling_serialization": SAMPLING_SERIALIZATION,
            "sampled_distinct_key_count": len(selected_keys),
            "selected_key_count": len(selected_keys),
            "sampled_pair_count": len(sampled_pairs),
            "pair_construction_rule": (
                "sort selected full 27-character D026 InChIKeys lexicographically "
                "and pair adjacent keys"
            ),
            "rule_of_three_upper_bound_when_zero_false_merges": {
                "condition": "sample false merges == 0",
                "formula": "3 / 10000",
                "value": RULE_OF_THREE_UPPER_BOUND,
                "percent": RULE_OF_THREE_UPPER_BOUND * 100,
                "statement": (
                    "Approximately 95% confidence upper bound for the pairwise "
                    "false-merge rate; not proof of zero false merges across the "
                    "entire frozen population."
                ),
            }
            if sample_false_merges_zero
            else None,
        },
        "pass_criteria": {
            "conflicted_key_population": {
                "false_merges": 0,
                "false_splits": 0,
            },
            "different_key_sample": {"false_merges": 0},
        },
        "candidates": candidate_reports,
        "candidate_selection": candidate_selection(candidate_reports),
        "sampled_keys": [
            {
                "d026_inchikey": key,
                "distinct_source_smiles_count": len(selected_source_smiles_by_key[key]),
                "source_smiles": sorted(selected_source_smiles_by_key[key]),
                "candidate_identity_sets": {
                    name: identities_to_json(sample_results_by_candidate[name][key].identities)
                    for name in ("candidate_a", "candidate_b")
                },
            }
            for key in sorted(selected_keys)
        ],
        "sampled_pairs_with_detected_intersections": {
            name: candidate_reports[name]["representative_failure_examples"][
                "false_merges_sample"
            ]
            for name in ("candidate_a", "candidate_b")
        },
    }


def write_json_report(report: Mapping[str, Any], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(report, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the D029 D026-normalization compatibility experiment locally."
    )
    parser.add_argument("--conflict-file", required=True)
    parser.add_argument("--d026-stock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    start_timestamp = utc_timestamp()

    conflict_path = Path(args.conflict_file)
    stock_path = Path(args.d026_stock)
    conflict_rows = read_conflict_tsv(conflict_path)
    stock_record_count, stock_keys = read_d026_stock_key_population(stock_path)
    selected_keys = select_sampled_keys(stock_keys)
    stock_source_smiles_by_key = collect_stock_source_smiles_for_keys(
        stock_path,
        selected_keys,
    )

    report = build_report(
        conflict_rows=conflict_rows,
        d026_stock_record_count=stock_record_count,
        d026_stock_distinct_keys=stock_keys,
        d026_stock_source_smiles_by_key=stock_source_smiles_by_key,
        conflict_file_path=str(conflict_path),
        d026_stock_path=str(stock_path),
        conflict_file_sha256=sha256_file(conflict_path),
        d026_stock_sha256=sha256_file(stock_path),
        utc_start_timestamp=start_timestamp,
        utc_end_timestamp=utc_timestamp(),
    )
    write_json_report(report, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
