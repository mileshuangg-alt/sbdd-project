"""Build frozen prepared endpoint artifacts for the Session 016 ADMET pilot."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path

from admet.scripts.prepare_clearance import prepare_clearance_record
from admet.scripts.prepare_pka import (
    aggregate_selected_pka_records,
    classify_pka_record_eligibility,
    select_temperature_records,
)


ROOT = Path(__file__).resolve().parents[2]

SOURCE_PK = (
    ROOT / "admet/data/source/bundle-v5/admet-src/pk"
)
PREPARED = ROOT / "admet/data/prepared"

PKA_SOURCE = SOURCE_PK / "iupac_pka_v2.4a.csv"
CLEARANCE_SOURCE = SOURCE_PK / "human_hepa_owner_408.csv"

PKA_OUTPUT = PREPARED / "pka_v2.4a_session016.csv"
CLEARANCE_OUTPUT = PREPARED / "human_hepa_408_session016.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def build_pka_rows(source_rows: list[dict[str, str]]) -> list[dict]:
    output = []

    for side in ("base", "acid"):
        groups = defaultdict(list)

        for row in source_rows:
            result = classify_pka_record_eligibility(row, side=side)
            if result["eligible"]:
                groups[(row["unique_ID"], row["pka_type"])].append(row)

        for (unique_id, step), records in sorted(groups.items()):
            temperature = select_temperature_records(records)

            if not temperature["selected_records"]:
                continue

            aggregation = aggregate_selected_pka_records(
                temperature["selected_records"]
            )

            if aggregation["numeric_values"] and aggregation["non_numeric_values"]:
                raise RuntimeError(
                    f"{unique_id}/{step}: mixed numeric/non-numeric "
                    "selected pKa values require review"
                )

            if not aggregation["aggregatable"]:
                continue

            smiles = {
                row["SMILES"]
                for row in temperature["selected_records"]
            }

            if len(smiles) != 1:
                raise RuntimeError(
                    f"{unique_id}/{step}: multiple source SMILES: {smiles}"
                )

            result = {
                "unique_ID": unique_id,
                "smiles": next(iter(smiles)),
                "side": side,
                "step": step,
                "pka": aggregation["median_pka"],
                "replicate_count": aggregation["replicate_count"],
                "spread": aggregation["spread"],
                "temperature_selection": temperature["selection_class"],
                "selected_measurement_count": temperature["selected_count"],
            }
            output.append(result)

    output.sort(
        key=lambda row: (
            row["unique_ID"],
            row["side"],
            row["step"],
        )
    )
    return output


def build_clearance_rows(
    source_rows: list[dict[str, str]],
) -> list[dict]:
    output = [
        prepare_clearance_record(row)
        for row in source_rows
    ]

    output.sort(key=lambda row: row["activity_id"])
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty artifact: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0])

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pka_source = read_csv(PKA_SOURCE)
    clearance_source = read_csv(CLEARANCE_SOURCE)

    if len(pka_source) != 24211:
        raise RuntimeError(
            f"unexpected pKa source count: {len(pka_source)}"
        )

    if len(clearance_source) != 408:
        raise RuntimeError(
            f"unexpected clearance source count: {len(clearance_source)}"
        )

    pka_rows = build_pka_rows(pka_source)
    clearance_rows = build_clearance_rows(clearance_source)

    if len(pka_rows) != 6752:
        raise RuntimeError(
            f"unexpected prepared pKa count: {len(pka_rows)}"
        )

    if len({row["unique_ID"] for row in pka_rows}) != 5474:
        raise RuntimeError(
            "unexpected prepared pKa source-ID count"
        )

    if len(clearance_rows) != 408:
        raise RuntimeError(
            f"unexpected prepared clearance count: {len(clearance_rows)}"
        )

    write_csv(PKA_OUTPUT, pka_rows)
    write_csv(CLEARANCE_OUTPUT, clearance_rows)

    print("=== SESSION 016 PREPARED DATASETS ===")
    print(
        f"pKa: {PKA_OUTPUT.relative_to(ROOT)} "
        f"rows={len(pka_rows)} sha256={sha256(PKA_OUTPUT)}"
    )
    print(
        f"clearance: {CLEARANCE_OUTPUT.relative_to(ROOT)} "
        f"rows={len(clearance_rows)} "
        f"sha256={sha256(CLEARANCE_OUTPUT)}"
    )


if __name__ == "__main__":
    main()
