import tempfile
from pathlib import Path

import MDAnalysis as mda
import prolif as plf
from rdkit import Chem


ROOT = Path("references/stage5/native_complexes")

NEGATIVE_RESIDUE_OFFSET = 10000

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


def get_paths(control):
    """Return validated native-reader receptor and ligand paths."""

    pdb_id = control["pdb_id"]
    ligand_code = control["ligand_code"]

    directory = ROOT / pdb_id

    protein_path = (
        directory
        / f"{pdb_id}_receptor_pH7.4_restored.pqr"
    )

    ligand_path = (
        directory
        / f"{pdb_id}_{ligand_code}_native_pH7.4_restored.sdf"
    )

    return protein_path, ligand_path


def count_pqr_atom_records(path):
    """Count ATOM/HETATM records in the validated PQR."""

    count = 0

    with path.open() as handle:
        for line in handle:
            if line.startswith(("ATOM", "HETATM")):
                count += 1

    return count


def make_mdanalysis_compatible_pqr(source_path):
    """Create a temporary parser-compatible view of a validated PQR.

    The validated restored receptor is never modified.

    Adapter-only changes:

    1. Fixed-column PDB2PQR records are rewritten as whitespace-
       delimited PQR records so MDAnalysis can parse four-digit
       residue numbers.

    2. Genuine negative deposited residue numbers are temporarily
       mapped to a reserved positive range because ProLIF stores
       residue numbers as unsigned integers.

    Normal biological numbering, including Phe168 and Asn253,
    remains unchanged.
    """

    output_lines = []
    residue_mapping = {}

    with source_path.open() as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                output_lines.append(line)
                continue

            record_type = line[0:6].strip()
            serial = line[6:11].strip()
            atom_name = line[12:16].strip()
            resname = line[17:20].strip()
            chain = line[21].strip()

            deposited_resid = int(
                line[22:26].strip()
            )

            x = line[30:38].strip()
            y = line[38:46].strip()
            z = line[46:54].strip()

            trailing_fields = line[54:].split()

            if len(trailing_fields) != 2:
                raise ValueError(
                    "Unexpected PQR charge/radius fields: "
                    f"{line.rstrip()}"
                )

            charge, radius = trailing_fields

            temporary_resid = deposited_resid

            if deposited_resid < 0:
                mapping_key = (
                    chain,
                    resname,
                    deposited_resid,
                )

                if mapping_key not in residue_mapping:
                    temporary_resid = (
                        NEGATIVE_RESIDUE_OFFSET
                        + abs(deposited_resid)
                    )

                    residue_mapping[
                        mapping_key
                    ] = temporary_resid

                else:
                    temporary_resid = (
                        residue_mapping[
                            mapping_key
                        ]
                    )

            compatible_line = (
                f"{record_type} "
                f"{serial} "
                f"{atom_name} "
                f"{resname} "
                f"{chain} "
                f"{temporary_resid} "
                f"{x} "
                f"{y} "
                f"{z} "
                f"{charge} "
                f"{radius}\n"
            )

            output_lines.append(
                compatible_line
            )

    temporary = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".pqr",
        delete=False,
    )

    temporary.writelines(
        output_lines
    )

    temporary.close()

    temporary_path = Path(
        temporary.name
    )

    results = {
        "temporary_path": temporary_path,
        "residue_mapping": residue_mapping,
    }

    return results


def get_bond_partner(atom, bond):
    """Return the atom on the opposite side of a bond."""

    atom_a, atom_b = bond.atoms

    if atom_a.index == atom.index:
        partner = atom_b
    else:
        partner = atom_a

    return partner


def remove_hh_bonds(universe):
    """Remove impossible H-H bonds from inferred protein topology."""

    hh_bonds = []

    for bond in universe.bonds:
        atom_a, atom_b = bond.atoms

        is_hh = (
            atom_a.element == "H"
            and atom_b.element == "H"
        )

        if is_hh:
            hh_bonds.append(
                (
                    atom_a.index,
                    atom_b.index,
                )
            )

    if hh_bonds:
        universe.delete_bonds(
            hh_bonds
        )

    return len(hh_bonds)


def resolve_multiple_hydrogen_parents(universe):
    """Resolve unambiguous false inter-residue H bonds.

    After geometric bond inference and H-H removal, a hydrogen may
    still have more than one candidate heavy-atom parent.

    If exactly one candidate heavy atom belongs to the hydrogen's own
    residue, that atom is retained as the covalent parent and all
    inter-residue candidate bonds are removed.

    If there is not exactly one same-residue heavy-atom candidate,
    the topology is considered ambiguous and validation stops.
    """

    bonds_to_remove = []
    resolutions = []
    ambiguous = []

    for atom in universe.atoms:
        if atom.element != "H":
            continue

        bonds = list(
            atom.bonds
        )

        heavy_candidates = []

        for bond in bonds:
            partner = get_bond_partner(
                atom,
                bond,
            )

            if partner.element != "H":
                heavy_candidates.append(
                    (
                        bond,
                        partner,
                    )
                )

        if len(heavy_candidates) <= 1:
            continue

        same_residue_candidates = [
            (
                bond,
                partner,
            )
            for bond, partner
            in heavy_candidates
            if (
                partner.resid == atom.resid
                and partner.resname == atom.resname
                and partner.segid == atom.segid
            )
        ]

        if len(same_residue_candidates) != 1:
            candidate_details = []

            for _, partner in heavy_candidates:
                candidate_detail = {
                    "index": partner.index,
                    "name": partner.name,
                    "element": partner.element,
                    "resname": partner.resname,
                    "resid": partner.resid,
                    "segid": partner.segid,
                }

                candidate_details.append(
                    candidate_detail
                )

            problem = {
                "hydrogen_index": atom.index,
                "hydrogen_name": atom.name,
                "hydrogen_resname": atom.resname,
                "hydrogen_resid": atom.resid,
                "candidates": candidate_details,
            }

            ambiguous.append(
                problem
            )

            continue

        retained_bond, retained_parent = (
            same_residue_candidates[0]
        )

        removed_partners = []

        for bond, partner in heavy_candidates:
            if bond == retained_bond:
                continue

            bonds_to_remove.append(
                (
                    atom.index,
                    partner.index,
                )
            )

            removed_partners.append(
                {
                    "index": partner.index,
                    "name": partner.name,
                    "element": partner.element,
                    "resname": partner.resname,
                    "resid": partner.resid,
                }
            )

        resolution = {
            "hydrogen_index": atom.index,
            "hydrogen_name": atom.name,
            "hydrogen_resname": atom.resname,
            "hydrogen_resid": atom.resid,
            "retained_parent": {
                "index": retained_parent.index,
                "name": retained_parent.name,
                "element": retained_parent.element,
                "resname": retained_parent.resname,
                "resid": retained_parent.resid,
            },
            "removed_partners": removed_partners,
        }

        resolutions.append(
            resolution
        )

    if ambiguous:
        raise ValueError(
            "Ambiguous multiple heavy-atom parents "
            "remain for protein hydrogens: "
            f"{ambiguous}"
        )

    if bonds_to_remove:
        universe.delete_bonds(
            bonds_to_remove
        )

    results = {
        "removed_interresidue_h_bonds":
            len(bonds_to_remove),
        "resolutions": resolutions,
    }

    return results


def validate_hydrogen_connectivity(universe):
    """Require every H to have exactly one heavy-atom parent."""

    invalid_hydrogens = []
    validated_hydrogens = 0

    for atom in universe.atoms:
        if atom.element != "H":
            continue

        bonds = list(
            atom.bonds
        )

        partners = [
            get_bond_partner(
                atom,
                bond,
            )
            for bond in bonds
        ]

        heavy_partners = [
            partner
            for partner in partners
            if partner.element != "H"
        ]

        valid = (
            len(bonds) == 1
            and len(heavy_partners) == 1
        )

        if valid:
            validated_hydrogens += 1
            continue

        partner_details = []

        for partner in partners:
            partner_detail = {
                "index": partner.index,
                "name": partner.name,
                "element": partner.element,
                "resname": partner.resname,
                "resid": partner.resid,
            }

            partner_details.append(
                partner_detail
            )

        invalid = {
            "index": atom.index,
            "name": atom.name,
            "resname": atom.resname,
            "resid": atom.resid,
            "bond_count": len(bonds),
            "heavy_parent_count": len(
                heavy_partners
            ),
            "partners": partner_details,
        }

        invalid_hydrogens.append(
            invalid
        )

    if invalid_hydrogens:
        raise ValueError(
            "Invalid hydrogen connectivity remains "
            "after protein topology cleanup: "
            f"{invalid_hydrogens}"
        )

    return validated_hydrogens


def clean_and_validate_protein_bonds(universe):
    """Clean inferred protein topology and validate all hydrogens.

    Cleanup order:

    1. Remove impossible H-H bonds.
    2. Resolve multiple heavy-atom parents only when exactly one
       same-residue heavy parent exists.
    3. Require every H to have exactly one heavy-atom parent.

    No residue-specific exceptions are used.
    """

    removed_hh_bonds = remove_hh_bonds(
        universe
    )

    parent_results = (
        resolve_multiple_hydrogen_parents(
            universe
        )
    )

    validated_hydrogens = (
        validate_hydrogen_connectivity(
            universe
        )
    )

    results = {
        "removed_hh_bonds":
            removed_hh_bonds,
        "removed_interresidue_h_bonds":
            parent_results[
                "removed_interresidue_h_bonds"
            ],
        "parent_resolutions":
            parent_results[
                "resolutions"
            ],
        "validated_hydrogens":
            validated_hydrogens,
    }

    return results


def audit_anchor_numbering(universe):
    """Require biological anchor numbering to remain unchanged."""

    expected = {
        168: "PHE",
        253: "ASN",
    }

    results = {}

    for resid, expected_resname in expected.items():
        matches = [
            residue
            for residue in universe.residues
            if residue.resid == resid
            and residue.resname == expected_resname
            and residue.segid == "A"
        ]

        if len(matches) != 1:
            raise ValueError(
                "Temporary ProLIF adapter changed or "
                "ambiguated anchor numbering: "
                f"expected exactly one "
                f"{expected_resname}{resid}.A, "
                f"found {len(matches)}."
            )

        results[resid] = (
            expected_resname
        )

    return results


def load_protein(path):
    """Load a validated restored receptor into ProLIF."""

    expected_atoms = count_pqr_atom_records(
        path
    )

    adapter_results = (
        make_mdanalysis_compatible_pqr(
            path
        )
    )

    temporary_path = adapter_results[
        "temporary_path"
    ]

    residue_mapping = adapter_results[
        "residue_mapping"
    ]

    protein = None
    topology_audit = None
    anchor_audit = None

    try:
        universe = mda.Universe(
            str(temporary_path)
        )

        if universe.atoms.n_atoms != expected_atoms:
            raise ValueError(
                "MDAnalysis-compatible PQR changed "
                "atom count: "
                f"expected {expected_atoms}, "
                f"parsed {universe.atoms.n_atoms}."
            )

        anchor_audit = audit_anchor_numbering(
            universe
        )

        universe.guess_TopologyAttrs(
            to_guess=[
                "elements",
                "bonds",
            ]
        )

        topology_audit = (
            clean_and_validate_protein_bonds(
                universe
            )
        )

        universe.add_TopologyAttr(
            "chainIDs",
            universe.atoms.segids.copy(),
        )

        protein = plf.Molecule.from_mda(
            universe
        )

        if protein.GetNumAtoms() != expected_atoms:
            raise ValueError(
                "ProLIF protein atom count differs "
                "from the validated receptor artifact: "
                f"expected {expected_atoms}, "
                f"got {protein.GetNumAtoms()}."
            )

    finally:
        temporary_path.unlink(
            missing_ok=True
        )

    if protein is None:
        raise ValueError(
            f"Failed to construct ProLIF protein "
            f"from {path}."
        )

    results = {
        "protein": protein,
        "expected_atoms": expected_atoms,
        "removed_hh_bonds":
            topology_audit[
                "removed_hh_bonds"
            ],
        "removed_interresidue_h_bonds":
            topology_audit[
                "removed_interresidue_h_bonds"
            ],
        "parent_resolutions":
            topology_audit[
                "parent_resolutions"
            ],
        "validated_hydrogens":
            topology_audit[
                "validated_hydrogens"
            ],
        "residue_mapping":
            residue_mapping,
        "anchor_audit":
            anchor_audit,
    }

    return results


def load_ligand(path):
    """Load a restored native experimental ligand pose."""

    ligand_rdkit = Chem.SDMolSupplier(
        str(path),
        removeHs=False,
    )[0]

    if ligand_rdkit is None:
        raise ValueError(
            f"Failed to load ligand: {path}"
        )

    ligand = plf.Molecule.from_rdkit(
        ligand_rdkit
    )

    return ligand


def run_interaction_reader(
    protein,
    ligand,
):
    """Run the frozen default ProLIF interaction reader."""

    fingerprint = plf.Fingerprint()

    interactions = fingerprint.generate(
        ligand,
        protein,
        metadata=True,
    )

    return interactions


def find_anchor_interactions(
    interactions,
    residue_name,
    residue_number,
):
    """Return interactions for one chain-A anchor residue."""

    matches = []

    for pair, residue_interactions in interactions.items():
        _, protein_residue = pair

        is_anchor = (
            protein_residue.name
            == residue_name
            and protein_residue.number
            == residue_number
            and protein_residue.chain
            == "A"
        )

        if is_anchor:
            matches.append(
                residue_interactions
            )

    return matches


def interaction_names(matches):
    """Return all interaction classes detected for an anchor."""

    names = set()

    for residue_interactions in matches:
        names.update(
            residue_interactions.keys()
        )

    return names


def print_anchor(
    label,
    matches,
):
    """Print all interactions detected for one anchor."""

    print()
    print(label)

    if not matches:
        print("  NOT DETECTED")
        return

    for residue_interactions in matches:
        for interaction_name, metadata in (
            residue_interactions.items()
        ):
            print(
                f"  {interaction_name}: "
                f"{metadata}"
            )


def print_residue_mapping(mapping):
    """Print temporary negative-residue mappings."""

    if not mapping:
        print(
            "Temporary negative-residue mappings: none"
        )
        return

    print(
        "Temporary negative-residue mappings:"
    )

    for key, temporary_resid in sorted(
        mapping.items()
    ):
        chain, resname, deposited_resid = key

        print(
            f"  {resname} {chain} "
            f"{deposited_resid} "
            f"-> {temporary_resid}"
        )


def print_parent_resolutions(resolutions):
    """Print any false inter-residue H bonds removed."""

    if not resolutions:
        print(
            "Hydrogen parent resolutions: none"
        )
        return

    print(
        "Hydrogen parent resolutions:"
    )

    for resolution in resolutions:
        retained = resolution[
            "retained_parent"
        ]

        print(
            f"  {resolution['hydrogen_name']} "
            f"{resolution['hydrogen_resname']}"
            f"{resolution['hydrogen_resid']} "
            f"-> retained "
            f"{retained['name']} "
            f"{retained['resname']}"
            f"{retained['resid']}"
        )

        for removed in resolution[
            "removed_partners"
        ]:
            print(
                "    removed inferred bond to "
                f"{removed['name']} "
                f"{removed['resname']}"
                f"{removed['resid']}"
            )


def validate_control(control):
    """Run reader proof of life for one native experimental complex."""

    pdb_id = control["pdb_id"]
    ligand_name = control["ligand_name"]

    protein_path, ligand_path = (
        get_paths(
            control
        )
    )

    protein_results = load_protein(
        protein_path
    )

    protein = protein_results[
        "protein"
    ]

    ligand = load_ligand(
        ligand_path
    )

    interactions = run_interaction_reader(
        protein,
        ligand,
    )

    phe168 = find_anchor_interactions(
        interactions,
        "PHE",
        168,
    )

    asn253 = find_anchor_interactions(
        interactions,
        "ASN",
        253,
    )

    phe_names = interaction_names(
        phe168
    )

    asn_names = interaction_names(
        asn253
    )

    phe_recovered = bool(
        phe168
    )

    asn_recovered = bool(
        asn253
    )

    reader_pass = (
        phe_recovered
        and asn_recovered
    )

    print()
    print("=" * 72)
    print(
        f"{pdb_id} — {ligand_name}"
    )
    print("=" * 72)

    print(
        "Protein:",
        protein_path,
    )

    print(
        "Ligand:",
        ligand_path,
    )

    print(
        "Protein atoms:",
        protein.GetNumAtoms(),
    )

    print(
        "Protein residues:",
        len(protein.residues),
    )

    print(
        "Ligand atoms:",
        ligand.GetNumAtoms(),
    )

    print_residue_mapping(
        protein_results[
            "residue_mapping"
        ]
    )

    print(
        "Anchor numbering audit:",
        protein_results[
            "anchor_audit"
        ],
    )

    print(
        "Inferred H-H bonds removed:",
        protein_results[
            "removed_hh_bonds"
        ],
    )

    print(
        "False inter-residue H bonds removed:",
        protein_results[
            "removed_interresidue_h_bonds"
        ],
    )

    print(
        "Hydrogens with validated "
        "single-heavy-atom parent:",
        protein_results[
            "validated_hydrogens"
        ],
    )

    print_parent_resolutions(
        protein_results[
            "parent_resolutions"
        ]
    )

    print_anchor(
        "Phe168 interactions:",
        phe168,
    )

    print_anchor(
        "Asn253 interactions:",
        asn253,
    )

    print()
    print(
        "Phe168 interaction classes:",
        sorted(phe_names),
    )

    print(
        "Asn253 interaction classes:",
        sorted(asn_names),
    )

    print(
        "Phe168 recovered:",
        phe_recovered,
    )

    print(
        "Asn253 recovered:",
        asn_recovered,
    )

    print(
        "Reader pass:",
        reader_pass,
    )

    if not reader_pass:
        raise AssertionError(
            f"{pdb_id}/{ligand_name}: "
            "native ProLIF reader failed "
            "predeclared anchor recovery."
        )

    results = {
        "pdb_id": pdb_id,
        "ligand_name": ligand_name,
        "phe168_recovered":
            phe_recovered,
        "asn253_recovered":
            asn_recovered,
        "phe168_interactions":
            sorted(phe_names),
        "asn253_interactions":
            sorted(asn_names),
        "removed_hh_bonds":
            protein_results[
                "removed_hh_bonds"
            ],
        "removed_interresidue_h_bonds":
            protein_results[
                "removed_interresidue_h_bonds"
            ],
        "residue_mapping":
            protein_results[
                "residue_mapping"
            ],
        "reader_pass":
            reader_pass,
    }

    return results


def main():
    results = []

    for control in CONTROLS:
        result = validate_control(
            control
        )

        results.append(
            result
        )

    passed = sum(
        result["reader_pass"]
        for result in results
    )

    total = len(results)

    print()
    print("=" * 72)
    print(
        "NATIVE READER PROOF OF LIFE"
    )
    print("=" * 72)

    for result in results:
        status = (
            "PASS"
            if result["reader_pass"]
            else "FAIL"
        )

        print(
            f"{result['pdb_id']} / "
            f"{result['ligand_name']}: "
            f"{status}"
        )

        print(
            "  Phe168:",
            result[
                "phe168_interactions"
            ],
        )

        print(
            "  Asn253:",
            result[
                "asn253_interactions"
            ],
        )

        print(
            "  H-H bonds removed:",
            result[
                "removed_hh_bonds"
            ],
        )

        print(
            "  False inter-residue H bonds removed:",
            result[
                "removed_interresidue_h_bonds"
            ],
        )

        if result["residue_mapping"]:
            print(
                "  Temporary residue mapping:",
                result[
                    "residue_mapping"
                ],
            )

    print()
    print(
        f"Reader controls passed: "
        f"{passed}/{total}"
    )

    if passed != total:
        raise AssertionError(
            "Native interaction-reader proof of life "
            f"failed: {passed}/{total} controls passed."
        )

    print(
        "PASS: ProLIF recovered both predeclared "
        "A2A anchor residues in all native controls."
    )


if __name__ == "__main__":
    main()
