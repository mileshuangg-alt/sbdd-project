from pathlib import Path
import re
import subprocess

import numpy as np
from Bio.PDB import PDBIO, PDBParser, Select


ROOT = Path("references/stage5/native_complexes")

COMPLEXES = [
    "3REY",
    "5OLH",
    "5OLO",
]

CHAIN_ID = "A"
PH = 7.4
COORD_TOLERANCE = 1e-4


class ReceptorSelect(Select):
    """Keep only standard protein residues from chain A."""

    def accept_chain(self, chain):
        return chain.id == CHAIN_ID

    def accept_residue(self, residue):
        return residue.id[0] == " "


def resolve_altlocs(structure):
    """Resolve alternate locations deterministically.

    Selection rule:
    1. Highest occupancy wins.
    2. On an occupancy tie, prefer altloc A.
    3. If A is absent, choose the lexicographically first altloc.

    After selection, the altloc identifier is blanked so downstream
    preparation sees one ordinary deposited conformer.
    """

    selections = []

    for residue in structure.get_residues():
        if residue.id[0] != " ":
            continue

        for atom in residue:
            if not atom.is_disordered():
                continue

            alternatives = atom.disordered_get_list()

            ranked = sorted(
                alternatives,
                key=lambda candidate: (
                    -(
                        candidate.get_occupancy()
                        if candidate.get_occupancy() is not None
                        else 0.0
                    ),
                    (
                        0
                        if candidate.get_altloc().strip() == "A"
                        else 1
                    ),
                    candidate.get_altloc().strip(),
                ),
            )

            selected = ranked[0]
            selected_altloc = selected.get_altloc()
            occupancy = selected.get_occupancy()

            atom.disordered_select(selected_altloc)

            selection = {
                "chain": residue.get_parent().id,
                "resname": residue.get_resname(),
                "resid": residue.id[1],
                "atom": atom.get_name(),
                "altloc": selected_altloc.strip(),
                "occupancy": occupancy,
            }

            selections.append(selection)

            # The alternate-location decision is complete.
            selected.set_altloc(" ")

    return selections


def extract_receptor(pdb_id):
    """Extract one deterministic chain-A receptor conformer."""

    source = ROOT / f"{pdb_id}.pdb"
    directory = ROOT / pdb_id
    output = directory / f"{pdb_id}_receptor_raw.pdb"

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    parser = PDBParser(QUIET=True)

    structure = parser.get_structure(
        pdb_id,
        str(source),
    )

    altloc_selections = resolve_altlocs(
        structure
    )

    io = PDBIO()
    io.set_structure(structure)

    io.save(
        str(output),
        ReceptorSelect(),
    )

    return output, altloc_selections


def run_pdb2pqr(pdb_id, raw_pdb):
    """Prepare receptor under the frozen D007 protonation policy."""

    directory = ROOT / pdb_id

    output_pqr = (
        directory
        / f"{pdb_id}_receptor_pH7.4.pqr"
    )

    output_log = (
        directory
        / f"{pdb_id}_receptor_pH7.4.log"
    )

    command = [
        "pdb2pqr",
        "--ff=AMBER",
        "--titration-state-method=propka",
        f"--with-ph={PH}",
        "--keep-chain",
        "--noopt",
        "--nodebump",
        str(raw_pdb),
        str(output_pqr),
    ]

    with output_log.open("w") as log:
        subprocess.run(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

    return output_pqr, output_log


def load_structure(path, name):
    """Load a PDB/PQR structure with BioPython."""

    parser = PDBParser(QUIET=True)

    structure = parser.get_structure(
        name,
        str(path),
    )

    return structure


def audit_anchor_residues(structure, pdb_id):
    """Require the predeclared A2A anchor-region residues."""

    chain = structure[0][CHAIN_ID]

    expected = {
        168: "PHE",
        250: "HIS",
        253: "ASN",
    }

    results = {}

    for number, expected_name in expected.items():
        matches = [
            residue
            for residue in chain
            if residue.id[0] == " "
            and residue.id[1] == number
        ]

        if len(matches) != 1:
            raise ValueError(
                f"{pdb_id}: expected exactly one "
                f"chain-A residue {number}, "
                f"found {len(matches)}."
            )

        residue = matches[0]

        if residue.get_resname() != expected_name:
            raise ValueError(
                f"{pdb_id}: residue {number} is "
                f"{residue.get_resname()}, "
                f"expected {expected_name}."
            )

        results[number] = residue.get_resname()

    return results


def heavy_atom_dictionary(structure):
    """Map receptor heavy atoms by chain/residue/atom identity."""

    atoms = {}

    for residue in structure.get_residues():
        chain = residue.get_parent().id

        for atom in residue.get_atoms():
            if atom.element.strip().upper() == "H":
                continue

            key = (
                chain,
                residue.id[1],
                residue.get_resname(),
                atom.get_name(),
            )

            atoms[key] = np.array(
                atom.coord,
                dtype=float,
            )

    return atoms


def calculate_heavy_atom_displacements(
    raw_structure,
    prepared_structure,
):
    """Measure deposited-heavy-atom displacement."""

    raw = heavy_atom_dictionary(
        raw_structure
    )

    prepared = heavy_atom_dictionary(
        prepared_structure
    )

    common = set(raw) & set(prepared)
    missing = set(raw) - set(prepared)
    added = set(prepared) - set(raw)

    if missing:
        raise ValueError(
            "Deposited heavy atoms are missing "
            f"from prepared receptor: {sorted(missing)}"
        )

    displacements = {}

    for key in common:
        displacement = float(
            np.linalg.norm(
                raw[key] - prepared[key]
            )
        )

        displacements[key] = displacement

    values = np.array(
        list(displacements.values()),
        dtype=float,
    )

    results = {
        "raw_heavy_atoms": len(raw),
        "prepared_heavy_atoms": len(prepared),
        "matched_heavy_atoms": len(common),
        "added_heavy_atoms": sorted(added),
        "max_displacement": float(values.max()),
        "mean_displacement": float(values.mean()),
        "displacements": displacements,
    }

    return results


def build_prepared_atom_lookup(prepared_structure):
    """Map all prepared receptor atoms by identity."""

    lookup = {}

    for residue in prepared_structure.get_residues():
        chain = residue.get_parent().id

        for atom in residue.get_atoms():
            key = (
                chain,
                residue.id[1],
                residue.get_resname(),
                atom.get_name(),
            )

            lookup[key] = atom

    return lookup


def find_attached_hydrogens(
    heavy_atom,
    residue,
):
    """Find hydrogens attached to one prepared heavy atom.

    PQR does not provide explicit bond topology here, so attachment is
    inferred from prepared geometry.

    A 1.25 A cutoff includes normal X-H covalent bonds while remaining
    well below ordinary nonbonded distances.
    """

    attached = []

    heavy_coord = np.array(
        heavy_atom.coord,
        dtype=float,
    )

    for candidate in residue.get_atoms():
        if candidate.element.strip().upper() != "H":
            continue

        hydrogen_coord = np.array(
            candidate.coord,
            dtype=float,
        )

        distance = float(
            np.linalg.norm(
                heavy_coord - hydrogen_coord
            )
        )

        if distance <= 1.25:
            attached.append(candidate)

    return attached


def restore_deposited_heavy_atoms(
    raw_structure,
    prepared_structure,
):
    """Restore all deposited receptor heavy atoms.

    PDB2PQR/PROPKA remains authoritative for the pH-7.4
    protonation-state assignment and generated hydrogens.

    Every heavy atom present in the selected deposited receptor is
    restored to its experimental coordinate.

    Hydrogens attached to a restored heavy atom are rigidly translated
    by the same vector as their parent. This retains PDB2PQR's local
    X-H geometry while restoring experimental heavy-atom geometry.

    Heavy atoms added by PDB2PQR, such as terminal OXT atoms, are
    retained because no deposited coordinate exists for restoration.
    """

    raw_heavy = heavy_atom_dictionary(
        raw_structure
    )

    prepared_lookup = build_prepared_atom_lookup(
        prepared_structure
    )

    processed_heavy_atoms = 0
    processed_hydrogens = 0
    moved_heavy_atoms = 0
    moved_hydrogens = 0
    restoration_records = []

    for key, native_coord in raw_heavy.items():
        if key not in prepared_lookup:
            raise ValueError(
                "Cannot restore missing prepared atom: "
                f"{key}"
            )

        prepared_atom = prepared_lookup[key]

        if prepared_atom.element.strip().upper() == "H":
            raise ValueError(
                "Heavy-atom restoration lookup unexpectedly "
                f"resolved to hydrogen: {key}"
            )

        prepared_coord = np.array(
            prepared_atom.coord,
            dtype=float,
        )

        translation = (
            native_coord - prepared_coord
        )

        displacement = float(
            np.linalg.norm(translation)
        )

        residue = prepared_atom.get_parent()

        attached_hydrogens = find_attached_hydrogens(
            prepared_atom,
            residue,
        )

        processed_heavy_atoms += 1
        processed_hydrogens += len(attached_hydrogens)

        for hydrogen in attached_hydrogens:
            hydrogen.coord = (
                np.array(
                    hydrogen.coord,
                    dtype=float,
                )
                + translation
            )

        prepared_atom.coord = np.array(
            native_coord,
            dtype=float,
        )

        if displacement > COORD_TOLERANCE:
            moved_heavy_atoms += 1
            moved_hydrogens += len(attached_hydrogens)

            record = {
                "atom": key,
                "pre_restoration_displacement": displacement,
                "translated_hydrogens": [
                    hydrogen.get_name()
                    for hydrogen in attached_hydrogens
                ],
            }

            restoration_records.append(record)

    results = {
        "processed_heavy_atoms": processed_heavy_atoms,
        "processed_hydrogens": processed_hydrogens,
        "moved_heavy_atoms": moved_heavy_atoms,
        "moved_hydrogens": moved_hydrogens,
        "restoration_records": restoration_records,
    }

    return results


def audit_heavy_atom_preservation(
    raw_structure,
    prepared_structure,
    pdb_id,
):
    """Measure, restore, and verify deposited receptor geometry."""

    pre_restoration = (
        calculate_heavy_atom_displacements(
            raw_structure,
            prepared_structure,
        )
    )

    restoration = (
        restore_deposited_heavy_atoms(
            raw_structure,
            prepared_structure,
        )
    )

    post_restoration = (
        calculate_heavy_atom_displacements(
            raw_structure,
            prepared_structure,
        )
    )

    if (
        post_restoration["max_displacement"]
        > COORD_TOLERANCE
    ):
        raise ValueError(
            f"{pdb_id}: deposited receptor geometry "
            "was not successfully restored; "
            "post-restoration max displacement="
            f"{post_restoration['max_displacement']:.6f} A"
        )

    results = {
        "raw_heavy_atoms":
            post_restoration["raw_heavy_atoms"],

        "prepared_heavy_atoms":
            post_restoration["prepared_heavy_atoms"],

        "matched_heavy_atoms":
            post_restoration["matched_heavy_atoms"],

        "added_heavy_atoms":
            post_restoration["added_heavy_atoms"],

        "pre_max_displacement":
            pre_restoration["max_displacement"],

        "pre_mean_displacement":
            pre_restoration["mean_displacement"],

        "post_max_displacement":
            post_restoration["max_displacement"],

        "post_mean_displacement":
            post_restoration["mean_displacement"],

        "processed_heavy_atoms":
            restoration["processed_heavy_atoms"],

        "processed_hydrogens":
            restoration["processed_hydrogens"],

        "moved_heavy_atoms":
            restoration["moved_heavy_atoms"],

        "moved_hydrogens":
            restoration["moved_hydrogens"],

        "restoration_records":
            restoration["restoration_records"],
    }

    return results


def audit_hydrogens(prepared_structure):
    """Require explicit hydrogens in the prepared receptor."""

    atoms = list(
        prepared_structure.get_atoms()
    )

    hydrogens = [
        atom
        for atom in atoms
        if atom.element.strip().upper() == "H"
    ]

    if not hydrogens:
        raise ValueError(
            "Prepared receptor contains "
            "no explicit hydrogens."
        )

    return len(atoms), len(hydrogens)


def audit_his250(
    prepared_structure,
    pdb_id,
):
    """Record the explicit His250 protonation state."""

    chain = prepared_structure[0][CHAIN_ID]

    matches = [
        residue
        for residue in chain
        if residue.id[0] == " "
        and residue.id[1] == 250
    ]

    if len(matches) != 1:
        raise ValueError(
            f"{pdb_id}: could not uniquely "
            "identify His250."
        )

    residue = matches[0]

    names = {
        atom.get_name()
        for atom in residue.get_atoms()
    }

    hd1 = "HD1" in names
    he2 = "HE2" in names

    if hd1 and not he2:
        state = (
            "ND1-protonated / "
            "NE2-unprotonated"
        )

    elif he2 and not hd1:
        state = (
            "NE2-protonated / "
            "ND1-unprotonated"
        )

    elif hd1 and he2:
        state = "doubly protonated"

    else:
        state = "no ring proton detected"

    results = {
        "HD1": hd1,
        "HE2": he2,
        "state": state,
    }

    return results


def extract_his250_pka(log_path):
    """Extract the PROPKA His250 pKa when present."""

    text = log_path.read_text(
        errors="replace"
    )

    pattern = (
        r"HIS\s+250\s+A\s+"
        r"(-?\d+(?:\.\d+)?)"
    )

    match = re.search(
        pattern,
        text,
    )

    if match:
        pka = float(
            match.group(1)
        )

        return pka

    return None


def summarize_altloc_selections(selections):
    """Collapse atom-level selections into residue-level reporting."""

    summary = {}

    for selection in selections:
        key = (
            selection["chain"],
            selection["resname"],
            selection["resid"],
        )

        value = (
            selection["altloc"],
            selection["occupancy"],
        )

        if key not in summary:
            summary[key] = set()

        summary[key].add(value)

    return summary


def print_altloc_selections(selections):
    """Print deterministic deposited conformers selected."""

    if not selections:
        print(
            "Resolved alternate locations: none"
        )
        return

    print(
        "Resolved alternate locations:"
    )

    summary = summarize_altloc_selections(
        selections
    )

    sorted_keys = sorted(
        summary,
        key=lambda item: (
            item[0],
            item[2],
            item[1],
        ),
    )

    for key in sorted_keys:
        chain, resname, resid = key
        choices = summary[key]

        formatted = ", ".join(
            f"{altloc} "
            f"(occupancy {occupancy})"
            for altloc, occupancy
            in sorted(choices)
        )

        print(
            f"  {resname} {resid} "
            f"chain {chain} "
            f"-> {formatted}"
        )


def print_restoration_records(records):
    """Print only nontrivial PDB2PQR heavy-atom movements."""

    if not records:
        print(
            "Nontrivial heavy-atom restorations: none"
        )
        return

    print(
        "Nontrivial heavy-atom restorations:"
    )

    for record in records:
        print(
            " ",
            record["atom"],
            "pre-restoration displacement="
            f"{record['pre_restoration_displacement']:.6f} A",
            "translated hydrogens="
            f"{record['translated_hydrogens']}",
        )


def write_restored_pqr(
    source_pqr,
    prepared_structure,
    output_pqr,
):
    """Persist restored coordinates while preserving PDB2PQR formatting.

    The original PDB2PQR record is retained byte-for-byte except for
    the XYZ coordinate columns.

    This preserves atom-name alignment, residue formatting, charges,
    radii, and protonation-derived atom identities.
    """

    restored_lookup = build_prepared_atom_lookup(
        prepared_structure
    )

    output_lines = []
    written_atoms = 0

    with source_pqr.open() as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                output_lines.append(line)
                continue

            atom_name = line[12:16].strip()
            resname = line[17:20].strip()
            chain = line[21].strip()

            # PDB2PQR uses fixed PDB-style residue columns here.
            resid = int(
                line[22:26].strip()
            )

            key = (
                chain,
                resid,
                resname,
                atom_name,
            )

            if key not in restored_lookup:
                raise ValueError(
                    "Could not find restored coordinates "
                    f"for PQR atom {key}."
                )

            atom = restored_lookup[key]

            x, y, z = np.array(
                atom.coord,
                dtype=float,
            )

            # Preserve every original character except XYZ.
            restored_line = (
                line[:30]
                + f"{x:8.3f}"
                + f"{y:8.3f}"
                + f"{z:8.3f}"
                + line[54:]
            )

            output_lines.append(
                restored_line
            )

            written_atoms += 1

    output_pqr.write_text(
        "".join(output_lines)
    )

    results = {
        "written_atoms": written_atoms,
        "output_pqr": output_pqr,
    }

    return results


def prepare_complex(pdb_id):
    """Prepare, restore, persist, and audit one native A2A receptor."""

    print()
    print("=" * 72)
    print(
        f"{pdb_id} receptor"
    )
    print("=" * 72)

    raw_pdb, altloc_selections = (
        extract_receptor(
            pdb_id
        )
    )

    print_altloc_selections(
        altloc_selections
    )

    raw_structure = load_structure(
        raw_pdb,
        f"{pdb_id}_raw",
    )

    anchors = audit_anchor_residues(
        raw_structure,
        pdb_id,
    )

    output_pqr, output_log = (
        run_pdb2pqr(
            pdb_id,
            raw_pdb,
        )
    )

    prepared_structure = load_structure(
        output_pqr,
        f"{pdb_id}_prepared",
    )

    preservation = (
        audit_heavy_atom_preservation(
            raw_structure,
            prepared_structure,
            pdb_id,
        )
    )

    total_atoms, hydrogen_count = (
        audit_hydrogens(
            prepared_structure
        )
    )

    his250 = audit_his250(
        prepared_structure,
        pdb_id,
    )

    his250_pka = extract_his250_pka(
        output_log
    )

    restored_pqr = (
        ROOT
        / pdb_id
        / f"{pdb_id}_receptor_pH7.4_restored.pqr"
    )

    write_results = write_restored_pqr(
        output_pqr,
        prepared_structure,
        restored_pqr,
    )

    persisted_structure = load_structure(
        restored_pqr,
        f"{pdb_id}_persisted_restored",
    )

    persisted_audit = (
        calculate_heavy_atom_displacements(
            raw_structure,
            persisted_structure,
        )
    )

    if (
        persisted_audit["max_displacement"]
        > COORD_TOLERANCE
    ):
        raise ValueError(
            f"{pdb_id}: persisted restored receptor "
            "does not preserve deposited geometry; "
            "max displacement="
            f"{persisted_audit['max_displacement']:.6f} A"
        )

    (
        persisted_total_atoms,
        persisted_hydrogens,
    ) = audit_hydrogens(
        persisted_structure
    )

    persisted_his250 = audit_his250(
        persisted_structure,
        pdb_id,
    )

    if persisted_total_atoms != total_atoms:
        raise ValueError(
            f"{pdb_id}: atom count changed during "
            "restored-PQR persistence."
        )

    if persisted_hydrogens != hydrogen_count:
        raise ValueError(
            f"{pdb_id}: hydrogen count changed during "
            "restored-PQR persistence."
        )

    if persisted_his250["state"] != his250["state"]:
        raise ValueError(
            f"{pdb_id}: His250 state changed during "
            "restored-PQR persistence."
        )

    print(
        "Anchor residues:",
        anchors,
    )

    print(
        "Raw heavy atoms:",
        preservation["raw_heavy_atoms"],
    )

    print(
        "Prepared heavy atoms:",
        preservation["prepared_heavy_atoms"],
    )

    print(
        "Matched deposited heavy atoms:",
        preservation["matched_heavy_atoms"],
    )

    print(
        "Added heavy atoms:",
        preservation["added_heavy_atoms"],
    )

    print(
        "Total prepared atoms:",
        total_atoms,
    )

    print(
        "Hydrogens:",
        hydrogen_count,
    )

    print(
        "Pre-restoration max deposited "
        "heavy-atom displacement:",
        f"{preservation['pre_max_displacement']:.6f} A",
    )

    print(
        "Pre-restoration mean deposited "
        "heavy-atom displacement:",
        f"{preservation['pre_mean_displacement']:.6f} A",
    )

    print(
        "Post-restoration max deposited "
        "heavy-atom displacement:",
        f"{preservation['post_max_displacement']:.6f} A",
    )

    print(
        "Post-restoration mean deposited "
        "heavy-atom displacement:",
        f"{preservation['post_mean_displacement']:.6f} A",
    )

    print(
        "Deposited heavy atoms processed:",
        preservation["processed_heavy_atoms"],
    )

    print(
        "Parent-attached hydrogens processed:",
        preservation["processed_hydrogens"],
    )

    print(
        "Deposited heavy atoms actually moved:",
        preservation["moved_heavy_atoms"],
    )

    print(
        "Parent-attached hydrogens actually moved:",
        preservation["moved_hydrogens"],
    )

    print_restoration_records(
        preservation["restoration_records"]
    )

    print(
        "His250 state:",
        his250["state"],
    )

    print(
        "His250 HD1:",
        his250["HD1"],
    )

    print(
        "His250 HE2:",
        his250["HE2"],
    )

    print(
        "His250 PROPKA pKa:",
        (
            f"{his250_pka:.2f}"
            if his250_pka is not None
            else "not parsed"
        ),
    )

    print(
        "Persisted restored atoms:",
        write_results["written_atoms"],
    )

    print(
        "Persisted restored hydrogens:",
        persisted_hydrogens,
    )

    print(
        "Persisted post-restoration max "
        "heavy-atom displacement:",
        f"{persisted_audit['max_displacement']:.6f} A",
    )

    print(
        "Persisted His250 state:",
        persisted_his250["state"],
    )

    print(
        "Raw PDB2PQR receptor:",
        output_pqr,
    )

    print(
        "Restored receptor:",
        restored_pqr,
    )

    print(
        "Preparation log:",
        output_log,
    )

    print(
        "PASS: receptor preparation, restoration, "
        "persistence, and coordinate/protonation "
        "audits passed."
    )


def main():
    for pdb_id in COMPLEXES:
        prepare_complex(
            pdb_id
        )


if __name__ == "__main__":
    main()
