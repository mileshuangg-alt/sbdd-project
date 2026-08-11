# Week 1 — Session 1 (2026-08-05)

## Objective

Determine whether DiffSBDD is a viable starting point for a pocket-conditioned molecular generation project.

---

## Decision

Use **DiffSBDD** as the initial reproduction target because:

- It is the official implementation accompanying the publication.
- Published pretrained checkpoints are available.
- It supports pocket-conditioned **de novo** ligand generation.
- It provides example inference workflows that can be reproduced before attempting modifications.

---

## What I Learned

### Repository Structure

`generate_ligands.py` is the command-line entry point for de novo ligand generation.

Its responsibilities are:

- Parse command-line arguments.
- Load a pretrained DiffSBDD model from a checkpoint.
- Pass the protein structure and pocket definition to the model.
- Write the generated ligands to an output SDF file.

The diffusion model itself is implemented elsewhere (`LigandPocketDDPM`). `generate_ligands.py` is primarily an orchestration script rather than the implementation of the model.

---

### Inputs

**Required**

- Pretrained model checkpoint (`.ckpt`)
- Protein structure (`.pdb`)
- Binding pocket definition

**Pocket definition can be specified by:**

- A reference ligand already present in the PDB (`--ref_ligand A:330`)
- An external reference ligand (`.sdf`)
- A list of binding-site residues (`--resi_list`)

---

### Outputs

The model produces:

- Generated ligand molecules
- Saved as an SDF file
- Each molecule contains explicit 3D atomic coordinates

Unlike the MACCS fingerprint approach used in Kadurin et al., DiffSBDD generates molecular structures directly rather than molecular descriptors.

---

## Concepts Clarified

### Checkpoints

- Store pretrained model weights.
- Created during training.
- Loaded during inference.
- Remain unchanged during inference.
- Only change during additional training or fine-tuning.

### `generate_ligands.py`

Used for **de novo ligand generation**.

A known ligand may be supplied to define the location of the binding pocket, but the generated ligand is entirely new.

### `inpaint.py`

Used for **molecular editing** rather than de novo generation.

Part of an existing ligand is kept fixed while the model generates the missing or modified portion.

---

## Key Takeaway

DiffSBDD separates the command-line interface from the machine learning model.

`generate_ligands.py` orchestrates inference by:

1. Parsing user inputs.
2. Loading a pretrained model checkpoint.
3. Calling `model.generate_ligands(...)`.
4. Writing the generated molecules to an SDF file.

The actual diffusion model is implemented within the `LigandPocketDDPM` class.

---

## Open Questions

- Can the official README example still be executed in 2026?
- Does the repository install cleanly in a modern Linux/Colab environment?
- What operations occur inside `LigandPocketDDPM.generate_ligands()`? (Investigate only if needed.)

---

## Next Session

### Objective

Determine whether the official DiffSBDD example is still reproducible.

### Success Criteria

- [ ] Create a Google Colab notebook.
- [ ] Clone the DiffSBDD repository.
- [ ] Download the published checkpoint.
- [ ] Attempt the official README inference example without modification.
- [ ] If successful, save the generated SDF.
- [ ] If unsuccessful, record the first blocking error.
- [ ] Classify the failure as one of:
  - Environment setup
  - Dependency/version issue
  - Checkpoint access
  - Repository drift
  - Runtime/model error