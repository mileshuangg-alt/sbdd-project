# Session 2 — 2026-08-11

## Objective

Determine whether the released DiffSBDD checkpoint can still be used to reproduce the official 3RFM pocket-conditioned ligand generation example on a free Google Colab GPU.

---

## Success Criteria

- [x] Obtain a GPU runtime.
- [x] Reconstruct a working DiffSBDD environment.
- [x] Load the released CrossDocked checkpoint.
- [x] Run inference on the example 3RFM pocket.
- [x] Generate 20 ligand samples.
- [x] Write the generated molecules to an SDF file.
- [x] Confirm that an external RDKit reader can parse all 20 SDF records.

---

## Environment

### Hardware

- Google Colab free tier
- NVIDIA Tesla T4
- ~15 GB VRAM

### Working DiffSBDD Environment

A separate Conda environment named `diffsbdd` was created with:

- Python 3.10.4
- PyTorch 2.0.1 + CUDA 11.8
- PyTorch Lightning 1.8.4
- RDKit 2022.03.3
- NumPy 1.22.4
- SciPy 1.7.3
- Matplotlib 3.5.3
- OpenBabel 3.1.1
- PyG / torch-scatter built for PyTorch 2.0.1 + CUDA 11.8
- Setuptools <81
- Additional pinned supporting dependencies

PyTorch successfully detected the Tesla T4 GPU.

---

## What I Did

### 1. Tested the official Colab workflow

The authors' official DiffSBDD Colab notebook was used as the starting point.

The notebook's original dependency installation did **not** reproduce successfully on the current Colab environment.

Current Colab uses a substantially newer software stack, including Python 3.12, while DiffSBDD depends on an older Python/PyTorch ecosystem.

Multiple original dependency installations failed, including older versions of:

- PyTorch
- RDKit
- Biopython
- SciPy
- torch-scatter
- OpenBabel

### 2. Reconstructed the legacy environment

Installed `condacolab` and created a separate Python 3.10.4 environment.

Installed PyTorch 2.0.1 with CUDA 11.8 support and reconstructed the remaining dependency stack.

Additional compatibility issues identified during reconstruction included:

- `pkg_resources` required by the older PyTorch Lightning stack, resolved by pinning `setuptools<81`.
- RDKit and SciPy binaries were incompatible with NumPy 2.x, resolved by pinning NumPy 1.22.4.
- Modern Matplotlib required a newer NumPy version, resolved by using Matplotlib 3.5.3.
- Several dependencies used by the current repository were absent from the older Colab installation recipe.

The final environment successfully imported the actual `LigandPocketDDPM` model class.

### 3. Reproduced DiffSBDD inference

Used the released:

`crossdocked_fullatom_cond.ckpt`

with the official example:

- Protein: `3rfm.pdb`
- Pocket definition: reference ligand `A:330`
- Samples requested: 20

The generation command completed successfully and produced:

`3rfm_mol.sdf`

### 4. Verified the generator output

The output SDF contained:

- 20 SDF records
- 20 records readable by RDKit with `sanitize=False`
- 0 records that failed basic RDKit parsing

This check intentionally did **not** perform RDKit sanitization.

Chemical validity will be evaluated separately as the first stage of the generator-agnostic evaluation cascade.

---

## Key Findings

### DiffSBDD is still runnable

The released DiffSBDD CrossDocked checkpoint successfully performs pocket-conditioned ligand generation on a free Colab Tesla T4.

The main reproducibility problem was the software environment rather than the model or checkpoint.

### The published Colab environment has drifted

The official Colab installation workflow no longer runs unchanged on the current Colab runtime.

A compatible legacy environment had to be reconstructed manually.

### Generator output can be treated as a file boundary

DiffSBDD successfully produced a standalone SDF containing 20 generated molecules.

This provides a clean interface between generation and evaluation:

`protein pocket -> DiffSBDD -> SDF -> evaluation cascade`

Downstream evaluation should consume the SDF rather than DiffSBDD model internals.

---

## Artifact

Generated output:

`experiments/phase1_diffsbdd/3rfm_mol.sdf`

Contains 20 generated ligand records from the 3RFM example pocket.

The SDF is stored as an experiment artifact and is not tracked by Git.

---

## Known Warnings

The reconstructed environment produces a deprecation warning related to `pkg_resources`.

This warning does not prevent inference and is expected from the older PyTorch Lightning software stack.

OpenBabel may also emit a warning about its older import syntax.

Neither warning affected generation.

---

## Key Takeaway

DiffSBDD itself is not dead.

The original environment has experienced substantial dependency drift, but a compatible legacy environment can still be reconstructed, the released checkpoint loads successfully, and the official example produces 20 parseable molecular structures on a free Colab T4.

Phase 1 now has a working pretrained-generator baseline.

---

## Next Session

### Objective

Begin the generator-agnostic evaluation cascade using the saved SDF as the only input.

### First Question

Of the 20 generated structures, how many pass independent RDKit sanitization?

### Architecture Rule

The evaluation code must:

- accept an SDF file as input
- have no dependency on DiffSBDD internals
- report the number of molecules entering and surviving each stage
- preserve failures rather than silently dropping them

This will become the first row of the project's attrition table.