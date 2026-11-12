"""Preparation primitives for the Session 016 pKa pilot.

This module contains scientifically consequential preparation logic.
Raw source records are classified, not silently discarded.
"""

from __future__ import annotations

import re
from typing import Mapping


BASE_TYPES = frozenset(f"pKaH{i}" for i in range(1, 6))
ACID_TYPES = frozenset(f"pKa{i}" for i in range(1, 7))
ALLOWED_ASSESSMENTS = frozenset({"Reliable", "Approximate"})

O6_O7_PATTERN = re.compile(r"(?<![A-Za-z0-9])O[67](?![A-Za-z0-9])")

EXPECTED_O6_O7_COMPOSITES = frozenset(
    {
        "O5, O6",
        "O6, R4",
        "O6, O7",
        "O7, R4",
        "O5, O7",
        "O6, O5",
        "O5/O6",
        "O5 and O6",
        "O6, E3bg",
        "O7,R4",
    }
)

EXPLICIT_MEDIUM_KEEP = frozenset(
    {
        "",
        "KCl",
        "phosphate and HCl",
    }
)

AMBIGUOUS_MEDIUM_EXCLUDE = {
    ("perrin_supp4324", "Hydrochloric acid"),
    ("perrin_supp6234", "alkale"),
}

# Exact source-version values whose interpretation is intentionally unnecessary
# when another settled criterion already excludes the record.
DEFER_IF_INDEPENDENTLY_INELIGIBLE = frozenset(
    {
        "HC",
        "In",
        "0.4M",
        "aqueous",
    }
)


def classify_medium(unique_id: str, cosolvent: str) -> str:
    """Classify the recorded medium under the approved Session 016 rule.

    Returns one of:
        keep
        ambiguous_exclude
        organic_exclude
        deuterated_exclude
        mineral_acid_alkali_exclude
        unresolved

    This function classifies only explicitly approved cases. It does not guess
    the meaning of unmatched source strings.
    """
    if cosolvent in EXPLICIT_MEDIUM_KEEP:
        return "keep"

    if (unique_id, cosolvent) in AMBIGUOUS_MEDIUM_EXCLUDE:
        return "ambiguous_exclude"

    lower = cosolvent.strip().lower()

    # Explicit deuterated media observed in this frozen source vocabulary.
    if (
        "d2o" in lower
        or "d2so4" in lower
        or lower == "dcl"
        or "dcl and d2so4" in lower
    ):
        return "deuterated_exclude"

    # Explicit organic cosolvent/media vocabulary observed in v2.4a.
    organic_tokens = (
        "ethanol",
        "methanol",
        "ch3oh",
        "dioxan",
        "dioxane",
        "n-propanol",
        "methanolic",
        "etoh",
    )
    if any(token in lower for token in organic_tokens):
        return "organic_exclude"

    # Explicit concentrated mineral-acid / alkali annotations.
    # The approved phosphate-buffer keep case has already returned above.
    mineral_or_alkali_tokens = (
        "h2so4",
        "hclo4",
        "hno3",
        "hbr",
        "naoh",
        "koh",
        "sulphuric acid",
        "nitric acid",
        "perchloric acid",
        "hydrochloric acid",
        "alkaline",
        "trichloroacetic acid",
        "trifluoroacetic acid",
        "methanesulphonic acid",
    )

    if lower == "hcl" or lower == "aq. hcl" or lower == "hcl":
        return "mineral_acid_alkali_exclude"

    if any(token in lower for token in mineral_or_alkali_tokens):
        return "mineral_acid_alkali_exclude"

    return "unresolved"


def classify_pka_record_eligibility(
    record: Mapping[str, str],
    *,
    side: str,
) -> dict:
    """Classify one raw IUPAC pKa measurement under settled pilot filters.

    Parameters
    ----------
    record
        One unmodified source CSV record.
    side
        "base" or "acid". This controls only the approved canonical step names.

    Returns
    -------
    dict
        Auditable measurement-level classification. No record is transformed
        or silently discarded.
    """
    if side not in {"base", "acid"}:
        raise ValueError("side must be 'base' or 'acid'")

    unique_id = record["unique_ID"]
    pka_type = record["pka_type"]
    assessment = record["assessment"]
    method = record["method"]
    cosolvent = record["cosolvent"]

    allowed_types = BASE_TYPES if side == "base" else ACID_TYPES

    step_ok = pka_type in allowed_types
    assessment_ok = assessment in ALLOWED_ASSESSMENTS
    method_o6_o7 = bool(O6_O7_PATTERN.search(method))
    method_ok = not method_o6_o7

    independently_eligible_before_medium = (
        step_ok and assessment_ok and method_ok
    )

    medium_class = classify_medium(unique_id, cosolvent)

    if medium_class == "keep":
        medium_ok = True
        medium_resolved = True
    elif medium_class in {
        "ambiguous_exclude",
        "organic_exclude",
        "deuterated_exclude",
        "mineral_acid_alkali_exclude",
    }:
        medium_ok = False
        medium_resolved = True
    else:
        medium_ok = False
        medium_resolved = False

    # An unresolved medium remains visible even when another settled criterion
    # already makes the record ineligible. It is never guessed into a class.
    eligible = (
        independently_eligible_before_medium
        and medium_resolved
        and medium_ok
    )

    reasons = []
    if not step_ok:
        reasons.append("noncanonical_step")
    if not assessment_ok:
        reasons.append("assessment_excluded")
    if method_o6_o7:
        reasons.append("o6_o7_method")
    if medium_class != "keep":
        reasons.append(f"medium_{medium_class}")

    result = {
        "unique_ID": unique_id,
        "side": side,
        "eligible": eligible,
        "step_ok": step_ok,
        "assessment_ok": assessment_ok,
        "method_ok": method_ok,
        "method_o6_o7": method_o6_o7,
        "medium_class": medium_class,
        "medium_ok": medium_ok,
        "medium_resolved": medium_resolved,
        "independently_eligible_before_medium": independently_eligible_before_medium,
        "reasons": tuple(reasons),
    }
    return result


def parse_temperature_celsius(value: str) -> float | None:
    """Parse a numeric source T value without interpreting free text."""
    text = value.strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def select_temperature_records(
    records: list[Mapping[str, str]],
) -> dict:
    """Apply the approved temperature preference to one molecule-step group.

    Input records are assumed already eligible under the measurement-level
    classifier and to belong to one unique_ID / canonical pKa-step group.

    Selection rule:
      1. If one or more records have T == 25 C, retain all such records.
      2. Otherwise retain all records with 20 <= T <= 30 C.
      3. Non-numeric/missing temperatures and values outside the window
         are not selected.

    This function selects measurements only. It does not aggregate pKa values.
    """
    parsed = [
        (record, parse_temperature_celsius(record["T"]))
        for record in records
    ]

    at_25 = [
        record
        for record, temperature in parsed
        if temperature == 25.0
    ]

    if at_25:
        selected = at_25
        selection_class = "exact_25"
    else:
        selected = [
            record
            for record, temperature in parsed
            if temperature is not None and 20.0 <= temperature <= 30.0
        ]
        selection_class = "window_20_30" if selected else "no_eligible_temperature"

    result = {
        "selected_records": selected,
        "selection_class": selection_class,
        "input_count": len(records),
        "selected_count": len(selected),
        "unparseable_temperature_count": sum(
            temperature is None
            for _, temperature in parsed
        ),
    }
    return result


def parse_numeric_pka(value: str) -> float | None:
    """Parse an exact numeric pKa value without interpreting qualifiers."""
    text = value.strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def aggregate_selected_pka_records(
    records: list[Mapping[str, str]],
) -> dict:
    """Aggregate selected records for one source-ID / canonical pKa step.

    Only exact numeric pKa strings contribute. Qualified, bounded, approximate
    notation in the value field, or ranges are never converted to point values.

    Returns an auditable result rather than silently dropping a group.
    """
    if not records:
        result = {
            "aggregatable": False,
            "median_pka": None,
            "replicate_count": 0,
            "spread": None,
            "numeric_values": (),
            "non_numeric_values": (),
        }
        return result

    parsed = [
        (record["pka_value"], parse_numeric_pka(record["pka_value"]))
        for record in records
    ]

    numeric_values = [value for _, value in parsed if value is not None]
    non_numeric_values = [
        raw for raw, value in parsed if value is None
    ]

    if not numeric_values:
        result = {
            "aggregatable": False,
            "median_pka": None,
            "replicate_count": 0,
            "spread": None,
            "numeric_values": (),
            "non_numeric_values": tuple(non_numeric_values),
        }
        return result

    values = sorted(numeric_values)
    n = len(values)

    if n % 2:
        median = values[n // 2]
    else:
        median = (values[n // 2 - 1] + values[n // 2]) / 2.0

    spread = max(values) - min(values)

    result = {
        "aggregatable": True,
        "median_pka": median,
        "replicate_count": n,
        "spread": spread,
        "numeric_values": tuple(values),
        "non_numeric_values": tuple(non_numeric_values),
    }
    return result
