from pathlib import Path
import json

from evaluation.d017_visualization import (
    build_pocket_selections,
    render_pocket_focused_pml,
    write_pocket_focused_pml,
    write_whole_structure_review_pml,
)


ROOT = Path("references/stage5/d017")
RUN = ROOT / "calibration_runs/P1/post_emitter_fix"


def build_whole_protein_pocket_pml(
    *,
    canonical_pml: Path,
    output_pml: Path,
    output_png: Path,
    ligand_source: Path,
    homolog_selection: str,
    target_selection: str,
) -> None:
    """Add frozen ligand/pocket highlights to the canonical whole-structure PML."""

    canonical_text = canonical_pml.read_text()

    zoom_marker = "zoom polymer and ((structure1 and chain A) or (structure2 and chain R)), 8\n"

    if canonical_text.count(zoom_marker) != 1:
        raise RuntimeError(
            "Expected exactly one canonical zoom marker in whole-structure PML"
        )

    highlights = "\n".join(
        [
            f"load {ligand_source}, ligand_source",
            "remove ligand_source and not (chain R and resn ADN and resi 400)",
            "",
            f"select homolog_pocket, structure2 and ({homolog_selection})",
            f"select target_pocket, structure1 and ({target_selection})",
            "select ligand, ligand_source and chain R and resn ADN and resi 400",
            "",
            "show sticks, homolog_pocket",
            "show sticks, target_pocket",
            "show sticks, ligand",
            "",
            "color orange, homolog_pocket",
            "color cyan, target_pocket",
            "color yellow, ligand",
            "",
        ]
    ) + "\n"

    highlighted_pml = canonical_text.replace(
        zoom_marker,
        highlights + zoom_marker,
        1,
    )

    lines = highlighted_pml.splitlines(True)

    png_indices = [
        index
        for index, line in enumerate(lines)
        if line.startswith("png ")
    ]

    if len(png_indices) != 1:
        raise RuntimeError(
            "Expected exactly one PNG output line in canonical whole-structure PML"
        )

    lines[png_indices[0]] = f"png {output_png}, dpi=300\n"

    output_pml.write_text("".join(lines))


def main() -> None:
    measurement_path = RUN / "pocket_measurement.json"

    with measurement_path.open() as handle:
        artifact = json.load(handle)

    measurement = artifact["measurement"]

    homolog_selection, target_selection = build_pocket_selections(
        homolog_pocket_residues=measurement["pocket_residues"],
        mapped_pocket_residues=measurement["mapped_pocket_residues"],
    )

    pocket_pml = RUN / "pocket_review.pml"
    pocket_png = RUN / "pocket_review.png"

    write_pocket_focused_pml(
        superposition_cif=RUN / "usalign_superposition.cif",
        homolog_structure_cif=ROOT / "receptor_inputs/6D9H_R.cif",
        ligand_source_cif=ROOT / "structures/raw/6D9H.cif",
        homolog_chain=artifact["homolog"]["chain"],
        target_chain=artifact["target"]["chain"],
        homolog_selection=homolog_selection,
        target_selection=target_selection,
        output_png=pocket_png,
        output_pml=pocket_pml,
    )

    render_pocket_focused_pml(
        pml_path=pocket_pml,
    )

    whole_pml = RUN / "whole_structure_review.pml"
    whole_png = RUN / "whole_structure_review.png"

    write_whole_structure_review_pml(
        superposition_cif=RUN / "usalign_superposition.cif",
        homolog_structure_cif=ROOT / "receptor_inputs/6D9H_R.cif",
        output_png=whole_png,
        output_pml=whole_pml,
    )

    render_pocket_focused_pml(
        pml_path=whole_pml,
    )

    whole_protein_pml = RUN / "whole_protein_pocket_review.pml"
    whole_protein_png = RUN / "whole_protein_pocket_review.png"

    build_whole_protein_pocket_pml(
        canonical_pml=whole_pml,
        output_pml=whole_protein_pml,
        output_png=whole_protein_png,
        ligand_source=ROOT / "structures/raw/6D9H.cif",
        homolog_selection=homolog_selection,
        target_selection=target_selection,
    )

    render_pocket_focused_pml(
        pml_path=whole_protein_pml,
    )

    print("wrote:", pocket_pml)
    print("wrote:", whole_pml)
    print("wrote:", whole_protein_pml)
    print("rendered:", pocket_png)
    print("rendered:", whole_png)
    print("rendered:", whole_protein_png)


if __name__ == "__main__":
    main()
