"""Diagnose ASKCOS canonical-SMILES idempotence for Stage-6 conflicts.

This tool is intentionally read-only with respect to the conflict artifact. It
does not choose canonical representatives or change the Stage-6 scientific
contract; it only replays observed ASKCOS spellings through the existing
canonicalizer and reports whether each D026 identity converges to one result.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from evaluation.stage6_planner_stock_contract import (
    ASKCOS_STATUS_REPRESENTABLE,
    canonicalize_askcos_smiles,
)


EXPECTED_CONFLICT_FIELDS = (
    "d026_inchikey",
    "existing_status",
    "existing_canonical_smiles",
    "existing_failure_reason",
    "new_status",
    "new_canonical_smiles",
    "new_failure_reason",
)

DEFAULT_SAMPLE_SIZE = 2000
DEFAULT_SAMPLE_SEED = 20261001
MAX_NON_CONVERGENT_EXAMPLES = 20


def read_conflict_tsv(path: str | Path) -> list[dict[str, str]]:
    """Read the preserved Stage-6 ASKCOS conflict TSV."""

    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        if fieldnames != EXPECTED_CONFLICT_FIELDS:
            raise ValueError(
                "unexpected conflict TSV columns: "
                f"expected {EXPECTED_CONFLICT_FIELDS!r}, got {fieldnames!r}"
            )
        return [dict(row) for row in reader]


def build_evidence_map(
    rows: Iterable[Mapping[str, str]],
) -> dict[str, dict[str, frozenset[str]]]:
    """Group observed statuses and ASKCOS spellings by full D026 InChIKey."""

    evidence: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        d026_inchikey = row["d026_inchikey"]
        if len(d026_inchikey) != 27:
            raise ValueError(
                f"D026 InChIKey must be the full 27-character key: "
                f"{d026_inchikey!r}"
            )

        key_evidence = evidence.setdefault(
            d026_inchikey,
            {
                "observed_askcos_smiles": set(),
                "observed_statuses": set(),
            },
        )
        key_evidence["observed_statuses"].add(row["existing_status"])
        key_evidence["observed_statuses"].add(row["new_status"])

        for field in ("existing_canonical_smiles", "new_canonical_smiles"):
            observed_smiles = row[field]
            if observed_smiles != "":
                key_evidence["observed_askcos_smiles"].add(observed_smiles)

    return {
        d026_inchikey: {
            "observed_askcos_smiles": frozenset(
                key_evidence["observed_askcos_smiles"]
            ),
            "observed_statuses": frozenset(key_evidence["observed_statuses"]),
        }
        for d026_inchikey, key_evidence in sorted(evidence.items())
    }


def select_keys_for_analysis(
    evidence_map: Mapping[str, Mapping[str, frozenset[str]]],
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    seed: int = DEFAULT_SAMPLE_SEED,
) -> dict[str, Any]:
    """Select all >=3-spelling keys plus a deterministic sample of the rest."""

    high_multiplicity_keys = sorted(
        d026_inchikey
        for d026_inchikey, evidence in evidence_map.items()
        if len(evidence["observed_askcos_smiles"]) >= 3
    )
    remaining_keys = sorted(
        set(evidence_map).difference(high_multiplicity_keys)
    )
    sampled_count = min(sample_size, len(remaining_keys))
    sampled_keys = sorted(
        random.Random(seed).sample(remaining_keys, sampled_count)
    )

    return {
        "high_multiplicity_keys": high_multiplicity_keys,
        "sampled_keys": sampled_keys,
        "selected_keys": sorted(high_multiplicity_keys + sampled_keys),
    }


def _source_record_for_observed_smiles(
    d026_inchikey: str,
    observed_smiles: str,
) -> dict[str, str]:
    return {
        "smiles": observed_smiles,
        "zinc_id": "ASKCOS_IDEMPOTENCE_DIAGNOSTIC",
        "zinc_inchikey": d026_inchikey,
        "d026_inchikey": d026_inchikey,
        "full_key_match": "True",
        "connectivity_match": "True",
        "source_file": "stage6_askcos_conflict_artifact",
        "source_line_number": "0",
    }


def analyze_selected_keys(
    evidence_map: Mapping[str, Mapping[str, frozenset[str]]],
    selected_keys: Iterable[str],
    canonicalizer: Callable[[Mapping[str, Any]], dict[str, str | None]] | None = None,
) -> list[dict[str, Any]]:
    """Recanonicalize every observed ASKCOS spelling for selected keys."""

    if canonicalizer is None:
        canonicalizer = canonicalize_askcos_smiles

    analyses = []
    for d026_inchikey in sorted(selected_keys):
        evidence = evidence_map[d026_inchikey]
        observed_spellings = sorted(evidence["observed_askcos_smiles"])
        recanonicalizations = []
        successful_outputs = set()
        failures = []

        for observed_smiles in observed_spellings:
            result = canonicalizer(
                _source_record_for_observed_smiles(
                    d026_inchikey,
                    observed_smiles,
                )
            )
            recanonicalized = {
                "observed_askcos_smiles": observed_smiles,
                "askcos_status": result["askcos_status"],
                "canonical_smiles": result["canonical_smiles"],
                "representation_failure_reason": result[
                    "representation_failure_reason"
                ],
            }
            recanonicalizations.append(recanonicalized)

            if result["askcos_status"] == ASKCOS_STATUS_REPRESENTABLE:
                successful_outputs.add(str(result["canonical_smiles"]))
            else:
                failures.append(
                    {
                        "observed_askcos_smiles": observed_smiles,
                        "askcos_status": result["askcos_status"],
                        "representation_failure_reason": result[
                            "representation_failure_reason"
                        ],
                    }
                )

        idempotent = len(successful_outputs) == 1 and len(failures) == 0
        analyses.append(
            {
                "d026_inchikey": d026_inchikey,
                "observed_spelling_count": len(observed_spellings),
                "observed_askcos_smiles": observed_spellings,
                "observed_statuses": sorted(evidence["observed_statuses"]),
                "recanonicalizations": recanonicalizations,
                "distinct_recanonicalized_output_count": len(
                    successful_outputs
                ),
                "distinct_recanonicalized_outputs": sorted(successful_outputs),
                "representation_failures": failures,
                "idempotent": idempotent,
            }
        )

    return analyses


def build_report(
    rows: Iterable[Mapping[str, str]],
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    seed: int = DEFAULT_SAMPLE_SEED,
    canonicalizer: Callable[[Mapping[str, Any]], dict[str, str | None]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic diagnostic report from conflict rows."""

    evidence_map = build_evidence_map(rows)
    selection = select_keys_for_analysis(evidence_map, sample_size, seed)
    key_reports = analyze_selected_keys(
        evidence_map,
        selection["selected_keys"],
        canonicalizer,
    )

    idempotent_keys = [
        key_report["d026_inchikey"]
        for key_report in key_reports
        if key_report["idempotent"]
    ]
    non_idempotent_keys = [
        key_report["d026_inchikey"]
        for key_report in key_reports
        if not key_report["idempotent"]
    ]
    selected_count = len(key_reports)

    aggregate = {
        "total_conflicted_keys": len(evidence_map),
        "keys_with_at_least_3_spellings": len(
            selection["high_multiplicity_keys"]
        ),
        "random_sample_size": len(selection["sampled_keys"]),
        "sampled_keys": len(selection["sampled_keys"]),
        "selected_keys": selected_count,
        "idempotent_keys": len(idempotent_keys),
        "non_idempotent_keys": len(non_idempotent_keys),
        "idempotence_fraction": (
            len(idempotent_keys) / selected_count
            if selected_count > 0
            else None
        ),
    }

    reports_by_key = {
        key_report["d026_inchikey"]: key_report
        for key_report in key_reports
    }
    non_convergent_examples = [
        reports_by_key[d026_inchikey]
        for d026_inchikey in non_idempotent_keys[:MAX_NON_CONVERGENT_EXAMPLES]
    ]

    return {
        "parameters": {
            "sample_seed": seed,
            "requested_random_sample_size": sample_size,
            "max_non_convergent_examples": MAX_NON_CONVERGENT_EXAMPLES,
        },
        "aggregate": aggregate,
        "selection": {
            "high_multiplicity_keys": selection["high_multiplicity_keys"],
            "sampled_keys": selection["sampled_keys"],
        },
        "keys": key_reports,
        "non_convergent_examples": non_convergent_examples,
    }


def write_json_report(report: Mapping[str, Any], output_path: str | Path) -> None:
    with Path(output_path).open("w", encoding="utf-8", newline="") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose Stage-6 ASKCOS canonical-SMILES idempotence from a "
            "preserved conflict TSV."
        )
    )
    parser.add_argument(
        "--conflict-file",
        required=True,
        help="Path to the Stage-6 ASKCOS conflict TSV artifact.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a deterministic JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_conflict_tsv(args.conflict_file)
    report = build_report(rows)

    if args.output is not None:
        write_json_report(report, args.output)

    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
