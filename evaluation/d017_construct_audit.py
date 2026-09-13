"""Read-only D017 construct-boundary audit helpers."""

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shlex


THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


@dataclass(frozen=True)
class AuthorResidue:
    """One coordinate-bearing polymer residue in an author chain."""

    chain: str
    number: str
    insertion_code: str
    name: str
    label_sequence_id: int


@dataclass(frozen=True)
class ReferenceSpan:
    """One mmCIF-deposited mapping interval."""

    construct_start: int
    construct_end: int
    accession: str
    canonical_start: int
    canonical_end: int


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise(value: str) -> str:
    return "" if value in {".", "?"} else value


def _read_loop(path: Path, prefix: str) -> list[dict[str, str]]:
    """Read one simple tabular mmCIF loop used by the deposited inputs."""

    lines = Path(path).read_text().splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        cursor = index + 1
        columns: list[str] = []
        while cursor < len(lines) and lines[cursor].startswith(prefix):
            columns.append(lines[cursor].strip())
            cursor += 1
        if not columns:
            continue
        values: list[str] = []
        while cursor < len(lines) and lines[cursor].strip() != "#":
            values.extend(shlex.split(lines[cursor], posix=True))
            cursor += 1
        if len(values) % len(columns):
            raise ValueError(f"Malformed {prefix} loop in {path}")
        return [
            dict(zip(columns, values[offset : offset + len(columns)]))
            for offset in range(0, len(values), len(columns))
        ]
    raise ValueError(f"Missing {prefix} loop in {path}")


def _read_category(path: Path, prefix: str) -> list[dict[str, str]]:
    """Read a loop or singleton mmCIF category into row dictionaries."""

    try:
        return _read_loop(path, prefix)
    except ValueError as error:
        if not str(error).startswith("Missing"):
            raise
    row: dict[str, str] = {}
    for line in Path(path).read_text().splitlines():
        if not line.startswith(prefix):
            continue
        tokens = shlex.split(line, posix=True)
        if len(tokens) != 2:
            raise ValueError(f"Malformed singleton {prefix} category in {path}")
        row[tokens[0]] = tokens[1]
    if not row:
        raise ValueError(f"Missing {prefix} category in {path}")
    return [row]


def parse_coordinate_residues(path: Path, author_chain: str) -> tuple[AuthorResidue, ...]:
    """Return unique coordinate-bearing ATOM residues for one author chain."""

    rows = _read_loop(path, "_atom_site.")
    residues: dict[tuple[str, str, str], AuthorResidue] = {}
    for row in rows:
        if row["_atom_site.group_PDB"] != "ATOM":
            continue
        if row["_atom_site.auth_asym_id"] != author_chain:
            continue
        if row["_atom_site.pdbx_PDB_model_num"] != "1":
            continue
        key = (
            row["_atom_site.auth_asym_id"],
            row["_atom_site.auth_seq_id"],
            _normalise(row["_atom_site.pdbx_PDB_ins_code"]),
        )
        residue = AuthorResidue(
            chain=key[0],
            number=key[1],
            insertion_code=key[2],
            name=row["_atom_site.auth_comp_id"],
            label_sequence_id=int(row["_atom_site.label_seq_id"]),
        )
        previous = residues.setdefault(key, residue)
        if previous != residue:
            raise ValueError(f"Conflicting author residue identity in {path}: {key}")
    return tuple(residues.values())


def parse_coordinate_atoms(path: Path, author_chain: str) -> tuple[dict[str, str], ...]:
    """Return deposited ATOM records for one author chain and model."""

    atoms = []
    for row in _read_loop(path, "_atom_site."):
        if row["_atom_site.group_PDB"] != "ATOM":
            continue
        if row["_atom_site.auth_asym_id"] != author_chain:
            continue
        if row["_atom_site.pdbx_PDB_model_num"] != "1":
            continue
        atoms.append(row)
    return tuple(atoms)


def parse_reference_spans(path: Path, author_chain: str) -> tuple[ReferenceSpan, ...]:
    """Read deposited author-chain to database-reference spans."""

    rows = _read_category(path, "_struct_ref_seq.")
    spans = []
    for row in rows:
        if row["_struct_ref_seq.pdbx_strand_id"] != author_chain:
            continue
        values = (
            row["_struct_ref_seq.seq_align_beg"],
            row["_struct_ref_seq.seq_align_end"],
            row["_struct_ref_seq.db_align_beg"],
            row["_struct_ref_seq.db_align_end"],
        )
        if any(value in {".", "?"} for value in values):
            continue
        spans.append(
            ReferenceSpan(
                construct_start=int(values[0]),
                construct_end=int(values[1]),
                accession=row["_struct_ref_seq.pdbx_db_accession"],
                canonical_start=int(values[2]),
                canonical_end=int(values[3]),
            )
        )
    return tuple(spans)


def parse_fasta(path: Path) -> tuple[str, str]:
    """Return the UniProt accession and sequence from one frozen FASTA."""

    lines = Path(path).read_text().splitlines()
    if not lines or not lines[0].startswith(">sp|"):
        raise ValueError(f"Expected a UniProt FASTA header in {path}")
    fields = lines[0][1:].split("|")
    if len(fields) < 2 or not fields[1]:
        raise ValueError(f"Missing UniProt accession in {path}")
    sequence = "".join(line.strip() for line in lines[1:])
    if not sequence or any(letter not in THREE_TO_ONE.values() for letter in sequence):
        raise ValueError(f"Invalid amino-acid sequence in {path}")
    return fields[1], sequence


def _ranges(values: list[int]) -> list[list[int]]:
    if not values:
        return []
    result: list[list[int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        result.append([start, previous])
        start = previous = value
    result.append([start, previous])
    return result


def _author_ranges(residues: tuple[AuthorResidue, ...]) -> list[dict[str, object]]:
    ranges = []
    current = [residues[0]] if residues else []
    for residue in residues[1:]:
        previous = current[-1]
        if (
            residue.insertion_code == ""
            and previous.insertion_code == ""
            and residue.number.lstrip("-").isdigit()
            and previous.number.lstrip("-").isdigit()
            and int(residue.number) == int(previous.number) + 1
        ):
            current.append(residue)
        else:
            ranges.append(current)
            current = [residue]
    if current:
        ranges.append(current)
    return [
        {
            "start": {"number": group[0].number, "insertion_code": group[0].insertion_code},
            "end": {"number": group[-1].number, "insertion_code": group[-1].insertion_code},
        }
        for group in ranges
    ]


def audit_construct(
    *,
    structure_id: str,
    structure_path: Path,
    author_chain: str,
    fasta_path: Path,
) -> dict[str, object]:
    """Audit one deposited construct using its mmCIF reference spans."""

    accession, canonical_sequence = parse_fasta(fasta_path)
    residues = parse_coordinate_residues(structure_path, author_chain)
    spans = parse_reference_spans(structure_path, author_chain)
    canonical_spans = tuple(span for span in spans if span.accession == accession)
    non_receptor_spans = tuple(span for span in spans if span.accession != accession)
    errors: list[str] = []
    if not residues:
        errors.append("selected author chain has no coordinate-bearing ATOM residues")
    if not canonical_spans:
        errors.append("no deposited reference span matches the canonical FASTA accession")
    covered_construct_positions: set[int] = set()
    covered_canonical_positions: set[int] = set()
    for span in canonical_spans:
        if span.construct_end - span.construct_start != span.canonical_end - span.canonical_start:
            errors.append("deposited canonical span is not one-to-one")
            continue
        if not 1 <= span.canonical_start <= span.canonical_end <= len(canonical_sequence):
            errors.append("deposited canonical span exceeds frozen FASTA")
            continue
        for offset in range(span.construct_end - span.construct_start + 1):
            covered_construct_positions.add(span.construct_start + offset)
            covered_canonical_positions.add(span.canonical_start + offset)
    if len(covered_construct_positions) != sum(
        span.construct_end - span.construct_start + 1 for span in canonical_spans
    ):
        errors.append("deposited canonical spans overlap")

    mappings = []
    non_receptor = []
    unmapped = []
    for residue in residues:
        if residue.label_sequence_id in covered_construct_positions:
            matching = next(
                span for span in canonical_spans
                if span.construct_start <= residue.label_sequence_id <= span.construct_end
            )
            canonical_position = matching.canonical_start + (
                residue.label_sequence_id - matching.construct_start
            )
            mappings.append(
                {
                    "author_residue": asdict(residue),
                    "canonical_position": canonical_position,
                    "canonical_residue": canonical_sequence[canonical_position - 1],
                }
            )
        elif any(
            span.construct_start <= residue.label_sequence_id <= span.construct_end
            for span in non_receptor_spans
        ):
            non_receptor.append(asdict(residue))
        else:
            unmapped.append(asdict(residue))
    mapped_positions = [entry["canonical_position"] for entry in mappings]
    missing_canonical = sorted(covered_canonical_positions - set(mapped_positions))
    return {
        "structure_id": structure_id,
        "author_chain": author_chain,
        "coordinate_bearing_author_residue_ranges": _author_ranges(residues),
        "canonical_receptor": {"accession": accession, "length": len(canonical_sequence)},
        "canonical_receptor_matching_spans": [asdict(span) for span in canonical_spans],
        "non_receptor_engineered_construct_spans": _author_ranges(
            tuple(AuthorResidue(**entry) for entry in non_receptor)
        ),
        "unmapped_coordinate_residues": unmapped,
        "ambiguous_regions": errors,
        "construct_to_canonical_mapping": mappings,
        "coordinate_bearing_canonical_residue_count": len(mappings),
        "coordinate_bearing_noncanonical_residue_count": len(non_receptor) + len(unmapped),
        "canonical_residues_without_experimental_coordinates": _ranges(missing_canonical),
        "source_mmcif": {"path": str(structure_path), "sha256": sha256_file(structure_path)},
        "canonical_fasta": {"path": str(fasta_path), "sha256": sha256_file(fasta_path)},
        "status": "AMBIGUOUS" if errors else "PASS",
    }


def write_audit_artifact(audit: dict[str, object], output_path: Path) -> None:
    """Write a stable JSON audit artifact."""

    with Path(output_path).open("w") as handle:
        json.dump(audit, handle, indent=2)
        handle.write("\n")
