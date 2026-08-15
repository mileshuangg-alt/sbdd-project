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

## D003 — Define the Stage 3 structural-plausibility gate

**Date:** 2026-08-13

### Decision

Stage 3 will evaluate 3D structural plausibility using a pinned version of PoseBusters.

The full PoseBusters suite will be executed and its outputs preserved, but Stage 3 attrition will be determined only by a predeclared hard gate consisting of:

- bond-length plausibility
- bond-angle plausibility
- steric-clash checks

Ring planarity, double-bond geometry, chirality, energy-related checks, and other available PoseBusters metrics will initially be retained as diagnostics rather than hard attrition criteria.

Stage 3 will be separated into:

- Stage 3A — ligand-intrinsic structural plausibility
- Stage 3B — pocket-relative structural plausibility

Stage 3B must receive an explicitly prepared pocket as an input. The shared evaluator must not silently inherit DiffSBDD-specific pocket-preparation assumptions.

All structural evaluation must use the generator's original generated coordinates. Conformers must not be regenerated before evaluation.

The PoseBusters version will be pinned, and the implementation will be mapped against the API, check names, thresholds, and semantics of that exact release.

Any future change to the hard attrition gate requires a new versioned project decision.

For the Stage 3A / Stage 3B interface, the predeclared steric-clash criterion is interpreted as:

- Stage 3A: PoseBusters `internal_steric_clash`
- Stage 3B: PoseBusters protein–ligand `no_clashes_protein`

The PoseBusters protein-distance check `not_too_far_away_protein` and protein volume-overlap check remain diagnostics and are not part of the current hard attrition gate.

This mapping was defined from the pinned PoseBusters 0.6.5 configuration before Stage 3B outcomes were inspected.

### Rationale

- Structural plausibility is distinct from chemical validity and 2D molecular-property feasibility.
- Running the full PoseBusters suite preserves information that may become scientifically useful without allowing diagnostic metrics to redefine attrition after results are observed.
- Declaring the hard gate before examining the 3RFM results prevents outcome-dependent threshold selection.
- Preserving original generated coordinates evaluates generator performance rather than RDKit conformer generation or geometry optimization.
- Separating ligand-intrinsic and pocket-relative evaluation prevents protein-preparation assumptions from being conflated with intrinsic ligand geometry.
- Explicit prepared-pocket inputs allow DiffSBDD and FLOWR to be compared through the same structural-evaluation interface.
- Pinning PoseBusters prevents changes in check names, defaults, thresholds, or implementation across releases from silently changing the comparison.

### Alternatives considered

- Treat every PoseBusters check as a hard attrition criterion.
- Use only a subset of PoseBusters checks and discard the remaining outputs.
- Choose the hard gate after inspecting the 3RFM results.
- Regenerate or optimize ligand conformers before structural evaluation.
- Allow each generator to provide its own implicitly prepared pocket.
- Use the latest available PoseBusters release without pinning its version.

These approaches were rejected because they would reduce auditability, change the object being evaluated, or weaken the apples-to-apples DiffSBDD-versus-FLOWR comparison.

### Revisit when

- Stage 3 diagnostics provide evidence that additional metrics should become hard gates.
- PoseBusters changes materially enough to justify a version upgrade.
- The same Stage 3 implementation is applied to FLOWR.
- Prepared-pocket methodology is standardized or changed.
- Larger benchmark sets reveal that the predeclared gate is insufficient or systematically misleading.

## D004 — Predeclare target-selection logic and TEAD developability expectation

**Date:** 2026-08-13

### Decision

No fallback target will be locked until a predefined target-selection rubric is applied.

A target selected by the Bivona lab supersedes the fallback target-selection process.

The fallback rubric will score generative tractability and developability tractability separately so that target properties affecting both generation and downstream molecular properties are not counted twice.

SOS1 will be considered primarily as a conservative "pipeline works" target, while TEAD will be considered as a higher-information "cascade is useful" target.

If TEAD is selected, elevated downstream developability attrition is expected in advance because its deep, predominantly hydrophobic lipid pocket may favor generated chemotypes with greater lipophilic character.

Accordingly, high Stage 2 property / Rule-of-Five attrition or later ADME/developability liabilities will not, by themselves, be interpreted as generator or pipeline failure.

The TEAD experiment will distinguish between:

- generative tractability — whether the generator produces chemically and structurally plausible molecules compatible with the TEAD pocket
- developability tractability — whether those pocket-compatible molecules also satisfy broader physicochemical, ADME, and safety constraints

Pocket-compatible generation followed by substantial downstream developability attrition will be interpreted as evidence that target-conditioned generative success and development viability are distinct objectives.

This expectation is declared before target selection and before any TEAD generation or evaluation results are observed.

### Revisit when

- the Bivona lab provides a target
- the predefined target-selection rubric is applied
- structural evidence materially changes the assessment of TEAD or SOS1
- a different fallback target clearly dominates the rubric

## D005 — Define Stage 4 chemical-similarity characterization

**Date:** 2026-08-15

### Decision

Stage 4 will characterize chemical similarity and novelty without causing cascade attrition.

All molecules that pass Stage 3 will proceed through Stage 4 and remain eligible for subsequent stages regardless of their similarity scores.

The primary molecular representation will be:

- Morgan fingerprint
- radius = 2
- 2048 bits
- chirality enabled

Pairwise molecular similarity will be measured using Tanimoto similarity.

Stage 4 will contain three primary analyses:

- Stage 4A — internal generated-set diversity
- Stage 4B — target-space novelty
- Stage 4C — general drug-space novelty

### Stage 4A — Internal generated-set diversity

Each Stage-3 survivor will be compared against the other surviving generated molecules.

The analysis will preserve at minimum:

- nearest generated-neighbor molecule ID
- nearest generated-neighbor Tanimoto similarity

Additional distribution-level or pairwise diagnostics may also be retained.

### Stage 4B — Target-space novelty

Each generated molecule will be compared against a frozen reference set of known ligands for the relevant human target.

The initial reference source will be ChEMBL 37.

For the 3RFM baseline, the target is the human adenosine A2A receptor.

The target-ligand reference set will use a predefined, target-independent extraction rule based on:

- human target
- single-protein target assignment
- directly measured quantitative activity
- supported activity types such as Ki, Kd, IC50, and EC50
- pChEMBL >= 6
- valid standardized molecular structure
- deduplication by standardized structure

Functional direction such as agonism or antagonism will not determine inclusion by itself.

The analysis will preserve at minimum:

- nearest target-ligand identity
- nearest target-ligand similarity
- target reference-set size

### Stage 4C — General drug-space novelty

Each generated molecule will also be compared against a fixed reference set representing established approved-drug chemistry.

The approved-drug reference set will be derived from the same frozen ChEMBL 37 release where possible.

The same Stage 4C reference set will be reused across future targets and generators.

The analysis will preserve at minimum:

- nearest approved-drug identity
- nearest approved-drug similarity

### Conditioning-ligand diagnostic

When generation used a reference ligand to define the pocket, similarity to that conditioning ligand may be recorded as an optional provenance diagnostic.

For the 3RFM baseline, this is similarity to caffeine.

Conditioning-ligand similarity is not a required Stage 4 metric because residue-defined pockets may not have a conditioning ligand.

Pocket-residue interaction or pose-complementarity measurements are not substitutes for conditioning-ligand similarity and belong to later target-compatibility evaluation.

### Interpretation

Similarity values are continuous characterization features rather than pass/fail criteria.

High similarity may represent chemical redundancy or proximity to established medicinal chemistry.

Low similarity may represent greater novelty but may also correspond to greater distance from established chemical space.

No Stage 4 similarity threshold will currently determine cascade survival.

Any future conversion of Stage 4 similarity into an attrition criterion requires a new versioned project decision declared before affected results are inspected.

### Revisit when

- the ChEMBL reference-set extraction rules require revision
- approved-drug reference-set construction is finalized or changed
- Stage 4 is applied to additional biological targets
- Stage 4 is applied to FLOWR
- evidence supports adding alternative fingerprint representations as secondary sensitivity analyses
- similarity is proposed as a future attrition criterion