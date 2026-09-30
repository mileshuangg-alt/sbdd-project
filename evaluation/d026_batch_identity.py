from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Callable, TextIO

from evaluation.stage6_candidate_b_filter import (
    ZINC_METADATA_HEADER,
    ZincMetadataRecord,
    parse_zinc_metadata_line,
)


FILTERED_RECORDS_HEADER = (
    "smiles",
    "zinc_id",
    "source_file",
    "source_line_number",
)

OUTPUT_HEADER = (
    "smiles",
    "zinc_id",
    "zinc_inchikey",
    "d026_inchikey",
    "full_key_match",
    "connectivity_match",
    "source_file",
    "source_line_number",
)

QUARANTINE_OUTPUT_HEADER = (
    "smiles",
    "zinc_id",
    "source_file",
    "source_line_number",
    "quarantine_reasons",
)

DEFAULT_FILTERED_RECORDS = Path.home() / "stage6_candidate_b_frozen/filtered_records.tsv"
DEFAULT_SOURCE_ROOT = Path("/nfs/exl/zinc20/2D")

PILOT_FULL_KEY_MATCHES = 93
PILOT_RECORD_COUNT = 100
PILOT_CONNECTIVITY_MISMATCHES = 0
PILOT_MISMATCH_CASE_COUNTS = {
    "A_input_stereo_present_but_D026_key_empty_stereo_layer": 3,
    "B_input_stereo_absent_but_ZINC_key_has_stereo": 0,
    "C_both_keys_have_stereo_but_stereo_layer_differs": 4,
}
PILOT_SEVEN_RECORD_AUDIT_ARTIFACT = {
    "path": "/nfs/home/mhuang/stage6_candidate_b_d026_pilot/stereo_audit_7_mismatches.tsv",
    "sha256": "0fd004af4052729dc14c196833fea823d26dfbc6498aea6fd39a8b96bfb900f6",
    "role": "input/reference to this waiver",
    "rewritten_by_this_artifact": False,
}
PILOT_SUMMARY_ARTIFACT = {
    "path": "/nfs/home/mhuang/stage6_candidate_b_d026_pilot/stereo_audit_summary.json",
    "sha256": "a8e7bd2eace3f111f646d63b16c67becb732056b9a3e78c2a846b0f39bd10632",
    "role": "associated preserved pilot summary artifact",
}

D026_QUARANTINE_Q1 = re.compile(r"\[[Nn]\]")
D026_QUARANTINE_Q2 = re.compile(r"\[[Nn][^\]]*\][\\/]\(=O")


class D026BatchError(RuntimeError):
    """Raised when D026 batch lineage or source recovery fails."""


def inchikey_connectivity_layer(inchikey: str) -> str:
    return inchikey[:14]


def full_key_match(zinc_inchikey: str, d026_inchikey: str) -> bool:
    return zinc_inchikey == d026_inchikey


def connectivity_match(zinc_inchikey: str, d026_inchikey: str) -> bool:
    return inchikey_connectivity_layer(zinc_inchikey) == inchikey_connectivity_layer(
        d026_inchikey
    )


def classify_d026_quarantine(smiles: str) -> tuple[str, ...]:
    """Classify source-SMILES representations requiring D026 quarantine.

    Q1: bare bracketed nitrogen atom, e.g. [N].
    Q2: bracketed nitrogen followed by a directional bond into (=O),
        e.g. [N+]\\(=O) or [N+]/(=O).

    Returns deterministic reason codes in fixed order.
    """
    reasons = []

    if D026_QUARANTINE_Q1.search(smiles):
        reasons.append("D026_EXOTIC_VALENCE_Q1")

    if D026_QUARANTINE_Q2.search(smiles):
        reasons.append("D026_EXOTIC_VALENCE_Q2")

    return tuple(reasons)


def build_d026_quarantine_record(
    *,
    smiles: str,
    zinc_id: str,
    source_file: str,
    source_line_number: int,
    quarantine_reasons: tuple[str, ...],
) -> dict[str, object]:
    """Build the deterministic artifact record for a quarantined source row."""
    if not quarantine_reasons:
        raise ValueError("quarantine_reasons must contain at least one reason")

    record = {
        "smiles": smiles,
        "zinc_id": zinc_id,
        "source_file": source_file,
        "source_line_number": source_line_number,
        "quarantine_reasons": list(quarantine_reasons),
    }

    return record


def record_d026_quarantine(
    *,
    counts: dict[str, int],
) -> None:
    """Increment the quarantine count without retaining records in memory."""
    counts["quarantined_count"] += 1
    return None


def _default_smiles_to_inchikey(smiles: str) -> str:
    from evaluation.d026_identity import smiles_to_inchikey

    return smiles_to_inchikey(smiles)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _strip_record_terminator(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def _validate_source_header(header_line: str, source_file: str) -> None:
    header = tuple(_strip_record_terminator(header_line).split("\t"))
    if header != ZINC_METADATA_HEADER:
        raise D026BatchError(
            f"Invalid ZINC source header for {source_file}: "
            f"expected {ZINC_METADATA_HEADER!r}, found {header!r}"
        )


def _source_path(source_root: Path, source_file: str) -> Path:
    relative_path = Path(source_file)
    if len(relative_path.parts) > 1:
        return source_root / relative_path

    stem = relative_path.stem
    if len(stem) < 2:
        raise D026BatchError(
            f"Cannot derive source tranche directory from source_file={source_file!r}"
        )
    return source_root / stem[:2] / relative_path.name


def _count_filtered_records(filtered_records_path: Path) -> int:
    with filtered_records_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise D026BatchError("filtered_records.tsv is empty") from exc
        if header != FILTERED_RECORDS_HEADER:
            raise D026BatchError(
                f"Invalid filtered-record header: expected {FILTERED_RECORDS_HEADER!r}, "
                f"found {header!r}"
            )
        return sum(1 for _row in reader)


def _open_source(
    source_root: Path,
    source_file: str,
) -> tuple[Path, TextIO, int]:
    path = _source_path(source_root, source_file)
    handle = path.open("r", encoding="utf-8", newline="")
    header = handle.readline()
    if not header:
        handle.close()
        raise D026BatchError(f"Empty source file: {source_file}")
    _validate_source_header(header, source_file)
    return path, handle, 1


def _read_source_record_at_line(
    handle: TextIO,
    current_line_number: int,
    target_line_number: int,
    source_file: str,
) -> tuple[ZincMetadataRecord, int]:
    if target_line_number <= current_line_number:
        raise D026BatchError(
            f"Non-increasing source line request for {source_file}: "
            f"current line {current_line_number}, requested {target_line_number}"
        )

    line = ""
    while current_line_number < target_line_number:
        line = handle.readline()
        current_line_number += 1
        if not line:
            raise D026BatchError(
                f"Source file {source_file} ended before line {target_line_number}"
            )

    result = (
        parse_zinc_metadata_line(line, line_number=target_line_number),
        current_line_number,
    )

    return result


def _initial_counts() -> dict[str, int]:
    counts = {
        "processed_count": 0,
        "quarantined_count": 0,
        "full_key_matches": 0,
        "full_key_mismatches": 0,
        "connectivity_matches": 0,
        "connectivity_mismatches": 0,
    }

    return counts


def _fraction(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _summary(
    *,
    container_environment_id: str,
    input_artifact_sha256: str,
    input_record_count: int,
    counts: dict[str, int],
    stopping_status: str,
    first_connectivity_mismatch: dict | None,
) -> dict:
    processed_count = counts["processed_count"]

    summary = {
        "schema_version": 2,
        "container_environment_id": container_environment_id,
        "input_artifact_sha256": input_artifact_sha256,
        "input_record_count": input_record_count,
        "processed_count": processed_count,
        "full_key_matches": counts["full_key_matches"],
        "full_key_mismatches": counts["full_key_mismatches"],
        "connectivity_matches": counts["connectivity_matches"],
        "connectivity_mismatches": counts["connectivity_mismatches"],
        "connectivity_concordance_fraction": _fraction(
            counts["connectivity_matches"], processed_count
        ),
        "full_key_concordance_fraction": _fraction(
            counts["full_key_matches"], processed_count
        ),
        "stopping_status": stopping_status,
        "first_connectivity_mismatch": first_connectivity_mismatch,
        "quarantined_count": counts["quarantined_count"],
        "eligible_record_count": input_record_count - counts["quarantined_count"],
    }

    return summary


def transform_candidate_b_identities(
    filtered_records_path: Path | str,
    source_root: Path | str,
    output_tsv_path: Path | str,
    summary_json_path: Path | str,
    quarantine_tsv_path: Path | str,
    container_environment_id: str,
    smiles_to_inchikey: Callable[[str], str] | None = None,
) -> dict:
    """Transform Candidate-B identities with approved D026 quarantine handling."""
    filtered_records_path = Path(filtered_records_path)
    source_root = Path(source_root)
    output_tsv_path = Path(output_tsv_path)
    summary_json_path = Path(summary_json_path)
    quarantine_tsv_path = Path(quarantine_tsv_path)
    smiles_to_inchikey = smiles_to_inchikey or _default_smiles_to_inchikey

    input_artifact_sha256 = _sha256_file(filtered_records_path)
    input_record_count = _count_filtered_records(filtered_records_path)
    counts = _initial_counts()
    first_connectivity_mismatch = None
    stopping_status = "completed"
    exit_code = 0

    output_tsv_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    quarantine_tsv_path.parent.mkdir(parents=True, exist_ok=True)

    current_source_file = None
    current_source_handle = None
    current_source_line_number = 0

    try:
        with (
            filtered_records_path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as filtered_handle,
            output_tsv_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as output_handle,
            quarantine_tsv_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as quarantine_handle,
        ):
            reader = csv.DictReader(filtered_handle, delimiter="\t")
            if tuple(reader.fieldnames or ()) != FILTERED_RECORDS_HEADER:
                raise D026BatchError(
                    f"Invalid filtered-record header: expected {FILTERED_RECORDS_HEADER!r}, "
                    f"found {tuple(reader.fieldnames or ())!r}"
                )

            writer = csv.DictWriter(
                output_handle,
                fieldnames=OUTPUT_HEADER,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()

            quarantine_writer = csv.DictWriter(
                quarantine_handle,
                fieldnames=QUARANTINE_OUTPUT_HEADER,
                delimiter="\t",
                lineterminator="\n",
            )
            quarantine_writer.writeheader()

            for filtered_record in reader:
                source_file = filtered_record["source_file"]
                source_line_number = int(filtered_record["source_line_number"])
                smiles = filtered_record["smiles"]
                zinc_id = filtered_record["zinc_id"]

                quarantine_reasons = classify_d026_quarantine(smiles)
                if quarantine_reasons:
                    quarantine_record = build_d026_quarantine_record(
                        smiles=smiles,
                        zinc_id=zinc_id,
                        source_file=source_file,
                        source_line_number=source_line_number,
                        quarantine_reasons=quarantine_reasons,
                    )

                    record_d026_quarantine(
                        counts=counts,
                    )

                    quarantine_writer.writerow(
                        {
                            "smiles": quarantine_record["smiles"],
                            "zinc_id": quarantine_record["zinc_id"],
                            "source_file": quarantine_record["source_file"],
                            "source_line_number": quarantine_record[
                                "source_line_number"
                            ],
                            "quarantine_reasons": "|".join(
                                quarantine_record["quarantine_reasons"]
                            ),
                        }
                    )
                    continue

                if source_file != current_source_file:
                    if current_source_handle is not None:
                        current_source_handle.close()

                    (
                        _source_file_path,
                        current_source_handle,
                        current_source_line_number,
                    ) = _open_source(source_root, source_file)
                    current_source_file = source_file

                source_record, current_source_line_number = (
                    _read_source_record_at_line(
                        current_source_handle,
                        current_source_line_number,
                        source_line_number,
                        source_file,
                    )
                )

                if source_record.smiles != smiles:
                    raise D026BatchError(
                        f"SMILES lineage mismatch for {source_file}:{source_line_number}"
                    )

                if source_record.zinc_id != zinc_id:
                    raise D026BatchError(
                        f"ZINC ID lineage mismatch for {source_file}:{source_line_number}"
                    )

                d026_inchikey = smiles_to_inchikey(smiles)
                is_full_match = full_key_match(source_record.inchikey, d026_inchikey)
                is_connectivity_match = connectivity_match(
                    source_record.inchikey,
                    d026_inchikey,
                )

                counts["processed_count"] += 1

                if is_full_match:
                    counts["full_key_matches"] += 1
                else:
                    counts["full_key_mismatches"] += 1

                if is_connectivity_match:
                    counts["connectivity_matches"] += 1
                else:
                    counts["connectivity_mismatches"] += 1

                output_row = {
                    "smiles": smiles,
                    "zinc_id": zinc_id,
                    "zinc_inchikey": source_record.inchikey,
                    "d026_inchikey": d026_inchikey,
                    "full_key_match": _bool_text(is_full_match),
                    "connectivity_match": _bool_text(is_connectivity_match),
                    "source_file": source_file,
                    "source_line_number": source_line_number,
                }
                writer.writerow(output_row)

                if not is_connectivity_match:
                    first_connectivity_mismatch = {
                        "smiles": smiles,
                        "zinc_id": zinc_id,
                        "zinc_inchikey": source_record.inchikey,
                        "d026_inchikey": d026_inchikey,
                        "zinc_connectivity_layer": inchikey_connectivity_layer(
                            source_record.inchikey
                        ),
                        "d026_connectivity_layer": inchikey_connectivity_layer(
                            d026_inchikey
                        ),
                        "source_file": source_file,
                        "source_line_number": source_line_number,
                    }
                    stopping_status = "stopped_connectivity_mismatch"
                    exit_code = 1
                    break
    finally:
        if current_source_handle is not None:
            current_source_handle.close()

    summary = _summary(
        container_environment_id=container_environment_id,
        input_artifact_sha256=input_artifact_sha256,
        input_record_count=input_record_count,
        counts=counts,
        stopping_status=stopping_status,
        first_connectivity_mismatch=first_connectivity_mismatch,
    )
    _write_json(summary_json_path, summary)

    result = {
        "exit_code": exit_code,
        "summary": summary,
        "output_tsv": str(output_tsv_path),
        "summary_json": str(summary_json_path),
        "quarantine_tsv": str(quarantine_tsv_path),
    }

    return result


def d026_pilot_waiver() -> dict:
    waiver = {
        "schema_version": 1,
        "seven_record_audit_artifact": PILOT_SEVEN_RECORD_AUDIT_ARTIFACT,
        "pilot_summary_artifact": PILOT_SUMMARY_ARTIFACT,
        "d026_identity_authority": "D026-generated InChIKey",
        "structure_representation_for_downstream_stages": "original frozen SMILES",
        "zinc_stored_inchikey_role": "reference measurement for concordance only",
        "full_historical_zinc_inchikey_concordance_required": False,
        "connectivity_concordance_required": True,
        "pilot_connectivity_result": {
            "matches": 7,
            "mismatches": PILOT_CONNECTIVITY_MISMATCHES,
            "mismatch_panel_size": 7,
        },
        "pilot_full_key_result": {
            "matches": PILOT_FULL_KEY_MATCHES,
            "records": PILOT_RECORD_COUNT,
        },
        "mismatch_case_counts": PILOT_MISMATCH_CASE_COUNTS,
        "pilot_scope": (
            "qualification evidence, not proof that all 24,249,767 records "
            "behave identically"
        ),
    }

    return waiver


def write_d026_pilot_waiver(output_path: Path | str) -> dict:
    output_path = Path(output_path)
    waiver = d026_pilot_waiver()
    _write_json(output_path, waiver)

    result = {
        "waiver_output": str(output_path),
        "waiver_sha256": _sha256_file(output_path),
    }

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run D026 Candidate-B identity transformation."
    )
    parser.add_argument(
        "--filtered-records",
        default=str(DEFAULT_FILTERED_RECORDS),
        help="filtered_records.tsv from frozen Candidate-B filtering.",
    )
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help="Preserved BKS ZINC 2D source root.",
    )
    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--quarantine-tsv", required=True)
    parser.add_argument("--container-environment-id", required=True)
    parser.add_argument("--waiver-output")
    args = parser.parse_args(argv)

    if args.waiver_output:
        write_d026_pilot_waiver(args.waiver_output)

    result = transform_candidate_b_identities(
        filtered_records_path=args.filtered_records,
        source_root=args.source_root,
        output_tsv_path=args.output_tsv,
        summary_json_path=args.summary_json,
        quarantine_tsv_path=args.quarantine_tsv,
        container_environment_id=args.container_environment_id,
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
