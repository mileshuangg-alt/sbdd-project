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

### Stage 3B positive-control validation

A positive control was constructed before relying on the 3RFM Stage 3B result in future generator comparisons.

The control was generated from a real Stage 3 survivor (`molecule_id = 0`). Its molecular geometry was preserved by rigid translation, while ligand atom 0 was translated directly onto the nitrogen atom of TYR 9 in chain A of the prepared 3RFM pocket.

This deliberately created a protein–ligand steric clash without altering the ligand's internal geometry.

The unchanged Stage 3B evaluator produced:

```text
minimum_distance_to_protein:   False
smallest_distance_protein:     0.0 Å
num_pairwise_clashes_protein:  9
most_extreme_clash_protein:    True
stage3b_passes:                False
```
Therefore, the deliberately clashing positive control was rejected by the existing Stage 3B hard gate.

This provides positive-control evidence that the Stage 3B protein–ligand steric-clash gate is capable of firing. The original 18/18 3RFM Stage 3B pass result can therefore be interpreted as an observed absence of gate-triggering clashes in that baseline set rather than evidence of an inactive gate.

The validation also clarified PoseBusters 0.6.5 output naming. D003 originally referred to the intended protein–ligand clash criterion as `no_clashes_protein`. In the pinned PoseBusters 0.6.5 full report used by the implementation, the corresponding Boolean output consumed by the existing gate is `minimum_distance_to_protein`, while underlying clash diagnostics include `smallest_distance_protein`, `num_pairwise_clashes_protein`, and `most_extreme_clash_protein`.

The positive control empirically confirmed the intended relationship: forcing a zero-distance protein–ligand overlap produced nine detected pairwise clashes, set `most_extreme_clash_protein = True`, flipped `minimum_distance_to_protein = False`, and therefore produced `stage3b_passes = False`.

Positive-control artifacts are retained separately from experimental outputs under:

`tests/stage3b_positive_control/`


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

## D006 — Stage 4 is non-attritional chemical-space characterization

**Decision:** Stage 4 will characterize and rank surviving molecules in multiple chemical reference spaces without applying a hard novelty attrition threshold.

All Stage 4 comparisons use the same molecular representation:

- Morgan fingerprint
- radius = 2
- 2048 bits
- chirality enabled
- Tanimoto similarity

Stage 4 is divided into:

### Stage 4A — Internal generated-set similarity

Generated molecules are compared against the other surviving generated molecules.

Outputs include:

- full pairwise similarity distribution
- nearest generated neighbor per molecule

This measures internal redundancy within the generated set.

### Stage 4B — Known target-ligand-space similarity

Generated molecules are compared against a frozen reference set of known ligands for the current target.

For the Phase 1 A2A baseline, the reference is derived from ChEMBL 37 using:

- target: CHEMBL251
- organism: Homo sapiens
- target type: SINGLE PROTEIN
- activity types: Ki, Kd, IC50, EC50
- non-null standardized activity values
- standard relation in `=`, `<`, `<=`
- pChEMBL >= 6.0
- RDKit canonical-structure deduplication

The resulting frozen A2A reference contains 5,344 unique structures.

Stage 4B measures proximity to **known target-associated ligand chemistry**. Reference ligands do not need to be approved drugs.

### Stage 4C — Approved-drug-space similarity

Generated molecules are compared against a frozen target-independent reference of approved small-molecule chemistry from ChEMBL 37.

Initial selection:

- `max_phase = 4`
- `molecule_type = Small molecule`

Approved salts and alternative forms are normalized to their ChEMBL parent structures where possible. Structures are canonicalized with RDKit and deduplicated by canonical structure.

Approved records without a resolvable molecular structure cannot participate in fingerprint-based chemical-space analysis and are explicitly counted as structurally unevaluable reference records.

The resulting frozen reference contains:

- 2,198 unique parent-normalized approved-drug structures
- 158 approved records excluded because no usable structure could be resolved

Withdrawal status and first-approval information are retained as descriptive provenance and do not affect similarity calculations or reference inclusion.

Stage 4C measures proximity to **established approved-drug chemistry across targets**, not target-specific ligand chemistry.

### Reference-data policy

Live database access is separated from evaluation.

ChEMBL is used only to construct versioned reference artifacts. Normal Stage 4 evaluation consumes frozen local reference files so that:

- generator comparisons use identical reference populations
- database updates cannot silently change results
- network availability does not affect normal evaluation
- ChEMBL-specific retrieval logic remains outside the generator-independent evaluator

Current reference release:

`ChEMBL 37`

Future reference updates must be versioned rather than silently replacing the current reference sets.

### Attrition policy

Stage 4 applies no hard similarity threshold.

All 16 molecules entering Stage 4 remain eligible downstream.

Any future introduction of a Stage 4 similarity-based attrition threshold must be documented as a new versioned project decision.

### Predeclared Stage 4 similarity reading bands

Before the FLOWR comparison, Stage 4 similarity interpretation is frozen using a hybrid framework:

- upper boundaries are universal and convention-anchored
- lower boundaries are calibrated to the empirical null distribution of each frozen reference set

These bands are **interpretive priors, never filters or attrition thresholds**.

Stage 4B and Stage 4C labels remain separate because proximity to known target-ligand chemistry and proximity to approved-drug chemistry represent different forms of chemical precedent.

#### Frozen reading bands

| Reference space | Statistic | Extrapolative / corroboration required | Novel-but-grounded | Established / high precedent |
| --- | --- | ---: | ---: | ---: |
| Stage 4B — target ligands | Nearest similarity | < 0.2727 | 0.2727 to < 0.40 | >= 0.40 |
| Stage 4B — target ligands | Top-5 mean similarity | < 0.2118 | 0.2118 to < 0.30 | >= 0.30 |
| Stage 4C — approved drugs | Nearest similarity | < 0.1690 | 0.1690 to < 0.40 | >= 0.40 |
| Stage 4C — approved drugs | Top-5 mean similarity | < 0.1284 | 0.1284 to < 0.30 | >= 0.30 |

Interpretation:

- **Established / high precedent** indicates that the generated molecule occupies chemical space with substantial structural precedent in the relevant reference.
- **Novel-but-grounded** indicates structural novelty while remaining above the similarity expected from the reference's random-pair background.
- **Extrapolative / corroboration required** indicates that the molecule lies sufficiently far from established reference chemistry that stronger independent downstream evidence is required before the extrapolation is trusted.

An extrapolative label does **not** imply that a molecule is chemically implausible or that it should be removed from the cascade.

Instead, it changes the evidentiary burden downstream.

For example:

- Stage 4B extrapolative chemistry places greater evidentiary weight on later target-compatibility results.
- Stage 4C extrapolative chemistry places greater evidentiary weight on later developability, ADME, and safety characterization.
- A molecule that is extrapolative in both spaces requires convergent downstream support but is not automatically rejected.
- High similarity in both spaces provides stronger chemical precedent but may reduce the strength of a structural-novelty claim.

Stage 4B and Stage 4C labels must not be collapsed into a single novelty score.

### Null calibration

The lower boundaries were calibrated against empirical random-similarity null distributions constructed from the exact frozen ChEMBL 37 reference artifacts used by Stage 4.

Reproducibility parameters:

```text
Random seed:
20260816

Random within-reference pairs per reference:
1,000,000

Random five-pair means per reference:
200,000

Stage 4B reference:
references/chembl37/ADORA2A_target_ligands.csv

Stage 4C reference:
references/chembl37/approved_drugs.csv

Fingerprint:
Morgan radius 2
2048 bits
chirality enabled

Similarity:
Tanimoto

```

#### Boundary null percentiles

Stage 4B — target-ligand reference:

```text
Nearest lower boundary:
0.2727
95th null percentile by construction

Nearest upper boundary:
0.40
98.33rd null percentile

Top-5 mean lower boundary:
0.2118
95th null percentile by construction

Top-5 mean upper boundary:
0.30
99.83rd null percentile
```

Stage 4C — approved-drug reference:

```text
Nearest lower boundary:
0.1690
95th null percentile by construction

Nearest upper boundary:
0.40
99.85th null percentile

Top-5 mean lower boundary:
0.1284
95th null percentile by construction

Top-5 mean upper boundary:
0.30
approximately the 99.9995th null percentile
```

The reference-specific lower boundaries are necessary because the two frozen chemical reference spaces have different background similarity distributions.

In particular, a fixed nearest-neighbor lower boundary of 0.20 lies at only the **87.69th percentile** of the A2A random-pair null, meaning that roughly 12% of random within-reference comparisons exceed it. A fixed 0.20 lower boundary on this dense, scaffold-concentrated reference would therefore misclassify too much chance-level similarity as chemically grounded.

Accordingly, "grounded" is anchored to the chance distribution of the specific frozen reference rather than to one universal lower Tanimoto value.

### 3RFM sanity preview

Under the frozen framework, the current 3RFM baseline reads as follows:

**The Stage 4B nearest-similarity mean of 0.225 is below the target-reference null-calibrated lower boundary of 0.2727 and therefore reads as extrapolative / corroboration required, while the Stage 4C nearest-similarity mean of 0.246 remains novel-but-grounded.**

The Stage 4B nearest grounded band is intentionally narrow:

```text
0.2727 to < 0.40
```

Therefore, many FLOWR molecules may be expected to read as extrapolative on the Stage 4B nearest-neighbor statistic. For a novelty-seeking generator, this posture is expected and is **not itself evidence of generator failure**. Such molecules instead carry a greater requirement for independent downstream corroboration.

### Reference-version rule

The null-calibrated lower boundaries belong to these exact frozen reference sets.

If either:

- the frozen target-ligand reference set changes, or
- the frozen approved-drug reference set changes,

the corresponding null distribution must be recomputed and new lower boundaries derived from the new reference's empirical 95th percentile.

Reference-specific lower boundaries must not be carried forward automatically to a new target, reference release, or modified reference population.

The universal convention-anchored upper boundaries remain:

```text
Nearest similarity >= 0.40
Top-5 mean similarity >= 0.30
```

unless a future versioned project decision explicitly changes them.

### Reporting rule

Whenever a Stage 4 similarity label is reported in future result artifacts or summaries, its **null percentile must be reported alongside the label**.

The similarity value, interpretive label, and null percentile therefore remain distinguishable:

```text
similarity value
+
reference-specific interpretive label
+
empirical null percentile
```

This preserves both convention-anchored cheminformatics interpretation and the empirical rarity of the observed similarity within the relevant frozen reference space.