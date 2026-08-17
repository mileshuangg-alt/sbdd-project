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

## D007 — Predeclare Stage 5 target-compatibility methodology

**Date:** 2026-08-16

**Status:** PENDING VALIDATION

### Decision

Stage 5 will evaluate **target compatibility**: whether a generated molecule's existing 3D pose expresses a credible, target-specific interaction pattern within the intended binding site.

Stage 5 is explicitly distinct from Stage 3B.

```text
Stage 3B
"Is this pose physically plausible relative to the pocket?"
→ primarily tests protein-ligand steric compatibility

Stage 5
"Does this physically plausible pose make target-relevant interactions
consistent with credible recognition by the intended binding site?"
```

Passing Stage 3B is therefore necessary but not sufficient evidence of target compatibility.

The primary Stage 5 gate material will be **target-specific interaction recovery**.

Pose/contact geometry will provide secondary gate evidence.

Docking scores, approximate binding energies, and fast rescoring functions may be retained for characterization and ranking but will **never certify target compatibility or determine the Stage 5 hard gate**.

If target-specific interaction recovery cannot be computed robustly, Stage 5 implementation stops for methodological review rather than falling back to a docking-score gate.

The final Stage 5 gate will not be frozen until the interaction reader, docking protocol, and candidate gate formulations pass the predeclared validation sequence below.

No DiffSBDD Stage 5 baseline results may be inspected before that validation sequence is complete.

---

### Generator parity

DiffSBDD and FLOWR will be evaluated under the **identical frozen Stage 5 protocol**.

This includes the same:

- receptor preparation
- ligand preparation
- protonation policy
- docking engine and parameters
- search box
- pose allowance
- interaction reader
- target anchor definitions
- positive and negative controls
- gate formulation
- characterization metrics

Generator identity must not alter Stage 5 methodology.

The purpose of this decision is therefore not only to define target compatibility, but to protect the fairness of the eventual DiffSBDD-versus-FLOWR comparison.

---

## Stage 5 target-interaction definition

Target-relevant interactions must be derived from experimentally determined A2A receptor-ligand complexes and recorded with structural provenance.

They must not be defined from memory of 3RFM or selected after generated-molecule results are inspected.

For the 3RFM / human A2A baseline, the initial experimental reference complexes are:

| Ligand | ChEMBL ID | Experimental A2A complex |
| --- | --- | --- |
| XAC | CHEMBL273094 | PDB 3REY |
| Vipadenant | CHEMBL447664 | PDB 5OLH |
| Tozadenant | CHEMBL2105747 | PDB 5OLO |

All three ligands occur in the frozen Stage 4B A2A target-ligand reference.

The crystallographic 3RFM caffeine ligand remains a structural/pocket anchor but is not part of the formal positive-control panel because the Stage 4B frozen target reference requires pChEMBL >= 6.0.

### Core A2A recognition anchors

Published structural evidence across the experimental complexes supports a cross-chemotype A2A recognition core centered on:

- **Phe168** — aromatic / hydrophobic core recognition
- **Asn253^6.55** — polar hydrogen-bond anchoring

These two residues define the initial core target-interaction anchors.

Supporting interactions that may provide additional target-compatibility evidence include:

- Met177
- Trp246
- Leu249
- His250^6.52
- Thr256^6.58 where chemotype-appropriate
- Met270
- Ile274

Supporting contacts are not automatically mandatory individually.

Stage 5 must test target recognition rather than exact imitation of one reference ligand's complete interaction fingerprint.

The experimental PDB IDs, ligand identities, and interaction anchors above are part of the frozen methodology provenance.

---

## Predeclared control panel

Controls are nominated **before candidate Stage 5 gate formulations are evaluated**.

A candidate metric does not earn hard-gate status merely because it appears chemically reasonable.

It must demonstrate proof of life against the predeclared controls before being trusted on generated molecules.

### Positive controls

The formal positive controls are:

1. XAC — CHEMBL273094
2. Vipadenant — CHEMBL447664
3. Tozadenant — CHEMBL2105747

These represent experimentally supported human A2A ligand chemistry and span multiple chemotypes.

Their experimental complexes provide structural provenance for the target-recognition anchors.

### Negative controls

The initial negative panel consists of chemically varied approved drugs whose established pharmacology provides no reason to expect recognition of the A2A orthosteric site:

1. Imatinib — CHEMBL941
2. Oseltamivir — CHEMBL1229
3. Warfarin — CHEMBL1464
4. Apixaban — CHEMBL231779
5. Sildenafil — CHEMBL192

These are described as **predeclared unrelated-target negatives**, not proven A2A nonbinders.

The negative panel must not be changed after Stage 5 control results are inspected merely to improve apparent separation.

A negative control must also receive a fair opportunity to explore the A2A pocket. Deliberately placing a negative in an obviously clashing pose would test Stage 3B rather than Stage 5 and is therefore not an acceptable Stage 5 negative-control procedure.

---

# Frozen Stage 5 pose-generation protocol

The docking protocol is used as a **pose-generation mechanism**.

Its scoring function is not treated as evidence that a molecule binds the target.

### Docking engine

AutoDock Vina 1.2.x will be used, with the exact patch version pinned when the Stage 5 environment is finalized.

Frozen search parameters:

```text
Scoring function:
Vina

Receptor:
rigid

Exhaustiveness:
32

Random seed:
20260816

Maximum retained poses:
20

Energy range:
5 kcal/mol
```

Vina scores may be retained for characterization and ranking only.

They do not contribute to Stage 5 pass/fail status.

---

## Protein preparation

Protein structures will be protonated using:

```text
PDB2PQR
+
PROPKA
+
pH 7.4
```

Experimental protein heavy-atom coordinates will be preserved.

Protein heavy atoms will not be geometry-minimized before Stage 5 evaluation.

The receptor will then be converted to the required docking representation using Meeko.

The protonation / tautomer assignment of **His250^6.52** will be explicitly recorded for:

- 3REY
- 5OLH
- 5OLO
- 3RFM

because His250 participates in the A2A ligand-recognition environment and hidden differences in its protonation state could alter interaction interpretation.

The pH 7.4 preparation condition is a standardized physiological preparation policy, not a claim that every microscopic protonation state within the binding pocket is known with certainty.

---

## Ligand preparation

Ligands will be prepared using:

```text
Molscrub
pH 7.4
one protonation / tautomer state per molecule
```

followed by Meeko preparation for docking.

Each molecule receives exactly **one** prepared state during the initial Stage 5 protocol.

Multiple protonation or tautomer states will not be enumerated because doing so would give some molecules more opportunities than others to satisfy the gate.

For experimental positive controls, the prepared state must remain chemically consistent with the ligand identity in the crystallographic complex.

If the frozen preparation policy produces an obviously inappropriate state for a known positive, this is treated as a **preparation-protocol failure** and Stage 5 stops for review rather than manually repairing that molecule.

---

### Native-reader versus docking ligand preparation

The frozen ligand-preparation policy has two coordinate-handling paths because the two validation tasks ask different questions.

**Native interaction-reader proof of life**

For deposited experimental complexes, experimental heavy-atom geometry is part of the ground truth and must be preserved.

Molscrub 0.2.2 was empirically tested with `--ph 7.4 --skip_tautomers --skip_gen3d`. It correctly produced a single pH-7.4 chemical state but replaced the deposited 3D coordinates with a 2D depiction. Therefore, Molscrub coordinates are not trusted for native-reader validation.

For native reader controls:

1. RCSB CCD chemistry is combined with the deposited ligand coordinates.
2. Molscrub assigns one pH-7.4 state with tautomer enumeration disabled.
3. The prepared heavy-atom graph is mapped back to the validated native ligand graph.
4. Deposited heavy-atom coordinates are restored through that graph mapping.
5. Only hydrogen coordinates are generated afterward.
6. Heavy-atom coordinate preservation is asserted before ProLIF is run.

**Docking validation and common control-panel docking**

For Vina runs, initial ligand coordinates are not evidence because Vina regenerates the binding pose. Molscrub output coordinates therefore do not need restoration before docking, provided the frozen single-state chemistry assertions pass.

The same pH-7.4 state policy and tautomer restriction apply in both paths; only coordinate preservation differs.

Before ProLIF native-reader validation, each restored experimental ligand must also pass a geometric sanity check showing that its aromatic/core region remains in contact range of Phe168 and that a chemically eligible polar atom remains within hydrogen-bond distance of Asn253. This geometric check verifies preservation of the published pocket occupancy; ProLIF remains responsible for the subsequent interaction-type assignment.

### Native interaction-reader validation — COMPLETE

**Status: PASS (3/3)**

Before ProLIF was permitted to judge redocked, control-panel, or generated poses, the interaction-reader layer was tested against the untouched crystallographic poses of the three predeclared experimental A2A positive controls.

Results:

| PDB | Ligand | Phe168 | Asn253 | Result |
|---|---|---|---|---|
| 3REY | XAC | Hydrophobic, VdWContact | HBAcceptor, VdWContact | PASS |
| 5OLH | Vipadenant / 9XT | PiStacking, VdWContact | HBAcceptor, HBDonor, VdWContact | PASS |
| 5OLO | Tozadenant / 9XW | Hydrophobic, PiStacking, VdWContact | HBAcceptor, HBDonor, VdWContact | PASS |

ProLIF therefore recovered both predeclared A2A anchor residues in 3/3 experimentally determined positive complexes.

#### Native-reader preparation refinement

Validation exposed preparation behaviors that required deterministic handling before the reader could be trusted.

For native-reader controls, deposited receptor and ligand heavy-atom geometry is experimentally authoritative.

Receptor alternate locations are resolved before preparation by highest occupancy; occupancy ties prefer altloc A, followed by lexical order if required.

PDB2PQR 3.7.1 / PROPKA 3.5.1 at pH 7.4 supplies receptor protonation-state assignment and generated hydrogens. After preparation, every selected deposited receptor heavy atom is restored to its experimental coordinate. Hydrogens attached to a restored heavy atom are rigidly translated by the same vector as their parent so the PDB2PQR-generated local X-H geometry is retained.

PROPKA assigns protonation states on the pre-restoration geometry. The observed preparation-induced displacement was side-chain-scale, so state assignment is treated as unaffected.

Pre-restoration maximum deposited-heavy-atom displacement:

- 3REY: 0.000000 Å
- 5OLH: 0.000000 Å
- 5OLO: 1.354101 Å

Persisted post-restoration maximum displacement:

- 3REY: 0.000000 Å
- 5OLH: 0.000000 Å
- 5OLO: 0.000000 Å

The nontrivial 5OLO movement was localized to ASN284, including OD1 = 1.258351 Å and ND2 = 1.354101 Å.

His250 was ND1-protonated / NE2-unprotonated in all three receptors. PROPKA pKa values were 3.87 (3REY), 3.71 (5OLH), and 3.81 (5OLO).

Molscrub supplies ligand pH-7.4 state assignment but is not trusted for crystallographic coordinates in the native-reader proof-of-life path. Native ligand heavy-atom coordinates are restored by graph mapping after state assignment. This restoration requirement is specific to native-reader controls; docking regenerates ligand poses.

#### ProLIF adapter refinement

The validated restored receptor artifacts are not altered for ProLIF.

A temporary reader-only adapter:

- converts PDB2PQR fixed-column records to an MDAnalysis-compatible representation;
- maps genuine negative deposited residue numbers into a reserved positive range only for ProLIF (`GLY A -1 -> GLY A 10001`);
- explicitly verifies that Phe168 and Asn253 retain their biological numbering;
- removes geometrically inferred H-H bonds;
- resolves multiple inferred hydrogen parents only when exactly one same-residue heavy-atom parent exists;
- fails rather than guessing if hydrogen-parent assignment remains ambiguous.

After topology cleanup, every explicit receptor hydrogen had exactly one heavy-atom parent in all three positive controls.

Observed topology cleanup:

- 3REY: 0 H-H bonds; 0 false inter-residue H bonds
- 5OLH: 1 H-H bond; 0 false inter-residue H bonds
- 5OLO: 1 H-H bond; 1 false inter-residue H bond

The 5OLO false inter-residue inference connected ASN144 HD22 to PRO139 O at 1.421 Å; the chemically local ASN144 ND2 parent at 1.001 Å was retained.

These rules are universal adapter rules, not residue-specific exceptions.

### Validation state after reader proof of life

1. Native interaction-reader proof of life — **PASS, 3/3**
2. Cognate self-redocking — **PENDING**
3. Common-3RFM positive/negative control panel — **PENDING**
4. Gate-formulation ledger — **PENDING**
5. Final Stage 5 hard gate — **NOT FROZEN**
6. DiffSBDD 16-molecule Stage 5 baseline — **NOT YET PERMITTED**

No docking score, binding-energy score, interaction formulation, or generated-molecule result has been promoted to a Stage 5 hard gate.

## Search-box definition

Search boxes are defined from experimental ligand coordinates **before docking results are inspected**.

All boxes use:

```text
20 Å × 20 Å × 20 Å
```

### Native redocking validation

For each experimental positive:

```text
XAC        → 3REY
Vipadenant → 5OLH
Tozadenant → 5OLO
```

the search-box center is the centroid of that complex's crystallographic ligand.

The numerical XYZ center coordinates must be calculated once and recorded before the corresponding docking output is inspected.

The box center must not be adjusted after any failed or successful docking result.

### Common Stage 5 control experiment

After docking validation succeeds, the positive and negative control panel will be docked into one common receptor:

```text
3RFM
```

The common search-box center will be the centroid of crystallographic caffeine in 3RFM.

That center will likewise be calculated once before the control experiment and will not be adjusted after results are inspected.

The same common 3RFM receptor and search region will later be used wherever docking-derived Stage 5 characterization is applied consistently to generator outputs.

---

# Validation sequence

Stage 5 validation proceeds in a fixed order.

```text
1. Interaction-reader proof of life
        ↓
2. Docking-protocol proof of life
        ↓
3. Positive / negative control panel
        ↓
4. Candidate formulation ledger
        ↓
5. Freeze final Stage 5 gate
        ↓
6. Evaluate 16-molecule DiffSBDD baseline
        ↓
7. Later evaluate FLOWR under identical protocol
```

A later layer cannot compensate for failure of an earlier layer.

---

# Validation Layer 1 — Interaction-reader proof of life

The primary interaction reader will be:

```text
ProLIF
explicit-hydrogen workflow
```

PLIP may be retained as an independent diagnostic or sensitivity analysis, but ProLIF is the primary Stage 5 interaction-fingerprint candidate.

Before any redocking validation is performed, ProLIF must demonstrate that it can recover the published A2A recognition anchors from the **true deposited experimental poses**.

The native complexes are:

```text
3REY — XAC
5OLH — Vipadenant
5OLO — Tozadenant
```

The crystallographic ligand coordinates are preserved during this test.

The structures are prepared under the frozen Stage 5 preparation policy:

```text
protein:
PDB2PQR / PROPKA
pH 7.4
experimental protein heavy atoms preserved
His250 state recorded

ligand:
Molscrub
pH 7.4
one state
experimental ligand pose preserved

reader:
ProLIF
explicit hydrogens
```

For each complex, ProLIF must recover:

```text
Phe168
AND
Asn253
```

The interaction type must also be recorded rather than reducing the result to residue presence alone.

### Reader-validation ledger

| Complex | Ligand | Phe168 detected? | Phe168 interaction type(s) | Asn253 detected? | Asn253 interaction type(s) | Reader pass? |
| --- | --- | --- | --- | --- | --- | --- |
| 3REY | XAC | Pending | Pending | Pending | Pending | Pending |
| 5OLH | Vipadenant | Pending | Pending | Pending | Pending | Pending |
| 5OLO | Tozadenant | Pending | Pending | Pending | Pending | Pending |

Reader proof of life requires:

```text
3 / 3 native complexes
→ Phe168 recovered
→ Asn253 recovered
```

If ProLIF fails to recover either published core anchor from any correctly prepared native complex:

**STOP Stage 5.**

Do not proceed to redocking.

The failure must first be attributed to:

- protein preparation
- ligand preparation
- protonation
- hydrogen placement
- atom typing
- ProLIF interaction definitions
- or the interaction reader itself

The interaction definition must not be weakened merely to obtain a passing reader result.

---

# Validation Layer 2 — Docking-protocol proof of life

Only after the interaction reader passes 3/3 native complexes may the docking protocol be tested.

The experimental ligands will be removed from their deposited poses and independently self-redocked into their own cognate receptor structures:

```text
XAC        → 3REY
Vipadenant → 5OLH
Tozadenant → 5OLO
```

The experimental ligand pose is retained only as the validation reference.

It is not supplied to the docking search.

For each redocking experiment, up to 20 poses are retained.

### Redocking success criterion

A complex passes docking validation only if at least one retained pose satisfies:

```text
symmetry-aware heavy-atom RMSD
to crystallographic ligand pose
<= 2.0 Å

AND

Phe168 anchor recovered

AND

Asn253 anchor recovered
```

The validated ProLIF interaction reader is used for anchor recovery.

All three experimental positives must pass.

```text
3 / 3 pass
→ docking protocol earns permission
  to generate Stage 5 control poses

< 3 / 3 pass
→ STOP
→ docking protocol is not validated
```

A favorable Vina score cannot rescue a failed RMSD or interaction-recovery result.

---

## Redocking validation ledger

For each experimental complex, record:

- crystallographic box-center XYZ coordinates
- best symmetry-aware heavy-atom RMSD
- rank of the first successful pose within the retained 20-pose ensemble
- Phe168 recovery
- Asn253 recovery
- relevant interaction types
- Vina score of the successful pose, for description only
- final validation outcome

| Complex | Ligand | Best RMSD | First successful pose rank | Phe168 | Asn253 | Vina score | Validation |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| 3REY | XAC | Pending | Pending | Pending | Pending | Pending | Pending |
| 5OLH | Vipadenant | Pending | Pending | Pending | Pending | Pending | Pending |
| 5OLO | Tozadenant | Pending | Pending | Pending | Pending | Pending | Pending |

The rank of the successful pose is **not a pass/fail criterion**.

It is retained as a search-quality diagnostic.

For example:

```text
native-like solution at rank 1
→ strong pose-search / ranking behavior

native-like solution only near rank 20
→ protocol technically recovered the pose
→ weaker confidence that the same search
  will reliably identify useful poses for novel chemistry
```

---

# Validation Layer 3 — Common 3RFM control experiment

Only after the interaction reader and docking protocol both pass their complete validation requirements may the predeclared positive/negative panel be evaluated.

All controls are independently docked into:

```text
the same prepared 3RFM receptor
the same fixed 3RFM caffeine-centered search box
the same preparation policy
the same docking parameters
the same 20-pose allowance
the same interaction reader
```

Experimental positive poses are **not** supplied to the control experiment.

This removes the crystallographic-pose advantage and gives positive and negative controls the same opportunity to explore the 3RFM pocket.

For each control molecule, target-interaction evidence may be evaluated across the fixed retained pose ensemble.

A molecule's interaction evidence may be represented by its best qualifying interaction-recovery pose among the fixed 20 generated poses.

Vina score may determine the docking engine's search/output ordering but is not part of the Stage 5 gate.

---

# Candidate Stage 5 gate material

## Primary — target-specific interaction recovery

The primary candidate gate material is recovery of target-relevant A2A interactions.

Candidate formulations may include:

- recovery of one or more predeclared core anchor interactions
- recovery of Asn253 plus evidence of the Phe168/core-recognition region
- weighted recovery of the broader target interaction set
- residue + interaction-type fingerprint similarity to experimental A2A complexes
- consensus interaction recovery across multiple experimental target ligands

Interaction recovery should be represented at least at the:

```text
residue
+
interaction type
```

level.

Generic total-contact counts are insufficient.

For example:

```text
Asn253 — hydrogen bond recovered
```

is target-specific evidence.

By contrast:

```text
7 total hydrogen bonds
```

does not establish that the molecule is engaging target-relevant residues.

---

## Secondary — pose/contact geometry

Pose/contact geometry may provide secondary gate evidence.

Candidate measurements include:

- ligand occupancy within the intended binding region
- fraction of ligand atoms participating in protein contacts
- contact with predeclared binding-site residues
- distances to target anchor residues
- gross displacement from the experimentally defined orthosteric region

These measurements can identify poses that technically avoid steric clashes but fail to occupy or engage the intended binding site.

Generic contact count alone cannot substitute for target-specific interaction recovery.

---

# Characterization only — docking and binding-energy scores

Docking scores, empirical binding-energy scores, and fast rescoring functions are **characterization and ranking features only**.

They may be retained for:

- ranking Stage 5 survivors
- prioritization
- generator comparison
- sensitivity analysis
- descriptive characterization

They may never certify Stage 5 target compatibility.

A favorable docking score cannot compensate for failure to recover target-relevant interactions.

A less favorable docking score does not automatically invalidate an otherwise credible interaction pattern.

---

# Candidate formulation ledger

No exact Stage 5 Boolean gate is frozen yet.

Candidate formulations are tested only after:

```text
interaction reader passes 3/3 native complexes

AND

docking protocol passes 3/3 self-redocking tests
```

Every tested formulation must be recorded, including unsuccessful formulations.

For every candidate formulation, D007 will record the complete control outcome:

```text
Positive controls:
XAC
Vipadenant
Tozadenant

Negative controls:
Imatinib
Oseltamivir
Warfarin
Apixaban
Sildenafil
```

Example ledger structure:

| Formulation | XAC | Vipadenant | Tozadenant | Imatinib | Oseltamivir | Warfarin | Apixaban | Sildenafil | Eligible? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| B | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| C | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

A candidate formulation remains eligible for the hard gate only if it **cleanly separates the complete predeclared control panel**:

```text
all positive controls
→ pass

all negative controls
→ fail
```

A formulation that fails this requirement is retained in the methodology ledger as a rejected candidate rather than silently disappearing.

This record is required so that later methodology can defensibly state:

> The selected gate formulation was chosen because it separated predeclared known controls before generated molecules were inspected.

The formulation may not be selected based on DiffSBDD or FLOWR outcomes.

---

# Parameter-lock rule

The Stage 5 methodology is locked hierarchically.

### Reader lock

Once the first native-complex ProLIF validation is executed, the frozen preparation and interaction-reader configuration is locked.

Any change to:

- pH
- protonation procedure
- hydrogen handling
- ligand state handling
- ProLIF interaction definitions
- interaction distance criteria
- interaction angular criteria
- anchor interpretation

creates a **new named methodology candidate**.

The complete 3/3 native-reader validation must then restart and be recorded separately.

### Docking lock

Once the first docking-validation run is executed, all frozen docking parameters are locked.

A failed or successful redocking result cannot trigger an undocumented adjustment to:

- receptor preparation
- ligand preparation
- search-box center
- search-box dimensions
- exhaustiveness
- random seed
- pose count
- energy range
- receptor flexibility
- scoring function
- or pose-selection policy

Any proposed change creates a **new named docking-protocol candidate**.

The complete 3/3 self-redocking validation must then restart and be recorded separately.

### Control/gate lock

Once the common control experiment begins:

- positive controls are fixed
- negative controls are fixed
- the 3RFM receptor is fixed
- the search box is fixed
- preparation is fixed
- docking is fixed
- the interaction reader is fixed

Candidate gate formulations may only be evaluated through the predeclared formulation ledger.

No parameter may be altered in response to a failed or successful control merely to improve separation.

---

# Failure policy

If any validation layer fails, Stage 5 stops at that layer.

```text
Native reader failure
→ reader/preparation problem
→ do not dock

Native reader passes
but self-redocking fails
→ pose-generation problem
→ do not run control panel

Reader + redocking pass
but controls cannot be separated
→ gate formulation inadequate
→ do not evaluate generated molecules
```

Stage 5 must not respond to failure by:

- substituting docking score as the hard gate
- choosing a metric after inspecting generated molecules
- manually altering individual positive controls
- changing search boxes after seeing docking output
- giving different ligands different numbers of protonation states
- silently redocking or optimizing generated poses and treating them as generator output
- weakening the gate to obtain a desired survival rate

Any methodological revision must be explicit and must restart the affected validation layer.

---

# Relationship to generated poses

The primary Stage 5 target-compatibility evaluation remains conceptually focused on the **generator's existing pose**.

Docking is introduced here primarily to:

1. validate that the pose-generation protocol can reproduce known A2A binding modes;
2. place the positive and negative control panel fairly into one common receptor;
3. provide optional standardized pose-based characterization where explicitly defined.

Docking must not silently replace the generator's original coordinates when the Stage 5 hard gate is intended to evaluate generator pose quality.

Any later decision to apply redocking as a separate rescue, ranking, or standardized-binding-mode analysis must remain distinct from the primary generator-pose evaluation.

---

# Relationship to Stage 4

Stage 4 and Stage 5 provide complementary evidence.

```text
Stage 4B extrapolative
+
Stage 5 target-compatible
→ novel target chemistry with independent
  target-level corroboration

Stage 4B extrapolative
+
Stage 5 incompatible
→ unsupported target-space extrapolation

Stage 4B established
+
Stage 5 target-compatible
→ precedent-backed target chemistry

Stage 4B established
+
Stage 5 incompatible
→ 2D target-ligand similarity does not rescue
  an incompatible target pose
```

Stage 4 similarity therefore remains characterization rather than a binding proxy.

D006 remains in force: whenever Stage 4 similarity labels are reported in future result artifacts or summaries, the corresponding empirical null percentile must accompany the label.

---

# Current validation status

At the time this decision is written:

```text
Stage 5 protocol specification:
FROZEN PENDING VALIDATION

Interaction-reader proof of life:
PENDING

3/3 experimental self-redocking validation:
PENDING

Common positive/negative control panel:
PENDING

Candidate formulation ledger:
PENDING

Final Stage 5 hard gate:
NOT YET FROZEN

16-molecule DiffSBDD Stage 5 baseline:
NOT PERMITTED YET

FLOWR Stage 5 evaluation:
FUTURE — MUST USE IDENTICAL FINAL PROTOCOL
```

D007 remains stamped **PENDING VALIDATION** until:

1. ProLIF recovers Phe168 and Asn253 from all three prepared native experimental complexes;
2. all three experimental positives self-redock with at least one retained pose satisfying <=2.0 Å symmetry-aware heavy-atom RMSD plus Phe168 and Asn253 recovery;
3. the successful-pose rank and validation metrics are recorded for each self-redock;
4. the predeclared positive/negative control panel is evaluated under the common 3RFM protocol;
5. every tested gate formulation and its complete control outcomes are recorded;
6. a formulation cleanly separating all predeclared positives and negatives is identified.

Only then will the final Stage 5 hard gate be frozen and the 16-molecule DiffSBDD baseline become eligible for evaluation.

### Revisit when

- the interaction-reader proof-of-life test has been completed;
- the 3/3 self-redocking validation has been completed;
- the common 3RFM control panel has been evaluated;
- the formulation ledger is complete;
- no candidate formulation cleanly separates the controls;
- preparation or protonation policy requires revision;
- the docking protocol fails native-pose recovery;
- the interaction reader fails published-anchor recovery;
- Stage 5 is ready to be applied to DiffSBDD;
- Stage 5 is later applied to FLOWR;
- evidence supports changing the target-interaction definition or adding secondary characterization metrics.