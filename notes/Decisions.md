# Project Decisions

## D001 — Choose DiffSBDD as the initial reproduction target

**Date:** 2026-08-05

### Decision

Use **DiffSBDD** as the first structure-based generative model to reproduce.

### Rationale

- Official implementation accompanying the publication.
- Published pretrained checkpoints are available.
- Supports pocket-conditioned de novo ligand generation.
- Provides documented inference examples that can be reproduced before attempting modifications.
- Establishes a concrete baseline before evaluating alternative models (e.g., TargetDiff or SemlaFlow).

### Alternatives considered

- TargetDiff
- SemlaFlow

These remain candidates for future comparison but were not selected as the initial reproduction target.

### Revisit when

- The official example cannot be reproduced.
- The repository is no longer maintainable.
- Another model proves substantially easier to reproduce or better aligned with the project goals.

## D002 — Reframe the long-term goal as an end-to-end in silico drug discovery pipeline

**Date:** 2026-08-12

### Decision

Reframe the long-term goal of the project as an **end-to-end in silico drug discovery pipeline**.

The planned architecture is:

1. **SBDD generation**
   - Phase 1: DiffSBDD reproducible checkpoint baseline.
   - Phase 2: FLOWR comparison through the same generator-independent interface.

2. **Progressive triage / attrition cascade**
   - Chemical validity.
   - Drug-likeness / property feasibility.
   - 3D / structural plausibility.
   - Novelty.
   - Target compatibility.
   - Synthetic feasibility.
   - ADME / disposition characterization.
   - Safety-risk characterization, including DILI.

3. **Virtual-cell simulation**
   - Intended as the final in silico validation gate before any proposed wet-lab step.

The DiffSBDD-vs-FLOWR comparison will be evaluated as an **attrition-cascade comparison**. The primary question is whether improved generative modeling produces a greater fraction of molecules that survive progressively more development-relevant constraints, rather than which generator simply produces more chemically valid molecules.

Disposition and DILI will remain late-stage characterization components rather than early chemistry filters.

A structure-only DILI risk module may be used as a placeholder interface during development, but it will not be treated as the intended final biological safety assessment.

The virtual-cell-versus-structure-only DILI experiment will serve as a feasibility study for the proposed final validation gate. It will first be evaluated on known drugs with real DILIrank labels, stratified by BDDCS class, and evaluated against the performance bar motivated by Benet's framework and Chan & Benet.

Phase 1 scope remains unchanged: build and validate the core generator-agnostic cascade in order.

### Rationale

- Chemical validity alone is insufficient to determine whether generated molecules are useful drug-discovery candidates.
- A progressive attrition cascade allows generator performance to be evaluated against increasingly development-relevant constraints.
- Comparing DiffSBDD and FLOWR through the identical cascade provides a more meaningful comparison than generator-native validity metrics alone.
- ADME, disposition, and safety characterization extend the evaluation toward developability rather than stopping at molecular plausibility or target binding.
- Virtual-cell simulation could potentially provide a biologically richer final validation layer than structure-only prediction.
- Validating the virtual-cell approach on known drugs with real labels before applying it to generated molecules provides a falsifiable test of whether the proposed final gate is credible.
- The major known weak link is mapping arbitrary generated molecular structures to credible cellular responses. This limitation should be tested explicitly rather than assumed away.

### Alternatives considered

- Limit the project to benchmarking SBDD generators using validity and conventional molecular metrics.
- End the cascade after target compatibility or docking.
- End the cascade after synthetic feasibility.
- Use structure-only ADME and toxicity prediction as the final in silico stage.
- Apply virtual-cell simulation directly to generated molecules without first validating the approach on known drugs.

These remain possible fallback scopes if later stages prove infeasible, particularly if reliable structure-to-cell-response mapping cannot be established.

### Revisit when

- The core generator-agnostic cascade has been implemented and validated.
- The DiffSBDD-vs-FLOWR attrition comparison is ready to be performed.
- Appropriate disposition, BDDCS, DILIrank, and virtual-cell resources have been identified.
- The virtual-cell-versus-structure-only DILI feasibility study has been completed.
- Evidence shows that structure-to-cell-response mapping for arbitrary generated molecules is not sufficiently reliable.
- The expanded scope begins to interfere with completion of the core Phase 1 cascade.
