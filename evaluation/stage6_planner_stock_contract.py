"""Scientific-core primitives for Stage-6 planner-stock construction.

D028 freezes the full D026-generated InChIKey as the authoritative
molecular identity. Planner-specific representations must derive from
that frozen identity record without silently redefining molecular identity.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


_INCHIKEY_RE = re.compile(r"^[A-Z]{14}-[A-Z]{10}-[A-Z]$")

_REQUIRED_SOURCE_FIELDS = (
    "smiles",
    "zinc_id",
    "zinc_inchikey",
    "d026_inchikey",
    "full_key_match",
    "connectivity_match",
    "source_file",
    "source_line_number",
)

ASKCOS_STATUS_REPRESENTABLE = "representable"
ASKCOS_STATUS_REPRESENTATION_FAILURE = "representation_failure"
ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED = "canonical_collision_excluded"

_ASKCOS_REPRESENTATION_STATUSES = frozenset(
    {
        ASKCOS_STATUS_REPRESENTABLE,
        ASKCOS_STATUS_REPRESENTATION_FAILURE,
        ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED,
    }
)


def read_frozen_identity_record(row: Mapping[str, Any]) -> dict[str, str]:
    """Read one frozen D026/D027 identity-stock record without transforming it.

    The full D026-generated InChIKey is the authoritative molecular identity.
    The original frozen SMILES is preserved exactly for later structure-consuming
    transformations.

    This function performs source-contract validation only. It does not
    canonicalize SMILES, deduplicate records, determine ASKCOS representability,
    detect cross-record collisions, or decide planner-stock inclusion.
    """

    missing_fields = [
        field for field in _REQUIRED_SOURCE_FIELDS if field not in row
    ]
    if missing_fields:
        raise ValueError(
            "missing required frozen-source field(s): "
            + ", ".join(missing_fields)
        )

    smiles = row["smiles"]
    d026_inchikey = row["d026_inchikey"]

    if not isinstance(smiles, str) or smiles == "":
        raise ValueError("frozen source SMILES must be a non-empty string")

    if not isinstance(d026_inchikey, str) or d026_inchikey == "":
        raise ValueError(
            "D026 InChIKey must be a non-empty string"
        )

    if _INCHIKEY_RE.fullmatch(d026_inchikey) is None:
        raise ValueError(
            f"invalid full D026 InChIKey format: {d026_inchikey!r}"
        )

    result = {
        "smiles": smiles,
        "d026_inchikey": d026_inchikey,
        "zinc_id": str(row["zinc_id"]),
        "zinc_inchikey": str(row["zinc_inchikey"]),
        "full_key_match": str(row["full_key_match"]),
        "connectivity_match": str(row["connectivity_match"]),
        "source_file": str(row["source_file"]),
        "source_line_number": str(row["source_line_number"]),
    }
    return result


def measure_d026_identity_inventory(
    records: Iterable[Mapping[str, Any]],
    connection: sqlite3.Connection,
) -> dict[str, int]:
    """Measure multiplicity of authoritative D026 identities exactly.

    Each input row is first validated through ``read_frozen_identity_record``.
    The full D026-generated InChIKey is the only identity used for counting.

    This function measures source-record multiplicity only. It does not
    deduplicate planner stock, canonicalize SMILES, identify ASKCOS
    representation collisions, or decide planner-stock eligibility.
    """

    with connection:
        connection.execute(
            "DROP TABLE IF EXISTS d026_identity_inventory"
        )
        connection.execute(
            """
            CREATE TABLE d026_identity_inventory (
                d026_inchikey TEXT PRIMARY KEY,
                occurrence_count INTEGER NOT NULL
            )
            """
        )

        total_records = 0

        for row in records:
            source_record = read_frozen_identity_record(row)
            d026_inchikey = source_record["d026_inchikey"]

            connection.execute(
                """
                INSERT INTO d026_identity_inventory (
                    d026_inchikey,
                    occurrence_count
                )
                VALUES (?, 1)
                ON CONFLICT(d026_inchikey)
                DO UPDATE SET
                    occurrence_count = occurrence_count + 1
                """,
                (d026_inchikey,),
            )
            total_records += 1

        unique_d026_keys = connection.execute(
            """
            SELECT COUNT(*)
            FROM d026_identity_inventory
            """
        ).fetchone()[0]

        duplicate_d026_keys = connection.execute(
            """
            SELECT COUNT(*)
            FROM d026_identity_inventory
            WHERE occurrence_count > 1
            """
        ).fetchone()[0]

    duplicate_rows = total_records - unique_d026_keys

    result = {
        "total_records": total_records,
        "unique_d026_keys": unique_d026_keys,
        "duplicate_rows": duplicate_rows,
        "duplicate_d026_keys": duplicate_d026_keys,
    }
    return result


def write_d026_duplicate_identity_report(
    connection: sqlite3.Connection,
    output_path: str | Path,
) -> dict[str, int]:
    """Write a deterministic audit of D026 identities with source multiplicity.

    The inventory table must already have been created by
    ``measure_d026_identity_inventory``.

    This report is descriptive only. A repeated authoritative D026 identity
    is not an ASKCOS representation collision and does not by itself trigger
    planner-stock exclusion.
    """

    output_path = Path(output_path)

    duplicate_rows = connection.execute(
        """
        SELECT d026_inchikey, occurrence_count
        FROM d026_identity_inventory
        WHERE occurrence_count > 1
        ORDER BY d026_inchikey ASC
        """
    )

    duplicate_d026_keys = 0
    represented_source_rows = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("d026_inchikey\toccurrence_count\n")

        for d026_inchikey, occurrence_count in duplicate_rows:
            handle.write(
                f"{d026_inchikey}\t{occurrence_count}\n"
            )
            duplicate_d026_keys += 1
            represented_source_rows += occurrence_count

    result = {
        "duplicate_d026_keys": duplicate_d026_keys,
        "represented_source_rows": represented_source_rows,
    }
    return result


def write_aizynthfinder_d026_key_stock(
    connection: sqlite3.Connection,
    output_path: str | Path,
) -> dict[str, int]:
    """Write the deterministic AiZynthFinder-facing D026 identity set.

    The inventory table must already have been created by
    ``measure_d026_identity_inventory``.

    Each full D026 InChIKey is emitted exactly once, in lexicographic order.
    No molecular identity is regenerated from SMILES and no connectivity-only
    reduction is permitted here.

    This artifact defines planner-facing molecular membership. Conversion into
    a build-specific AiZynthFinder storage container is a later mechanical
    ingestion step and must preserve this exact key set.
    """

    output_path = Path(output_path)

    rows = connection.execute(
        """
        SELECT d026_inchikey
        FROM d026_identity_inventory
        ORDER BY d026_inchikey ASC
        """
    )

    stock_keys_written = 0

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for (d026_inchikey,) in rows:
            handle.write(f"{d026_inchikey}\n")
            stock_keys_written += 1

    result = {
        "stock_keys_written": stock_keys_written,
    }
    return result


def compute_d026_identity_set_sha256(
    connection: sqlite3.Connection,
) -> dict[str, int | str]:
    """Hash the exact sorted set of authoritative full D026 identities.

    The inventory table must already have been created by
    ``measure_d026_identity_inventory``.

    Serialization is frozen as lexicographically sorted full D026 InChIKeys,
    each UTF-8 encoded and terminated by exactly one newline.

    This hash is an audit quantity for molecular-set membership. It does not
    replace complete set comparison.
    """

    rows = connection.execute(
        """
        SELECT d026_inchikey
        FROM d026_identity_inventory
        ORDER BY d026_inchikey ASC
        """
    )

    digest = hashlib.sha256()
    identity_count = 0

    for (d026_inchikey,) in rows:
        digest.update(d026_inchikey.encode("utf-8"))
        digest.update(b"\n")
        identity_count += 1

    result = {
        "identity_count": identity_count,
        "identity_set_sha256": digest.hexdigest(),
    }
    return result


def make_askcos_representation_result(
    source_record: Mapping[str, Any],
    *,
    status: str,
    canonical_smiles: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, str | None]:
    """Construct one pre-collision ASKCOS representation result.

    This function records the outcome of planner-specific molecular encoding.
    It does not perform canonicalization itself and it does not perform
    cross-record collision detection.

    Under D028, row-level representation may be either ``representable`` or
    ``representation_failure``. ``canonical_collision_excluded`` is reserved
    for the later dataset-level collision pass because collision is a property
    of multiple D026 identities mapping to the same ASKCOS lookup string.
    """

    frozen_record = read_frozen_identity_record(source_record)

    if status not in _ASKCOS_REPRESENTATION_STATUSES:
        raise ValueError(
            f"unknown ASKCOS representation status: {status!r}"
        )

    if status == ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED:
        raise ValueError(
            "canonical collision status may only be assigned by the "
            "dataset-level collision pass"
        )

    if status == ASKCOS_STATUS_REPRESENTABLE:
        if not isinstance(canonical_smiles, str) or canonical_smiles == "":
            raise ValueError(
                "representable ASKCOS result requires non-empty canonical SMILES"
            )
        if failure_reason is not None:
            raise ValueError(
                "representable ASKCOS result cannot carry a failure reason"
            )

    if status == ASKCOS_STATUS_REPRESENTATION_FAILURE:
        if canonical_smiles is not None:
            raise ValueError(
                "ASKCOS representation failure cannot carry canonical SMILES"
            )
        if not isinstance(failure_reason, str) or failure_reason == "":
            raise ValueError(
                "ASKCOS representation failure requires a non-empty reason"
            )

    result = {
        "d026_inchikey": frozen_record["d026_inchikey"],
        "source_smiles": frozen_record["smiles"],
        "askcos_status": status,
        "canonical_smiles": canonical_smiles,
        "representation_failure_reason": failure_reason,
    }
    return result


def canonicalize_askcos_smiles(
    source_record: Mapping[str, Any],
) -> dict[str, str | None]:
    """Create the ASKCOS canonical single-component SMILES.

    The frozen source SMILES is parsed directly with RDKit. The molecule must
    contain exactly one disconnected component. No fragment selection,
    neutralization, tautomer normalization, stereo removal, or other
    identity-changing standardization is performed.

    Canonicalization uses RDKit's canonical isomeric SMILES representation.
    """

    source = read_frozen_identity_record(source_record)
    source_smiles = source["smiles"]

    try:
        from rdkit import Chem
    except ImportError as exc:
        raise RuntimeError(
            "RDKit is required for ASKCOS SMILES representation"
        ) from exc

    try:
        mol = Chem.MolFromSmiles(source_smiles)
    except Exception as exc:
        result = {
            "d026_inchikey": source["d026_inchikey"],
            "source_smiles": source_smiles,
            "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
            "canonical_smiles": None,
            "representation_failure_reason": (
                f"ASKCOS_RDKit_EXCEPTION:{type(exc).__name__}"
            ),
        }
        return result

    if mol is None:
        result = {
            "d026_inchikey": source["d026_inchikey"],
            "source_smiles": source_smiles,
            "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
            "canonical_smiles": None,
            "representation_failure_reason": "ASKCOS_PARSE_FAILURE",
        }
        return result

    fragments = Chem.GetMolFrags(mol, asMols=False, sanitizeFrags=False)

    if len(fragments) != 1:
        result = {
            "d026_inchikey": source["d026_inchikey"],
            "source_smiles": source_smiles,
            "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
            "canonical_smiles": None,
            "representation_failure_reason": (
                f"ASKCOS_MULTIPLE_COMPONENTS:{len(fragments)}"
            ),
        }
        return result

    try:
        canonical_smiles = Chem.MolToSmiles(
            mol,
            isomericSmiles=True,
            canonical=True,
        )
    except Exception as exc:
        result = {
            "d026_inchikey": source["d026_inchikey"],
            "source_smiles": source_smiles,
            "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
            "canonical_smiles": None,
            "representation_failure_reason": (
                f"ASKCOS_CANONICALIZATION_EXCEPTION:{type(exc).__name__}"
            ),
        }
        return result

    if canonical_smiles == "":
        result = {
            "d026_inchikey": source["d026_inchikey"],
            "source_smiles": source_smiles,
            "askcos_status": ASKCOS_STATUS_REPRESENTATION_FAILURE,
            "canonical_smiles": None,
            "representation_failure_reason": "ASKCOS_EMPTY_CANONICAL_SMILES",
        }
        return result

    result = {
        "d026_inchikey": source["d026_inchikey"],
        "source_smiles": source_smiles,
        "askcos_status": ASKCOS_STATUS_REPRESENTABLE,
        "canonical_smiles": canonical_smiles,
        "representation_failure_reason": None,
    }
    return result

def measure_askcos_canonical_collisions(
    records: Iterable[Mapping[str, Any]],
    connection: sqlite3.Connection,
) -> dict[str, int]:
    """Measure distinct D026 identities sharing an ASKCOS canonical SMILES.

    Every source record is transformed with ``canonicalize_askcos_smiles``.
    Representation failures are counted and excluded from collision analysis.

    A collision exists only when one canonical ASKCOS SMILES is associated
    with more than one distinct full D026 InChIKey. Repeated source rows for
    the same D026 identity do not constitute a collision.

    Under D028, all D026 identities in a collision group are later excluded
    from planner stock and logged. This function only measures the affected
    identities; it does not perform the exclusion itself.
    """

    with connection:
        connection.execute(
            "DROP TABLE IF EXISTS askcos_representations"
        )
        connection.execute(
            """
            CREATE TABLE askcos_representations (
                d026_inchikey TEXT NOT NULL,
                canonical_smiles TEXT NOT NULL,
                PRIMARY KEY (d026_inchikey, canonical_smiles)
            )
            """
        )

        total_source_records = 0
        representable_source_records = 0
        representation_failure_records = 0

        for row in records:
            total_source_records += 1
            result = canonicalize_askcos_smiles(row)

            if result["askcos_status"] == ASKCOS_STATUS_REPRESENTATION_FAILURE:
                representation_failure_records += 1
                continue

            canonical_smiles = result["canonical_smiles"]
            d026_inchikey = result["d026_inchikey"]

            if not isinstance(canonical_smiles, str) or canonical_smiles == "":
                raise ValueError(
                    "representable ASKCOS result must contain canonical SMILES"
                )
            if not isinstance(d026_inchikey, str) or d026_inchikey == "":
                raise ValueError(
                    "representable ASKCOS result must contain D026 identity"
                )

            connection.execute(
                """
                INSERT OR IGNORE INTO askcos_representations (
                    d026_inchikey,
                    canonical_smiles
                )
                VALUES (?, ?)
                """,
                (d026_inchikey, canonical_smiles),
            )
            representable_source_records += 1

        distinct_representable_keys = connection.execute(
            """
            SELECT COUNT(DISTINCT d026_inchikey)
            FROM askcos_representations
            """
        ).fetchone()[0]

        collision_canonical_smiles = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT canonical_smiles
                FROM askcos_representations
                GROUP BY canonical_smiles
                HAVING COUNT(DISTINCT d026_inchikey) > 1
            )
            """
        ).fetchone()[0]

        collision_d026_keys = connection.execute(
            """
            SELECT COUNT(DISTINCT d026_inchikey)
            FROM askcos_representations
            WHERE canonical_smiles IN (
                SELECT canonical_smiles
                FROM askcos_representations
                GROUP BY canonical_smiles
                HAVING COUNT(DISTINCT d026_inchikey) > 1
            )
            """
        ).fetchone()[0]

    result = {
        "total_source_records": total_source_records,
        "representable_source_records": representable_source_records,
        "representation_failure_records": representation_failure_records,
        "distinct_representable_d026_keys": distinct_representable_keys,
        "collision_canonical_smiles": collision_canonical_smiles,
        "collision_d026_keys": collision_d026_keys,
    }
    return result

def write_askcos_collision_exclusion_report(
    connection: sqlite3.Connection,
    output_path: str | Path,
) -> dict[str, int]:
    """Write the complete D028 collision-exclusion audit artifact.

    The ``askcos_representations`` table must already have been populated by
    ``measure_askcos_canonical_collisions``.

    Every D026 identity belonging to a canonical-SMILES collision group is
    emitted. Collision groups are ordered by canonical SMILES and D026
    identities are ordered within each group.

    Under D028 Amendment 1, these identities are excluded from planner stock
    but remain members of the frozen D026 molecular universe.
    """

    output_path = Path(output_path)

    rows = connection.execute(
        """
        SELECT canonical_smiles, d026_inchikey
        FROM askcos_representations
        WHERE canonical_smiles IN (
            SELECT canonical_smiles
            FROM askcos_representations
            GROUP BY canonical_smiles
            HAVING COUNT(DISTINCT d026_inchikey) > 1
        )
        ORDER BY canonical_smiles ASC, d026_inchikey ASC
        """
    )

    collision_d026_keys = 0
    collision_canonical_smiles = set()

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("canonical_smiles\td026_inchikey\n")

        for canonical_smiles, d026_inchikey in rows:
            handle.write(
                f"{canonical_smiles}\t{d026_inchikey}\n"
            )
            collision_d026_keys += 1
            collision_canonical_smiles.add(canonical_smiles)

    result = {
        "collision_canonical_smiles": len(collision_canonical_smiles),
        "collision_d026_keys": collision_d026_keys,
    }
    return result

def write_askcos_qualified_stock(
    connection: sqlite3.Connection,
    output_path: str | Path,
) -> dict[str, int]:
    """Write the qualified ASKCOS planner-stock identity set.

    The ``askcos_representations`` table must have been populated by
    ``measure_askcos_canonical_collisions``.

    Inclusion rule under D028:
      * representable records are eligible;
      * any canonical-SMILES collision group is excluded wholesale;
      * representation failures are not present in this table and therefore
        remain documented outside the qualified stock.

    The frozen D026 molecular universe is not modified by this function.
    """

    output_path = Path(output_path)

    rows = connection.execute(
        """
        SELECT d026_inchikey, canonical_smiles
        FROM askcos_representations
        WHERE canonical_smiles NOT IN (
            SELECT canonical_smiles
            FROM askcos_representations
            GROUP BY canonical_smiles
            HAVING COUNT(DISTINCT d026_inchikey) > 1
        )
        ORDER BY d026_inchikey ASC
        """
    )

    qualified_d026_keys = 0
    qualified_canonical_smiles = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("d026_inchikey\tcanonical_smiles\n")

        for d026_inchikey, canonical_smiles in rows:
            handle.write(
                f"{d026_inchikey}\t{canonical_smiles}\n"
            )
            qualified_d026_keys += 1
            qualified_canonical_smiles += 1

    result = {
        "qualified_d026_keys": qualified_d026_keys,
        "qualified_canonical_smiles": qualified_canonical_smiles,
    }
    return result

def build_askcos_identity_accounting(
    records: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, str | None]], dict[str, int]]:
    """Classify each unique frozen D026 identity into one ASKCOS state.

    States are mutually exclusive and defined by D028:

      representation_failure
          ASKCOS could not encode the frozen molecule.

      canonical_collision_excluded
          The molecule was representable, but its canonical ASKCOS SMILES was
          shared by another distinct D026 identity.

      qualified
          The molecule was representable and its canonical ASKCOS SMILES was
          unique among representable D026 identities.

    Repeated frozen source rows for one D026 identity are collapsed during
    accounting. The frozen molecular universe itself is not modified.

    The returned records are sorted deterministically by D026 InChIKey.
    """

    materialized_records = list(records)

    seen_source_keys: dict[str, dict[str, Any]] = {}

    for row in materialized_records:
        source_record = read_frozen_identity_record(row)
        d026_inchikey = source_record["d026_inchikey"]

        if d026_inchikey in seen_source_keys:
            continue

        seen_source_keys[d026_inchikey] = source_record

    row_results: dict[str, dict[str, str | None]] = {}
    canonical_to_d026: dict[str, set[str]] = {}

    for d026_inchikey in sorted(seen_source_keys):
        source_record = seen_source_keys[d026_inchikey]
        representation = canonicalize_askcos_smiles(source_record)

        row_results[d026_inchikey] = representation

        if representation["askcos_status"] == ASKCOS_STATUS_REPRESENTABLE:
            canonical_smiles = representation["canonical_smiles"]

            if not isinstance(canonical_smiles, str) or canonical_smiles == "":
                raise ValueError(
                    "representable ASKCOS identity accounting requires "
                    "non-empty canonical SMILES"
                )

            canonical_to_d026.setdefault(
                canonical_smiles,
                set(),
            ).add(d026_inchikey)

    collision_d026_keys: set[str] = set()

    for d026_keys in canonical_to_d026.values():
        if len(d026_keys) > 1:
            collision_d026_keys.update(d026_keys)

    accounting_records: list[dict[str, str | None]] = []

    representation_failures = 0
    collision_exclusions = 0
    qualified_keys = 0

    for d026_inchikey in sorted(row_results):
        representation = row_results[d026_inchikey]
        status = representation["askcos_status"]

        if status == ASKCOS_STATUS_REPRESENTATION_FAILURE:
            accounting_status = ASKCOS_STATUS_REPRESENTATION_FAILURE
            representation_failures += 1
        elif d026_inchikey in collision_d026_keys:
            accounting_status = ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED
            collision_exclusions += 1
        else:
            accounting_status = "qualified"
            qualified_keys += 1

        accounting_records.append(
            {
                "d026_inchikey": d026_inchikey,
                "askcos_status": accounting_status,
                "canonical_smiles": representation["canonical_smiles"],
                "representation_failure_reason": (
                    representation["representation_failure_reason"]
                ),
            }
        )

    result_summary = {
        "unique_frozen_d026_keys": len(seen_source_keys),
        "representation_failure_keys": representation_failures,
        "canonical_collision_excluded_keys": collision_exclusions,
        "qualified_keys": qualified_keys,
    }

    if (
        representation_failures
        + collision_exclusions
        + qualified_keys
        != len(seen_source_keys)
    ):
        raise AssertionError(
            "ASKCOS identity accounting partition does not reconcile"
        )

    return accounting_records, result_summary

def write_askcos_identity_accounting_report(
    accounting_records: Iterable[Mapping[str, Any]],
    output_path: str | Path,
) -> dict[str, int]:
    """Write the complete deterministic ASKCOS identity-accounting artifact.

    Exactly one row is written for each unique frozen D026 identity.
    Records are ordered by full D026 InChIKey.

    The artifact preserves the D028 distinction between representation
    failures, collision exclusions, and qualified planner-stock identities.
    """

    output_path = Path(output_path)

    records = sorted(
        accounting_records,
        key=lambda record: str(record["d026_inchikey"]),
    )

    seen_d026_keys: set[str] = set()
    status_counts = {
        ASKCOS_STATUS_REPRESENTATION_FAILURE: 0,
        ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED: 0,
        "qualified": 0,
    }

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "d026_inchikey\taskcos_status\tcanonical_smiles\t"
            "representation_failure_reason\n"
        )

        for record in records:
            d026_inchikey = record["d026_inchikey"]
            status = record["askcos_status"]
            canonical_smiles = record["canonical_smiles"]
            failure_reason = record["representation_failure_reason"]

            if not isinstance(d026_inchikey, str) or d026_inchikey == "":
                raise ValueError(
                    "ASKCOS accounting report requires a D026 InChIKey"
                )

            if d026_inchikey in seen_d026_keys:
                raise ValueError(
                    f"duplicate D026 key in accounting records: "
                    f"{d026_inchikey}"
                )

            if status not in status_counts:
                raise ValueError(
                    f"unknown ASKCOS accounting status: {status!r}"
                )

            if status == ASKCOS_STATUS_REPRESENTATION_FAILURE:
                if canonical_smiles is not None:
                    raise ValueError(
                        "representation failure cannot contain canonical SMILES"
                    )
                if not isinstance(failure_reason, str) or failure_reason == "":
                    raise ValueError(
                        "representation failure requires a failure reason"
                    )
                canonical_field = ""
                failure_field = failure_reason

            else:
                if not isinstance(canonical_smiles, str) or canonical_smiles == "":
                    raise ValueError(
                        "representable ASKCOS accounting row requires "
                        "canonical SMILES"
                    )
                if failure_reason is not None:
                    raise ValueError(
                        "representable ASKCOS accounting row cannot contain "
                        "a failure reason"
                    )
                canonical_field = canonical_smiles
                failure_field = ""

            handle.write(
                f"{d026_inchikey}\t"
                f"{status}\t"
                f"{canonical_field}\t"
                f"{failure_field}\n"
            )

            seen_d026_keys.add(d026_inchikey)
            status_counts[status] += 1

    result = {
        "total_d026_keys": len(seen_d026_keys),
        "representation_failure_keys": (
            status_counts[ASKCOS_STATUS_REPRESENTATION_FAILURE]
        ),
        "canonical_collision_excluded_keys": (
            status_counts[ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED]
        ),
        "qualified_keys": status_counts["qualified"],
    }
    return result

def compute_askcos_identity_sets_and_proof(
    accounting_records: Iterable[Mapping[str, Any]],
    aizynthfinder_keys: Iterable[str],
) -> dict[str, Any]:
    """Compute ASKCOS identity subsets and prove representable-set equality.

    The authorized D028 claim is:
        set equality across all representable keys.

    Representation failures are explicitly exempted from equality.
    Canonical-collision exclusions remain in the representable frozen domain
    but are excluded from the qualified ASKCOS planner stock.

    The proof uses complete set differences, not hashes alone. Hashes are
    deterministic audit quantities over sorted full D026 InChIKeys.
    """

    accounting = list(accounting_records)

    frozen_keys: set[str] = set()
    failure_keys: set[str] = set()
    collision_keys: set[str] = set()
    qualified_keys: set[str] = set()

    for record in accounting:
        d026_inchikey = record["d026_inchikey"]
        status = record["askcos_status"]

        if not isinstance(d026_inchikey, str) or d026_inchikey == "":
            raise ValueError(
                "identity proof requires non-empty D026 InChIKeys"
            )

        if d026_inchikey in frozen_keys:
            raise ValueError(
                f"duplicate D026 key in accounting records: {d026_inchikey}"
            )

        frozen_keys.add(d026_inchikey)

        if status == ASKCOS_STATUS_REPRESENTATION_FAILURE:
            failure_keys.add(d026_inchikey)
        elif status == ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED:
            collision_keys.add(d026_inchikey)
        elif status == "qualified":
            qualified_keys.add(d026_inchikey)
        else:
            raise ValueError(
                f"unknown ASKCOS accounting status: {status!r}"
            )

    if (
        failure_keys & collision_keys
        or failure_keys & qualified_keys
        or collision_keys & qualified_keys
    ):
        raise AssertionError(
            "ASKCOS identity subsets are not pairwise disjoint"
        )

    if (
        failure_keys | collision_keys | qualified_keys
    ) != frozen_keys:
        raise AssertionError(
            "ASKCOS identity subsets do not partition the frozen identity set"
        )

    aizynthfinder_key_set = set(aizynthfinder_keys)

    if any(
        not isinstance(key, str) or key == ""
        for key in aizynthfinder_key_set
    ):
        raise ValueError(
            "AiZynthFinder identity set contains an invalid key"
        )

    representable_keys = frozen_keys - failure_keys

    aizynth_only = aizynthfinder_key_set - representable_keys
    representable_only = representable_keys - aizynthfinder_key_set

    qualified_only = qualified_keys - aizynthfinder_key_set
    aizynth_missing_from_qualified = (
        aizynthfinder_key_set - qualified_keys
    )

    digest = hashlib.sha256

    def hash_key_set(keys: set[str]) -> str:
        local_digest = digest()

        for d026_inchikey in sorted(keys):
            local_digest.update(
                d026_inchikey.encode("utf-8")
            )
            local_digest.update(b"\n")

        return local_digest.hexdigest()

    equality_pass = (
        len(aizynth_only) == 0
        and len(representable_only) == 0
    )

    result = {
        "frozen_count": len(frozen_keys),
        "representation_failure_count": len(failure_keys),
        "collision_excluded_count": len(collision_keys),
        "qualified_count": len(qualified_keys),
        "representable_count": len(representable_keys),
        "aizynthfinder_count": len(aizynthfinder_key_set),
        "aizynthfinder_only_count": len(aizynth_only),
        "representable_only_count": len(representable_only),
        "qualified_only_count": len(qualified_only),
        "aizynthfinder_missing_from_qualified_count": (
            len(aizynth_missing_from_qualified)
        ),
        "frozen_key_set_sha256": hash_key_set(frozen_keys),
        "representation_failure_set_sha256": hash_key_set(
            failure_keys
        ),
        "collision_excluded_set_sha256": hash_key_set(
            collision_keys
        ),
        "qualified_set_sha256": hash_key_set(
            qualified_keys
        ),
        "representable_set_sha256": hash_key_set(
            representable_keys
        ),
        "aizynthfinder_set_sha256": hash_key_set(
            aizynthfinder_key_set
        ),
        "representable_set_equality_pass": equality_pass,
        "representable_only_keys": sorted(representable_only),
        "aizynthfinder_only_keys": sorted(aizynth_only),
    }
    return result

