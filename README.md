# SBDD Drug Discovery Pipeline

An experimental, generator-agnostic pipeline for evaluating structure-based de novo molecular generation through progressively more development-relevant constraints.

## Project Goal

The long-term goal is an **end-to-end in silico drug discovery pipeline** that connects structure-based molecular generation to progressively deeper computational triage before any proposed wet-lab validation.

The central question is not simply whether a generative model produces chemically valid molecules, but:

> **Do generated molecules survive progressively more development-relevant constraints?**

## Architecture

```text
SBDD Generation
      ↓
Chemical Validity
      ↓
Drug-Likeness / Property Feasibility
      ↓
3D / Structural Plausibility
      ↓
Novelty
      ↓
Target Compatibility
      ↓
Synthetic Feasibility
      ↓
ADME / Disposition Characterization
      ↓
Safety-Risk Characterization
including DILI
      ↓
Virtual-Cell Simulation
      ↓
Final In Silico Validation Gate
      ↓
Potential Wet-Lab Validation
```

Generation and evaluation are intentionally separated.

Generators produce standardized molecular files such as SDFs. Downstream evaluation stages consume those files rather than model internals.

This allows different generators to be evaluated through the identical cascade.

## Generator Plan

### Phase 1 — DiffSBDD

Reproduce DiffSBDD using its released pretrained checkpoint and establish the initial generation baseline.

### Phase 2 — FLOWR

Add FLOWR through the same generator interface and compare DiffSBDD and FLOWR through the identical evaluation cascade.

The comparison will focus on **attrition across development-relevant stages**, rather than generator-native validity metrics alone.

## Current Status

### Generation Baseline

DiffSBDD checkpoint inference has been successfully reproduced.

Initial test:

- Target: 3RFM
- Generated molecules: 20

### Stage 1 — Chemical Validity

Implemented in:

`evaluation/validity.py`

Initial DiffSBDD result:

```text
20 generated
    ↓
20 RDKit parsed
    ↓
19 RDKit sanitized
    ↓
95% Stage 1 survival
```

One molecule failed sanitization because of an explicit carbon valence of 5.

The evaluator also successfully handles deliberately malformed SDF records without silently dropping them.

### Stage 2 — Molecular Property Profiling and Rule-of-Five Classification

Implemented in:

`evaluation/properties.py`

Stage 2 consumes the machine-readable Stage 1 validity results and evaluates only molecules that passed chemical validity while preserving their original molecule IDs.

For each surviving molecule, it calculates:

- molecular weight
- cLogP
- TPSA
- hydrogen-bond donors
- hydrogen-bond acceptors
- rotatable bonds
- QED
- heavy atom count
- formal charge

Rule-of-Five criteria are also recorded individually, together with the total number of violations and a strict zero-violation classification.

Initial DiffSBDD result:

```text
19 Stage-1-valid molecules
    ↓
18 zero Rule-of-Five violations
 1 Rule-of-Five flagged
    ↓
94.74% Stage 2 zero-violation rate
```

### Stage 3 — 3D / Structural Plausibility

Implemented in:

`evaluation/structure.py`

Stage 3 uses PoseBusters `0.6.5` to evaluate the generator's **original generated 3D coordinates** rather than regenerated or optimized conformers.

The evaluation is separated into:

- **Stage 3A — ligand-intrinsic structural plausibility**
- **Stage 3B — pocket-relative structural plausibility**

The predeclared hard gate evaluates:

- bond-length plausibility
- bond-angle plausibility
- internal ligand steric clashes
- protein-ligand steric clashes

Other PoseBusters outputs are retained as diagnostics rather than hard attrition criteria.

#### Stage 3A

Stage 3A evaluates ligand-intrinsic geometry independently of the protein pocket.

The hard gate uses:

- `bond_lengths`
- `bond_angles`
- `internal_steric_clash`

Initial DiffSBDD result:

```text
18 Stage-2 survivors
    ↓
16 pass Stage 3A
 2 fail Stage 3A
    ↓
88.89% Stage 3A survival
```

The two failures were:

- `molecule_id=13` — failed bond-length plausibility because of one short bond outlier
- `molecule_id=16` — failed bond-length, bond-angle, and internal steric-clash criteria

The full PoseBusters Stage 3A report is preserved in:

`experiments/phase1_diffsbdd/evaluation/structure_3a.csv`

#### Stage 3B

Stage 3B evaluates generated ligand poses relative to an explicitly prepared pocket.

Pocket preparation is kept outside the shared Stage 3B evaluator so that the evaluator does not silently inherit generator-specific preprocessing assumptions.

For the 3RFM baseline, the pocket is defined from:

- source protein: `3rfm.pdb`
- reference ligand: `3rfm_B_CFF.sdf`
- standard amino acids only
- minimum residue-atom to reference-ligand-atom distance `< 8.0 Å`

This produces a 36-residue evaluation pocket while preserving the deposited protein heavy-atom coordinates.

The Phase 1 baseline does not add receptor hydrogens, alter protonation, or optimize receptor geometry.

The explicit pocket artifact is stored at:

`experiments/phase1_diffsbdd/evaluation/prepared_3rfm_pocket.pdb`

The Stage 3B hard gate uses the PoseBusters protein-ligand steric-clash result returned as:

`minimum_distance_to_protein`

Protein maximum-distance and volume-overlap checks remain diagnostic-only.

Initial DiffSBDD result:

```text
18 Stage-2 survivors evaluated
    ↓
18 pass protein-ligand clash gate
 0 fail
    ↓
100% Stage 3B survival
```

The full PoseBusters Stage 3B report is preserved in:

`experiments/phase1_diffsbdd/evaluation/structure_3b.csv`

#### Combined Stage 3 Result

The final Stage 3 decision is:

```text
stage3_passes = stage3a_passes AND stage3b_passes
```

Initial DiffSBDD result:

```text
18 Stage-2 survivors
    ↓
16 pass combined Stage 3
 2 fail combined Stage 3
    ↓
88.89% Stage 3 survival
```

Both final Stage 3 failures passed the pocket-relative clash gate. Their attrition therefore resulted from ligand-intrinsic structural problems rather than protein-pocket clashes.

The compact downstream Stage 3 handoff is stored in:

`experiments/phase1_diffsbdd/evaluation/structure.csv`

### Current Attrition Cascade

```text
20 generated
    ↓
19 chemically valid
    ↓
18 zero Rule-of-Five violations
    ↓
16 structurally plausible
```

**Current strict cascade survival: 16/20 (80%)**

## Current Development Principle

The evaluation cascade is the central reusable component of the project.

Each evaluation stage should:

- consume standardized molecular files or standardized upstream results
- preserve molecule-level provenance
- record explicit pass/fail outcomes where applicable
- preserve failure reasons
- produce machine-readable outputs
- avoid generator-specific assumptions

Generator-specific preprocessing and model internals should remain outside the shared evaluation interface.

## Long-Term Developability Layer

Later stages are planned to include:

- ADME/disposition characterization
- BCS/BDDCS-related prediction
- DILI risk characterization
- virtual-cell simulation

Disposition and DILI are intended as **late-stage characterization**, not early chemistry filters.

The proposed virtual-cell stage has a major unresolved limitation: mapping arbitrary generated molecular structures to credible cellular responses remains an open problem.

Therefore, the virtual-cell gate must first be validated on known drugs with real outcome labels before being applied to generated molecules.

A planned feasibility study will compare structure-only and virtual-cell-informed DILI prediction using known drugs with DILIrank labels, including analysis stratified by BDDCS class.

## Evaluation Environment

The generator-independent evaluation cascade uses the `sbdd-eval` Conda environment.

Create it with:

```bash
conda env create -f environment.yml
conda activate sbdd-eval
```

The current environment specification pins:

- Python `3.12`
- RDKit `2026.3.5`
- pandas `3.0.5`
- NumPy `2.5.2`
- PoseBusters `0.6.5`
- BioPython `1.88`

The environment is version-pinned to preserve evaluation behavior across cascade stages and future generator comparisons.

## Repository Structure

```text
sbdd-project/
├── environment.yml
├── evaluation/
│   ├── __init__.py
│   ├── validity.py
│   ├── properties.py
│   └── structure.py
├── experiments/
│   └── phase1_diffsbdd/
│       └── evaluation/
│           ├── validity.csv
│           ├── properties.csv
│           ├── prepared_3rfm_pocket.pdb
│           ├── structure_3a.csv
│           ├── structure_3b.csv
│           └── structure.csv
├── notes/
│   ├── Decisions.md
│   ├── project_log.md
│   └── Session_XXX.md
├── tests/
│   └── data/
└── README.md
```

External generator repositories, model checkpoints, and generated molecular SDF files are intentionally excluded from Git.

Evaluation outputs required to reproduce and audit cascade decisions are retained where appropriate.

## Project Status

**Current phase:** Phase 1  
**Current generator:** DiffSBDD  
**Completed cascade stages:** Chemical validity; molecular property profiling / Rule-of-Five classification; 3D / structural plausibility
**Next implementation:** Stage 4 — novelty / chemical-space redundancy
**Current strict cascade survival:** 16/20 (80%)