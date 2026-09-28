from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO


ZINC_METADATA_HEADER = (
    "smiles",
    "zinc_id",
    "inchikey",
    "mwt",
    "logp",
    "reactive",
    "purchasable",
    "tranche_name",
    "features",
)


class ZincMetadataParseError(ValueError):
    """Raised when a ZINC 2D metadata line cannot be parsed."""


@dataclass(frozen=True)
class ZincMetadataRecord:
    smiles: str
    zinc_id: str
    inchikey: str
    mwt: float
    logp: float
    reactive: int
    purchasable: int
    tranche_name: str
    features: str


def _line_context(line_number: int | None) -> str:
    if line_number is None:
        return ""
    return f" at line {line_number}"


def _strip_record_terminator(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def parse_zinc_metadata_line(
    line: str,
    line_number: int | None = None,
) -> ZincMetadataRecord:
    line = _strip_record_terminator(line)
    fields = line.split("\t")

    if len(fields) != len(ZINC_METADATA_HEADER):
        raise ZincMetadataParseError(
            "Malformed ZINC metadata record"
            f"{_line_context(line_number)}: expected "
            f"{len(ZINC_METADATA_HEADER)} tab-delimited fields, "
            f"found {len(fields)}"
        )

    (
        smiles,
        zinc_id,
        inchikey,
        mwt_text,
        logp_text,
        reactive_text,
        purchasable_text,
        tranche_name,
        features,
    ) = fields

    try:
        mwt = float(mwt_text)
        logp = float(logp_text)
        reactive = int(reactive_text)
        purchasable = int(purchasable_text)
    except ValueError as exc:
        raise ZincMetadataParseError(
            "Invalid numeric field in ZINC metadata record"
            f"{_line_context(line_number)}"
        ) from exc

    return ZincMetadataRecord(
        smiles=smiles,
        zinc_id=zinc_id,
        inchikey=inchikey,
        mwt=mwt,
        logp=logp,
        reactive=reactive,
        purchasable=purchasable,
        tranche_name=tranche_name,
        features=features,
    )


def passes_literature_filter(record: ZincMetadataRecord) -> bool:
    return (
        record.mwt <= 250.0
        and record.logp <= 3.5
        and record.reactive in (30, 50)
        and record.purchasable >= 10
    )


def _validate_header(header_line: str, source_name: str) -> None:
    header = tuple(_strip_record_terminator(header_line).split("\t"))
    if header != ZINC_METADATA_HEADER:
        raise ZincMetadataParseError(
            f"Invalid ZINC metadata header in {source_name}: "
            f"expected {ZINC_METADATA_HEADER!r}, found {header!r}"
        )


def _write_tsv_row(handle: TextIO, values: Iterable[object]) -> None:
    handle.write("\t".join(str(value) for value in values))
    handle.write("\n")


def _json_text(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _process_one_file(
    input_path: Path,
    filtered_handle: TextIO,
    malformed_handle: TextIO,
) -> dict:
    source_file = input_path.name
    counts = {
        "input_records": 0,
        "accepted_records": 0,
        "rejected_records": 0,
        "malformed_records": 0,
    }
    input_digest = hashlib.sha256()

    with input_path.open("rb") as raw_handle:
        raw_header = raw_handle.readline()
        if not raw_header:
            raise ZincMetadataParseError(
                f"Missing ZINC metadata header in {source_file}"
            )
        input_digest.update(raw_header)
        _validate_header(raw_header.decode("utf-8"), source_file)

        for line_number, raw_line in enumerate(raw_handle, start=2):
            input_digest.update(raw_line)
            line = raw_line.decode("utf-8")
            counts["input_records"] += 1

            try:
                record = parse_zinc_metadata_line(
                    line,
                    line_number=line_number,
                )
            except ZincMetadataParseError as exc:
                counts["malformed_records"] += 1
                _write_tsv_row(
                    malformed_handle,
                    (
                        source_file,
                        line_number,
                        exc,
                        _json_text(_strip_record_terminator(line)),
                    ),
                )
                continue

            if passes_literature_filter(record):
                counts["accepted_records"] += 1
                _write_tsv_row(
                    filtered_handle,
                    (
                        record.smiles,
                        record.zinc_id,
                        source_file,
                        line_number,
                    ),
                )
            else:
                counts["rejected_records"] += 1

    return {
        "source_file": source_file,
        "source_sha256": input_digest.hexdigest(),
        "header": list(ZINC_METADATA_HEADER),
        "counts": counts,
    }


def process_zinc_metadata_files(
    input_paths: Iterable[Path | str],
    output_dir: Path | str,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(Path(path) for path in input_paths)
    if not paths:
        raise ValueError("At least one input file is required")

    filtered_path = output_dir / "filtered_records.tsv"
    malformed_path = output_dir / "malformed_records.tsv"
    per_input_manifest_path = output_dir / "per_input_manifest.json"
    aggregate_manifest_path = output_dir / "aggregate_manifest.json"
    checksums_path = output_dir / "checksums.sha256"

    per_file_manifests = []
    with filtered_path.open("w", encoding="utf-8", newline="\n") as filtered_handle:
        with malformed_path.open("w", encoding="utf-8", newline="\n") as malformed_handle:
            _write_tsv_row(
                filtered_handle,
                ("smiles", "zinc_id", "source_file", "source_line_number"),
            )
            _write_tsv_row(
                malformed_handle,
                ("source_file", "source_line_number", "error", "record_json"),
            )
            for input_path in paths:
                per_file_manifests.append(
                    _process_one_file(
                        input_path,
                        filtered_handle,
                        malformed_handle,
                    )
                )

    aggregate_counts = {
        "input_records": sum(
            item["counts"]["input_records"] for item in per_file_manifests
        ),
        "accepted_records": sum(
            item["counts"]["accepted_records"] for item in per_file_manifests
        ),
        "rejected_records": sum(
            item["counts"]["rejected_records"] for item in per_file_manifests
        ),
        "malformed_records": sum(
            item["counts"]["malformed_records"] for item in per_file_manifests
        ),
    }

    _write_json(
        per_input_manifest_path,
        {
            "schema_version": 1,
            "inputs": per_file_manifests,
        },
    )

    artifact_hashes = {
        filtered_path.name: sha256_file(filtered_path),
        malformed_path.name: sha256_file(malformed_path),
        per_input_manifest_path.name: sha256_file(per_input_manifest_path),
    }
    aggregate_manifest = {
        "schema_version": 1,
        "filter": {
            "mwt_max": 250.0,
            "logp_max": 3.5,
            "reactive_allowed": [30, 50],
            "purchasable_min": 10,
        },
        "input_files": [path.name for path in paths],
        "counts": aggregate_counts,
        "artifacts": artifact_hashes,
    }
    _write_json(aggregate_manifest_path, aggregate_manifest)
    artifact_hashes[aggregate_manifest_path.name] = sha256_file(
        aggregate_manifest_path
    )

    with checksums_path.open("w", encoding="utf-8", newline="\n") as handle:
        for name in sorted(artifact_hashes):
            handle.write(f"{artifact_hashes[name]}  {name}\n")
    artifact_hashes[checksums_path.name] = sha256_file(checksums_path)

    return {
        "output_dir": str(output_dir),
        "filtered_records": str(filtered_path),
        "malformed_records": str(malformed_path),
        "per_input_manifest": str(per_input_manifest_path),
        "aggregate_manifest": str(aggregate_manifest_path),
        "checksums": str(checksums_path),
        "counts": aggregate_counts,
        "artifacts": artifact_hashes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Filter BKS ZINC pre-how2 2D metadata exports."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for deterministic filtered outputs and manifests.",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="One or more tab-delimited ZINC 2D metadata .txt files.",
    )
    args = parser.parse_args(argv)

    result = process_zinc_metadata_files(args.inputs, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
