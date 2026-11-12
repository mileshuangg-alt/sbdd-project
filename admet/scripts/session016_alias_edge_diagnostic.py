"""Session 016 alias-edge provenance diagnostic.

This script is diagnostic-only. It uses the frozen Session 016 grouping
implementation without changing grouping rules, chemistry settings, split
assignment, or prepared inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from collections import Counter, defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize

from admet.scripts import alias_grouping as aliases


ROOT = Path(__file__).resolve().parents[2]
PKA_INPUT = ROOT / "admet/data/prepared/pka_v2.4a_session016.csv"
CLEARANCE_INPUT = ROOT / "admet/data/prepared/human_hepa_408_session016.csv"
ALIAS_GROUPING_SCRIPT = ROOT / "admet/scripts/alias_grouping.py"
DIAGNOSTIC_SCRIPT = Path(__file__).resolve()

REQUIRED_RDKIT_VERSION = "2023.09.6"

EXPECTED_AUDIT_COUNTS = {
    "input_identities": 5882,
    "successful_identities_component_assigned": 5881,
    "explicit_grouping_failures": 1,
    "components": 1740,
    "largest_component": 1315,
    "ring_free_no_scaffold_notes": 996,
    "identities_with_scaffold_key": 4885,
    "distinct_scaffold_keys": 893,
    "identities_with_family_key": 5881,
    "distinct_family_keys": 5446,
    "cross_endpoint_components": 20,
}

EDGE_TRACE_COMPONENT_SIZES = (1315, 335, 288)

IDENTITIES_SCHEMA_VERSION = "session016_alias_edge_diagnostic.identities.v1"
COMPONENTS_SCHEMA_VERSION = "session016_alias_edge_diagnostic.components.v1"
KEY_MEMBERSHIPS_SCHEMA_VERSION = "session016_alias_edge_diagnostic.key_memberships.v1"
GROUPING_FAILURES_SCHEMA_VERSION = "session016_alias_edge_diagnostic.grouping_failures.v1"
TAUTOMER_STATUS_SCHEMA_VERSION = "session016_alias_edge_diagnostic.tautomer_status.v1"
COMPONENT_SUMMARY_SCHEMA_VERSION = "session016_alias_edge_diagnostic.component_summary.v1"
RUN_METADATA_SCHEMA_VERSION = "session016_alias_edge_diagnostic.run_metadata.v1"


@dataclass(frozen=True)
class IdentitySource:
    identity: str
    endpoint: str
    source_id: str
    source_smiles: str


@dataclass(frozen=True)
class TautomerWitness:
    identity: str
    endpoint: str
    source_id: str
    witness_role: str
    witness_input_provenance: str
    rdkit_version: str
    largest_fragment_smiles: str
    uncharged_tautomer_input_smiles: str
    max_tautomers: int
    max_transforms: int
    status: str
    tautomer_count: int
    modified_atoms: tuple[int, ...]
    modified_bonds: tuple[int, ...]


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.fd = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o644,
        )

    def log(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        os.write(self.fd, f"{timestamp} {message}\n".encode("utf-8"))

    @contextmanager
    def capture_process_stderr(self):
        """Redirect process stderr to the same descriptor used for markers.

        Markers are written with unbuffered os.write() and stderr is dup2()'d to
        the same append-mode file descriptor, avoiding independent buffered
        handles while preserving RDKit warning output.
        """

        sys.stderr.flush()
        stderr_fd = sys.stderr.fileno()
        saved_fd = os.dup(stderr_fd)
        try:
            os.dup2(self.fd, stderr_fd)
            yield
        finally:
            sys.stderr.flush()
            os.dup2(saved_fd, stderr_fd)
            os.close(saved_fd)

    def close(self) -> None:
        os.close(self.fd)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fieldnames})


def write_json(path: Path, data: Mapping[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def csv_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (tuple, list)):
        return json.dumps(list(value), separators=(",", ":"), sort_keys=False)
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def status_to_text(status: object) -> str:
    text = str(status)
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def require_authoritative_runtime() -> None:
    if rdBase.rdkitVersion != REQUIRED_RDKIT_VERSION:
        raise RuntimeError(
            "Session 016 alias-edge diagnostic requires actual RDKit runtime "
            f"{REQUIRED_RDKIT_VERSION}; current runtime is {rdBase.rdkitVersion}"
        )

    if rdBase.rdkitVersion != aliases.AUTHORITATIVE_RDKIT_BEHAVIOR:
        raise RuntimeError(
            "alias_grouping.py authoritative behavior constant does not match "
            "the required diagnostic runtime"
        )


def prepare_output_dir(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"output path exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise RuntimeError(f"refusing to overwrite non-empty output directory: {path}")
    else:
        path.mkdir(parents=True)


def build_identity_sources() -> list[IdentitySource]:
    pka_rows = read_csv(PKA_INPUT)
    clearance_rows = read_csv(CLEARANCE_INPUT)

    pka_smiles_by_id: dict[str, set[str]] = defaultdict(set)
    for row in pka_rows:
        pka_smiles_by_id[row["unique_ID"]].add(row["smiles"])

    identities: list[IdentitySource] = []
    for unique_id in sorted(pka_smiles_by_id):
        smiles = pka_smiles_by_id[unique_id]
        if len(smiles) != 1:
            raise RuntimeError(
                f"pKa identity pka:{unique_id} has {len(smiles)} source-recorded SMILES"
            )
        identities.append(
            IdentitySource(
                identity=f"pka:{unique_id}",
                endpoint="pka",
                source_id=unique_id,
                source_smiles=next(iter(smiles)),
            )
        )

    clearance_smiles_by_id: dict[str, set[str]] = defaultdict(set)
    for row in clearance_rows:
        clearance_smiles_by_id[row["molecule_chembl_id"]].add(row["smiles"])

    for molecule_id in sorted(clearance_smiles_by_id):
        smiles = clearance_smiles_by_id[molecule_id]
        if len(smiles) != 1:
            raise RuntimeError(
                "clearance identity clearance:"
                f"{molecule_id} has {len(smiles)} source-recorded SMILES"
            )
        identities.append(
            IdentitySource(
                identity=f"clearance:{molecule_id}",
                endpoint="clearance",
                source_id=molecule_id,
                source_smiles=next(iter(smiles)),
            )
        )

    identities.sort(key=lambda item: item.identity)
    if len({item.identity for item in identities}) != len(identities):
        raise RuntimeError("endpoint-qualified identities are not unique")
    return identities


def build_grouped_record(source: IdentitySource, logger: RunLogger) -> dict:
    record = {
        "id": source.identity,
        "endpoint": source.endpoint,
        "source_id": source.source_id,
        "smiles": source.source_smiles,
    }
    logger.log(f"GROUPING_BEGIN identity={source.identity}")
    output = aliases.add_alias_grouping_fields_for_artifact(record)
    logger.log(f"GROUPING_END identity={source.identity}")
    return output


def build_tautomer_witness(source: IdentitySource, logger: RunLogger) -> TautomerWitness | None:
    mol = aliases.parse_smiles(source.source_smiles)
    if mol is None:
        return None

    fragment_selection = aliases.select_unique_largest_fragment(mol)
    if fragment_selection.failure_reason is not None or fragment_selection.fragment_mol is None:
        return None

    tautomer_input = Chem.Mol(fragment_selection.fragment_mol)
    Chem.RemoveStereochemistry(tautomer_input)
    tautomer_input = rdMolStandardize.Uncharger().uncharge(tautomer_input)

    enumerator = rdMolStandardize.TautomerEnumerator()
    if not hasattr(enumerator, "Enumerate"):
        raise RuntimeError("RDKit TautomerEnumerator is missing Enumerate")
    if not hasattr(enumerator, "GetMaxTautomers"):
        raise RuntimeError("RDKit TautomerEnumerator is missing GetMaxTautomers")
    if not hasattr(enumerator, "GetMaxTransforms"):
        raise RuntimeError("RDKit TautomerEnumerator is missing GetMaxTransforms")

    logger.log(f"TAUTOMER_WITNESS_BEGIN identity={source.identity}")
    result = enumerator.Enumerate(tautomer_input)
    logger.log(f"TAUTOMER_WITNESS_END identity={source.identity}")

    if not hasattr(result, "status"):
        raise RuntimeError("RDKit TautomerEnumeratorResult is missing status attribute")
    status_attr = result.status
    if callable(status_attr):
        raise RuntimeError(
            "RDKit TautomerEnumeratorResult.status is callable; expected Python "
            "attribute behavior for the qualified API"
        )
    for required_attr in ("tautomers", "modifiedAtoms", "modifiedBonds"):
        if not hasattr(result, required_attr):
            raise RuntimeError(
                f"RDKit TautomerEnumeratorResult is missing {required_attr} attribute"
            )

    return TautomerWitness(
        identity=source.identity,
        endpoint=source.endpoint,
        source_id=source.source_id,
        witness_role=(
            "diagnostic_only_not_used_for_frozen_family_key_generation_or_validation"
        ),
        witness_input_provenance=(
            "independently_reconstructed_from_source_smiles_using_the_same_documented_"
            "frozen_sequence_largest_fragment_remove_stereochemistry_uncharger;"
            "not_a_direct_observation_or_equality_proof_of_the_internal_"
            "pre_tautomer_molecule_used_by_alias_grouping_Canonicalize"
        ),
        rdkit_version=rdBase.rdkitVersion,
        largest_fragment_smiles=fragment_selection.fragment_smiles or "",
        uncharged_tautomer_input_smiles=Chem.MolToSmiles(
            tautomer_input,
            canonical=True,
            isomericSmiles=False,
        ),
        max_tautomers=int(enumerator.GetMaxTautomers()),
        max_transforms=int(enumerator.GetMaxTransforms()),
        status=status_to_text(status_attr),
        tautomer_count=len(result.tautomers),
        modified_atoms=tuple(int(atom) for atom in result.modifiedAtoms),
        modified_bonds=tuple(int(bond) for bond in result.modifiedBonds),
    )


def assignment_maps(assignments: list[dict[str, object]]) -> tuple[dict[str, str | None], dict[str, str | None]]:
    component_by_identity = {
        str(row["identity"]): (str(row["component_id"]) if row["component_id"] else None)
        for row in assignments
    }
    grouping_failure_by_identity = {
        str(row["identity"]): (
            str(row["grouping_failure"]) if row["grouping_failure"] else None
        )
        for row in assignments
    }
    return component_by_identity, grouping_failure_by_identity


def records_by_identity(records: Iterable[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    return {str(record["id"]): record for record in records}


def alias_record(record: Mapping[str, object]) -> Mapping[str, object]:
    alias = record["alias_grouping"]
    if not isinstance(alias, Mapping):
        raise RuntimeError(f"record {record['id']} has invalid alias_grouping")
    return alias


def build_identity_rows(
    records: list[dict],
    component_by_identity: Mapping[str, str | None],
    grouping_failure_by_identity: Mapping[str, str | None],
) -> list[dict[str, object]]:
    rows = []
    for record in sorted(records, key=lambda item: item["id"]):
        alias = alias_record(record)
        rows.append(
            {
                "identity": record["id"],
                "endpoint": record["endpoint"],
                "source_id": record["source_id"],
                "source_recorded_smiles": record["smiles"],
                "rdkit_version": alias["rdkit_version"],
                "largest_fragment_smiles": alias["largest_fragment_smiles"],
                "largest_fragment_heavy_atom_count": alias[
                    "largest_fragment_heavy_atom_count"
                ],
                "fragment_heavy_atom_counts_json": alias[
                    "fragment_heavy_atom_counts"
                ],
                "scaffold_key": alias["scaffold_key"],
                "family_key": alias["family_key"],
                "failures_json": alias["failures"],
                "notes_json": alias["notes"],
                "component_id": component_by_identity[record["id"]],
                "grouping_failure": grouping_failure_by_identity[record["id"]],
            }
        )
    return rows


def build_component_rows(assignments: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for assignment in assignments:
        component_id = assignment["component_id"]
        if not component_id:
            continue
        rows.append({"component_id": component_id, "identity": assignment["identity"]})
    return sorted(rows, key=lambda item: (item["component_id"], item["identity"]))


def build_key_membership_rows(records: list[dict], component_by_identity: Mapping[str, str | None]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        identity = record["id"]
        if component_by_identity[identity] is None:
            continue
        alias = alias_record(record)
        for key_type in ("scaffold_key", "family_key"):
            key = alias[key_type]
            if key is not None:
                rows.append(
                    {
                        "key_type": key_type.replace("_key", ""),
                        "key": key,
                        "identity": identity,
                    }
                )
    return sorted(rows, key=lambda item: (item["key_type"], item["key"], item["identity"]))


def build_grouping_failure_rows(
    records: list[dict],
    grouping_failure_by_identity: Mapping[str, str | None],
) -> list[dict[str, object]]:
    rows = []
    for record in sorted(records, key=lambda item: item["id"]):
        failure = grouping_failure_by_identity[record["id"]]
        if failure is None:
            continue
        alias = alias_record(record)
        rows.append(
            {
                "identity": record["id"],
                "endpoint": record["endpoint"],
                "source_id": record["source_id"],
                "source_recorded_smiles": record["smiles"],
                "rdkit_version": alias["rdkit_version"],
                "largest_fragment_smiles": alias["largest_fragment_smiles"],
                "largest_fragment_heavy_atom_count": alias[
                    "largest_fragment_heavy_atom_count"
                ],
                "fragment_heavy_atom_counts_json": alias[
                    "fragment_heavy_atom_counts"
                ],
                "scaffold_key": alias["scaffold_key"],
                "family_key": alias["family_key"],
                "failures_json": alias["failures"],
                "notes_json": alias["notes"],
                "grouping_failure": failure,
            }
        )
    return rows


def build_tautomer_rows(witnesses: list[TautomerWitness]) -> list[dict[str, object]]:
    rows = []
    for witness in sorted(witnesses, key=lambda item: item.identity):
        rows.append(
            {
                "identity": witness.identity,
                "endpoint": witness.endpoint,
                "source_id": witness.source_id,
                "witness_role": witness.witness_role,
                "witness_input_provenance": witness.witness_input_provenance,
                "rdkit_version": witness.rdkit_version,
                "largest_fragment_smiles": witness.largest_fragment_smiles,
                "uncharged_tautomer_input_smiles": witness.uncharged_tautomer_input_smiles,
                "enumerator_max_tautomers": witness.max_tautomers,
                "enumerator_max_transforms": witness.max_transforms,
                "diagnostic_enumeration_status": witness.status,
                "diagnostic_tautomer_count": witness.tautomer_count,
                "modified_atoms_json": witness.modified_atoms,
                "modified_bonds_json": witness.modified_bonds,
            }
        )
    return rows


def component_members(component_rows: list[dict[str, object]]) -> dict[str, list[str]]:
    members: dict[str, list[str]] = defaultdict(list)
    for row in component_rows:
        members[str(row["component_id"])].append(str(row["identity"]))
    return {component_id: sorted(values) for component_id, values in members.items()}


def key_members_by_component(
    key_rows: list[dict[str, object]],
    component_by_identity: Mapping[str, str | None],
) -> dict[str, dict[tuple[str, str], list[str]]]:
    output: dict[str, dict[tuple[str, str], list[str]]] = defaultdict(lambda: defaultdict(list))
    for row in key_rows:
        identity = str(row["identity"])
        component_id = component_by_identity[identity]
        if component_id is None:
            continue
        output[component_id][(str(row["key_type"]), str(row["key"]))].append(identity)
    return {
        component_id: {key: sorted(members) for key, members in key_map.items()}
        for component_id, key_map in output.items()
    }


def is_traversable_by_shared_keys(members: list[str], key_map: Mapping[tuple[str, str], list[str]]) -> bool:
    if not members:
        return False
    if len(members) == 1:
        return True

    adjacency: dict[str, set[str]] = {member: set() for member in members}
    for owners in key_map.values():
        if len(owners) < 2:
            continue
        for owner in owners:
            adjacency[owner].update(other for other in owners if other != owner)

    start = members[0]
    seen = {start}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(members)


def build_component_summary_rows(
    component_rows: list[dict[str, object]],
    key_rows: list[dict[str, object]],
    records_by_id: Mapping[str, Mapping[str, object]],
    component_by_identity: Mapping[str, str | None],
    reproduction_gate_passed: bool,
) -> list[dict[str, object]]:
    members_by_component = component_members(component_rows)
    keys_by_component = key_members_by_component(key_rows, component_by_identity)
    target_sizes = set(EDGE_TRACE_COMPONENT_SIZES) if reproduction_gate_passed else set()
    rows = []

    for component_id in sorted(members_by_component):
        members = members_by_component[component_id]
        endpoint_counts = Counter(str(records_by_id[identity]["endpoint"]) for identity in members)
        key_map = keys_by_component.get(component_id, {})
        scaffold_key_counts = sorted(
            [
                {"key": key, "member_count": len(owners), "members": owners}
                for (key_type, key), owners in key_map.items()
                if key_type == "scaffold"
            ],
            key=lambda item: (item["key"], item["member_count"]),
        )
        family_key_counts = sorted(
            [
                {"key": key, "member_count": len(owners), "members": owners}
                for (key_type, key), owners in key_map.items()
                if key_type == "family"
            ],
            key=lambda item: (item["key"], item["member_count"]),
        )

        direct_joins = sorted(
            [
                {
                    "key_type": key_type,
                    "key": key,
                    "member_count": len(owners),
                    "members": owners,
                }
                for (key_type, key), owners in key_map.items()
                if len(owners) >= 2
            ],
            key=lambda item: (-item["member_count"], item["key_type"], item["key"]),
        )
        largest_join_size = direct_joins[0]["member_count"] if direct_joins else 1
        largest_direct_joins = [
            join for join in direct_joins if join["member_count"] == largest_join_size
        ]

        clearance_connecting_keys = sorted(
            [
                {
                    "key_type": key_type,
                    "key": key,
                    "member_count": len(owners),
                    "clearance_members": [
                        owner
                        for owner in owners
                        if str(records_by_id[owner]["endpoint"]) == "clearance"
                    ],
                    "members": owners,
                }
                for (key_type, key), owners in key_map.items()
                if any(str(records_by_id[owner]["endpoint"]) == "clearance" for owner in owners)
                and len(owners) >= 2
            ],
            key=lambda item: (item["key_type"], item["key"]),
        )

        include_edge_trace = len(members) in target_sizes
        rows.append(
            {
                "component_id": component_id,
                "size": len(members),
                "pka_count": endpoint_counts["pka"],
                "clearance_count": endpoint_counts["clearance"],
                "distinct_scaffold_key_count": len(scaffold_key_counts),
                "distinct_family_key_count": len(family_key_counts),
                "direct_shared_key_count": len(direct_joins),
                "largest_direct_key_join_size": largest_join_size,
                "cross_endpoint": endpoint_counts["pka"] > 0 and endpoint_counts["clearance"] > 0,
                "traversable_by_persisted_shared_key_relations": is_traversable_by_shared_keys(
                    members,
                    key_map,
                ),
                "edge_trace_included": include_edge_trace,
                "component_members_json": members if include_edge_trace else (),
                "scaffold_key_memberships_json": scaffold_key_counts if include_edge_trace else (),
                "family_key_memberships_json": family_key_counts if include_edge_trace else (),
                "largest_direct_key_defined_joins_json": largest_direct_joins
                if include_edge_trace
                else (),
                "clearance_connecting_keys_json": clearance_connecting_keys
                if include_edge_trace
                else (),
            }
        )

    return sorted(rows, key=lambda item: (int(item["size"]) * -1, item["component_id"]))


def reproduction_counts(
    records: list[dict],
    component_rows: list[dict[str, object]],
    grouping_failure_rows: list[dict[str, object]],
) -> dict[str, int]:
    assigned_identities = {str(row["identity"]) for row in component_rows}
    component_sizes = Counter(str(row["component_id"]) for row in component_rows)
    endpoint_by_identity = {str(record["id"]): str(record["endpoint"]) for record in records}
    aliases_by_id = {str(record["id"]): alias_record(record) for record in records}

    cross_endpoint_components = 0
    members_by_component: dict[str, list[str]] = defaultdict(list)
    for row in component_rows:
        members_by_component[str(row["component_id"])].append(str(row["identity"]))
    for members in members_by_component.values():
        endpoints = {endpoint_by_identity[identity] for identity in members}
        if len(endpoints) > 1:
            cross_endpoint_components += 1

    scaffold_keys = [
        str(alias["scaffold_key"])
        for identity, alias in aliases_by_id.items()
        if identity in assigned_identities and alias["scaffold_key"] is not None
    ]
    family_keys = [
        str(alias["family_key"])
        for identity, alias in aliases_by_id.items()
        if identity in assigned_identities and alias["family_key"] is not None
    ]

    return {
        "input_identities": len(records),
        "successful_identities_component_assigned": len(assigned_identities),
        "explicit_grouping_failures": len(grouping_failure_rows),
        "components": len(component_sizes),
        "largest_component": max(component_sizes.values()) if component_sizes else 0,
        "ring_free_no_scaffold_notes": sum(
            aliases.RING_FREE_NO_SCAFFOLD in tuple(alias["notes"])
            for alias in aliases_by_id.values()
        ),
        "identities_with_scaffold_key": len(scaffold_keys),
        "distinct_scaffold_keys": len(set(scaffold_keys)),
        "identities_with_family_key": len(family_keys),
        "distinct_family_keys": len(set(family_keys)),
        "cross_endpoint_components": cross_endpoint_components,
    }


def reproduction_discrepancies(observed: Mapping[str, int]) -> dict[str, dict[str, int]]:
    discrepancies = {}
    for key, expected in EXPECTED_AUDIT_COUNTS.items():
        actual = observed.get(key)
        if actual != expected:
            discrepancies[key] = {"expected": expected, "actual": int(actual or 0)}
    return discrepancies


def write_sha256s(output_dir: Path) -> None:
    output_files = sorted(
        path for path in output_dir.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    sums_path = output_dir / "SHA256SUMS.txt"
    with sums_path.open("w", encoding="utf-8", newline="\n") as handle:
        for path in output_files:
            handle.write(f"{sha256(path)}  {path.name}\n")


def output_schemas() -> dict[str, object]:
    structured_cell_note = (
        "CSV columns ending in _json contain deterministic compact JSON. "
        "Tuple-valued alias_grouping fields are serialized as JSON arrays."
    )
    return {
        "identities.csv": {
            "schema_version": IDENTITIES_SCHEMA_VERSION,
            "structured_cell_representation": structured_cell_note,
        },
        "components.csv": {"schema_version": COMPONENTS_SCHEMA_VERSION},
        "key_memberships.csv": {"schema_version": KEY_MEMBERSHIPS_SCHEMA_VERSION},
        "grouping_failures.csv": {
            "schema_version": GROUPING_FAILURES_SCHEMA_VERSION,
            "structured_cell_representation": structured_cell_note,
        },
        "tautomer_status.csv": {
            "schema_version": TAUTOMER_STATUS_SCHEMA_VERSION,
            "witness_role": (
                "diagnostic-only; not used for frozen family_key generation, "
                "reproduction-gate checks, or grouping interpretation"
            ),
            "witness_input_provenance": (
                "The witness input is independently reconstructed from the "
                "source-recorded SMILES using the same documented frozen "
                "sequence: selected largest fragment, remove stereochemistry, "
                "RDKit Uncharger. It is not a direct observation and not an "
                "equality proof of the internal pre-tautomer molecule used by "
                "the frozen alias_grouping.py Canonicalize() call."
            ),
            "structured_cell_representation": structured_cell_note,
        },
        "component_summary.csv": {
            "schema_version": COMPONENT_SUMMARY_SCHEMA_VERSION,
            "structured_cell_representation": structured_cell_note,
        },
        "run_metadata.json": {"schema_version": RUN_METADATA_SCHEMA_VERSION},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Session 016 alias-edge diagnostic provenance outputs."
    )
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    require_authoritative_runtime()
    output_dir = args.output_dir.resolve()
    prepare_output_dir(output_dir)

    logger = RunLogger(output_dir / "run.log")
    try:
        logger.log("SESSION016_ALIAS_EDGE_DIAGNOSTIC_BEGIN")
        logger.log(f"python_version={platform.python_version()}")
        logger.log(f"rdkit_version={rdBase.rdkitVersion}")

        with logger.capture_process_stderr():
            sources = build_identity_sources()
            grouped_records = []
            tautomer_witnesses = []
            for source in sources:
                grouped_records.append(build_grouped_record(source, logger))
                witness = build_tautomer_witness(source, logger)
                if witness is not None:
                    tautomer_witnesses.append(witness)

        assignments = aliases.construct_alias_connected_components(
            grouped_records,
            identity_field="id",
        )
        component_by_identity, grouping_failure_by_identity = assignment_maps(assignments)
        identity_rows = build_identity_rows(
            grouped_records,
            component_by_identity,
            grouping_failure_by_identity,
        )
        component_rows = build_component_rows(assignments)
        key_rows = build_key_membership_rows(grouped_records, component_by_identity)
        grouping_failure_rows = build_grouping_failure_rows(
            grouped_records,
            grouping_failure_by_identity,
        )
        tautomer_rows = build_tautomer_rows(tautomer_witnesses)
        observed_counts = reproduction_counts(
            grouped_records,
            component_rows,
            grouping_failure_rows,
        )
        discrepancies = reproduction_discrepancies(observed_counts)
        gate_passed = not discrepancies
        if gate_passed:
            logger.log("REPRODUCTION_GATE_PASS")
        else:
            logger.log(f"REPRODUCTION_GATE_FAIL discrepancies={json.dumps(discrepancies, sort_keys=True)}")

        record_by_id = records_by_identity(grouped_records)
        component_summary_rows = build_component_summary_rows(
            component_rows,
            key_rows,
            record_by_id,
            component_by_identity,
            gate_passed,
        )

        write_csv(
            output_dir / "identities.csv",
            [
                "identity",
                "endpoint",
                "source_id",
                "source_recorded_smiles",
                "rdkit_version",
                "largest_fragment_smiles",
                "largest_fragment_heavy_atom_count",
                "fragment_heavy_atom_counts_json",
                "scaffold_key",
                "family_key",
                "failures_json",
                "notes_json",
                "component_id",
                "grouping_failure",
            ],
            identity_rows,
        )
        write_csv(output_dir / "components.csv", ["component_id", "identity"], component_rows)
        write_csv(output_dir / "key_memberships.csv", ["key_type", "key", "identity"], key_rows)
        write_csv(
            output_dir / "grouping_failures.csv",
            [
                "identity",
                "endpoint",
                "source_id",
                "source_recorded_smiles",
                "rdkit_version",
                "largest_fragment_smiles",
                "largest_fragment_heavy_atom_count",
                "fragment_heavy_atom_counts_json",
                "scaffold_key",
                "family_key",
                "failures_json",
                "notes_json",
                "grouping_failure",
            ],
            grouping_failure_rows,
        )
        write_csv(
            output_dir / "tautomer_status.csv",
            [
                "identity",
                "endpoint",
                "source_id",
                "witness_role",
                "witness_input_provenance",
                "rdkit_version",
                "largest_fragment_smiles",
                "uncharged_tautomer_input_smiles",
                "enumerator_max_tautomers",
                "enumerator_max_transforms",
                "diagnostic_enumeration_status",
                "diagnostic_tautomer_count",
                "modified_atoms_json",
                "modified_bonds_json",
            ],
            tautomer_rows,
        )
        write_csv(
            output_dir / "component_summary.csv",
            [
                "component_id",
                "size",
                "pka_count",
                "clearance_count",
                "distinct_scaffold_key_count",
                "distinct_family_key_count",
                "direct_shared_key_count",
                "largest_direct_key_join_size",
                "cross_endpoint",
                "traversable_by_persisted_shared_key_relations",
                "edge_trace_included",
                "component_members_json",
                "scaffold_key_memberships_json",
                "family_key_memberships_json",
                "largest_direct_key_defined_joins_json",
                "clearance_connecting_keys_json",
            ],
            component_summary_rows,
        )

        metadata = {
            "schema_version": RUN_METADATA_SCHEMA_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "rdkit_version": rdBase.rdkitVersion,
            "required_rdkit_version": REQUIRED_RDKIT_VERSION,
            "input_hashes_sha256": {
                str(PKA_INPUT.relative_to(ROOT)): sha256(PKA_INPUT),
                str(CLEARANCE_INPUT.relative_to(ROOT)): sha256(CLEARANCE_INPUT),
            },
            "alias_grouping_py_sha256": sha256(ALIAS_GROUPING_SCRIPT),
            "diagnostic_script_sha256": sha256(DIAGNOSTIC_SCRIPT),
            "alias_grouping_schema_version": aliases.SCHEMA_VERSION,
            "identity_convention": {
                "pka": (
                    "collapse molecule-step rows to pka:{unique_ID}; require exactly "
                    "one source-recorded SMILES per unique_ID"
                ),
                "clearance": "one molecular identity clearance:{molecule_chembl_id}",
                "expected_combined_population": 5882,
            },
            "output_schema_versions": output_schemas(),
            "grouping_rules_unchanged": True,
            "grouping_implementation": "admet.scripts.alias_grouping.add_alias_grouping_fields_for_artifact and construct_alias_connected_components",
            "no_train_test_cv_split_assigned": True,
            "no_grouping_changes": True,
            "no_exclusions_or_new_chemistry_rules": True,
            "tautomer_witness_statement": (
                "tautomer_status.csv is diagnostic witness information only. "
                "The witness input is independently reconstructed using the same "
                "documented frozen sequence and is not a direct observation or "
                "equality proof of the internal pre-tautomer molecule used by the "
                "frozen Canonicalize() call. Witness results do not supply, "
                "replace, modify, validate, or invalidate the frozen family_key "
                "generated by alias_grouping.py, and they are excluded from the "
                "reproduction gate and grouping interpretation."
            ),
            "expected_reproduction_counts": EXPECTED_AUDIT_COUNTS,
            "observed_reproduction_counts": observed_counts,
            "reproduction_gate_passed": gate_passed,
            "reproduction_discrepancies": discrepancies,
            "edge_trace_component_sizes": list(EDGE_TRACE_COMPONENT_SIZES),
            "edge_trace_written": gate_passed,
        }
        write_json(output_dir / "run_metadata.json", metadata)

        logger.log("SESSION016_ALIAS_EDGE_DIAGNOSTIC_OUTPUTS_COMPLETE")
    finally:
        logger.close()

    write_sha256s(output_dir)


if __name__ == "__main__":
    main()
