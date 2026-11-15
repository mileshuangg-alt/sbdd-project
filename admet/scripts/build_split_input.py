"""Build the frozen ADMET family-level split input.

Implements D031 (immutable family units, per-family fields), D032 (alias
grouping with duplicate-tie resolution) and D033 (molecular similarity and
complete family-mean S_ij). It produces optimizer input only; it does not
assign families to partitions or run any optimizer.

Only the identity column and the SMILES column of each prepared endpoint file
are retained. Label values are discarded as each row is read and are never
stored, used or written.

Usage (from the repository root, under the pinned runtime):

    python -m admet.scripts.build_split_input \
        --config admet/data/splits/split_input_config.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from rdkit import Chem, rdBase

import evaluation.novelty as novelty
from admet.scripts import alias_grouping


SCHEMA_VERSION = "admet_split_input.v1"

FAMILIES_FILENAME = "families.csv"
MEMBERSHIPS_FILENAME = "memberships.csv"
SIMILARITY_FILENAME = "family_similarity_upper.npy"
METADATA_FILENAME = "run_metadata.json"
CHECKSUMS_FILENAME = "SHA256SUMS.txt"


@dataclass(frozen=True)
class SplitIdentity:
    """One endpoint-qualified molecular identity used for splitting."""

    endpoint: str
    identity: str
    source_smiles: str
    family_key: str


@dataclass(frozen=True)
class SourceIdentity:
    """One endpoint identity before grouping: identity key and SMILES only."""

    endpoint: str
    identity: str
    source_smiles: str


@dataclass(frozen=True)
class Family:
    """One immutable family F_i with its D031 per-family fields."""

    family_index: int
    family_key: str
    members: tuple[SplitIdentity, ...]

    @property
    def weight(self) -> int:
        return len(self.members)

    def endpoint_count(self, endpoint: str) -> int:
        return sum(1 for member in self.members if member.endpoint == endpoint)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def executed_code_hashes() -> dict[str, str]:
    """SHA-256 of the module files actually imported by this run."""

    modules = {
        "admet.scripts.build_split_input": sys.modules[__name__],
        "admet.scripts.alias_grouping": alias_grouping,
        "evaluation.novelty": novelty,
    }
    hashes = {}
    for name, module in modules.items():
        path = Path(module.__file__).resolve()
        hashes[name] = {"path": str(path), "sha256": sha256_file(path)}
    return hashes


def read_manifest(manifest_path: Path) -> dict[str, str]:
    """Read a `shasum -a 256` style manifest into {filename: digest}."""

    entries: dict[str, str] = {}
    for line in manifest_path.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        entries[name.strip().lstrip("*")] = digest
    return entries


def verify_inputs_against_manifest(
    input_paths: list[Path], manifest_path: Path
) -> dict[str, str]:
    """Halt unless every input file is in the manifest's directory and matches it."""

    manifest = read_manifest(manifest_path)
    manifest_dir = manifest_path.resolve().parent
    verified: dict[str, str] = {}

    for path in input_paths:
        if path.resolve().parent != manifest_dir:
            raise ValueError(
                f"{path} is not in the manifest directory {manifest_dir}"
            )
        if path.name not in manifest:
            raise ValueError(f"{path.name!r} is not listed in {manifest_path}")
        observed = sha256_file(path)
        if observed != manifest[path.name]:
            raise ValueError(
                f"SHA-256 mismatch for {path}: observed {observed}, "
                f"manifest {manifest[path.name]}"
            )
        verified[str(path)] = observed

    return verified


def load_source_identities(
    path: Path,
    *,
    endpoint: str,
    identity_column: str,
    smiles_column: str,
) -> list[SourceIdentity]:
    """Load one SMILES per identity, retaining no other column.

    Every row of an identity must carry the same SMILES string; any
    disagreement halts. Label values are discarded as each row is read.
    """

    smiles_by_identity: dict[str, set[str]] = defaultdict(set)

    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        for column in (identity_column, smiles_column):
            if column not in header:
                raise ValueError(f"{path} has no column {column!r}")
        identity_index = header.index(identity_column)
        smiles_index = header.index(smiles_column)

        for row in reader:
            if len(row) != len(header):
                raise ValueError(
                    f"{path} line {reader.line_num}: expected {len(header)} "
                    f"fields, found {len(row)}"
                )
            identity = row[identity_index]
            smiles = row[smiles_index]
            if not identity or not smiles:
                raise ValueError(
                    f"{path} line {reader.line_num}: empty identity or SMILES"
                )
            smiles_by_identity[identity].add(smiles)

    identities: list[SourceIdentity] = []
    for identity in sorted(smiles_by_identity):
        smiles = smiles_by_identity[identity]
        if len(smiles) != 1:
            raise ValueError(
                f"{endpoint}:{identity} has {len(smiles)} distinct "
                "source-recorded SMILES"
            )
        identities.append(
            SourceIdentity(
                endpoint=endpoint,
                identity=identity,
                source_smiles=next(iter(smiles)),
            )
        )

    return identities


def group_identities(
    sources: list[SourceIdentity],
) -> tuple[list[SplitIdentity], dict[tuple[str, str], object]]:
    """Apply D032 alias grouping; any grouping failure halts."""

    split_identities: list[SplitIdentity] = []
    results: dict[tuple[str, str], object] = {}
    failures: list[str] = []

    for source in sources:
        result = alias_grouping.build_alias_grouping_result(source.source_smiles)
        key = (source.endpoint, source.identity)
        results[key] = result

        if not result.success or result.family_key is None:
            failures.append(
                f"{source.endpoint}:{source.identity} {result.failures}"
            )
            continue

        split_identities.append(
            SplitIdentity(
                endpoint=source.endpoint,
                identity=source.identity,
                source_smiles=source.source_smiles,
                family_key=result.family_key,
            )
        )

    if failures:
        raise ValueError(
            f"{len(failures)} grouping failure(s); D031 requires every "
            "identity to belong to a family: " + "; ".join(failures)
        )

    return split_identities, results


def build_families(identities: list[SplitIdentity]) -> list[Family]:
    """Collect identities into immutable families ordered by family_key."""

    members_by_key: dict[str, list[SplitIdentity]] = defaultdict(list)
    for record in identities:
        members_by_key[record.family_key].append(record)

    families = []
    for family_index, family_key in enumerate(sorted(members_by_key)):
        members = sorted(
            members_by_key[family_key],
            key=lambda member: (member.endpoint, member.identity),
        )
        families.append(Family(family_index, family_key, tuple(members)))

    return families


def check_expected_counts(observed: dict, expected: dict) -> None:
    """Halt on any difference from the frozen expected counts."""

    mismatches = []
    for name, expected_value in expected.items():
        if name not in observed:
            mismatches.append(f"{name}: not measured")
        elif observed[name] != expected_value:
            mismatches.append(
                f"{name}: observed {observed[name]!r}, expected {expected_value!r}"
            )
    if mismatches:
        raise ValueError("Expected-count mismatch: " + "; ".join(mismatches))


def fingerprint_split_identities(
    identities: list[SplitIdentity],
):
    """Fingerprint preserved prepared-source SMILES.

    Molecular representations are parsed directly from the preserved
    prepared-source SMILES. No family-key normalization, canonical-SMILES
    substitution, or representative-molecule substitution is permitted.
    """

    generator = novelty.make_morgan_generator()
    fingerprints = {}

    for record in identities:
        mol = Chem.MolFromSmiles(record.source_smiles)

        if mol is None:
            raise ValueError(
                "Split similarity-input SMILES failed sanitized RDKit "
                f"parsing: endpoint={record.endpoint!r}, "
                f"identity={record.identity!r}, "
                f"smiles={record.source_smiles!r}"
            )

        key = (record.endpoint, record.identity)

        if key in fingerprints:
            raise ValueError(
                f"Duplicate split identity encountered: {key!r}"
            )

        fingerprints[key] = generator.GetFingerprint(mol)

    return fingerprints


def mean_pairwise_similarity(fingerprints_a, fingerprints_b) -> float:
    """Complete mean of calculate_tanimoto over all a x b molecule pairs."""

    if not fingerprints_a or not fingerprints_b:
        raise ValueError("Family similarity requires two non-empty families.")

    total = 0.0
    for fp_a in fingerprints_a:
        for fp_b in fingerprints_b:
            total += novelty.calculate_tanimoto(fp_a, fp_b)

    return total / (len(fingerprints_a) * len(fingerprints_b))


def family_fingerprints(members, fingerprints) -> tuple:
    return tuple(fingerprints[(m.endpoint, m.identity)] for m in members)


def family_mean_similarity(
    family_a: list[SplitIdentity],
    family_b: list[SplitIdentity],
    fingerprints,
) -> float:
    """Return the complete mean molecular similarity between two families."""

    return mean_pairwise_similarity(
        family_fingerprints(family_a, fingerprints),
        family_fingerprints(family_b, fingerprints),
    )


def upper_triangle_length(family_count: int) -> int:
    return family_count * (family_count - 1) // 2


def upper_triangle_index(i: int, j: int, family_count: int) -> int:
    """Position of pair (i, j), i < j, in row-major upper-triangle order."""

    if not 0 <= i < j < family_count:
        raise ValueError(f"invalid pair ({i}, {j}) for {family_count} families")
    return i * family_count - i * (i + 1) // 2 + (j - i - 1)


def complete_family_similarities(
    families: list[Family], fingerprints
) -> np.ndarray:
    """Complete S_ij for every unordered family pair, upper-triangle order.

    No pair is pruned, thresholded, sampled or approximated.
    """

    family_count = len(families)
    per_family = [family_fingerprints(f.members, fingerprints) for f in families]
    similarities = np.empty(upper_triangle_length(family_count), dtype=np.float64)
    position = 0

    for i in range(family_count):
        fingerprints_i = per_family[i]
        for j in range(i + 1, family_count):
            similarities[position] = mean_pairwise_similarity(
                fingerprints_i, per_family[j]
            )
            position += 1

    if position != similarities.size:
        raise AssertionError(
            f"Filled {position} of {similarities.size} family pairs"
        )
    if not np.all(np.isfinite(similarities)):
        raise ValueError("Non-finite family similarity encountered")
    if similarities.size and (similarities.min() < 0.0 or similarities.max() > 1.0):
        raise ValueError("Family similarity outside [0, 1]")

    return similarities


def _write_artifacts(
    directory: Path,
    families: list[Family],
    endpoint_names: list[str],
    grouping_results: dict[tuple[str, str], object],
    similarities: np.ndarray,
    metadata: dict,
) -> dict[str, str]:
    with (directory / FAMILIES_FILENAME).open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["family_index", "family_key", "w"]
            + [f"{name}_identities" for name in endpoint_names]
            + ["diagnostic_scaffold_keys"]
        )
        for family in families:
            scaffold_keys = sorted(
                {
                    grouping_results[(m.endpoint, m.identity)].scaffold_key
                    for m in family.members
                    if grouping_results[(m.endpoint, m.identity)].scaffold_key
                }
            )
            writer.writerow(
                [family.family_index, family.family_key, family.weight]
                + [family.endpoint_count(name) for name in endpoint_names]
                + [";".join(scaffold_keys)]
            )

    with (directory / MEMBERSHIPS_FILENAME).open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "endpoint",
                "identity",
                "source_smiles",
                "family_index",
                "family_key",
                "scaffold_key",
                "grouping_notes",
            ]
        )
        for family in families:
            for member in family.members:
                result = grouping_results[(member.endpoint, member.identity)]
                writer.writerow(
                    [
                        member.endpoint,
                        member.identity,
                        member.source_smiles,
                        family.family_index,
                        family.family_key,
                        result.scaffold_key or "",
                        ";".join(result.notes),
                    ]
                )

    np.save(directory / SIMILARITY_FILENAME, similarities, allow_pickle=False)

    (directory / METADATA_FILENAME).write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )

    checksums = {
        name: sha256_file(directory / name)
        for name in (
            FAMILIES_FILENAME,
            MEMBERSHIPS_FILENAME,
            SIMILARITY_FILENAME,
            METADATA_FILENAME,
        )
    }
    (directory / CHECKSUMS_FILENAME).write_text(
        "".join(f"{digest}  {name}\n" for name, digest in checksums.items())
    )
    return checksums


def write_outputs(
    output_dir: Path,
    families: list[Family],
    endpoint_names: list[str],
    grouping_results: dict[tuple[str, str], object],
    similarities: np.ndarray,
    metadata: dict,
) -> dict[str, str]:
    """Write all artifacts to a temporary sibling, then move it into place.

    A non-empty output directory is never overwritten. A failed write leaves
    no partial artifact set at the output path.
    """

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"{output_dir} already contains files; frozen outputs are not overwritten"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.partial-", dir=output_dir.parent)
    )
    try:
        checksums = _write_artifacts(
            staging, families, endpoint_names, grouping_results, similarities, metadata
        )
        if output_dir.exists():
            output_dir.rmdir()
        staging.rename(output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return checksums


def build_split_input(config_path: Path, repo_root: Path) -> dict:
    """Run the complete build under the frozen configuration."""

    alias_grouping.assert_authoritative_rdkit_runtime()

    config_text = config_path.read_text()
    config = json.loads(config_text)
    if rdBase.rdkitVersion != config["authoritative_rdkit_version"]:
        raise RuntimeError(
            f"Config requires RDKit {config['authoritative_rdkit_version']}; "
            f"runtime is {rdBase.rdkitVersion}"
        )

    timings: dict[str, float] = {}
    started = time.perf_counter()

    endpoint_specs = config["endpoints"]
    endpoint_names = [spec["endpoint"] for spec in endpoint_specs]
    input_paths = [repo_root / spec["path"] for spec in endpoint_specs]
    input_hashes = verify_inputs_against_manifest(
        input_paths, repo_root / config["prepared_manifest"]
    )

    sources: list[SourceIdentity] = []
    endpoint_identities: dict[str, int] = {}
    for spec, path in zip(endpoint_specs, input_paths):
        loaded = load_source_identities(
            path,
            endpoint=spec["endpoint"],
            identity_column=spec["identity_column"],
            smiles_column=spec["smiles_column"],
        )
        endpoint_identities[spec["endpoint"]] = len(loaded)
        sources.extend(loaded)
    timings["load_seconds"] = time.perf_counter() - started

    phase = time.perf_counter()
    identities, grouping_results = group_identities(sources)
    families = build_families(identities)
    scaffold_keys = {
        result.scaffold_key
        for result in grouping_results.values()
        if result.scaffold_key is not None
    }
    timings["grouping_seconds"] = time.perf_counter() - phase

    observed_counts = {
        "endpoint_identities": endpoint_identities,
        "endpoint_qualified_identities": len(sources),
        "successfully_grouped": len(identities),
        "grouping_failures": len(sources) - len(identities),
        "distinct_family_keys": len(families),
        "distinct_scaffold_keys": len(scaffold_keys),
    }
    check_expected_counts(observed_counts, config["expected_counts"])

    phase = time.perf_counter()
    fingerprints = fingerprint_split_identities(identities)
    timings["fingerprint_seconds"] = time.perf_counter() - phase

    phase = time.perf_counter()
    similarities = complete_family_similarities(families, fingerprints)
    timings["similarity_seconds"] = time.perf_counter() - phase
    timings["total_seconds_before_write"] = time.perf_counter() - started

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "governing_decisions": config["governing_decisions"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": hashlib.sha256(config_text.encode()).hexdigest(),
        "input_sha256": input_hashes,
        "executed_code_sha256": executed_code_hashes(),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "rdkit": rdBase.rdkitVersion,
            "numpy": np.__version__,
        },
        "fingerprint": {
            "type": "Morgan",
            "radius": novelty.MORGAN_RADIUS,
            "fp_size": novelty.MORGAN_FP_SIZE,
            "use_chirality": novelty.MORGAN_USE_CHIRALITY,
            "similarity": "Tanimoto",
            "input": "complete prepared-source SMILES, no fragment selection or desalting",
        },
        "endpoints": endpoint_names,
        "observed_counts": observed_counts,
        "family_count": len(families),
        "similarity_layout": {
            "file": SIMILARITY_FILENAME,
            "dtype": "float64",
            "length": int(similarities.size),
            "order": (
                "row-major upper triangle over family_index: pairs (i, j) with "
                "i < j, i ascending then j ascending; position = "
                "i*F - i*(i+1)/2 + (j - i - 1), F = family_count"
            ),
        },
        "timings_seconds": timings,
    }

    checksums = write_outputs(
        repo_root / config["output_dir"],
        families,
        endpoint_names,
        grouping_results,
        similarities,
        metadata,
    )
    return {"metadata": metadata, "output_sha256": checksums}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    summary = build_split_input(args.config, args.repo_root)
    print(json.dumps(summary["metadata"]["observed_counts"], indent=2))
    print(json.dumps(summary["metadata"]["timings_seconds"], indent=2))
    for name, digest in summary["output_sha256"].items():
        print(f"{digest}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
