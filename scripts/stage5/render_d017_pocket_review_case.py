#!/usr/bin/env python3

from pathlib import Path
import argparse
import json

from evaluation.d017_visualization import (
    build_pocket_selections,
    render_pocket_focused_pml,
    write_pocket_focused_pml,
    write_whole_structure_review_pml,
)

ROOT = Path("references/stage5/d017")


def load_manifest_row(row_id):
    with (ROOT / "calibration_structure_manifest.json").open() as handle:
        manifest = json.load(handle)

    for row in manifest["rows"]:
        if row["row_id"] == row_id:
            return row

    raise KeyError(f"Calibration row not found: {row_id}")


def patch_ligand_selection(pml_path, ligand_component, ligand_residue):
    text = pml_path.read_text()

    old = "resn ADN and resi 400"
    new = f"resn {ligand_component} and resi {ligand_residue}"

    if old not in text:
        raise RuntimeError(
            f"Expected P1 ligand selector not found in {pml_path}"
        )

    pml_path.write_text(text.replace(old, new))


def patch_structure_chains(pml_path, target_chain, homolog_chain):
    text = pml_path.read_text()

    text = text.replace(
        "chain A",
        f"chain {target_chain}",
    )
    text = text.replace(
        "chain R",
        f"chain {homolog_chain}",
    )

    pml_path.write_text(text)


def build_whole_protein_pocket_pml(
    *,
    canonical_pml,
    output_pml,
    output_png,
    ligand_source,
    homolog_selection,
    target_selection,
    target_chain,
    homolog_chain,
    ligand_component,
    ligand_residue,
):
    canonical_text = canonical_pml.read_text()

    highlights = "\n".join(
        [
            f"load {ligand_source}, ligand_source",
            f"remove ligand_source and not "
            f"(chain {homolog_chain} and "
            f"resn {ligand_component} and resi {ligand_residue})",
            "",
            f"select homolog_pocket, structure2 and ({homolog_selection})",
            f"select target_pocket, structure1 and ({target_selection})",
            f"select ligand, ligand_source and chain {homolog_chain} "
            f"and resn {ligand_component} and resi {ligand_residue}",
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

    zoom_indices = [
        i
        for i, line in enumerate(canonical_text.splitlines(True))
        if line.startswith("zoom polymer")
    ]

    if len(zoom_indices) != 1:
        raise RuntimeError(
            f"Expected exactly one canonical zoom line in {canonical_pml}"
        )

    lines = canonical_text.splitlines(True)
    lines.insert(zoom_indices[0], highlights)

    png_indices = [
        i
        for i, line in enumerate(lines)
        if line.startswith("png ")
    ]

    if len(png_indices) != 1:
        raise RuntimeError(
            f"Expected exactly one PNG line in {canonical_pml}"
        )

    lines[png_indices[0]] = (
        f"png {output_png}, dpi=300\n"
    )

    output_pml.write_text("".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()

    run = args.run

    with (run / "pocket_measurement.json").open() as handle:
        artifact = json.load(handle)

    measurement = artifact["measurement"]
    homolog = artifact["homolog"]
    target = artifact["target"]

    ligand = artifact["ligand"]
    ligand_component = ligand["component"]
    ligand_instance = ligand["instance"]

    parts = ligand_instance.split()
    if len(parts) != 3:
        raise ValueError(
            f"Unexpected ligand instance: {ligand_instance!r}"
        )

    ligand_chain = parts[1]
    ligand_residue = parts[2]

    if ligand_chain != homolog["chain"]:
        raise ValueError(
            "Ligand chain does not match homolog chain: "
            f"{ligand_chain!r} != {homolog['chain']!r}"
        )

    homolog_selection, target_selection = build_pocket_selections(
        homolog_pocket_residues=measurement["pocket_residues"],
        mapped_pocket_residues=measurement["mapped_pocket_residues"],
    )

    superposition = run / "usalign_superposition.cif"
    homolog_cif = Path(homolog["structure_path"])
    ligand_source = (
        ROOT / "structures/raw" / f"{homolog['pdb_id']}.cif"
    )

    # ----------------------------------------------------------
    # 1. Existing pocket-focused renderer.
    # Only replace its P1 ligand selector.
    # Camera/rendering behavior is untouched.
    # ----------------------------------------------------------
    pocket_pml = run / "pocket_review.pml"
    pocket_png = run / "pocket_review.png"

    write_pocket_focused_pml(
        superposition_cif=superposition,
        homolog_structure_cif=homolog_cif,
        ligand_source_cif=ligand_source,
        homolog_chain=homolog["chain"],
        target_chain=target["chain"],
        homolog_selection=homolog_selection,
        target_selection=target_selection,
        output_png=pocket_png,
        output_pml=pocket_pml,
    )

    patch_ligand_selection(
        pocket_pml,
        ligand_component,
        ligand_residue,
    )

    render_pocket_focused_pml(
        pml_path=pocket_pml,
    )

    # ----------------------------------------------------------
    # 2. Existing whole-structure renderer.
    # Preserve its framing, but correct the chain placeholders.
    # ----------------------------------------------------------
    whole_pml = run / "whole_structure_review.pml"
    whole_png = run / "whole_structure_review.png"

    write_whole_structure_review_pml(
        superposition_cif=superposition,
        homolog_structure_cif=homolog_cif,
        output_png=whole_png,
        output_pml=whole_pml,
    )

    patch_structure_chains(
        whole_pml,
        target["chain"],
        homolog["chain"],
    )

    render_pocket_focused_pml(
        pml_path=whole_pml,
    )

    # ----------------------------------------------------------
    # 3. Existing whole-protein + pocket renderer pattern.
    # Same whole-protein framing as the canonical PML.
    # ----------------------------------------------------------
    whole_protein_pml = (
        run / "whole_protein_pocket_review.pml"
    )
    whole_protein_png = (
        run / "whole_protein_pocket_review.png"
    )

    build_whole_protein_pocket_pml(
        canonical_pml=whole_pml,
        output_pml=whole_protein_pml,
        output_png=whole_protein_png,
        ligand_source=ligand_source,
        homolog_selection=homolog_selection,
        target_selection=target_selection,
        target_chain=target["chain"],
        homolog_chain=homolog["chain"],
        ligand_component=ligand_component,
        ligand_residue=ligand_residue,
    )

    render_pocket_focused_pml(
        pml_path=whole_protein_pml,
    )

    print("rendered:", pocket_png)
    print("rendered:", whole_png)
    print("rendered:", whole_protein_png)


if __name__ == "__main__":
    main()
