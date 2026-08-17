from pathlib import Path
import subprocess

import numpy as np
from Bio.PDB import MMCIF2Dict, PDBParser
from rdkit import Chem
from rdkit.Chem import ChemicalFeatures
from rdkit import RDConfig
from rdkit.Geometry import Point3D


ROOT = Path("references/stage5/native_complexes")

CONTROLS = [
    {
        "pdb_id": "3REY",
        "ligand_name": "XAC",
        "ligand_code": "XAC",
    },
    {
        "pdb_id": "5OLH",
        "ligand_name": "Vipadenant",
        "ligand_code": "9XT",
    },
    {
        "pdb_id": "5OLO",
        "ligand_name": "Tozadenant",
        "ligand_code": "9XW",
    },
]

PH = 7.4

# These are broad geometric sanity checks, not the Stage 5 gate.
#
# Phe168:
# Published A2A structures place the ligand aromatic/core region
# against Phe168. 4.0 A is used here only as a contact-range
# preservation check.
PHE168_CONTACT_MAX = 4.0

# Asn253:
# Published structures contain direct polar contacts to Asn253.
# 3.5 A is a conventional broad donor/acceptor heavy-atom
# distance sanity range.
ASN253_POLAR_MAX = 3.5

COORD_TOLERANCE = 1e-4


FEATURE_FACTORY = ChemicalFeatures.BuildFeatureFactory(
    str(Path(RDConfig.RDDataDir) / "BaseFeatures.fdef")
)


def load_ccd_atom_table(cif_path):
    """Return CCD heavy-atom IDs/elements in authoritative ordinal order."""

    data = MMCIF2Dict.MMCIF2Dict(str(cif_path))

    atom_ids = data["_chem_comp_atom.atom_id"]
    elements = data["_chem_comp_atom.type_symbol"]
    ordinals = data["_chem_comp_atom.pdbx_ordinal"]

    rows = []

    for atom_id, element, ordinal in zip(
        atom_ids,
        elements,
        ordinals,
    ):
        if element.upper() == "H":
            continue

        rows.append(
            {
                "atom_id": atom_id,
                "element": element,
                "ordinal": int(ordinal),
            }
        )

    rows.sort(key=lambda row: row["ordinal"])

    return rows


def find_native_ligand(pdb_path, ligand_code):
    """Find exactly one deposited instance of the requested ligand."""

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(
        pdb_path.stem,
        str(pdb_path),
    )

    matches = []

    for residue in structure.get_residues():
        if residue.get_resname() == ligand_code:
            matches.append(residue)

    if len(matches) != 1:
        raise ValueError(
            f"{pdb_path.stem}: expected exactly one "
            f"{ligand_code} residue, found {len(matches)}."
        )

    return structure, matches[0]


def get_residue(structure, residue_number):
    """Find the A2A residue by deposited residue number."""

    matches = [
        residue
        for residue in structure.get_residues()
        if residue.id[1] == residue_number
        and residue.id[0] == " "
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one residue {residue_number}, "
            f"found {len(matches)}."
        )

    return matches[0]


def build_native_chemistry(
    template_sdf,
    ccd_cif,
    native_residue,
):
    """Combine authoritative CCD chemistry with deposited coordinates."""

    template = Chem.SDMolSupplier(
        str(template_sdf),
        removeHs=False,
    )[0]

    if template is None:
        raise ValueError(
            f"Failed to load template {template_sdf}"
        )

    ligand = Chem.RemoveHs(template)

    ccd_atoms = load_ccd_atom_table(ccd_cif)

    if ligand.GetNumAtoms() != len(ccd_atoms):
        raise ValueError(
            "CCD/template heavy-atom count mismatch: "
            f"{len(ccd_atoms)} vs {ligand.GetNumAtoms()}"
        )

    template_elements = [
        atom.GetSymbol()
        for atom in ligand.GetAtoms()
    ]

    ccd_elements = [
        row["element"]
        for row in ccd_atoms
    ]

    if template_elements != ccd_elements:
        raise ValueError(
            "Template atom order does not match CCD ordinal order."
        )

    native_by_name = {
        atom.get_name().strip(): atom
        for atom in native_residue.get_atoms()
        if atom.element.strip().upper() != "H"
    }

    ccd_names = [
        row["atom_id"]
        for row in ccd_atoms
    ]

    if set(ccd_names) != set(native_by_name):
        missing_native = sorted(
            set(ccd_names) - set(native_by_name)
        )
        extra_native = sorted(
            set(native_by_name) - set(ccd_names)
        )

        raise ValueError(
            "CCD/native atom-name mismatch. "
            f"Missing native={missing_native}; "
            f"extra native={extra_native}"
        )

    native_coords = np.array(
        [
            native_by_name[row["atom_id"]].coord
            for row in ccd_atoms
        ],
        dtype=float,
    )

    conformer = Chem.Conformer(ligand.GetNumAtoms())

    for atom_index, coord in enumerate(native_coords):
        conformer.SetAtomPosition(
            atom_index,
            Point3D(
                float(coord[0]),
                float(coord[1]),
                float(coord[2]),
            ),
        )

    ligand.RemoveAllConformers()
    ligand.AddConformer(conformer, assignId=True)

    Chem.SanitizeMol(ligand)

    return ligand, native_coords


def run_molscrub(input_sdf, output_sdf):
    """Assign one pH-7.4 state without tautomer enumeration."""

    command = [
        "scrub.py",
        str(input_sdf),
        "-o",
        str(output_sdf),
        "--ph",
        str(PH),
        "--skip_tautomers",
        "--skip_gen3d",
        "--cpu",
        "1",
    ]

    subprocess.run(
        command,
        check=True,
    )


def load_single_molscrub_state(path):
    """Require exactly one chemically valid Molscrub state."""

    molecules = [
        mol
        for mol in Chem.SDMolSupplier(
            str(path),
            removeHs=False,
        )
        if mol is not None
    ]

    if len(molecules) != 1:
        raise ValueError(
            f"Expected exactly one Molscrub state, "
            f"found {len(molecules)}."
        )

    return molecules[0]


def restore_native_coordinates(
    native_ligand,
    prepared_ligand,
):
    """Restore native heavy-atom coordinates through graph mapping."""

    native_heavy = Chem.RemoveHs(native_ligand)
    prepared_heavy = Chem.RemoveHs(prepared_ligand)

    if (
        native_heavy.GetNumAtoms()
        != prepared_heavy.GetNumAtoms()
    ):
        raise ValueError(
            "Prepared state changed heavy-atom count."
        )

    # Mapping semantics:
    # for each native atom index i,
    # match[i] is the corresponding prepared atom index.
    match = prepared_heavy.GetSubstructMatch(
        native_heavy
    )

    if len(match) != native_heavy.GetNumAtoms():
        raise ValueError(
            "Could not obtain complete native-to-prepared "
            "heavy-atom graph mapping."
        )

    native_coords = (
        native_heavy
        .GetConformer()
        .GetPositions()
    )

    restored = Chem.Mol(prepared_heavy)

    conformer = Chem.Conformer(
        restored.GetNumAtoms()
    )

    for native_index, prepared_index in enumerate(match):
        coord = native_coords[native_index]

        conformer.SetAtomPosition(
            prepared_index,
            Point3D(
                float(coord[0]),
                float(coord[1]),
                float(coord[2]),
            ),
        )

    restored.RemoveAllConformers()
    restored.AddConformer(
        conformer,
        assignId=True,
    )

    Chem.SanitizeMol(restored)

    # Generate hydrogen positions only after the experimental
    # heavy-atom geometry has been restored.
    restored_h = Chem.AddHs(
        restored,
        addCoords=True,
    )

    return restored_h, match


def audit_heavy_atom_coordinates(
    native_ligand,
    restored_ligand,
    match,
):
    """Require restored heavy atoms to reproduce native coordinates."""

    native = Chem.RemoveHs(native_ligand)
    restored = Chem.RemoveHs(restored_ligand)

    native_coords = (
        native.GetConformer().GetPositions()
    )

    restored_coords = (
        restored.GetConformer().GetPositions()
    )

    differences = np.array(
        [
            np.linalg.norm(
                native_coords[native_index]
                - restored_coords[prepared_index]
            )
            for native_index, prepared_index
            in enumerate(match)
        ]
    )

    max_difference = float(differences.max())
    mean_difference = float(differences.mean())

    if max_difference > COORD_TOLERANCE:
        raise ValueError(
            "Restored heavy atoms do not preserve "
            "native geometry: "
            f"max displacement={max_difference:.6f} A"
        )

    return max_difference, mean_difference


def get_ligand_aromatic_indices(mol):
    """Return aromatic heavy-atom indices."""

    return [
        atom.GetIdx()
        for atom in mol.GetAtoms()
        if atom.GetIsAromatic()
        and atom.GetAtomicNum() > 1
    ]


def get_ligand_polar_indices(mol):
    """Return donor/acceptor heavy atoms recognized by RDKit."""

    indices = set()

    for feature in FEATURE_FACTORY.GetFeaturesForMol(mol):
        if feature.GetFamily() not in {
            "Donor",
            "Acceptor",
        }:
            continue

        for atom_index in feature.GetAtomIds():
            if mol.GetAtomWithIdx(
                atom_index
            ).GetAtomicNum() > 1:
                indices.add(atom_index)

    return sorted(indices)


def minimum_distance(
    ligand,
    ligand_indices,
    protein_atoms,
):
    """Minimum heavy-atom distance between selected ligand/protein atoms."""

    if not ligand_indices:
        raise ValueError(
            "No eligible ligand atoms for distance audit."
        )

    if not protein_atoms:
        raise ValueError(
            "No eligible protein atoms for distance audit."
        )

    conformer = ligand.GetConformer()

    minimum = float("inf")
    minimum_pair = None

    for ligand_index in ligand_indices:
        ligand_coord = np.array(
            conformer.GetAtomPosition(
                ligand_index
            )
        )

        for protein_atom in protein_atoms:
            protein_coord = np.array(
                protein_atom.coord,
                dtype=float,
            )

            distance = float(
                np.linalg.norm(
                    ligand_coord - protein_coord
                )
            )

            if distance < minimum:
                minimum = distance
                minimum_pair = (
                    ligand_index,
                    protein_atom.get_name(),
                )

    return minimum, minimum_pair


def geometric_spot_check(
    restored_ligand,
    structure,
):
    """Verify published pocket occupancy before ProLIF."""

    phe168 = get_residue(
        structure,
        168,
    )

    asn253 = get_residue(
        structure,
        253,
    )

    # Phe168 aromatic side-chain atoms.
    phe_atoms = [
        atom
        for atom in phe168.get_atoms()
        if atom.get_name().strip()
        in {
            "CG",
            "CD1",
            "CD2",
            "CE1",
            "CE2",
            "CZ",
        }
    ]

    # Asn253 side-chain donor/acceptor atoms.
    asn_atoms = [
        atom
        for atom in asn253.get_atoms()
        if atom.get_name().strip()
        in {
            "OD1",
            "ND2",
        }
    ]

    aromatic_indices = (
        get_ligand_aromatic_indices(
            restored_ligand
        )
    )

    polar_indices = (
        get_ligand_polar_indices(
            restored_ligand
        )
    )

    phe_distance, phe_pair = minimum_distance(
        restored_ligand,
        aromatic_indices,
        phe_atoms,
    )

    asn_distance, asn_pair = minimum_distance(
        restored_ligand,
        polar_indices,
        asn_atoms,
    )

    if phe_distance > PHE168_CONTACT_MAX:
        raise ValueError(
            "Restored ligand failed Phe168 "
            "core-contact sanity check: "
            f"{phe_distance:.3f} A"
        )

    if asn_distance > ASN253_POLAR_MAX:
        raise ValueError(
            "Restored ligand failed Asn253 "
            "polar-contact sanity check: "
            f"{asn_distance:.3f} A"
        )

    return {
        "phe168_min_distance": phe_distance,
        "phe168_pair": phe_pair,
        "asn253_min_distance": asn_distance,
        "asn253_pair": asn_pair,
    }


def save_sdf(mol, path):
    writer = Chem.SDWriter(str(path))
    writer.write(mol)
    writer.close()


def prepare_control(control):
    pdb_id = control["pdb_id"]
    ligand_name = control["ligand_name"]
    ligand_code = control["ligand_code"]

    directory = ROOT / pdb_id

    pdb_path = ROOT / f"{pdb_id}.pdb"
    template_sdf = (
        directory
        / f"{ligand_code}_ideal.sdf"
    )
    ccd_cif = (
        directory
        / f"{ligand_code}.cif"
    )

    native_sdf = (
        directory
        / f"{pdb_id}_{ligand_code}_native_chemistry.sdf"
    )

    molscrub_sdf = (
        directory
        / f"{pdb_id}_{ligand_code}_molscrub_pH7.4.sdf"
    )

    restored_sdf = (
        directory
        / f"{pdb_id}_{ligand_code}_native_pH7.4_restored.sdf"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    structure, native_residue = (
        find_native_ligand(
            pdb_path,
            ligand_code,
        )
    )

    native_ligand, native_coords = (
        build_native_chemistry(
            template_sdf,
            ccd_cif,
            native_residue,
        )
    )

    native_ligand.SetProp(
        "_Name",
        f"{pdb_id}_{ligand_name}_native",
    )

    native_ligand.SetProp(
        "source_pdb",
        pdb_id,
    )

    native_ligand.SetProp(
        "source_ligand_code",
        ligand_code,
    )

    native_ligand.SetProp(
        "chemistry_provenance",
        f"RCSB CCD {ligand_code}",
    )

    native_ligand.SetProp(
        "coordinate_provenance",
        f"deposited {pdb_id}",
    )

    save_sdf(
        native_ligand,
        native_sdf,
    )

    run_molscrub(
        native_sdf,
        molscrub_sdf,
    )

    prepared = (
        load_single_molscrub_state(
            molscrub_sdf
        )
    )

    if (
        prepared.GetNumHeavyAtoms()
        != native_ligand.GetNumHeavyAtoms()
    ):
        raise ValueError(
            f"{pdb_id}: Molscrub changed "
            "heavy-atom count."
        )

    restored, match = (
        restore_native_coordinates(
            native_ligand,
            prepared,
        )
    )

    max_displacement, mean_displacement = (
        audit_heavy_atom_coordinates(
            native_ligand,
            restored,
            match,
        )
    )

    # Require a single formal chemical state.
    formal_charge = Chem.GetFormalCharge(
        restored
    )

    # Require explicit hydrogens after restoration.
    explicit_hydrogens = sum(
        1
        for atom in restored.GetAtoms()
        if atom.GetAtomicNum() == 1
    )

    if explicit_hydrogens == 0:
        raise ValueError(
            f"{pdb_id}: no explicit hydrogens "
            "after restoration."
        )

    spot = geometric_spot_check(
        restored,
        structure,
    )

    restored.SetProp(
        "preparation",
        "Molscrub pH 7.4 single-state; "
        "native heavy-atom coordinates restored; "
        "RDKit hydrogen coordinates",
    )

    save_sdf(
        restored,
        restored_sdf,
    )

    print()
    print("=" * 72)
    print(
        f"{pdb_id} — {ligand_name} "
        f"({ligand_code})"
    )
    print("=" * 72)
    print(
        "Heavy atoms:",
        restored.GetNumHeavyAtoms(),
    )
    print(
        "Explicit hydrogens:",
        explicit_hydrogens,
    )
    print(
        "Formal charge:",
        formal_charge,
    )
    print(
        "Prepared SMILES:",
        Chem.MolToSmiles(
            Chem.RemoveHs(restored),
            canonical=True,
            isomericSmiles=True,
        ),
    )
    print(
        "Max restored heavy-atom displacement:",
        f"{max_displacement:.6f} A",
    )
    print(
        "Mean restored heavy-atom displacement:",
        f"{mean_displacement:.6f} A",
    )
    print(
        "Phe168 aromatic/core minimum distance:",
        f"{spot['phe168_min_distance']:.3f} A",
        spot["phe168_pair"],
    )
    print(
        "Asn253 polar minimum distance:",
        f"{spot['asn253_min_distance']:.3f} A",
        spot["asn253_pair"],
    )
    print(
        "Output:",
        restored_sdf,
    )
    print(
        "PASS: native-reader ligand preparation "
        "and geometric spot checks passed."
    )


def main():
    for control in CONTROLS:
        prepare_control(control)


if __name__ == "__main__":
    main()
