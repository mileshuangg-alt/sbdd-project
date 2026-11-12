"""Preparation primitives for the Session 016 hepatocyte-clearance pilot."""

from __future__ import annotations

import math
from typing import Mapping


EXPECTED_CLEARANCE_UNIT = "uL.min-1.(10^6cells)-1"
ALLOWED_RELATIONS = frozenset({"=", "<", ">"})


def prepare_clearance_record(record: Mapping[str, str]) -> dict:
    """Prepare one authoritative human-hepatocyte clearance record.

    The source owner relation is preserved as censoring information:
      "=" -> exact regression observation
      "<" -> upper-bounded observation
      ">" -> lower-bounded observation

    The numeric target is log10(clearance). The source-recorded molecular
    representation is preserved unchanged.
    """
    activity_id = record["activity_id"]
    molecule_id = record["molecule_chembl_id"]
    smiles = record["owner_canonical_smiles"]
    relation = record["standard_relation"]
    units = record["standard_units"]

    if not activity_id:
        raise ValueError("missing activity_id")

    if not molecule_id:
        raise ValueError(f"{activity_id}: missing molecule_chembl_id")

    if not smiles:
        raise ValueError(f"{activity_id}: missing owner_canonical_smiles")

    if relation not in ALLOWED_RELATIONS:
        raise ValueError(
            f"{activity_id}: unsupported standard_relation {relation!r}"
        )

    if units != EXPECTED_CLEARANCE_UNIT:
        raise ValueError(
            f"{activity_id}: unexpected standard_units {units!r}"
        )

    try:
        clearance = float(record["standard_value"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{activity_id}: nonnumeric standard_value "
            f"{record['standard_value']!r}"
        ) from exc

    if not math.isfinite(clearance) or clearance <= 0:
        raise ValueError(
            f"{activity_id}: clearance must be finite and > 0; "
            f"got {clearance!r}"
        )

    log10_clearance = math.log10(clearance)

    result = {
        "activity_id": activity_id,
        "molecule_chembl_id": molecule_id,
        "smiles": smiles,
        "clearance": clearance,
        "log10_clearance": log10_clearance,
        "standard_relation": relation,
        "is_exact": relation == "=",
        "is_upper_bound": relation == "<",
        "is_lower_bound": relation == ">",
        "standard_units": units,
        "assay_chembl_id": record["assay_chembl_id"],
        "document_chembl_id": record["document_chembl_id"],
        "in_tdc_hepa_file": record["in_tdc_hepa_file"],
    }
    return result
