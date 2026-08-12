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

### Generation baseline

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

### Stage 2 — Planned

Molecular property profiling and Rule-of-Five feasibility classification.

Planned measurements include:

- molecular weight
- cLogP
- hydrogen-bond donors
- hydrogen-bond acceptors
- TPSA
- rotatable bonds
- QED
- heavy atom count
- formal charge
- Rule-of-Five violations

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

## Repository Structure

```text
sbdd-project/
├── evaluation/
│   ├── __init__.py
│   └── validity.py
├── experiments/
│   └── phase1_diffsbdd/
│       └── evaluation/
├── notes/
│   ├── Decisions.md
│   ├── project_log.md
│   └── Session_XXX.md
├── tests/
│   └── data/
└── README.md
```

External generator repositories, model checkpoints, and generated molecular SDF files are intentionally excluded from Git.

## Current Development Principle

The evaluation cascade is the central reusable component of the project.

Each evaluation stage should:

- consume standardized molecular files or standardized upstream results
- preserve molecule-level provenance
- record explicit pass/fail outcomes where applicable
- preserve failure reasons
- produce machine-readable outputs
- avoid generator-specific assumptions

## Project Status

**Current phase:** Phase 1  
**Current generator:** DiffSBDD  
**Completed cascade stage:** Chemical validity  
**Next implementation:** Molecular property profiling and Rule-of-Five feasibility classification

See `notes/Decisions.md` for major architectural decisions and `notes/project_log.md` for development history.