from pathlib import Path
import json

import MDAnalysis as mda
import numpy as np
from rdkit import Chem
from scipy.spatial.transform import Rotation

from test_native_reader_controls import (
    find_anchor_interactions,
    load_ligand,
    load_protein,
    make_mdanalysis_compatible_pqr,
    run_interaction_reader,
)


def load_native_complex(
    receptor_path: Path,
    ligand_path: Path,
) -> tuple:
    """Load validated native structures and coordinate representations."""

    protein_results = load_protein(
        receptor_path
    )

    protein = protein_results[
        "protein"
    ]

    ligand = load_ligand(
        ligand_path
    )

    receptor_adapter = (
        make_mdanalysis_compatible_pqr(
            receptor_path
        )
    )

    temporary_path = receptor_adapter[
        "temporary_path"
    ]

    try:
        receptor_universe = mda.Universe(
            str(temporary_path)
        )

        receptor_coordinates = (
            receptor_universe.atoms.positions
            .astype(float)
            .copy()
        )
    finally:
        temporary_path.unlink(
            missing_ok=True
        )

    ligand_rdkit = Chem.SDMolSupplier(
        str(ligand_path),
        removeHs=False,
    )[0]

    if ligand_rdkit is None:
        raise ValueError(
            f"Failed to load ligand: {ligand_path}"
        )

    if ligand_rdkit.GetNumConformers() == 0:
        raise ValueError(
            f"Ligand has no 3D conformer: {ligand_path}"
        )

    ligand_coordinates = np.asarray(
        ligand_rdkit.GetConformer().GetPositions(),
        dtype=float,
    ).copy()

    if not np.isfinite(
        receptor_coordinates
    ).all():
        raise ValueError(
            "Native receptor contains "
            "non-finite coordinates."
        )

    if not np.isfinite(
        ligand_coordinates
    ).all():
        raise ValueError(
            "Native ligand contains "
            "non-finite coordinates."
        )

    if (
        ligand_coordinates.shape[0]
        != ligand_rdkit.GetNumAtoms()
    ):
        raise ValueError(
            "Ligand coordinate count does not "
            "match ligand atom count."
        )

    return (
        protein,
        ligand,
        receptor_coordinates,
        ligand_coordinates,
        ligand_rdkit,
    )


def get_anchor_geometry(
    interactions: dict,
) -> dict:
    """Extract native Phe168 and Asn253 interaction geometry."""

    anchors = {
        "phe168": find_anchor_interactions(
            interactions,
            "PHE",
            168,
        ),
        "asn253": find_anchor_interactions(
            interactions,
            "ASN",
            253,
        ),
    }

    geometry = {}

    for anchor_name, matches in (
        anchors.items()
    ):
        if not matches:
            raise ValueError(
                f"No validated native interactions "
                f"found for {anchor_name}."
            )

        geometry[anchor_name] = {}

        for residue_interactions in matches:
            for interaction_name, metadata_records in (
                residue_interactions.items()
            ):
                geometry[
                    anchor_name
                ].setdefault(
                    interaction_name,
                    [],
                )

                for metadata in metadata_records:
                    record = {
                        "ligand_indices": tuple(
                            metadata[
                                "parent_indices"
                            ][
                                "ligand"
                            ]
                        ),
                        "protein_indices": tuple(
                            metadata[
                                "parent_indices"
                            ][
                                "protein"
                            ]
                        ),
                        "distance": float(
                            metadata[
                                "distance"
                            ]
                        ),
                    }

                    if "DHA_angle" in metadata:
                        record[
                            "DHA_angle"
                        ] = float(
                            metadata[
                                "DHA_angle"
                            ]
                        )

                    if "plane_angle" in metadata:
                        record[
                            "plane_angle"
                        ] = float(
                            metadata[
                                "plane_angle"
                            ]
                        )

                    if (
                        "normal_to_centroid_angle"
                        in metadata
                    ):
                        record[
                            "normal_to_centroid_angle"
                        ] = float(
                            metadata[
                                "normal_to_centroid_angle"
                            ]
                        )

                    geometry[
                        anchor_name
                    ][
                        interaction_name
                    ].append(
                        record
                    )

    return geometry


def get_principal_axes(
    coordinates: np.ndarray,
) -> np.ndarray:
    """Return the ligand's three principal geometric axes."""

    center = coordinates.mean(
        axis=0
    )

    centered = (
        coordinates - center
    )

    covariance = np.cov(
        centered,
        rowvar=False,
    )

    eigenvalues, eigenvectors = (
        np.linalg.eigh(
            covariance
        )
    )

    order = np.argsort(
        eigenvalues
    )[::-1]

    principal_axes = (
        eigenvectors[:, order].T
    )

    return principal_axes


def rotate_ligand(
    coordinates: np.ndarray,
    axis: np.ndarray,
    angle_degrees: float,
) -> np.ndarray:
    """Rigidly rotate ligand coordinates around their centroid."""

    center = coordinates.mean(
        axis=0
    )

    centered = (
        coordinates - center
    )

    axis_norm = np.linalg.norm(
        axis
    )

    if axis_norm == 0:
        raise ValueError(
            "Rotation axis cannot have "
            "zero length."
        )

    unit_axis = (
        axis / axis_norm
    )

    angle_radians = np.deg2rad(
        angle_degrees
    )

    rotation_vector = (
        unit_axis * angle_radians
    )

    rotation = Rotation.from_rotvec(
        rotation_vector
    )

    rotated_centered = (
        rotation.apply(
            centered
        )
    )

    rotated = (
        rotated_centered + center
    )

    return rotated


def measure_pose_geometry(
    native_coordinates: np.ndarray,
    rotated_coordinates: np.ndarray,
    receptor_coordinates: np.ndarray,
    anchor_geometry: dict,
) -> dict:
    """Measure structural changes caused by a rigid ligand rotation."""

    native_center = (
        native_coordinates.mean(
            axis=0
        )
    )

    rotated_center = (
        rotated_coordinates.mean(
            axis=0
        )
    )

    centroid_displacement = (
        np.linalg.norm(
            rotated_center
            - native_center
        )
    )

    native_distances = np.linalg.norm(
        native_coordinates[
            :, None, :
        ]
        - native_coordinates[
            None, :, :
        ],
        axis=2,
    )

    rotated_distances = np.linalg.norm(
        rotated_coordinates[
            :, None, :
        ]
        - rotated_coordinates[
            None, :, :
        ],
        axis=2,
    )

    max_internal_distance_change = (
        np.max(
            np.abs(
                native_distances
                - rotated_distances
            )
        )
    )

    protein_distances = np.linalg.norm(
        rotated_coordinates[
            :, None, :
        ]
        - receptor_coordinates[
            None, :, :
        ],
        axis=2,
    )

    minimum_protein_distance = (
        np.min(
            protein_distances
        )
    )

    anchor_measurements = {}

    for anchor_name, interactions in (
        anchor_geometry.items()
    ):
        anchor_measurements[
            anchor_name
        ] = {}

        for interaction_name, records in (
            interactions.items()
        ):
            measurements = []

            for record in records:
                ligand_indices = (
                    record[
                        "ligand_indices"
                    ]
                )

                protein_indices = (
                    record[
                        "protein_indices"
                    ]
                )

                ligand_coords = (
                    rotated_coordinates[
                        list(
                            ligand_indices
                        )
                    ]
                )

                protein_coords = (
                    receptor_coordinates[
                        list(
                            protein_indices
                        )
                    ]
                )

                distances = np.linalg.norm(
                    ligand_coords[
                        :, None, :
                    ]
                    - protein_coords[
                        None, :, :
                    ],
                    axis=2,
                )

                measurements.append(
                    {
                        "minimum_distance": float(
                            np.min(
                                distances
                            )
                        )
                    }
                )

            anchor_measurements[
                anchor_name
            ][
                interaction_name
            ] = measurements

    pose_geometry = {
        "centroid_displacement": float(
            centroid_displacement
        ),
        "max_internal_distance_change": float(
            max_internal_distance_change
        ),
        "minimum_protein_distance": float(
            minimum_protein_distance
        ),
        "anchor_measurements": anchor_measurements,
    }

    return pose_geometry


def analyze_complex(
    pdb_id: str,
    receptor_coordinates: np.ndarray,
    ligand_coordinates: np.ndarray,
    anchor_geometry: dict,
    angles: list[float],
) -> list[dict]:
    """Analyze the predefined rotation grid for one native complex."""

    principal_axes = (
        get_principal_axes(
            ligand_coordinates
        )
    )

    results = []

    for axis_index, axis in enumerate(
        principal_axes,
        start=1,
    ):
        for angle in angles:
            rotated_coordinates = (
                rotate_ligand(
                    ligand_coordinates,
                    axis,
                    angle,
                )
            )

            pose_geometry = (
                measure_pose_geometry(
                    ligand_coordinates,
                    rotated_coordinates,
                    receptor_coordinates,
                    anchor_geometry,
                )
            )

            perturbation_result = {
                "pdb_id": pdb_id,
                "axis": axis_index,
                "angle_degrees": angle,
                **pose_geometry,
            }

            results.append(
                perturbation_result
            )

    return results


def write_perturbed_pose(
    ligand_rdkit: Chem.Mol,
    coordinates: np.ndarray,
    output_path: Path,
    pdb_id: str,
    axis: int,
    angle_degrees: float,
) -> None:
    """Write one rigidly perturbed ligand pose as an SDF."""

    molecule = Chem.Mol(
        ligand_rdkit
    )

    conformer = (
        molecule.GetConformer()
    )

    if coordinates.shape != (
        molecule.GetNumAtoms(),
        3,
    ):
        raise ValueError(
            "Perturbed coordinate count does not "
            "match ligand atom count."
        )

    for atom_index, position in enumerate(
        coordinates
    ):
        conformer.SetAtomPosition(
            atom_index,
            (
                float(position[0]),
                float(position[1]),
                float(position[2]),
            ),
        )

    molecule.SetProp(
        "control_type",
        "stage5_rotation_candidate",
    )

    molecule.SetProp(
        "source_pdb",
        pdb_id,
    )

    molecule.SetProp(
        "rotation_axis",
        str(axis),
    )

    molecule.SetProp(
        "rotation_angle_degrees",
        str(angle_degrees),
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    writer = Chem.SDWriter(
        str(output_path)
    )

    if writer is None:
        raise OSError(
            f"Could not create SDF writer: {output_path}"
        )

    writer.write(
        molecule
    )

    writer.close()


def write_results(
    results: list[dict],
    output_path: Path,
) -> None:
    """Write structural perturbation results to JSON."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            results,
            handle,
            indent=2,
        )


def main() -> list[dict]:
    """Run structural perturbation analysis for all native A2A controls."""

    angles = [
        10.0,
        20.0,
        30.0,
        45.0,
    ]

    controls = [
        {
            "pdb_id": "3REY",
            "receptor_path": Path(
                "references/stage5/native_complexes/3REY/"
                "3REY_receptor_pH7.4_restored.pqr"
            ),
            "ligand_path": Path(
                "references/stage5/native_complexes/3REY/"
                "3REY_XAC_native_pH7.4_restored.sdf"
            ),
        },
        {
            "pdb_id": "5OLH",
            "receptor_path": Path(
                "references/stage5/native_complexes/5OLH/"
                "5OLH_receptor_pH7.4_restored.pqr"
            ),
            "ligand_path": Path(
                "references/stage5/native_complexes/5OLH/"
                "5OLH_9XT_native_pH7.4_restored.sdf"
            ),
        },
        {
            "pdb_id": "5OLO",
            "receptor_path": Path(
                "references/stage5/native_complexes/5OLO/"
                "5OLO_receptor_pH7.4_restored.pqr"
            ),
            "ligand_path": Path(
                "references/stage5/native_complexes/5OLO/"
                "5OLO_9XW_native_pH7.4_restored.sdf"
            ),
        },
    ]

    results = []

    for control in controls:
        (
            protein,
            ligand,
            receptor_coordinates,
            ligand_coordinates,
            ligand_rdkit,
        ) = load_native_complex(
            control[
                "receptor_path"
            ],
            control[
                "ligand_path"
            ],
        )

        interactions = (
            run_interaction_reader(
                protein,
                ligand,
            )
        )

        anchor_geometry = (
            get_anchor_geometry(
                interactions
            )
        )

        complex_results = (
            analyze_complex(
                control["pdb_id"],
                receptor_coordinates,
                ligand_coordinates,
                anchor_geometry,
                angles,
            )
        )

        results.extend(
            complex_results
        )

        principal_axes = (
            get_principal_axes(
                ligand_coordinates
            )
        )

        for axis_index, axis in enumerate(
            principal_axes,
            start=1,
        ):
            for candidate_angle in [
                10.0,
                15.0,
                20.0,
            ]:
                rotated_coordinates = rotate_ligand(
                    ligand_coordinates,
                    axis,
                    candidate_angle,
                )

                output_path = Path(
                    "references/stage5/fallback/"
                    "stage3b_candidates/"
                    f"{control['pdb_id']}_"
                    f"axis{axis_index}_"
                    f"{int(candidate_angle)}deg.sdf"
                )

                write_perturbed_pose(
                    ligand_rdkit,
                    rotated_coordinates,
                    output_path,
                    control["pdb_id"],
                    axis_index,
                    candidate_angle,
                )

    output_path = Path(
        "references/stage5/fallback/"
        "native_pose_perturbation_analysis.json"
    )

    write_results(
        results,
        output_path,
    )

    print(
        f"Wrote {len(results)} perturbation results "
        f"to {output_path}"
    )

    print(
        "Wrote 9 Stage-3B candidate SDFs to "
        "references/stage5/fallback/stage3b_candidates/"
    )

    return results


if __name__ == "__main__":
    main()
