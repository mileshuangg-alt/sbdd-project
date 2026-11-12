"""Frozen Session 016 alias-grouping primitives.

These molecular representations are grouping-only audit fields. They must not
replace source-recorded model-input SMILES.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping

from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold


SCHEMA_VERSION = "session016_alias_grouping.v1"
AUTHORITATIVE_RDKIT_BEHAVIOR = "2023.09.6"

PARSE_FAILURE = "parse_failure"
NO_FRAGMENTS = "no_fragments"
FRAGMENT_AMBIGUITY = "fragment_ambiguity_equal_largest_heavy_atom_count"
SCAFFOLD_KEY_FAILURE = "scaffold_key_generation_failure"
FAMILY_KEY_FAILURE = "family_key_generation_failure"
RING_FREE_NO_SCAFFOLD = "ring_free_no_scaffold_key"


@dataclass(frozen=True)
class FragmentSelection:
    """Auditable result for unique-largest-fragment selection."""

    fragment_mol: Chem.Mol | None
    fragment_smiles: str | None
    heavy_atom_count: int | None
    fragment_heavy_atom_counts: tuple[int, ...]
    failure_reason: str | None


@dataclass(frozen=True)
class AliasGroupingResult:
    """Grouping-only keys and failures for one source SMILES."""

    source_smiles: str
    rdkit_version: str
    largest_fragment_smiles: str | None
    largest_fragment_heavy_atom_count: int | None
    fragment_heavy_atom_counts: tuple[int, ...]
    scaffold_key: str | None
    family_key: str | None
    failures: tuple[str, ...]
    notes: tuple[str, ...]

    @property
    def success(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class AliasComponentAssignment:
    """Deterministic component assignment or frozen grouping failure."""

    identity: str
    component_id: str | None
    component_members: tuple[str, ...]
    grouping_failure: str | None


def _copy_mol(mol: Chem.Mol) -> Chem.Mol:
    return Chem.Mol(mol)


def parse_smiles(smiles: str) -> Chem.Mol | None:
    """Parse a source SMILES without rewriting or canonicalizing the source."""

    try:
        return Chem.MolFromSmiles(smiles)
    except Exception:
        return None


def assert_authoritative_rdkit_runtime() -> None:
    """Require the frozen production runtime for artifact generation."""

    if rdBase.rdkitVersion != AUTHORITATIVE_RDKIT_BEHAVIOR:
        raise RuntimeError(
            "Session 016 alias production artifacts require RDKit "
            f"{AUTHORITATIVE_RDKIT_BEHAVIOR}; current runtime is "
            f"{rdBase.rdkitVersion}"
        )


def select_unique_largest_fragment(mol: Chem.Mol) -> FragmentSelection:
    """Select the uniquely largest fragment by heavy-atom count.

    Equal-largest ties are reported as failures instead of being broken by
    SMILES ordering, input order, charge, or any other scientific rule.
    """

    fragments = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=True)
    counts = tuple(fragment.GetNumHeavyAtoms() for fragment in fragments)

    if not fragments:
        return FragmentSelection(None, None, None, counts, NO_FRAGMENTS)

    largest_count = max(counts)
    largest = [
        fragment
        for fragment, count in zip(fragments, counts, strict=True)
        if count == largest_count
    ]

    if len(largest) != 1:
        return FragmentSelection(None, None, largest_count, counts, FRAGMENT_AMBIGUITY)

    fragment = largest[0]
    fragment_smiles = Chem.MolToSmiles(
        fragment,
        canonical=True,
        isomericSmiles=True,
    )
    return FragmentSelection(fragment, fragment_smiles, largest_count, counts, None)


def make_typed_bemis_murcko_scaffold_key(fragment_mol: Chem.Mol) -> tuple[str | None, str | None]:
    """Return a stereo-insensitive typed Bemis-Murcko scaffold key.

    Ring-free molecules intentionally have no scaffold key and are not treated
    as key-generation failures.
    """

    mol = _copy_mol(fragment_mol)
    Chem.RemoveStereochemistry(mol)

    if not any(atom.IsInRing() for atom in mol.GetAtoms()):
        return None, None

    try:
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold is None or scaffold.GetNumAtoms() == 0:
            return None, SCAFFOLD_KEY_FAILURE
        key = Chem.MolToSmiles(
            scaffold,
            canonical=True,
            isomericSmiles=False,
        )
    except Exception:
        return None, SCAFFOLD_KEY_FAILURE

    if not key:
        return None, SCAFFOLD_KEY_FAILURE
    return key, None


def make_conservative_family_key(fragment_mol: Chem.Mol) -> tuple[str | None, str | None]:
    """Return the conservative family key for grouping only.

    The frozen pipeline is: remove stereochemistry, RDKit Uncharger, tautomer
    canonicalization, then canonical non-isomeric SMILES.
    """

    try:
        mol = _copy_mol(fragment_mol)
        Chem.RemoveStereochemistry(mol)
        mol = rdMolStandardize.Uncharger().uncharge(mol)
        mol = rdMolStandardize.TautomerEnumerator().Canonicalize(mol)
        key = Chem.MolToSmiles(
            mol,
            canonical=True,
            isomericSmiles=False,
        )
    except Exception:
        return None, FAMILY_KEY_FAILURE

    if not key:
        return None, FAMILY_KEY_FAILURE
    return key, None


def build_alias_grouping_result(smiles: str) -> AliasGroupingResult:
    """Build grouping-only keys for one source-recorded SMILES."""

    failures: list[str] = []
    notes: list[str] = []
    mol = parse_smiles(smiles)

    if mol is None:
        failures.append(PARSE_FAILURE)
        return AliasGroupingResult(
            source_smiles=smiles,
            rdkit_version=rdBase.rdkitVersion,
            largest_fragment_smiles=None,
            largest_fragment_heavy_atom_count=None,
            fragment_heavy_atom_counts=(),
            scaffold_key=None,
            family_key=None,
            failures=tuple(failures),
            notes=tuple(notes),
        )

    fragment_selection = select_unique_largest_fragment(mol)
    if fragment_selection.failure_reason is not None:
        failures.append(fragment_selection.failure_reason)
        return AliasGroupingResult(
            source_smiles=smiles,
            rdkit_version=rdBase.rdkitVersion,
            largest_fragment_smiles=fragment_selection.fragment_smiles,
            largest_fragment_heavy_atom_count=fragment_selection.heavy_atom_count,
            fragment_heavy_atom_counts=fragment_selection.fragment_heavy_atom_counts,
            scaffold_key=None,
            family_key=None,
            failures=tuple(failures),
            notes=tuple(notes),
        )

    scaffold_key, scaffold_failure = make_typed_bemis_murcko_scaffold_key(
        fragment_selection.fragment_mol
    )
    if scaffold_failure is not None:
        failures.append(scaffold_failure)
    elif scaffold_key is None:
        notes.append(RING_FREE_NO_SCAFFOLD)

    family_key, family_failure = make_conservative_family_key(
        fragment_selection.fragment_mol
    )
    if family_failure is not None:
        failures.append(family_failure)

    return AliasGroupingResult(
        source_smiles=smiles,
        rdkit_version=rdBase.rdkitVersion,
        largest_fragment_smiles=fragment_selection.fragment_smiles,
        largest_fragment_heavy_atom_count=fragment_selection.heavy_atom_count,
        fragment_heavy_atom_counts=fragment_selection.fragment_heavy_atom_counts,
        scaffold_key=scaffold_key,
        family_key=family_key,
        failures=tuple(failures),
        notes=tuple(notes),
    )


def alias_grouping_result_to_record(result: AliasGroupingResult) -> dict:
    """Serialize an alias-grouping result without changing source SMILES."""

    is_authoritative_runtime = result.rdkit_version == AUTHORITATIVE_RDKIT_BEHAVIOR

    return {
        "schema_version": SCHEMA_VERSION,
        "source_smiles": result.source_smiles,
        "rdkit_version": result.rdkit_version,
        "authoritative_rdkit_behavior": AUTHORITATIVE_RDKIT_BEHAVIOR,
        "is_authoritative_rdkit_runtime": is_authoritative_runtime,
        "largest_fragment_smiles": result.largest_fragment_smiles,
        "largest_fragment_heavy_atom_count": result.largest_fragment_heavy_atom_count,
        "fragment_heavy_atom_counts": result.fragment_heavy_atom_counts,
        "scaffold_key": result.scaffold_key,
        "family_key": result.family_key,
        "failures": result.failures,
        "notes": result.notes,
        "success": result.success,
    }


def add_alias_grouping_fields(
    record: Mapping[str, object],
    *,
    smiles_field: str = "smiles",
    require_authoritative_runtime: bool = False,
) -> dict:
    """Return a copy of a source record with grouping-only audit fields added."""

    if require_authoritative_runtime:
        assert_authoritative_rdkit_runtime()

    output = dict(record)
    source_smiles = str(record[smiles_field])
    result = build_alias_grouping_result(source_smiles)
    output["alias_grouping"] = alias_grouping_result_to_record(result)
    return output


def add_alias_grouping_fields_for_artifact(
    record: Mapping[str, object],
    *,
    smiles_field: str = "smiles",
) -> dict:
    """Add grouping fields for production artifacts under the frozen runtime."""

    return add_alias_grouping_fields(
        record,
        smiles_field=smiles_field,
        require_authoritative_runtime=True,
    )


def group_records_by_alias_key(
    records: Iterable[Mapping[str, object]],
    *,
    key_field: str,
) -> dict[str, list[Mapping[str, object]]]:
    """Group records by an existing alias key, skipping missing keys."""

    if key_field not in {"scaffold_key", "family_key"}:
        raise ValueError("key_field must be 'scaffold_key' or 'family_key'")

    groups: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for record in records:
        alias_grouping = record.get("alias_grouping")
        if not isinstance(alias_grouping, Mapping):
            raise ValueError("record is missing alias_grouping fields")
        key = alias_grouping.get(key_field)
        if key is not None:
            groups[str(key)].append(record)
    return {key: groups[key] for key in sorted(groups)}


def _alias_grouping_for_record(record: Mapping[str, object]) -> Mapping[str, object]:
    alias_grouping = record.get("alias_grouping")
    if not isinstance(alias_grouping, Mapping):
        raise ValueError("record is missing alias_grouping fields")
    return alias_grouping


def _find(parent: dict[str, str], identity: str) -> str:
    while parent[identity] != identity:
        parent[identity] = parent[parent[identity]]
        identity = parent[identity]
    return identity


def _union(parent: dict[str, str], first: str, second: str) -> None:
    first_root = _find(parent, first)
    second_root = _find(parent, second)
    if first_root == second_root:
        return
    if second_root < first_root:
        first_root, second_root = second_root, first_root
    parent[second_root] = first_root


def construct_alias_connected_components(
    records: Iterable[Mapping[str, object]],
    *,
    identity_field: str = "id",
) -> list[dict[str, object]]:
    """Assign deterministic alias connected components over successful records.

    An undirected edge exists when two successful records share a non-null
    scaffold_key or a non-null family_key. Components are transitive across key
    types. Records with frozen failures receive an explicit grouping failure and
    do not participate in edges.
    """

    rows = list(records)
    identities = [str(record[identity_field]) for record in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("input identities must be unique")

    parent = {identity: identity for identity in identities}
    failure_by_identity: dict[str, str] = {}
    key_owners: dict[tuple[str, str], list[str]] = defaultdict(list)

    for record, identity in zip(rows, identities, strict=True):
        alias_grouping = _alias_grouping_for_record(record)
        failures = tuple(str(failure) for failure in alias_grouping.get("failures", ()))
        if failures:
            failure_by_identity[identity] = ";".join(failures)
            continue

        for key_field in ("scaffold_key", "family_key"):
            key = alias_grouping.get(key_field)
            if key is not None:
                key_owners[(key_field, str(key))].append(identity)

    for owners in key_owners.values():
        sorted_owners = sorted(owners)
        if len(sorted_owners) < 2:
            continue
        first = sorted_owners[0]
        for identity in sorted_owners[1:]:
            _union(parent, first, identity)

    members_by_root: dict[str, list[str]] = defaultdict(list)
    for identity in sorted(identities):
        if identity not in failure_by_identity:
            members_by_root[_find(parent, identity)].append(identity)

    sorted_components = sorted(
        (tuple(members) for members in members_by_root.values()),
        key=lambda members: members,
    )
    component_id_by_member = {
        member: f"alias_component_{index:06d}"
        for index, members in enumerate(sorted_components, start=1)
        for member in members
    }
    component_members_by_member = {
        member: members
        for members in sorted_components
        for member in members
    }

    assignments = []
    for identity in sorted(identities):
        if identity in failure_by_identity:
            assignments.append(
                AliasComponentAssignment(
                    identity=identity,
                    component_id=None,
                    component_members=(),
                    grouping_failure=failure_by_identity[identity],
                )
            )
        else:
            assignments.append(
                AliasComponentAssignment(
                    identity=identity,
                    component_id=component_id_by_member[identity],
                    component_members=component_members_by_member[identity],
                    grouping_failure=None,
                )
            )

    return [
        {
            "identity": assignment.identity,
            "component_id": assignment.component_id,
            "component_members": assignment.component_members,
            "grouping_failure": assignment.grouping_failure,
        }
        for assignment in assignments
    ]
