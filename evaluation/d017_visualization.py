"""D017 human-review visualization of an existing US-align superposition."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile


def write_whole_structure_pml(
    *,
    superposition_cif: Path,
    reference_cif: Path,
    superposition_chain: str,
    reference_chain: str,
    output_png: Path,
    output_pml: Path,
    ray_size: int = 1800,
) -> None:
    """Write a review-only PyMOL script for an existing US-align superposition."""

    if ray_size <= 0:
        raise ValueError("ray_size must be positive")

    output_pml.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    pml = f"""reinitialize
load {superposition_cif}, structure1
load {reference_cif}, structure2

remove structure1 and not chain {superposition_chain}
remove structure2 and not chain {reference_chain}

hide everything
show cartoon, structure1
show cartoon, structure2
set cartoon_oval_width, 0.20
set cartoon_oval_length, 0.80
set cartoon_rect_width, 0.20
set cartoon_rect_length, 0.80
set cartoon_loop_radius, 0.12

color blue, structure1
color red, structure2

set cartoon_transparency, 0.55, structure1
set cartoon_transparency, 0.20, structure2

bg_color white
set ray_shadow, 0
set depth_cue, 0

orient structure1 or structure2
zoom structure1 or structure2, 5

ray {ray_size}, {ray_size}
png {output_png}, dpi=300
quit
"""

    output_pml.write_text(pml)


def render_whole_structure(
    *,
    superposition_cif: Path,
    reference_cif: Path,
    superposition_chain: str,
    reference_chain: str,
    output_png: Path,
    output_pml: Path,
) -> None:
    """Render a whole-structure D017 review image with PyMOL 3.1.0."""

    write_whole_structure_pml(
        superposition_cif=superposition_cif,
        reference_cif=reference_cif,
        superposition_chain=superposition_chain,
        reference_chain=reference_chain,
        output_png=output_png,
        output_pml=output_pml,
    )

    subprocess.run(
        ["pymol", "-cq", str(output_pml)],
        check=True,
    )


__all__ = [
    "render_whole_structure",
    "write_whole_structure_pml",
]


def build_pocket_selections(
    *,
    homolog_pocket_residues: tuple[dict[str, object], ...],
    mapped_pocket_residues: tuple[dict[str, object], ...],
) -> tuple[str, str]:
    """Build PyMOL residue selections for the homolog pocket and mapped target."""

    homolog_selection = " or ".join(
        (
            f"(chain {residue['chain']} and "
            f"resi {residue['number']} and "
            f"resn {residue['name']})"
        )
        for residue in homolog_pocket_residues
    )

    mapped_target_residues = tuple(
        record["target_residue"]
        for record in mapped_pocket_residues
        if record["target_residue"] is not None
    )

    target_selection = " or ".join(
        (
            f"(chain {residue['chain']} and "
            f"resi {residue['number']} and "
            f"resn {residue['name']})"
        )
        for residue in mapped_target_residues
    )

    if not homolog_selection:
        raise ValueError("Cannot build an empty homolog-pocket selection")

    if not target_selection:
        raise ValueError("Cannot build an empty mapped-target selection")

    return homolog_selection, target_selection


def write_pocket_focused_pml(
    *,
    superposition_cif: Path,
    homolog_structure_cif: Path,
    ligand_source_cif: Path,
    homolog_chain: str,
    target_chain: str,
    homolog_selection: str,
    target_selection: str,
    output_png: Path,
    output_pml: Path,
) -> None:
    """Write a review-only PyMOL script for the mapped D017 pocket."""

    output_pml.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    pml = f"""reinitialize

load {superposition_cif}, structure1
load {homolog_structure_cif}, structure2
load {ligand_source_cif}, ligand_source

hide everything
set all_states, off

remove structure1 and not chain {target_chain}
remove structure2 and not chain {homolog_chain}
remove ligand_source and not (chain {homolog_chain} and resn ADN and resi 400)

show cartoon, structure1 and chain {target_chain}
show cartoon, structure2 and chain {homolog_chain}

color blue, structure1 and chain {target_chain}
color red, structure2 and chain {homolog_chain}

set cartoon_transparency, 0.55, structure1 and chain {target_chain}
set cartoon_transparency, 0.20, structure2 and chain {homolog_chain}

select homolog_pocket, structure2 and ({homolog_selection})
select target_pocket, structure1 and ({target_selection})
select ligand, ligand_source and chain {homolog_chain} and resn ADN and resi 400

show sticks, homolog_pocket
show sticks, target_pocket
show sticks, ligand

color orange, homolog_pocket
color cyan, target_pocket
color yellow, ligand

bg_color white
set ray_shadow, 0
set depth_cue, 0

zoom ligand or homolog_pocket or target_pocket, 8

ray 1800, 1800
png {output_png}, dpi=300

quit
"""

    output_pml.write_text(pml)


def render_pocket_focused_pml(
    *,
    pml_path: Path,
) -> None:
    """Render a prepared D017 pocket-review PML with PyMOL."""

    subprocess.run(
        ["pymol", "-cq", str(pml_path)],
        check=True,
    )


def write_whole_structure_review_pml(
    *,
    superposition_cif: Path,
    homolog_structure_cif: Path,
    output_png: Path,
    output_pml: Path,
) -> None:
    """Write a review-only PyMOL script for the whole D017 superposition."""

    output_pml.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    pml = f"""reinitialize

load {superposition_cif}, structure1
load {homolog_structure_cif}, structure2

hide everything
set all_states, off

remove structure1 and not chain A
remove structure2 and not chain R

show cartoon, structure1 and chain A
show cartoon, structure2 and chain R

color blue, structure1 and chain A
color red, structure2 and chain R

set cartoon_transparency, 0.55, structure1 and chain A
set cartoon_transparency, 0.20, structure2 and chain R

bg_color white
set ray_shadow, 0
set depth_cue, 0

zoom polymer and ((structure1 and chain A) or (structure2 and chain R)), 8

ray 1800, 1800
png {output_png}, dpi=300

quit
"""

    output_pml.write_text(pml)
def write_whole_protein_pocket_review_pml(
    *,
    superposition_cif: Path,
    homolog_structure_cif: Path,
    ligand_source_cif: Path,
    homolog_chain: str,
    target_chain: str,
    homolog_selection: str,
    target_selection: str,
    output_png: Path,
    output_pml: Path,
) -> None:
    """Write a whole-protein review view with ligand and pocket highlights."""

    output_pml.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    pml = f"""reinitialize

load {superposition_cif}, structure1
load {homolog_structure_cif}, structure2
load {ligand_source_cif}, ligand_source

hide everything
set all_states, off

remove structure1 and not chain {target_chain}
remove structure2 and not chain {homolog_chain}
remove ligand_source and not (
    chain {homolog_chain} and resn ADN and resi 400
)

show cartoon, structure1 and chain {target_chain}
show cartoon, structure2 and chain {homolog_chain}
    color blue, structure1 and chain {target_chain}
    color red, structure2 and chain {homolog_chain}
set cartoon_transparency, 0.55, structure1 and chain {target_chain}
set cartoon_transparency, 0.20, structure2 and chain {homolog_chain}

bg_color white
set ray_shadow, 0
set depth_cue, 0

zoom polymer and ((structure1 and chain {target_chain}) or (structure2 and chain {homolog_chain})), 8

select homolog_pocket, structure2 and ({homolog_selection})
select target_pocket, structure1 and ({target_selection})
select ligand, ligand_source and chain {homolog_chain} and resn ADN and resi 400

show sticks, homolog_pocket
show sticks, target_pocket
show sticks, ligand

color orange, homolog_pocket
color cyan, target_pocket
color yellow, ligand

ray 1800, 1800
png {output_png}, dpi=300

quit
"""

    output_pml.write_text(pml)
