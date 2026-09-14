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

## D007 --- Predeclare and validate Stage 5 target-compatibility methodology

**Original decision date:** 2026-08-16\
**Last amended:** 2026-08-19\
**Status:** PENDING FALLBACK VALIDATION

### Decision

Stage 5 evaluates **target compatibility**: whether a generated
molecule's existing 3D pose expresses a credible, target-specific
interaction pattern within the intended binding site.

Stage 5 is distinct from Stage 3B.

``` text
Stage 3B
"Is this pose physically plausible relative to the pocket?"
→ primarily tests protein-ligand steric compatibility

Stage 5
"Does this physically plausible pose make target-relevant interactions
consistent with credible recognition by the intended binding site?"
```

Passing Stage 3B is therefore necessary but not sufficient evidence of
target compatibility.

The primary Stage-5 evidence is **target-specific interaction
recovery**. Pose/contact geometry provides complementary evidence.

Docking scores, approximate binding energies, CNN scores, and other
rescoring functions may be retained for characterization and ranking,
but they may never independently certify target compatibility.

The final Stage-5 gate must be validated and frozen before DiffSBDD
Stage-5 outcomes are inspected.

------------------------------------------------------------------------

# Generator parity

DiffSBDD and FLOWR must be evaluated under the **same finalized Stage-5
protocol**.

This includes the same receptor preparation, ligand preparation,
protonation policy, interaction reader, target-interaction definitions,
pose-handling rules, control strategy, hard-gate formulation, and
characterization metrics.

Generator identity must not change Stage-5 methodology.

------------------------------------------------------------------------

# Stage-5 target-interaction definition

Target-relevant interactions are derived from experimentally determined
human A2A receptor-ligand complexes and are not selected from
generated-molecule outcomes.

  Ligand       ChEMBL ID       Experimental A2A complex
  ------------ --------------- --------------------------
  XAC          CHEMBL273094    PDB 3REY
  Vipadenant   CHEMBL447664    PDB 5OLH
  Tozadenant   CHEMBL2105747   PDB 5OLO

The crystallographic 3RFM caffeine ligand remains useful as a structural
and pocket reference but is not one of the formal positive controls.

## Core A2A recognition anchors

Experimental structural evidence supports a cross-chemotype recognition
core centered on:

-   **Phe168** --- aromatic/hydrophobic recognition of the ligand core.
-   **Asn253\^6.55** --- polar hydrogen-bond anchoring.

Supporting interactions may include Met177, Trp246, Leu249,
His250\^6.52, Thr256\^6.58 where chemotype-appropriate, Met270, and
Ile274.

Supporting contacts are not automatically mandatory individually. Stage
5 tests credible A2A recognition rather than exact reproduction of every
interaction made by one reference ligand.

------------------------------------------------------------------------

# Interaction recovery requires chemistry, not residue presence alone

A residue cannot be considered recovered merely because some interaction
with that residue is detected.

Interaction recovery must preserve at least:

``` text
residue identity
+
interaction class
+
hydrogen-bond donor/acceptor direction where applicable
```

For 3REY/XAC, the experimentally observed native patterns are:

``` text
Phe168:
Hydrophobic
+
VdWContact

Asn253:
HBAcceptor
+
VdWContact
```

For the Asn253 interaction, XAC supplies the hydrogen-bond acceptor. A
ligand pose making an `HBDonor` interaction with Asn253 therefore does
not reproduce the native XAC interaction merely because the same residue
is contacted.

This clarification corrected an under-implementation of the original
target-recognition criterion. It did not introduce a new post-result
scientific requirement.

------------------------------------------------------------------------

# Protein preparation

Protein structures are prepared using:

``` text
PDB2PQR
+
PROPKA
+
pH 7.4
```

Experimental receptor heavy-atom coordinates are authoritative for
native structural validation and are not geometry-minimized before
Stage-5 native-reader evaluation.

His250\^6.52 protonation is explicitly recorded because it participates
in the A2A recognition environment.

The pH-7.4 condition is a standardized physiological preparation policy,
not a claim that every microscopic protonation state within the binding
pocket is known with certainty.

------------------------------------------------------------------------

# Ligand preparation

Ligands are prepared using:

``` text
Molscrub
pH 7.4
one protonation / tautomer state per molecule
```

followed by the appropriate downstream preparation.

Each molecule receives one prepared state under the initial Stage-5
protocol. This prevents some molecules from receiving additional
opportunities to pass merely because more protonation or tautomer states
were enumerated.

------------------------------------------------------------------------

# Native-reader coordinate-preservation rule

Native experimental complexes require special handling because deposited
ligand coordinates are part of the experimental ground truth.

Molscrub 0.2.2 was tested with:

``` text
--ph 7.4
--skip_tautomers
--skip_gen3d
```

It successfully assigned a single pH-7.4 chemical state but did not
preserve deposited crystallographic 3D coordinates. For XAC, the
displacement was sufficiently large to destroy the native binding pose.

Molscrub coordinates are therefore not trusted for native-reader
validation.

For native controls:

1.  deposited ligand heavy-atom coordinates provide the experimental
    geometry;
2.  Molscrub assigns the standardized pH-7.4 chemical state;
3.  the prepared heavy-atom graph is mapped back to the validated native
    ligand graph;
4.  deposited heavy-atom coordinates are restored through that mapping;
5.  hydrogen coordinates are generated afterward;
6.  heavy-atom coordinate preservation is asserted before interaction
    analysis.

This separates standardized chemical state from experimental geometry.

------------------------------------------------------------------------

# Native receptor restoration and reader adapter

Native receptor preparation similarly preserves deposited heavy-atom
geometry.

Receptor alternate locations are resolved before preparation by highest
occupancy, then altloc A on occupancy ties, then lexical order if a
further deterministic tie-break is required.

PDB2PQR 3.7.1 / PROPKA 3.5.1 at pH 7.4 supplies receptor
protonation-state assignment and generated hydrogens. After preparation,
selected deposited receptor heavy atoms are restored to their
experimental coordinates. Hydrogens attached to restored heavy atoms are
translated by the same vector as their parent atom.

Observed pre-restoration maximum deposited-heavy-atom displacement:

``` text
3REY: 0.000000 Å
5OLH: 0.000000 Å
5OLO: 1.354101 Å
```

Persisted post-restoration maximum displacement:

``` text
3REY: 0.000000 Å
5OLH: 0.000000 Å
5OLO: 0.000000 Å
```

The nontrivial 5OLO movement was localized to ASN284.

His250 was ND1-protonated / NE2-unprotonated in all three native
receptor controls. PROPKA pKa values were 3.87 for 3REY, 3.71 for 5OLH,
and 3.81 for 5OLO.

A temporary reader-only adapter handles representation issues without
modifying the validated receptor artifacts. It converts PDB2PQR records
to an MDAnalysis-compatible representation, handles genuine negative
residue numbers only for ProLIF, verifies Phe168 and Asn253 numbering,
removes inferred H-H bonds, resolves hydrogen-parent ambiguity only
under deterministic same-residue rules, and fails rather than guessing
if ambiguity remains.

These are universal adapter rules rather than residue-specific
exceptions.

------------------------------------------------------------------------

# Validation Layer 1 --- Interaction-reader proof of life

The primary Stage-5 interaction reader is:

``` text
ProLIF
explicit-hydrogen workflow
```

Before ProLIF could judge docked or generated poses, it had to recover
the experimentally established A2A recognition anchors from true
deposited experimental poses.

  --------------------------------------------------------------------------
  PDB            Ligand         Phe168         Asn253         Result
  -------------- -------------- -------------- -------------- --------------
  3REY           XAC            Hydrophobic;   HBAcceptor;    **PASS**
                                VdWContact     VdWContact     

  5OLH           Vipadenant     PiStacking;    HBAcceptor;    **PASS**
                                VdWContact     HBDonor;       
                                               VdWContact     

  5OLO           Tozadenant     Hydrophobic;   HBAcceptor;    **PASS**
                                PiStacking;    HBDonor;       
                                VdWContact     VdWContact     
  --------------------------------------------------------------------------

``` text
Native interaction-reader proof of life:
3 / 3 PASS
```

Layer 1 is complete.

------------------------------------------------------------------------

# Original Validation Layer 2 --- Independent docking proof of life

Layer 2 asked whether docking could independently reproduce
experimentally known A2A binding modes.

``` text
XAC        → 3REY
Vipadenant → 5OLH
Tozadenant → 5OLO
```

The crystallographic ligand pose was retained only as the validation
reference.

Because this is cognate self-redocking, each receptor was crystallized
with the same ligand and therefore already begins in an experimentally
observed ligand-compatible conformation.

A complex passes only if at least one retained pose satisfies:

``` text
symmetry-aware heavy-atom RMSD <= 2.0 Å
AND
Phe168 native interaction pattern
AND
Asn253 native interaction pattern
```

The same pose must satisfy all requirements. A favorable docking score
cannot rescue a failed RMSD or interaction criterion.

Search boxes are 20 Å × 20 Å × 20 Å and centered on the corresponding
crystallographic ligand centroid. Frozen parameters cannot be changed
silently after results are observed.

------------------------------------------------------------------------

# Candidate 1 --- AutoDock Vina

Candidate 1 used AutoDock Vina 1.2.7 with Vina scoring, a rigid
receptor, exhaustiveness 32, seed 20260816, maximum 20 retained poses, a
5 kcal/mol energy range, and the frozen 20 Å search box.

Candidate 1 produced a globally near-native XAC pose:

``` text
RMSD:
1.826 Å
```

However, that pose did not reproduce the native Phe168 or Asn253
interaction patterns.

Diagnostic geometry showed:

``` text
crystal XAC carbonyl → Asn253 ND2:
2.868 Å

Candidate-1 pose 7:
4.180 Å
```

Candidate 1 therefore demonstrated that RMSD alone is insufficient for
Stage-5 target compatibility.

**Verdict: PERMANENT FAIL.**

5OLH and 5OLO were not run.

------------------------------------------------------------------------

# Candidate 2 --- AM1-BCC ligand charges

Candidate 2 proposed replacing the default ligand partial charges with
AM1-BCC charges.

AmberTools / Antechamber successfully produced the XAC charge vector:

``` text
formal charge: +1
SQM total Mulliken charge: +1.000
serialized AM1-BCC charge sum: +0.995998 e
```

No post-hoc normalization was applied.

Before docking, the Vina scoring implementation was audited. The audit
established that Candidate-1 Vina scoring does not use user-supplied
ligand partial charges.

The proposed intervention therefore could not alter the Vina scoring
landscape.

**Verdict: ELIMINATED BEFORE EXECUTION.**

``` text
Candidate-2 docking runs:
0
```

Candidate 2 did not fail experimentally.

------------------------------------------------------------------------

# Candidate 3 --- smina / Vinardo

Candidate 3 changed the executable/scoring stack to smina with Vinardo
scoring while preserving the remaining frozen Layer-2 protocol.

Result:

``` text
retained poses:
19

best crystal-reference RMSD:
4.642 Å

Phe168 native chemistry:
recovered in many poses

Asn253 native XAC acceptor chemistry:
0 / 19 poses
```

No retained pose satisfied the complete Layer-2 criterion.

**Verdict: PERMANENT FAIL.**

5OLH and 5OLO were not run.

------------------------------------------------------------------------

# Candidate 4 --- GNINA CNN rescoring

Candidate 4 tested whether a learned pose-ranking model could improve
recognition of a native-like binding mode while leaving the receptor
rigid.

``` text
GNINA:
v1.3.3
master:6fe1ce2

CNN:
all_default_to_default_1_3_3

CNN mode:
--cnn_scoring rescore

Pose ordering:
--pose_sort_order CNNscore

CNN refinement:
disabled
```

The first attempted invocation included Vina's `--energy_range 5`. GNINA
rejected this during command-line parsing. No docking occurred during
that invocation.

GNINA v1.3.3 has no native hidden/config equivalent. The frozen 5
kcal/mol retention rule was therefore implemented after generation
using:

``` text
REMARK minimizedAffinity <float>

best_empirical =
minimum minimizedAffinity

eligible iff:
minimizedAffinity <= best_empirical + 5.0 kcal/mol
```

The maximum remained 20 poses.

## Candidate-4 execution

The corrected Candidate-4 experiment was executed once on 3REY/XAC.

``` text
generated poses:
20

eligible poses:
20 / 20

best empirical minimizedAffinity:
-7.304 kcal/mol

best crystal-reference RMSD:
1.678 Å
(rank 13)
```

Rank 13:

``` text
Phe168 native pattern:
NO

Asn253 native pattern:
NO

complete Layer-2 pass:
NO
```

GNINA recovered native Asn253 chemistry in rank 3:

``` text
RMSD:
8.592 Å

Asn253:
HBAcceptor + VdWContact

Phe168:
Hydrophobic only

complete Layer-2 pass:
NO
```

No pose satisfied the complete criterion.

**Verdict: PERMANENT FAIL.**

------------------------------------------------------------------------

# Cross-candidate conclusion

  -----------------------------------------------------------------------
  Candidate         Main lever        Status            3REY/XAC
  ----------------- ----------------- ----------------- -----------------
  Candidate 1       Vina scoring      **FAIL**          Best RMSD 1.826
                                                        Å; native anchor
                                                        chemistry absent

  Candidate 2       AM1-BCC charges   **ELIMINATED**    Proposed
                                                        intervention
                                                        cannot affect
                                                        Vina scoring; 0
                                                        runs

  Candidate 3       Vinardo scoring   **FAIL**          Best RMSD 4.642
                                                        Å; native Asn253
                                                        absent from all
                                                        19 poses

  Candidate 4       GNINA CNN rescore **FAIL**          Best RMSD 1.678
                                                        Å; no pose
                                                        satisfied
                                                        geometry plus
                                                        both anchors
  -----------------------------------------------------------------------

Two different approaches produced geometrically near-native poses while
failing the experimentally required local interaction chemistry.

Therefore:

> **RMSD and docking scores alone are not sufficient evidence of correct
> A2A target recognition under this harness.**

------------------------------------------------------------------------

# Candidate 5 --- limited receptor flexibility

Limited receptor side-chain flexibility was considered after Candidate
4.

The question is scientifically interesting because real protein side
chains can move while Candidates 1--4 kept the receptor rigid.

However, cognate self-redocking already begins from a receptor
crystallized with the same ligand, so the receptor is already presented
in an observed ligand-compatible conformation.

A rigorous flexible-receptor experiment would introduce a larger
methodological question: which residues should move, how should they be
selected without tailoring the method to the observed Asn253 failure,
how much flexibility should be allowed, whether additional flexibility
improves recovery or merely enlarges the search space, and whether any
benefit generalizes beyond A2A.

Answering these questions rigorously would turn this small Stage-5
validation arm into a separate docking-methodology study.

``` text
Candidate 5:
CONSIDERED
NOT SELECTED
NOT EXECUTED
```

The broader rigid-versus-flexible receptor question is reserved for
future work.

------------------------------------------------------------------------

# Docking-validation arm conclusion

The independent docking-validation arm is closed.

``` text
Candidate 1 — Vina:
PERMANENT FAIL

Candidate 2 — AM1-BCC:
ELIMINATED BEFORE EXECUTION

Candidate 3 — Vinardo:
PERMANENT FAIL

Candidate 4 — GNINA CNN:
PERMANENT FAIL

Candidate 5 — receptor flexibility:
CONSIDERED, NOT SELECTED
```

This is a **documented negative result for the docking-validation arm**.

It is not a failure of DiffSBDD.

DiffSBDD already supplies a ligand and its 3D pocket pose. Docking was
being tested as an additional independent source of pose corroboration.
Because docking failed its known-answer controls, it has not earned
permission to serve that role.

------------------------------------------------------------------------

# Reference-pose fallback

Stage 5 therefore transitions to the **reference-pose fallback
pathway**.

The fallback separates two questions:

``` text
Question A:
Can an independent docking method recover the correct pose?

Question B:
Given a physically plausible pose, does it contain
experimentally grounded A2A recognition chemistry?
```

Layer 2 failed Question A.

Layer 1 demonstrated that the interaction reader can address Question B
on known experimental structures.

The fallback therefore evaluates target compatibility **conditional on
the generator-provided pose**.

``` text
generator-provided pose
        ↓
Stage 3 physical-plausibility survival
        ↓
validated target-specific interaction analysis
        ↓
conditional target-compatibility evidence
```

The generator pose is not accepted blindly. It has already survived
Stage-3 physical-plausibility checks before Stage-5 target-interaction
analysis.

## What a fallback PASS means

A future fallback PASS may support:

> The generator-provided pose is physically plausible under the
> validated Stage-3 criteria and reproduces the experimentally grounded
> A2A recognition chemistry required by the finalized fallback gate.

It may not be interpreted as:

-   independent docking confirmation;
-   experimental binding confirmation;
-   proof that the pose is uniquely correct;
-   proof that the pose is thermodynamically preferred.

------------------------------------------------------------------------

# Fallback validation requirements

Before any DiffSBDD Stage-5 outcome is inspected, the fallback must
specify and validate:

1.  exact target-interaction features;
2.  how experimental reference poses define them;
3.  how generator-provided coordinates are evaluated without
    replacement;
4.  the required control/validation evidence;
5.  the Boolean fallback PASS/FAIL criterion;
6.  what claims the fallback supports;
7.  what claims remain prohibited because docking validation failed.

The fallback must remain generator-independent.

DiffSBDD and FLOWR must later use the same finalized fallback.

------------------------------------------------------------------------

# Original Layer-3 control panel

The original docking-dependent Layer-3 experiment is now **BLOCKED**.

The original positive controls were XAC, Vipadenant, and Tozadenant.

The original unrelated-target negative controls were Imatinib,
Oseltamivir, Warfarin, Apixaban, and Sildenafil. These negatives are not
claimed to be experimentally proven A2A nonbinders.

The original Layer-3 design cannot proceed as written because it depends
on an independently validated docking protocol to produce standardized
control poses.

A fallback-specific control strategy must instead be developed without
pretending that the failed docking arm has been validated.

------------------------------------------------------------------------

# Stage-4 relationship

Stage 4 and Stage 5 remain complementary.

``` text
Stage 4B extrapolative
+
Stage 5 target-compatible
→ novel target chemistry with target-level evidence

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
  an incompatible generator pose
```

Stage 4 remains characterization rather than a binding gate.

D006 remains in force: Stage-4 labels must be reported with the
associated empirical null percentile.

------------------------------------------------------------------------

# Current validation status

As of 2026-08-19:

  -----------------------------------------------------------------------
  Stage-5 component                   Status
  ----------------------------------- -----------------------------------
  Native interaction-reader proof of  **PASS --- 3/3**
  life                                

  Candidate 1 --- Vina                **PERMANENT FAIL**

  Candidate 2 --- AM1-BCC             **ELIMINATED BEFORE EXECUTION --- 0
                                      RUNS**

  Candidate 3 --- smina / Vinardo     **PERMANENT FAIL**

  Candidate 4 --- GNINA CNN rescore   **PERMANENT FAIL**

  Candidate 5 --- limited receptor    **CONSIDERED, NOT SELECTED**
  flexibility                         

  Independent docking-validation arm  **CLOSED --- DOCUMENTED NEGATIVE
                                      RESULT**

  Original docking-dependent Layer 3  **BLOCKED**

  Reference-pose fallback             **REQUIRES DEFINITION AND
                                      VALIDATION**

  Final Stage-5 gate                  **NOT YET FROZEN**

  DiffSBDD Stage-5 baseline           **NOT YET PERMITTED**

  FLOWR Stage-5 evaluation            **FUTURE --- MUST USE THE IDENTICAL
                                      FINALIZED STAGE-5 PATHWAY**
  -----------------------------------------------------------------------

D007 remains **PENDING FALLBACK VALIDATION**.

The interaction reader is validated.

The independent docking arm has completed validation and failed.

The remaining methodological work is to define and validate the
reference-pose fallback without inspecting DiffSBDD Stage-5 outcomes.

Only after that fallback is defined, validated, and frozen may the
16-molecule DiffSBDD Stage-5 baseline be evaluated.

### Revisit when

-   the reference-pose fallback has been formally defined;
-   fallback validation and controls have been completed;
-   the fallback Stage-5 gate is ready to freeze;
-   Stage 5 is ready for DiffSBDD;
-   Stage 5 is later applied to FLOWR;
-   evidence supports revising the target-interaction definition;
-   future work formally reopens rigid-versus-flexible receptor docking.

## D008 — Stage 5 target–ligand interaction evidence framework

**Decision date:** 2026-08-20  
**Status:** ACTIVE

### Decision

Stage 5 is defined as the **target–ligand interaction evidence layer** of the generator-agnostic evaluation cascade.

Stage 5 is **method-generalized but target-specific in implementation**.

The generalized framework determines:

1. whether Stage 5 is structurally in scope;
2. the target's interaction-evidence level;
3. what claims that evidence level permits;
4. whether a target-specific compatibility gate may be attempted;
5. how that gate must be validated;
6. whether hard attrition is permitted;
7. how unresolved interaction evidence propagates through downstream reporting.

The biological interaction definition itself is target-specific.

A gate validated for one target earns no authority on another target.

---

### Scope

A target with no available three-dimensional structure is out of scope for Stage 5.

A structurally defined target may be assigned one of three canonical interaction-evidence levels:

Level 1 - sufficient for validated compatibility testing  
Level 2 - sufficient for interaction characterization  
Level 3 - insufficient for target-compatibility assessment

These levels describe the available **target–ligand interaction evidence**.

They do not describe how well studied, biologically important, therapeutically relevant, or druggable the target is overall.

---

### Evidence sufficiency

#### Level 1

Requires an experimental complex containing the target and a cognate ligand.

Level 1 provides sufficient evidence to define and attempt validation of a target-specific compatibility gate.

Level 1 does not automatically authorize attrition.

#### Level 2

Applies when direct cognate target–ligand structural evidence is unavailable but interaction characterization is supportable from an apo target structure or ligand-bound homolog.

Homolog evidence is admissible only when the binding site itself is demonstrably conserved.

Pocket sequence identity and pocket-superposition RMSD must be documented.

Overall fold homology does not suffice when pocket residues materially differ.

Level-2 outputs are characterization only and are labeled **homology-inferred** when homolog evidence is used.

#### Level 3

Applies to a well-defined target structure for which insufficient target–ligand interaction evidence exists anywhere in the relevant family.

Level 3 is strictly an evidence-absence verdict.

It does not imply that the target, pocket, or potential binding interaction does not exist.

Target compatibility is **INCONCLUSIVE**.

---

### Gate-validation layer

Target evidence and gate validity are separate questions.

A hard target-compatibility claim requires both:

1. sufficient target–ligand evidence; and
2. a validated target-specific implementation.

Validation criteria must be predeclared before validation outcomes are inspected.

Validation is specific to both the **implementation and target**.

A gate validated on one target does not transfer hard-claim authority to another target.

Known cognate positive controls establish **sensitivity only**.

Hard attrition additionally requires established discrimination using **plausible-but-wrong negative poses**.

Negative controls are pose conditions, not molecule conditions.

A synthetic negative that fails physical plausibility does not test Stage-5 discrimination because the pose is already invalid at the geometry layer.

Gate-validation outcomes are recorded as:

- **ESTABLISHED**
- **NOT ESTABLISHED**

They are not recorded as target, evidence-level, or molecule failures.

When validation is not established, the target retains its evidence level but receives:

**CLAIMS CAPPED PENDING GATE VALIDATION**

The cap may later be lifted without regenerating molecules if the gate validates and the original generator-provided poses and characterization outputs remain available.

Under a capped gate, outputs are reported as pattern reproduction rather than Stage-5 PASS/FAIL.

---

### Level-3 fork

Level 3 does not terminate molecule evaluation.

It produces two parallel outputs: a **VERDICT arm** and a **LANE arm**.

#### VERDICT arm

The target record receives an explicit interaction-evidence gap.

Target compatibility is:

**INCONCLUSIVE**

No target-specific feasibility claim may be produced.

Absence of interaction evidence must not be converted into either compatibility or incompatibility.

#### LANE arm

Molecules are not failed because their target is Level 3.

They remain eligible for every evaluation whose claims do not require established target–ligand interaction evidence.

The sole target-side analysis permitted under the Level-3 lane is **predicted-pocket characterization**.

An established pocket-prediction method such as P2Rank or fpocket may be used to:

- nominate one or more candidate binding sites;
- characterize predicted pocket geometry;
- record pocket location and associated prediction outputs;
- provide predicted-pocket coordinates as the pocket artifact for Stage 3B.

Every such site must be labeled:

**PREDICTED POCKET**

and never presented as an experimentally observed target–ligand binding site.

A predicted pocket does not:

- establish a target-recognition pattern;
- establish target compatibility;
- upgrade the target's evidence level;
- authorize a Stage-5 interaction gate.

Stage 3B may evaluate whether a generator-provided pose is physically plausible relative to the predicted pocket, but that result remains geometry-only.

All molecules proceeding through this lane carry:

**INTERACTION-UNVERIFIED**

through every downstream stage and aggregate claim until qualifying target–ligand evidence becomes available.

The Level-3 VERDICT and LANE therefore coexist:

the VERDICT records what cannot be claimed, while the LANE preserves scientifically valid evaluation that does not depend on the missing interaction evidence.
---

### Stage-3 separation

Stage 3 and Stage 5 remain distinct.

Stage 3 evaluates physical and geometric plausibility.

Stage 5 evaluates target–ligand interaction evidence.

A Level-3 predicted pocket may be supplied to Stage 3B as its pocket artifact, but Stage-3 outputs remain geometry-only.

Physical plausibility cannot substitute for Stage-5 interaction evidence.

---

### Level reassignment

Evidence levels are reassessed during each session's evidence pull.

Relevant new evidence includes:

- new PDB depositions;
- new ChEMBL activity records;
- newly identified cognate ligands;
- newly available homolog complexes.

Targets upgrade when new evidence satisfies a higher level.

Levels never downgrade silently.

Any downgrade requires a documented reason.

Evidence-level reassignment and gate validation remain separate processes.

---

### A2A implementation

A2A is assigned:

**Target–ligand interaction evidence: LEVEL 1**

The A2A reference-recognition definition was derived from the native experimental complexes:

- 3REY / XAC;
- 5OLH / Vipadenant;
- 5OLO / Tozadenant.

The frozen characterization definition is:

**Phe168:** Hydrophobic OR PiStacking

AND

**Asn253:** ligand HBAcceptor

This represents conserved recognition roles rather than the exact interaction fingerprint of any single cognate ligand.

VdWContact is retained as characterization output but is not required by the reference pattern.

---

### A2A gate-validation status

Native experimental interaction-reader controls:

**3/3 POSITIVE RECOVERY**

Independent docking-validation arm:

**CLOSED — DOCUMENTED NEGATIVE RESULT**

Rigid-rotation plausible-negative study:

- axis-1 / 10°: Stage 3B plausible 3/3; native recognition retained 3/3;
- axis-1 / 15°: Stage 3B plausible 3/3; native recognition retained 3/3;
- axis-1 / 20°: 5OLO became physically invalid before a universal interaction-disrupted control was established.

The rigid-rotation negative-control strategy is therefore:

**NOT ADOPTED**

A2A hard-gate discrimination is:

**NOT ESTABLISHED**

Therefore:

**CLAIMS CAPPED PENDING GATE VALIDATION**

A2A remains Level 1.

It is not demoted because implementation validation remains incomplete.

---

### 3RFM implementation proof of life

The DiffSBDD baseline was generated in the 3RFM coordinate frame.

An interaction-ready 3RFM receptor was therefore prepared at pH 7.4 using the validated receptor-preparation pathway while preserving the original heavy-atom coordinate frame.

Preparation audits confirmed:

- Phe168 and Asn253 numbering;
- explicit receptor hydrogens;
- zero displacement of original heavy atoms after restoration.

The independent native 3RFM / caffeine complex was then evaluated using the same ProLIF interaction pathway and frozen A2A definition.

Observed native 3RFM interactions included:

- Phe168: PiStacking and VdWContact;
- Asn253: HBAcceptor and VdWContact.

The frozen A2A reference-recognition pattern was reproduced.

This establishes a same-coordinate-frame positive proof of life for the DiffSBDD Stage-5 characterization implementation.

It does not establish plausible-negative discrimination.

---

### DiffSBDD Stage-5 baseline

The 16 Stage-3-surviving DiffSBDD molecules were evaluated using:

- their original molecule IDs;
- their unmodified generator-provided coordinates;
- the interaction-ready 3RFM receptor;
- the validated ProLIF reader;
- the frozen A2A reference-recognition definition.

Results:

- Phe168 reference feature reproduced: **15/16**
- Asn253 reference feature reproduced: **4/16**
- complete A2A reference pattern reproduced: **3/16**

The three complete-pattern reproductions were molecule IDs:

- 0
- 3
- 18

These results are **characterization**, not attrition.

The permitted statement is:

**3/16 generator-provided DiffSBDD poses reproduced the predeclared A2A reference-recognition pattern.**

The prohibited statement is:

**3/16 passed Stage 5.**

No molecule is removed from the baseline on the basis of the current Stage-5 characterization.

---

### Generator parity

Stage 5 remains generator-independent.

FLOWR must later be evaluated using the same frozen:

- target evidence assignment procedure;
- A2A reference-recognition definition;
- interaction-ready target representation;
- ProLIF interaction-reading pathway;
- claims-cap status;
- reporting language.

The A2A definition must not be recalibrated using DiffSBDD or FLOWR outcomes.

---

### Governing principle

**The verdict keeps the science honest, the lane keeps the pipeline fair.**

### Revisit when

- a defensible A2A plausible-but-wrong negative control becomes available;
- A2A hard-gate discrimination is independently established;
- new target–ligand evidence changes the A2A evidence package;
- Stage 5 is applied to FLOWR;
- Stage 5 is instantiated for a new target;
- future work formally reopens independent docking or receptor-flexibility validation.

## D009 — Qualify the DOCK lineage for Stage-5 adversarial-pose generation and retain Vina as the production default

**Decision date:** 2026-08-27  
**Status:** ACTIVE

### Decision

The Shoichet/Kuntz **DOCK lineage is qualified for its planned Stage-5 role as an independent adversarial-pose source** in the A2A ProLIF proof-of-discrimination program.

This qualification is based on successful cognate self-redocking of the 3REY/XAC system.

Under the frozen DOCK search and strain settings, the qualified canonical XAC DB2 produced three retained poses. All three were native-like relative to the deposited 3REY XAC pose:

```text
Rank 1:
heavy-atom RMSD = 0.592 Å

Rank 2:
heavy-atom RMSD = 0.563 Å

Rank 3:
heavy-atom RMSD = 0.560 Å
```

These are direct receptor-frame RMSDs without post-hoc ligand superposition.

Therefore:

**DOCK A2A implementation proof of life: ESTABLISHED**

This qualification establishes that the implemented DOCK search can access the experimental XAC binding basin in the 3REY A2A system.

It does not establish that every DOCK-generated alternative pose is an eligible Stage-5 negative.

Negative eligibility remains governed by the frozen P1–P4 doctrine established for Stage-5 gate validation.

---

### Amendment to the earlier docking-validation conclusion

D007 recorded the original independent docking-validation arm as:

**CLOSED — DOCUMENTED NEGATIVE RESULT**

That conclusion remains historically accurate for the docking implementations tested prospectively at that time:

- AutoDock Vina;
- AM1-BCC intervention;
- smina / Vinardo;
- GNINA CNN rescoring;
- considered but unexecuted limited receptor flexibility.

However, Session 009 subsequently established that an independent docking implementation can recover the 3REY/XAC experimental binding mode when the DOCK lineage is correctly prepared and qualified.

The earlier zero-pose DOCK diagnostic result must not be interpreted as evidence that DOCK itself could not recover XAC.

Its root cause was invalid ligand DB2 strain metadata:

```text
total strain = +9999.990
max strain   = +9999.990
```

against the frozen DOCK thresholds:

```text
total_strain = 8
max_strain   = 3
```

DOCK therefore rejected the handcrafted ligand set through its strain bookkeeping before a viable pose could be retained.

The canonical strain calculation subsequently produced:

```text
total strain = 6.180
max strain   = 2.910
```

which passes the unchanged frozen thresholds.

Accordingly, the current methodological record is:

> **The original Vina/Vinardo/GNINA docking-validation experiment remains a documented negative result, but independent docking as a methodological concept is no longer considered globally unqualified. The separately implemented and prospectively qualified DOCK lineage has established system-specific proof of life for 3REY/XAC.**

D007 is not rewritten retrospectively. D009 records the later evidence that changes the current interpretation.

---

### Qualified XAC lineage

The qualified DOCK proof-of-life control uses the canonical XAC reconstruction derived from the wwPDB Chemical Component Dictionary and reconciled to the deposited 3REY ligand coordinates.

The qualified species is:

```text
formula: C21H28N6O4
formal/system charge: 0
heavy atoms: 31
hydrogens: 28
total atoms: 59
bonds: 61
```

The qualified preparation lineage is:

```text
wwPDB XAC CCD
→ deposited 3REY coordinates
→ RDKit reconstruction
→ SDF
→ Antechamber SYBYL typing
→ AMSOL
→ canonical torsional strain
→ mol2db2_py3_strain
→ audited DB2
→ DOCK
```

Coordinate preservation through the final DB2 was:

```text
all-atom RMSD:   0.000000 Å
heavy-atom RMSD: 0.000000 Å
maximum delta:   0.000000 Å
```

The earlier proposed +1 / 60-atom XAC reconstruction is superseded for this qualification record and must not be presented as the lineage that produced the successful DOCK proof of life.

---

### Production docking-backend policy

**AutoDock Vina remains the production pose-generation default for the upcoming ProLIF proof-of-discrimination cycle.**

DOCK is not promoted to the production default on the basis of the single 3REY/XAC qualification result.

The reasons are methodological:

1. the ProLIF validation cycle should not change its production pose generator in response to a newly obtained control result;
2. Vina remains operationally simpler for routine generated-molecule pose generation;
3. DOCK currently provides valuable methodological independence as an adversarial-pose lineage;
4. one successful DOCK cognate-redocking case is insufficient to establish comparative superiority.

The current roles are therefore:

```text
Vina:
production pose-generation default

DOCK:
qualified independent adversarial-pose lineage
and candidate future docking backend

ProLIF:
frozen primary interaction reader

PLIP / qualified equivalent:
post-validation independent interaction witness
```

These roles remain logically separate.

---

### Docking-backend independence

The evaluation architecture remains docking-engine agnostic.

Docking implementations must communicate with downstream evaluation through stable molecular and pose artifacts rather than implementation-specific internals.

A docking backend earns authority through explicit qualification in its intended role.

Successful qualification of one backend does not permanently privilege that backend, and qualification on one target does not establish universal docking performance.

The same implementation-agnostic principle applies to:

- molecular generators;
- docking engines;
- interaction readers and fingerprinters;
- independent witnesses.

One qualified default may occupy each production slot while alternative implementations remain swappable behind the corresponding interface.

---

### Future Vina-versus-DOCK robustness benchmark

A matched Vina-versus-DOCK experiment is reserved for post-ProLIF-validation robustness analysis.

The benchmark will use:

- the same receptors;
- the same experimental ligands;
- the same crystallographic references.

At minimum it will compare:

- best-pose heavy-atom RMSD;
- top-ranked-pose heavy-atom RMSD;
- success rate at RMSD <= 2.0 Å;
- docking failure rate;
- pose diversity;
- runtime and operational cost.

The primary methodological question is not:

> “Which docking engine wins?”

The primary question is:

> **“Is the downstream ProLIF interaction evidence materially sensitive to the pose-generation engine?”**

Concordant Vina and DOCK conclusions strengthen the robustness of the interaction evidence.

Discordant conclusions identify pose-generator dependence that must be reported and characterized.

Only after this matched benchmark exists may evidence support reconsidering DOCK for promotion to the primary production docking backend.

No comparative claim that DOCK is superior to Vina, or Vina superior to DOCK, is currently authorized.

---

### Relationship to ProLIF proof-of-discrimination

DOCK qualification does not itself establish ProLIF discrimination.

Its purpose is to qualify one independent source of physically plausible adversarial pose candidates.

A DOCK-generated pose enters the primary ProLIF validation panel only if it independently satisfies the frozen negative-eligibility doctrine:

```text
P1 — physically admissible

P2 — genuinely alternative, with a near-native solution
     demonstrated in the same search

P3 — negative status not attributable solely to the
     generating model

P4 — preferred adversarial strengthening when the
     alternative is ranked/scored at or above the
     sampled near-native solution
```

The successful XAC self-redocking provides direct evidence that the qualified DOCK implementation can access the native binding basin in this system.

This strengthens the same-search native-sampling requirement underlying P2 but does not itself establish P2 for any future negative candidate.

ProLIF output remains forbidden from determining negative-panel membership.

---

### Limitations

The present DOCK qualification rests on one highly controlled cognate-redocking case:

```text
3REY / XAC
```

The result is strong within that system:

```text
3 / 3 retained poses native-like
best direct-frame heavy-atom RMSD = 0.560 Å
```

but it does not establish performance across:

- additional A2A chemotypes;
- other targets;
- arbitrary generated molecules;
- alternative protonation states;
- broader receptor conformational variation.

The qualification therefore authorizes DOCK's planned Stage-5 adversarial-pose role within the current validation program but does not establish general superiority or universal production readiness.

### Revisit when

- the frozen A2A ProLIF proof-of-discrimination panel has been constructed;
- DOCK-derived candidate negatives are evaluated under P1–P4;
- the ProLIF validation result is locked;
- the matched Vina-versus-DOCK robustness benchmark is performed;
- evidence supports promoting DOCK to a production or second-pass docking backend;
- DOCK is qualified on additional A2A chemotypes or additional targets.

## D010 --- Close the Graves geometric-decoy program as a preregistered null and freeze the experimental-negative path to blind ProLIF POD

**Date:** 2026-08-28

### Decision

Close the strict Graves geometric-decoy program as a preregistered null
and do not tune or reopen it during the current Stage-5 validation
cycle.

Proceed to the blind A2A ProLIF proof-of-discrimination using
experimentally established human-A2A negatives whose negative status is
fixed independently of ProLIF. Before ProLIF sees the negative panel,
require at least two genuinely unrelated negative-generation families,
including the qualified Shoichet/Kuntz DOCK lineage.

The frozen experimental-negative candidates are:

-   **S-ENBA** --- human A2A Ki \>10,000 nM; human A1 Ki 0.38 ± 0.19 nM.
-   **N6-cyclooctyladenosine** --- human A2A Ki \>10,000 nM; human A1 Ki
    6.4 ± 1.4 nM.

Both values derive from the Gao et al. 2003 human adenosine-receptor
binding dataset and were frozen before pose generation.

N6-cyclooctyladenosine DOCK rank 1 is the first qualified independent
negative-panel representative. It passed the frozen
physical-plausibility instrument under PoseBusters 0.6.5 `dock.yml` with
zero protein clashes and remains ProLIF-unseen.

Fresh Vina 1.2.7 poses for the frozen experimental negatives are
retained as secondary/generalization controls only. Because Vina
participated in earlier ProLIF development, Vina does not satisfy the
second independent-generator-family requirement.

ProLIF remains embargoed from all new negatives until the second
unrelated-family negative is generated, passes the frozen P1 criterion,
and exact panel membership is frozen.

### Rationale

The Graves geometric-decoy route was tested prospectively under a
declared stopping ladder rather than tuned until a desired negative
appeared.

The completed evidence is:

-   cognate XAC/3REY docking recovered the native basin and did not
    yield a qualifying \>3.0 Å alternative;
-   the deeper XAC A1 search produced 20/20 near-native retained poses;
-   cognate 9XT/5OLH docking produced 20/20 near-native retained poses;
-   9XT→3REY cross-docking produced six gross alternatives at
    approximately 11.4--12.6 Å RMSD but no \<=2.0 Å native-like pose,
    making the result a sampling failure rather than a Graves scoring
    decoy;
-   XAC→5OLH cross-docking produced zero saved poses because of bump
    rejection.

The receptor-frame transfer used 281 whole-receptor C-alpha pairs, with
post-fit RMSD 0.893302 Å and det(R)=1. This alignment uncertainty is
reported alongside cross-docked ligand RMSDs and is not subtracted from
the frozen ligand thresholds.

The preregistered ladder therefore returned a scientifically informative
null. Continuing to alter search depth, bump handling, receptors, or
RMSD rules after observing that null would convert prospective
validation into post hoc decoy hunting.

Experimental molecular negatives provide an independent basis for
negative status that does not depend on ProLIF and does not require
manufacturing an interaction failure. Both frozen candidates are bona
fide adenosine-receptor ligands with direct human A2A binding
measurements above 10 micromolar while retaining nanomolar human A1
affinity.

The first successful DOCK negative is N6-cyclooctyladenosine rank 1:

-   experimental P3 status: PASS;
-   canonical DOCK total/max strain: 3.01 / 1.65, within the unchanged 8
    / 3 gate;
-   DOCK score: -27.96;
-   PoseBusters 0.6.5 `dock.yml`: PASS;
-   protein clashes: 0;
-   ProLIF exposure: none.

S-ENBA remains an eligible experimentally frozen P3 candidate, but its
frozen 3REY DOCK branch produced no saved poses because of bump
rejection. That branch is not to be rerun or tuned.

### Alternatives considered

-   Continue increasing DOCK search depth until a Graves geometric
    scoring decoy appears.
-   Relax the DOCK bump criterion or other frozen search settings.
-   Add a third cognate or cross-docking receptor after the
    preregistered null ladder.
-   Return to manufactured rigid-rotation negatives from Session 008.
-   Treat fresh Vina poses as the second independent negative-generation
    family.
-   Replace the frozen experimental-negative candidates based on
    downstream docking convenience.
-   Expose the current negatives to ProLIF before the second unrelated
    generation family is qualified.

These alternatives are rejected for the current validation cycle because
they would either violate the preregistered stopping rule, reopen a
previously closed negative-construction strategy, weaken
generator-family independence, condition panel membership on downstream
convenience, or jeopardize the blind ProLIF POD.

### Implementation freeze

The physical-plausibility instrument for the current negative-panel
cycle is:

-   PoseBusters 0.6.5;
-   shipped `dock.yml`;
-   original generated coordinates;
-   no repair or minimization;
-   `mol_true=None`;
-   qualified receptor supplied as `mol_cond`;
-   full reports preserved.

The completed Graves reference-frame alignment is frozen as:

-   281 whole-receptor C-alpha pairs;
-   5OLH→3REY post-fit C-alpha RMSD = 0.893302 Å;
-   det(R) = 1;
-   no ligand atoms in the fit;
-   no outlier rejection;
-   no binding-site-only refit;
-   no ligand-on-ligand superposition for cross-docked RMSD.

The strict Graves geometric threshold remains `RMSD > 3.0 Å`;
native-like remains `RMSD <= 2.0 Å`. A Graves scoring decoy additionally
requires a score better than the best native-like pose from the relevant
search.

### Current status

The Stage-5 A2A interaction gate remains:

**LEVEL 1 --- CLAIMS CAPPED PENDING GATE VALIDATION**

Positive sensitivity is already established.

Hard-gate discrimination is not yet established.

The primary negative-panel state at Session-010 close is:

-   **DOCK lineage:** one P1-qualified, experimentally negative,
    ProLIF-unseen representative established from N6-cyclooctyladenosine
    rank 1.
-   **Second unrelated lineage:** still required before panel freeze.
-   **Vina:** fresh ProLIF-unseen secondary/generalization controls
    available, but not counted as the second independent family.
-   **ProLIF:** embargoed from all new negatives.

### Revisit when

-   a second genuinely unrelated negative-generation family has produced
    at least one candidate satisfying the frozen experimental-negative
    provenance and P1 requirements;
-   exact negative-panel membership and family distribution have been
    frozen;
-   the blind frozen-ProLIF POD has been completed and its 100%/100%
    PASS/FAIL result has been locked as the next decision entry;
-   post-validation independent-witness qualification and concordance
    are ready to begin;
-   the later matched Vina-versus-DOCK robustness benchmark provides
    evidence relevant to docking-backend promotion.

Until those conditions are met, do not reopen the completed Graves/DOCK
null ladder, retune the frozen DOCK searches, substitute new
experimental negatives based on convenience, or expose the current
negative candidates to ProLIF.

## D011 — Establish bounded A2A molecule-level discrimination from the frozen experimental-negative panel

**Decision date:** 2026-09-06  
**Status:** ACTIVE

### Decision

The frozen A2A ProLIF validation program has established **molecule-level discrimination for one experimentally established human-A2A-negative molecule represented under two independent docking routes**.

The validated negative molecule is:

- **P3-002 — N6-cyclooctyladenosine**;
- human A2A `Ki >10,000 nM`;
- negative status fixed from experimental human receptor binding data before pose generation or ProLIF exposure.

Two independently generated, P1-qualified representatives were frozen before the blind ProLIF read:

1. **DOCK 3.8.5 lineage — rank 1**;
2. **rDock lineage — sole retained production pose**.

Both representatives were selected without ProLIF information and passed the frozen PoseBusters 0.6.5 `dock.yml` physical-plausibility instrument with zero protein pairwise clashes.

The blind read used the **unchanged historical ProLIF 2.2.0 interaction-reader route** recovered from `scripts/stage5/test_native_reader_controls.py`:

```text
validated restored receptor PQR
-> temporary MDAnalysis-compatible reader representation
-> deterministic inferred-topology cleanup
-> plf.Molecule.from_mda()
-> plf.Fingerprint()
-> Fingerprint.generate(..., metadata=True)
```

The frozen A2A recognition definition remained:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

`VdWContact` remains characterization output and does not independently satisfy the Phe168 recognition requirement.

Blind negative results:

```text
DOCK P3-002:
Phe168 = VdWContact
Asn253 = none
Frozen A2A pattern = NOT REPRODUCED

rDock P3-002:
Phe168 = none
Asn253 = none
Frozen A2A pattern = NOT REPRODUCED
```

A pre-read residue-75 guard was applied because the historical restored PQR and the rDock receptor PDB differed maximally at residue 75 CD2 during receptor-artifact comparison. Neither blind pose contacted residue 75.

Therefore:

> **Molecule-level discrimination is established for one experimentally established hA2A-negative molecule under two independent docking routes.**

This decision **does not establish pose sensitivity**. The two poses belong to the same molecular negative and therefore must not be counted as two independent molecular negatives.

This decision also **does not establish general discrimination across negative chemotypes**, broad A2A nonbinders, arbitrary generated molecules, other targets, or alternative receptor preparations.

### Claim boundary

The permitted claim is:

> **The frozen ProLIF A2A recognition implementation distinguished one experimentally established hA2A-negative molecule from the predeclared A2A recognition pattern when that molecule was represented by independently generated P1-qualified DOCK and rDock poses.**

The following stronger claims are not permitted from this evidence:

- ProLIF has established pose-level sensitivity;
- DOCK and rDock provide two independent molecular-negative observations;
- the gate has established general specificity across negative chemotypes;
- every A2A nonbinder will fail the recognition pattern;
- failure to reproduce the pattern proves experimental nonbinding;
- the result transfers to another target or receptor implementation;
- DOCK is superior to rDock, Vina, or another pose generator;
- the generated poses are uniquely correct or thermodynamically preferred.

### Relationship to prior A2A validation

The prior native interaction-reader proof of life remains frozen:

```text
3REY / XAC:       PASS
5OLH / Vipadenant: PASS
5OLO / Tozadenant: PASS

Native positive sensitivity:
3 / 3 PASS
```

D008 previously recorded A2A hard-gate discrimination as **NOT ESTABLISHED** because only positive sensitivity had been demonstrated and the rigid-rotation negative-control strategy failed to produce a suitable universal plausible negative.

D010 then froze an experimental-negative path in which negative molecular status was established independently of ProLIF and panel membership was frozen before ProLIF exposure.

Session 011 completed that prospective path by:

- qualifying rDock as the second unrelated pose-generation lineage for the frozen panel;
- obtaining a P1-qualified rDock representative for P3-002 without tuning after the production result;
- freezing the DOCK and rDock panel representatives before ProLIF exposure;
- performing the blind read through the unchanged historical ProLIF instrument;
- observing failure of the frozen A2A recognition pattern under both docking routes.

The new evidence therefore resolves the specific Session-010 blocker and establishes discrimination **at the bounded molecule-level scope stated above**.

It does not retroactively convert the failed rigid-rotation study into a successful pose-discrimination experiment and does not reopen the completed Graves geometric-decoy null.

### rDock lineage and production freeze

The second unrelated pose-generation lineage was rDock.

Frozen implementation provenance:

```text
rDock tag:
v24.04.204-legacy

Git commit:
3c029ecc65898166b234716b1609fb46212cbc6d
```

The built executable reported `v26.09-alpha` / `libRbt.so/26.09/alpha`; this metadata discrepancy is retained as observed provenance and was not modified. The pinned Git checkout and passing bundled tests define the implementation provenance.

The standard supplied free-docking protocol was used without scientific-parameter tuning.

Production cavity:

```text
cavities: 1
volume: 2139.75 A^3
center: (50.2752, 23.4218, 37.3767)
```

Production run:

```text
ligand: P3-002 N6-cyclooctyladenosine
run count: 1
seed: 20260906
retained SD records: 1
rDock SCORE: -10.5896
```

The sole rDock pose passed the frozen PoseBusters P1 instrument with:

```text
num_pairwise_clashes_protein = 0
smallest_distance_protein = 2.607812 A
```

No rDock tuning, rerun, alternate generator search, or ProLIF-conditioned pose selection was performed after the production result.

### Frozen panel provenance

DOCK representative:

```text
P3-002 N6-cyclooctyladenosine
DOCK 3.8.5
rank 1
DOCK score = -27.96
P1 = PASS
protein clashes = 0
SHA-256 = a232d950008861f3ee87d73e880b9e1627afa06a47182b3a1a249f4cf61eaddf
```

rDock representative:

```text
P3-002 N6-cyclooctyladenosine
rDock
sole production pose
rDock SCORE = -10.5896
P1 = PASS
protein clashes = 0
SHA-256 = 731661a5096209b80a56f6ecd48d520c69c834b949b3d456bd0101a5de48f81a
```

The panel-freeze manifest was written before the blind ProLIF read.

```text
negative_panel_freeze_session011.txt
SHA-256 = 7dcd620b4f4ad428c2375aff6adb308ef23dfb6ba5e069a6dbcdbe7a8b518bef
```

### Receptor-artifact comparison and loader decision

During Session 011, a proposed direct-RDKit receptor-loading route was investigated because the rDock receptor PDB lacked explicit `CONECT` records and failed the MDAnalysis inferred-topology conversion route.

Before any blind read, the historical restored PQR and rDock receptor PDB were compared by matching heavy atoms on residue number plus atom name.

Observed:

```text
PQR heavy atoms: 2251
PDB heavy atoms: 2250
matched heavy atoms: 2250
PQR-only atom: SER305 OXT
PDB-only atoms: none
mean matched-heavy-atom coordinate deviation: 0.006478297 A
maximum deviation: 2.312129322 A
maximum-deviation atom: residue 75 CD2
```

Because the receptor artifacts were not coordinate-identical, the direct-RDKit route was **not substituted for the historical instrument**.

The blind POD instead used the exact historical PQR/MDAnalysis reader route. The direct-RDKit receptor route therefore contributes no negative-panel evidence to D011.

The residue-75 guard was retained for the blind read. Neither negative contacted residue 75.

### Historical proof-of-life artifact retention defect

The original prepared XAC SDF expected by the historical native-reader script:

```text
3REY_XAC_native_pH7.4_restored.sdf
```

was not found in the retained project filesystem during Session 011.

This is recorded as an artifact-retention defect. It does not erase the retained Session-007/008 record of the completed 3/3 native ProLIF proof of life, but it prevents byte-for-byte reconstruction of that historical XAC input from the retained validation bundle.

The missing XAC SDF was **not regenerated** during Session 011.

The project-wide preservation rule remains in force: intermediate and validation artifacts must be retained until the relevant stage is finalized and frozen.

### Relationship to Stage 5

A2A remains a **Level-1** target under D008 because direct experimental cognate target-ligand complexes are available.

Positive sensitivity remains established from the frozen native controls.

D011 adds bounded negative-discrimination evidence at the molecule level.

Stage-5 reporting must preserve the distinction between:

- demonstrated native-positive sensitivity;
- demonstrated molecule-level discrimination for P3-002 under two docking routes;
- unestablished pose-level sensitivity;
- unestablished broad negative-chemotype specificity.

No Stage-5 implementation for another target inherits this validation automatically.

### Alternatives considered

The following were not adopted during Session 011:

- use the direct-RDKit receptor route for the blind negative read;
- regenerate the missing historical XAC SDF and treat it as the original proof-of-life input;
- reopen the Graves geometric-decoy program;
- tune rDock after observing its production result;
- rerun rDock to obtain additional poses;
- substitute Vina as the second independent generator family;
- use FLOWR or DiffSBDD to construct the validation panel;
- expose candidate negatives to ProLIF before panel freeze;
- count the two docking routes as two independent molecular negatives;
- claim pose sensitivity from the two-route result.

These alternatives were rejected because they would change the frozen instrument, weaken blindness, reopen completed validation branches, contaminate the later generator-comparison arm, or exceed the evidence actually obtained.

### Current status

As of 2026-09-06:

```text
A2A interaction evidence:
LEVEL 1

Native positive sensitivity:
ESTABLISHED — 3/3 experimental positives

Experimental-negative panel:
FROZEN

Independent pose-generation routes represented:
DOCK + rDock

Experimental negative molecules represented:
1 — P3-002 N6-cyclooctyladenosine

Blind ProLIF POD:
COMPLETE

Molecule-level discrimination for P3-002:
ESTABLISHED UNDER TWO DOCKING ROUTES

Pose-level sensitivity:
NOT ESTABLISHED

General negative-chemotype discrimination:
NOT ESTABLISHED
```

### Revisit when

- additional experimentally established A2A-negative chemotypes are prospectively added under a new validation plan;
- a future experiment is explicitly designed to test pose-level sensitivity;
- post-validation independent-witness concordance is performed;
- Stage 5 is applied to FLOWR through the frozen generator-independent pathway;
- the Stage-5 implementation is instantiated for another target;
- new evidence justifies broadening or narrowing the permitted discrimination claim.

Until then, do not inflate the Session-011 result beyond **one experimental negative molecule under two independent docking routes**, and do not reopen the completed Graves/DOCK null or tune the frozen rDock result.

## D012 — A2A Stage-5 molecule-level discrimination authority

**Decision date:** 2026-09-06

**Status:** PROPOSED — PENDING APPROVAL

### Decision

D008's A2A hard-attrition criterion is amended in light of the completed Session-011 validation program.

For the A2A Stage-5 implementation, **established molecule-level discrimination is sufficient to authorize molecule-level target–ligand interaction claims**. Demonstration of pose sensitivity is not required for molecule-level discrimination authority.

This amendment is specific to the authority established by the frozen A2A validation evidence and does not establish broader pose-level or specificity claims.

### Session-011 discrimination evidence

Session 011 evaluated one experimentally established human-A2A-negative molecule, **P3-002 N6-cyclooctyladenosine**, represented by P1-qualified poses generated through two independent docking routes:

* DOCK 3.8.5;
* rDock.

Neither representation reproduced the frozen A2A reference-recognition pattern:

**Phe168:** Hydrophobic OR PiStacking

AND

**Asn253:** HBAcceptor

**VdWContact is characterization only and cannot satisfy the Phe168 criterion.**

The supported validation result is therefore:

**Molecule-level discrimination: ESTABLISHED for the tested A2A-negative molecule across two independent docking routes.**

Pose sensitivity was tested through the Session-011 validation program but **was not demonstrated**.

Accordingly:

**Pose sensitivity: NOT DEMONSTRATED**

This result must not be represented as evidence of general discrimination across negative chemotypes, general sensitivity/specificity, or arbitrary pose-level discrimination.

### A2A claims-cap amendment

The D008 status:

**CLAIMS CAPPED PENDING GATE VALIDATION**

is lifted **for molecule-level claims only**, on the basis of the bounded Session-011 discrimination evidence.

The lifted cap does not authorize:

* pose-sensitivity claims;
* pose-level discrimination claims;
* general negative-chemotype discrimination claims;
* general sensitivity or specificity claims;
* universal ProLIF specificity claims;
* transfer of A2A validation authority to another target.

Those claims remain prohibited unless separately established.

### DiffSBDD Stage-5 interpretation

The existing DiffSBDD Stage-5 evaluation remains unchanged.

The 16 Stage-3-surviving DiffSBDD molecules were evaluated using their original molecule IDs, unmodified generator-provided coordinates, the interaction-ready 3RFM receptor, the frozen ProLIF interaction-reading pathway, and the frozen A2A reference-recognition definition.

Observed results remain:

* Phe168 reference feature reproduced: **15/16**
* Asn253 reference feature reproduced: **4/16**
* complete A2A reference pattern reproduced: **3/16**

Complete-pattern reproductions:

* molecule ID **0**
* molecule ID **3**
* molecule ID **18**

The Stage-5 result is reported as:

**3/16 generator-provided DiffSBDD poses reproduced the predeclared A2A reference-recognition pattern (IDs 0, 3, and 18).**

The remaining 13 molecules are retained as **non-reproducing characterization evidence**. They are not classified as Stage-5 failures and are not removed from the baseline on the basis of non-reproduction.

Accordingly, D012 does **not** convert the existing DiffSBDD characterization result into a `3 PASS / 13 FAIL` attrition result.

### Relationship to D008

D008 remains the governing Stage-5 target–ligand interaction evidence framework except for the A2A hard-attrition validation criterion amended here.

The D008 requirement:

**“Hard attrition additionally requires established discrimination using plausible-but-wrong negative poses.”**

is amended for the validated A2A implementation such that **molecule-level discrimination authority may be established by experimentally supported molecular negatives represented through independently generated, physically plausible pose-generation routes, without requiring demonstrated pose sensitivity.**

This amendment does not collapse Stage 3 and Stage 5. Physical plausibility remains a geometry-layer requirement, while Stage 5 remains the target–ligand interaction evidence layer.

### Generator parity

This decision does not alter generator parity.

DiffSBDD and FLOWR must be evaluated through the same frozen A2A Stage-5 implementation, including the same:

* target evidence assignment;
* A2A reference-recognition definition;
* interaction-ready target representation;
* ProLIF interaction-reading pathway;
* molecule-level claim authority;
* reporting language and claim prohibitions.

The A2A definition and validation criterion must not be recalibrated using DiffSBDD or FLOWR outcomes.

### Claim boundary

Following D012, the A2A Stage-5 implementation supports **bounded molecule-level interaction claims based on reproduction or non-reproduction of the frozen A2A recognition pattern**.

It does not support claims that the reader can discriminate arbitrary correct and incorrect poses, that non-reproduction establishes general molecular inactivity, or that the validated observations define general sensitivity or specificity.

**Molecule-level claims cap: LIFTED**

**Pose-level claims: PROHIBITED**

**Pose-sensitivity claims: PROHIBITED**

**General specificity claims: PROHIBITED**

**General negative-chemotype discrimination claims: PROHIBITED**

---

### Governing principle

**Molecule-level discrimination authority must remain bounded to the level of discrimination actually demonstrated.**

For A2A, Session 011 establishes molecule-level discrimination authority without establishing pose sensitivity or general specificity. Stage-5 reporting must preserve that distinction.

Non-reproduction of the frozen A2A reference-recognition pattern is therefore reportable molecule-level interaction evidence, but it does not by itself establish molecular inactivity and does not convert a generated molecule into a Stage-5 failure.

---

### Revisit when

* a defensible A2A pose-sensitivity validation is completed;
* discrimination is demonstrated across additional independent experimentally supported A2A-negative chemotypes;
* evidence becomes sufficient to estimate or claim general Stage-5 sensitivity or specificity;
* new target–ligand evidence changes the frozen A2A recognition definition or evidence package;
* Stage 5 is applied to FLOWR and an implementation issue requires reconsideration of generator parity;
* Stage 5 is instantiated for a new target;
* future work formally proposes changing the distinction between pattern non-reproduction, molecule-level interpretation, and hard attrition.

## D013 — PLIP independent Stage-5 witness selection

**Decision date:** 2026-09-06

**Status:** ACTIVE

### Decision

**PLIP is selected as the independent Stage-5 interaction witness** for the frozen A2A validation and concordance program.

PLIP remains separate from the frozen ProLIF verdict instrument. ProLIF defines the Stage-5 interaction result; PLIP provides an independent witness of the same experimental structures and, after qualification, may be used to measure concordance with the frozen ProLIF observations.

PLIP qualification must be completed before PLIP concordance is treated as evidence.

### Alternatives assessment

The alternatives pass considered serious independent interaction-analysis approaches, including **Arpeggio**, **ODDT interaction fingerprints**, and a **minimal RDKit geometric contact scorer**.

PLIP was selected because its interaction vocabulary maps directly onto the frozen A2A recognition roles with minimal analyst-defined translation, including:

* Hydrophobic contacts;
* Pi-stacking;
* Hydrogen-bond interactions.

The selection is **not** based on Arpeggio being scientifically inferior.

Arpeggio provides a broader interatomic-contact vocabulary and remains a scientifically viable alternative. Its broader ontology is useful for questions concerning interaction-repertoire characterization rather than the narrowly defined independent-witness role.

### Arpeggio status

Arpeggio is therefore **UNREJECTED**.

It is retained as the preferred candidate for a future **non-verdict interaction-characterization lane**, including:

* DiffSBDD-versus-FLOWR interaction-repertoire comparison;
* exploratory characterization of alternative interaction networks;
* future targets for which no frozen recognition definition yet exists.

Arpeggio must not define, modify, or rescue the frozen A2A Stage-5 verdict.

### Qualification requirement

PLIP must first be qualified against the frozen experimental A2A positive panel:

* **3REY / XAC**
* **5OLH / Vipadenant**
* **5OLO / Tozadenant**

Qualification uses the retained experimental structures without modification.

The qualification must not:

* modify experimental coordinates;
* tune PLIP parameters against ProLIF output;
* redefine the frozen A2A recognition pattern;
* use ProLIF results to select or modify PLIP interaction calls.

PLIP and ProLIF results must be recorded independently, with concordance reported as **measured**, not assumed.

### Input principle

The least-transformative input route is the retained experimental protein–ligand complex structure supplied directly to PLIP.

No structure rebuilding, ligand regeneration, coordinate repair, minimization, reprotonation, recharging, or other scientific transformation may be introduced merely to accommodate PLIP.

The missing historical prepared 3REY/XAC ligand SDF must not be regenerated for this qualification. Where the retained native experimental complex structure is available, that retained structure is the authoritative qualification input.

### Target-specific implementation

The PLIP witness implementation must remain generator-independent.

Target-specific content, including:

* Phe168;
* Asn253;
* 3REY;
* 3RFM;
* experimental positive-panel membership;

must reside in frozen configuration or artifact files and **must not be hardcoded in executable scripts**.

The PLIP implementation may read those frozen definitions as inputs, but the target-specific constants themselves must remain outside code.

### Relationship to the frozen ProLIF instrument

ProLIF 2.2.0 remains the frozen Stage-5 interaction reader and verdict instrument.

PLIP does not replace ProLIF, alter ProLIF parameters, modify the frozen A2A recognition definition, or establish an alternative Stage-5 gate.

Following successful independent qualification, PLIP may provide witness evidence and concordance analysis only.

### Generator parity

When used beyond qualification, PLIP must operate on the same generator-independent molecule–pose evaluation objects used by the Stage-5 cascade.

The witness must not introduce generator-specific preprocessing or interpretation.

### Governing principle

**The independent witness tests the frozen interaction interpretation; it does not redefine the instrument or the gate.**

PLIP is selected for methodological independence and direct mapping to the frozen A2A interaction roles, while broader alternatives such as Arpeggio remain available for future non-verdict characterization.

### Revisit when

* PLIP cannot be independently qualified on the frozen experimental A2A positive panel;
* PLIP's implementation requires a structural transformation inconsistent with the frozen qualification constraints;
* a future decision requires broader interaction-repertoire characterization rather than independent witnessing;
* Arpeggio or another independent method becomes necessary for a documented scientific question not adequately addressed by PLIP;
* Stage 5 is instantiated for a new target with interaction roles not adequately represented by the existing witness vocabulary.

## D014 — PLIP independent Stage-5 witness qualification and concordance

**Decision date:** 2026-09-06

**Status:** ACTIVE

### Decision

The PLIP independent Stage-5 witness program for the frozen A2A implementation is complete.

PLIP 3.0.1 is established as a **qualified independent interaction witness** for the tested A2A panel.

ProLIF 2.2.0 remains the frozen Stage-5 verdict instrument. PLIP does not replace ProLIF, redefine the frozen A2A recognition pattern, or independently determine Stage-5 molecule disposition.

### Witness qualification

PLIP was qualified prospectively against the frozen experimental A2A positive panel:

* 3REY / XAC;
* 5OLH / Vipadenant (9XT);
* 5OLO / Tozadenant (9XW).

Before measurement, witness concordance was defined against the frozen A2A recognition roles:

**Phe168:** Hydrophobic OR PiStacking

AND

**Asn253:** HBAcceptor

For the Asn253 role, directional concordance required:

**protein Asn253 = acceptor; ligand = donor**

VdWContact is characterization only and cannot satisfy the Phe168 criterion.

PLIP qualification used:

* PLIP 3.0.1;
* Open Babel 3.2.1;
* retained raw experimental complex PDBs;
* `--nofix`;
* PLIP default hydrogen addition;
* PLIP default interaction thresholds;
* one run per experimental complex;
* XML as the authoritative machine-readable result;
* TXT as the human-readable report;
* retained PLIP-generated protonated structures.

No PLIP parameter was tuned against ProLIF output.

Measured qualification result:

* 3REY / XAC: **PASS**
* 5OLH / Vipadenant: **PASS**
* 5OLO / Tozadenant: **PASS**

Therefore:

**PLIP POSITIVE QUALIFICATION: 3/3 PASS**

The two instruments used independent preparation pipelines. The frozen ProLIF proof-of-life used the pH7.4-restored receptor pathway, whereas PLIP analyzed the retained raw experimental complexes using PLIP's own hydrogen-addition procedure.

### Frozen negative-panel concordance

Following positive qualification, PLIP was applied once to each frozen Session-011 negative representative:

* P3-002 N6-cyclooctyladenosine — DOCK rank-1 representative;
* P3-002 N6-cyclooctyladenosine — rDock representative.

These are two independently generated pose representations of **one experimentally established human-A2A-negative molecule**.

PLIP reported for the DOCK representative:

* Phe168 frozen role: **NOT REPRODUCED**
* Asn253 frozen role: **NOT REPRODUCED**
* complete A2A recognition pattern: **NOT REPRODUCED**

The frozen ProLIF result for the same representative was also complete-pattern **NOT REPRODUCED**.

PLIP reported for the rDock representative:

* Phe168 frozen role: **NOT REPRODUCED**
* Asn253 frozen role: **NOT REPRODUCED**
* complete A2A recognition pattern: **NOT REPRODUCED**

The frozen ProLIF result for the same representative was also complete-pattern **NOT REPRODUCED**.

Therefore:

**PLIP–ProLIF complete-pattern concordance on the frozen negative representatives: 2/2**

### Adapter-preservation audit

The frozen negative ligand representatives required derived protein–ligand complex PDB adapters for PLIP.

The authoritative frozen ligand artifacts were not modified.

For both derived PLIP complexes, the ligand adapter audit demonstrated:

* 27/27 frozen ligand heavy atoms preserved;
* identical heavy-atom element ordering;
* unique ligand-component identification;
* maximum absolute per-coordinate deviation: **0.000500 Å**;
* maximum heavy-atom Euclidean displacement: **<0.001 Å**.

The observed ligand-coordinate differences are limited to PDB serialization rounding.

The receptor adapter audit demonstrated, independently for the DOCK and rDock derived complexes:

* frozen receptor atoms: **4568**
* adapter receptor atoms: **4568**
* matched atoms: **4568**
* source-only atoms: **0**
* adapter-only atoms: **0**
* mean Euclidean coordinate deviation: **0.000000 Å**
* maximum Euclidean coordinate deviation: **0.000000 Å**
* maximum absolute XYZ deviation: **0.000000 Å**

The receptor representation is therefore coordinate-identical to its frozen source in both derived PLIP complex inputs.

The complete adapter audit establishes preservation of the frozen negative-pose geometry to serialization-rounding precision for the ligand and exact coordinate identity for the receptor.

### Supported witness statement

The supported result is:

**PLIP independently reproduced the frozen A2A recognition pattern in 3/3 experimental cognate complexes and, after qualification, concorded with ProLIF in finding non-reproduction of that pattern for both frozen DOCK- and rDock-generated representations of P3-002 N6-cyclooctyladenosine.**

This establishes independent-instrument concordance for the tested frozen panel.

### Claim boundary

D014 does **not** establish:

* pose sensitivity;
* general pose-level discrimination;
* general negative-chemotype discrimination;
* general Stage-5 sensitivity or specificity;
* universal ProLIF specificity;
* universal PLIP specificity;
* equivalence of ProLIF and PLIP interaction ontologies;
* transfer of A2A witness qualification to another target.

The two negative representatives remain two pose-generation-route representations of **one experimental negative molecule**, not two independent negative chemotypes.

PLIP agreement does not enlarge the molecule-level claim authority established by D012 beyond the evidence actually tested.

### Instrument roles

The Stage-5 instrument hierarchy remains:

**ProLIF 2.2.0 — frozen verdict instrument**

**PLIP 3.0.1 — qualified independent witness**

PLIP concordance may strengthen confidence in a measured Stage-5 interaction interpretation but cannot redefine, rescue, or override the frozen ProLIF result.

### Implementation rule

The PLIP witness implementation remains generator-independent and config-driven.

Target-specific content, including target residues, target structures, ligand identities, panel membership, recognition roles, and directional requirements, must remain in frozen configuration or artifact files and must not be hardcoded in executable scripts.

### Governing principle

**Independent concordance strengthens confidence in the tested interaction interpretation without expanding the claim beyond the evidence independently witnessed.**

### Revisit when

* pose sensitivity is independently demonstrated;
* additional experimentally supported A2A-negative chemotypes are evaluated through the frozen witness framework;
* evidence becomes sufficient to support general sensitivity or specificity claims;
* a material ProLIF–PLIP discordance is observed on a future frozen evaluation panel;
* the frozen A2A recognition definition materially changes;
* Stage 5 is instantiated for a new target and requires target-specific witness qualification;
* a future non-verdict interaction-characterization lane is formally introduced.

## D015 — P2Rank selection for Level-3 predicted-pocket characterization

**Decision date:** 2026-09-06

**Status:** PROPOSED — PENDING APPROVAL

### Decision

**P2Rank is selected as the primary predicted-pocket method for the D008 Level-3 lane.**

Its role is limited to **predicted-pocket characterization** for structurally defined targets lacking sufficient target–ligand interaction evidence for compatibility assessment.

P2Rank output does not constitute target–ligand interaction evidence and does not define a Stage-5 compatibility gate.

### Selection rationale

A literature-backed alternatives assessment considered established pocket/site-detection approaches including:

* P2Rank;
* fpocket;
* DoGSiteScorer;
* ConCavity;
* LIGSITEcsc;
* DeepSite;
* PASS;
* CASTp;
* SiteMap.

P2Rank was selected because its standalone, ranked ligand-binding-site prediction workflow maps directly onto the D008 Level-3 requirement to:

* nominate candidate binding sites;
* characterize predicted pocket location and geometry;
* provide a predicted-pocket artifact usable by Stage 3B;
* operate efficiently in an automated, generator-independent evaluation pipeline.

The selection does **not** establish that P2Rank is scientifically superior to other established pocket-prediction methods.

### Alternatives status

**fpocket remains UNREJECTED** and is retained as the preferred geometry-first alternative.

Its geometry-based approach may be useful if P2Rank proves operationally unsuitable or if a future scientific question requires an independent geometric pocket-characterization perspective.

Other literature-supported alternatives considered in the selection pass remain **UNREJECTED** unless a future documented requirement or evaluation provides a specific reason to reject them.

### Level-3 role

P2Rank may be used to:

* nominate one or more candidate pockets;
* rank predicted pockets;
* record predicted-pocket location;
* characterize available pocket geometry/prediction outputs;
* provide predicted-pocket coordinates as the pocket artifact for Stage 3B.

Every resulting site must be labeled:

**PREDICTED POCKET**

P2Rank output must not:

* establish a target-recognition pattern;
* establish target compatibility;
* establish target incompatibility;
* upgrade a target from Level 3;
* authorize a Stage-5 interaction gate;
* rescue the Level-3 `INCONCLUSIVE` verdict.

### Stage-3 / Stage-5 separation

For a Level-3 target:

**Stage-5 VERDICT:** `INCONCLUSIVE`

**Stage-5 LANE:** evaluation continues as `INTERACTION-UNVERIFIED`

A P2Rank-predicted pocket may be supplied to Stage 3B for geometry-only evaluation of generator-provided poses.

Any resulting Stage-3B assessment remains a physical/geometric plausibility result and must not be represented as target–ligand interaction evidence.

### Implementation requirements

The P2Rank implementation must remain generator-independent.

Target-specific content, including target identifiers, structures, selected predicted-pocket artifacts, and any target-specific downstream configuration, must reside in frozen configuration or artifact files and must not be hardcoded in executable scripts.

P2Rank predictions must be retained as artifacts with sufficient provenance to reproduce the prediction, including software version, input structure identity, invocation/configuration, and relevant output files.

No target-specific P2Rank parameter tuning may be performed using generated-molecule outcomes.

### Governing principle

**A predicted pocket preserves evaluation opportunity; it does not manufacture interaction evidence.**

P2Rank provides a structurally useful hypothesis for the Level-3 lane while the Stage-5 verdict continues to record the underlying interaction-evidence gap.

### Revisit when

* P2Rank proves operationally unsuitable for the generator-independent Stage-5 pipeline;
* a Level-3 target exposes a pocket-prediction limitation material to downstream Stage-3B evaluation;
* an independent geometry-first pocket characterization is required;
* evidence supports reconsidering fpocket or another unrejected alternative;
* new comparative pocket-prediction evidence materially changes the implementation choice;
* qualifying target–ligand evidence upgrades a Level-3 target and removes the need for the predicted-pocket lane.
 
D015 — P2Rank selection for Level-3 predicted-pocket characterization

Decision date: 2026-09-06

Status: ACTIVE — IMPLEMENTATION FROZEN

Decision

P2Rank is selected as the primary predicted-pocket method for the D008 Level-3 lane.

Its role is limited to predicted-pocket characterization for structurally defined targets lacking sufficient target–ligand interaction evidence for compatibility assessment.

P2Rank output does not constitute target–ligand interaction evidence and does not define a Stage-5 compatibility gate.

Selection rationale

A literature-backed alternatives assessment considered established pocket/site-detection approaches including:

P2Rank;
fpocket;
DoGSiteScorer;
ConCavity;
LIGSITEcsc;
DeepSite;
PASS;
CASTp;
SiteMap.

P2Rank was selected because its standalone, ranked ligand-binding-site prediction workflow maps directly onto the D008 Level-3 requirement to:

nominate candidate binding sites;
characterize predicted pocket location and geometry;
provide a predicted-pocket artifact usable by Stage 3B;
operate efficiently in an automated, generator-independent evaluation pipeline.

The selection does not establish that P2Rank is scientifically superior to other established pocket-prediction methods.

Alternatives status

fpocket remains UNREJECTED and is retained as the preferred geometry-first alternative.

Its geometry-based approach may be useful if P2Rank proves operationally unsuitable or if a future scientific question requires an independent geometric pocket-characterization perspective.

Other literature-supported alternatives considered in the selection pass remain UNREJECTED unless a future documented requirement or evaluation provides a specific reason to reject them.

Level-3 role

P2Rank may be used to:

nominate one or more candidate pockets;
rank predicted pockets;
record predicted-pocket location;
characterize available pocket geometry/prediction outputs;
define an atom-level predicted-pocket selection from which the residue-complete pocket artifact is materialized for generation conditioning and Stage 3B.

Every resulting site must be labeled:

PREDICTED POCKET

P2Rank output must not:

establish a target-recognition pattern;
establish target compatibility;
establish target incompatibility;
upgrade a target from Level 3;
authorize a Stage-5 interaction gate;
rescue the Level-3 INCONCLUSIVE verdict.
Stage-3 / Stage-5 separation

For a Level-3 target:

Stage-5 VERDICT: INCONCLUSIVE

Stage-5 LANE: evaluation continues as INTERACTION-UNVERIFIED

A P2Rank-predicted pocket may be supplied to Stage 3B for geometry-only evaluation of generator-provided poses.

Any resulting Stage-3B assessment remains a physical/geometric plausibility result and must not be represented as target–ligand interaction evidence.

Pocket conditioning and evaluation parity

For a pocket-conditioned generator operating on a Level-3 target, the predicted pocket used for primary Stage-3B evaluation must be the same frozen pocket artifact used to condition generation.

The conditioning pocket must be selected and frozen before generated-molecule outcomes are inspected.

Its provenance must record:

the target structure used for pocket prediction;
the P2Rank implementation/version and invocation;
the native P2Rank prediction outputs;
the predicted-pocket identifier and rank;
the rule by which that pocket was selected;
the frozen selection-config identity and content hash;
the exact pocket artifact supplied to the generator.

The same frozen pocket artifact then defines the primary Stage-3B geometric reference for that generated cohort.

Other P2Rank-nominated sites may be retained and reported as PREDICTED POCKET characterization.

Evaluation of generated poses against a predicted site that did not condition generation is permitted only as a separately labeled cross-pocket characterization and must not replace or modify the primary Stage-3B result.

Cross-pocket characterization cannot establish target compatibility, rescue the Level-3 INCONCLUSIVE verdict, or be used post hoc to select a more favorable pocket for a generated cohort.

For generator comparisons, the conditioning/evaluation relationship must be held constant: each generator is evaluated relative to the same pocket artifact that defined its generation task.

Where generators are being directly compared on the same target, the preferred design is to supply the same frozen conditioning pocket to both generators whenever their interfaces permit it.

Predicted-pocket structural representation

The native P2Rank surf_atom_ids define the atom-level selection for the configured predicted pocket. These identifiers are mapped to PDB atom serial numbers in the authoritative source target structure.

P2Rank determines pocket membership; the source PDB remains authoritative for structural identity and coordinates.

The selected surface atoms are used to identify every source-PDB residue touched by at least one selected atom.

The derived structural pocket artifact must then contain all original ATOM records belonging to every touched residue. It must not contain only the P2Rank-selected surface atoms.

This residue-complete expansion is required to preserve parity with the existing crystallographic pocket representation consumed by Stage 3B and to prevent downstream tools from operating on incomplete protein residues.

The materialization step must:

retain complete touched residues;
preserve source-PDB atom identities;
preserve source-PDB atom ordering within each retained residue;
preserve source-PDB coordinates unchanged;
introduce no new geometric pocket definition or coordinate transformation.

P2Rank's original atom-level selection remains recorded separately in provenance metadata.

Implementation requirements

The P2Rank implementation must remain generator-independent.

Target-specific content, including target identifiers, structures, selected predicted-pocket artifacts, pocket-selection rules, and target-specific downstream configuration, must reside in frozen configuration or artifact files and must not be hardcoded in executable scripts.

Pocket selection must be configuration-driven. The generic implementation must not automatically select:

rank 1;
the highest-scoring pocket;
the highest-probability pocket;
a pocket favored by generated-molecule outcomes.

P2Rank predictions must be retained unchanged as artifacts with sufficient provenance to reproduce the prediction, including:

software version;
input structure identity and SHA-256;
invocation/configuration;
native predictions output and SHA-256;
native residues output and SHA-256;
selected-pocket native fields;
selected surf_atom_ids;
materialized residue identities;
frozen selection-config identity and SHA-256.

No target-specific P2Rank parameter tuning may be performed using generated-molecule outcomes.

Frozen implementation

The D015 predicted-pocket artifact adapter is implemented in:

evaluation/p2rank_pocket.py
evaluation/pocket_models.py

The implementation uses explicit typed representations for P2Rank pockets, residue identities, frozen pocket selections, file provenance, pocket lineage, and predicted-pocket metadata.

The frozen scientific transformation is:

native P2Rank prediction → frozen configured selection → source-PDB atom mapping → touched source-PDB residues → complete source-PDB residues → invariant validation → predicted-pocket PDB + provenance metadata

The implementation does not calculate a new pocket score, volume, radius, or geometric boundary.

Implementation qualification

The bundled P2Rank 1fbl.pdb example was used only as an implementation fixture. It does not constitute target-specific scientific validation and does not establish a general pocket-selection rule.

For the configured fixture pocket:

P2Rank selected 40 surface atoms;
those atoms mapped to 18 source-PDB residues;
residue-complete expansion produced 150 source-PDB ATOM records.

The complete-residue invariant was verified:

the derived artifact contained exactly the residues touched by the P2Rank atom selection;
no unrelated residues were introduced;
every selected residue was complete;
atom membership, ordering, identity, and coordinates matched the authoritative source PDB.

All 150 derived ATOM records were independently confirmed to occur verbatim in the source PDB.

Formal deterministic tests:

P2Rank-specific tests: 16/16 PASS
full repository suite at qualification: 34/34 PASS

The test suite covers native prediction parsing, malformed/missing columns, frozen selection, missing and ambiguous selection, missing source-PDB atom IDs, empty atom selection, atom-to-residue mapping, complete-residue expansion, exact source-record preservation, invariant validation, metadata construction and serialization, configuration loading, and provenance hashing.

Deterministic materialization

Repeated construction from identical inputs produced byte-identical structural and metadata artifacts.

Fixture predicted-pocket PDB SHA-256:

022946b4becaf2fe39881ba83d37a8c46de740d4b33333e449584cdd182da0d5

Fixture metadata JSON SHA-256:

3df2157651734770d7aca5d61575bbe8ea86a99aa2707e6f183ece51e0551827

P2Rank 2.5.1 distribution archive SHA-256:

30e20b05ca2f89e239ea6ec8efc312f08da26802b04ea0da49351d90ca70f593

These fixture artifact hashes document deterministic implementation qualification; they are not target-specific scientific reference values.

Governing principle

A predicted pocket preserves evaluation opportunity; it does not manufacture interaction evidence.

P2Rank provides a structurally useful hypothesis for the Level-3 lane while the Stage-5 verdict continues to record the underlying interaction-evidence gap.

For pocket-conditioned generation, the primary geometry evaluation remains anchored to the same prospectively frozen pocket that defined the generation task.

Scope boundary

D015 freezes the Level-3 predicted-pocket method and artifact-construction semantics. It does not establish:

that P2Rank identifies the biologically relevant pocket for a particular target;
a universal rank-1 or highest-probability selection policy;
target binding;
target engagement;
target compatibility;
affinity;
functional modulation;
biological relevance of a predicted site.

Target-specific pocket selection remains a prospective scientific decision recorded in frozen target configuration.

Revisit when
P2Rank proves operationally unsuitable for the generator-independent Stage-5 pipeline;
a Level-3 target exposes a pocket-prediction limitation material to downstream Stage-3B evaluation;
an independent geometry-first pocket characterization is required;
evidence supports reconsidering fpocket or another unrejected alternative;
new comparative pocket-prediction evidence materially changes the implementation choice;
a generator cannot consume the same frozen conditioning-pocket representation required for generator parity;
a scientific question requires cross-pocket characterization beyond the primary conditioning pocket;
qualifying target–ligand evidence upgrades a Level-3 target and removes the need for the predicted-pocket lane.

## D016 — Binding-affinity label gates for Level-2 homolog calibration

**Decision date:** 2026-09-09

**Status:** ACTIVE — FROZEN

### Decision

A global three-band binding-affinity labeling rule is frozen for the Level-2 homolog calibration set.

The gates are:

- **Positive:** `Ki < 50 nM`
- **Middle:** `50 nM <= Ki <= 100 nM`
- **Negative:** `Ki > 100 nM`

Accordingly:

- **N = 50 nM**
- **M = 100 nM**

These thresholds are global across all receptors and must never be tuned per receptor, target, homolog pair, ligand, or generated cohort.

The middle band is deliberately ungraded. Entries in the middle band retain their raw Ki values and are designated **probe-only**. They must not be converted to positive or negative labels and must not contribute to pass/fail calibration.

The three-band rule preserves uncertainty rather than forcing measurements near the decision region into binary classes.

### Scope

D016 defines the experimental binding labels used to calibrate the Level-2 homolog correspondence procedure.

It does **not** define:

- `pocket_sequence_identity` thresholds;
- `pocket_superposition_rmsd` thresholds;
- minimum mapped-residue counts;
- the final definition of `pocket_conserved`;
- the Level-2 apo-pocket method;
- any Stage-5 compatibility gate.

Those decisions remain separate.

D016 does not modify D015. The D015 Level-3 P2Rank predicted-pocket contract and the D016 Level-2 homolog binding-label contract are separate contracts and must never be merged.

### Frozen label source

The label source is the following frozen affinity dataset.

There are **13 adopted measured or censored affinity entries** represented in the receptor matrix below. Cells marked `NA` are explicitly excluded and must not be imputed, graded, or included in denominators.

| Compound | hA1 Ki (nM) | hA2A Ki (nM) | hA2B Ki (nM) | hA3 Ki (nM) | Adopted source / status |
|---|---:|---:|---:|---:|---|
| **NECA** | **6.8** | **2.2** | **NA** | **16.0** | hA1/hA2A/hA3 values adopted from Gao et al. 2004, PMID 15476669. The row carries an explicit **single-lab limitation**. hA2B is excluded: the Gao 140 nM value is EC50 rather than Ki, while the separately reported 1,890 nM value derives from a different A2B radioligand context and is retained only as contextual evidence. |
| **CCPA** | **0.83** | **2,270** | **18,800** | **38** | Frozen literature values. Cross-assay/provenance limitations remain attached where applicable. |
| **CGS21680** | **289** | **27** | **>10,000** | **67** | Frozen literature values. `>10,000` remains a censored observation and must not be converted to exactly 10,000 nM. Cross-assay/provenance limitations remain attached where applicable. |
| **ZM241385** | **NA** | **1.6** | **NA** | **743** | Selectivity-informed calibration row: potent hA2A binding provides the within-family positive while weak hA3 binding provides the discrimination negative. The hA2A/hA3 comparison remains usable but provenance-flagged; excluded receptors must not be imputed. |

The previously discussed NECA/hA2B measurements are not part of the adopted Ki dataset and cannot place either gate.

### Gao et al. 2004 limitation

The adopted NECA hA1, hA2A, and hA3 values come from Gao et al. 2004 (PMID 15476669).

They satisfy the frozen functionally-equivalent-protocol definition used during calibration:

- same research program and study;
- competition radioligand binding;
- recombinant human receptors;
- same expression background;
- agonist radioligands throughout;
- receptor values reported within the same study.

Receptor-specific agonist tracers are permitted because a single radioligand does not provide equivalent binding measurements across all adenosine receptor subtypes.

A bounded literature search did not identify an independent laboratory dataset satisfying the full protocol definition for the positive NECA comparisons. The NECA positive calibration therefore carries an explicit **single-lab limitation**.

This limitation was accepted because the observed positive/negative separation is substantially larger than the documented assay-context effect and because Stage-5 Level-2 evidence remains characterization-only.

### Assay-comparability rule

Assay comparability is evaluated **within a compound row**, not across the entire table.

Labels compare the same compound across receptor subtypes. Where a row is used to establish a cross-receptor relationship, the preferred evidence is:

- the same study;
- the same measurement modality;
- the same recombinant-human expression background;
- functionally equivalent radioligand-binding protocols.

Different compound rows may originate from different experimental studies or protocols.

The frozen N and M gates are nevertheless global. They must not be adjusted to accommodate a particular assay, compound, receptor, or target.

No cross-assay absolute comparison beyond application of the frozen gates is authorized.

The calibration provenance tiers are:

- **Tier 1:** functionally equivalent within-row protocol;
- **Tier 2:** cross-assay row whose separation is substantially larger than the documented assay-context effect; usable but explicitly flagged;
- **Tier 3:** cross-assay/context-sensitive row capable of moving across a candidate gate; context only and unable to place a threshold.

### Frozen labels at N=50 / M=100

Applying the frozen rule to the 13 adopted entries gives:

- hA1: **2 positive / 1 negative / 0 middle**
- hA2A: **3 positive / 1 negative / 0 middle**
- hA2B: **0 positive / 2 negative / 0 middle**
- hA3: **2 positive / 1 negative / 1 middle**

Total:

- **7 positive**
- **5 negative**
- **1 middle**
- **13 adopted entries**
- **12/13 graded = 92.3%**

The single middle-band entry is retained as probe-only with its raw Ki.

### Robustness appendix

Sensitivity was evaluated over:

- `N in {10, 25, 50, 75}`
- `M in {100, 250, 500, 1000}`
- only combinations satisfying `N < M`

using only the frozen 13-entry affinity dataset.

Each receptor cell below is reported as `positive / negative / middle`.

| N | M | hA1 | hA2A | hA2B | hA3 | Total | Graded |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 100 | 2/1/0 | 2/1/1 | 0/2/0 | 0/1/3 | 4/5/4 | 69.2% |
| 10 | 250 | 2/1/0 | 2/1/1 | 0/2/0 | 0/1/3 | 4/5/4 | 69.2% |
| 10 | 500 | 2/0/1 | 2/1/1 | 0/2/0 | 0/1/3 | 4/4/5 | 61.5% |
| 10 | 1000 | 2/0/1 | 2/1/1 | 0/2/0 | 0/0/4 | 4/3/6 | 53.8% |
| 25 | 100 | 2/1/0 | 2/1/1 | 0/2/0 | 1/1/2 | 5/5/3 | 76.9% |
| 25 | 250 | 2/1/0 | 2/1/1 | 0/2/0 | 1/1/2 | 5/5/3 | 76.9% |
| 25 | 500 | 2/0/1 | 2/1/1 | 0/2/0 | 1/1/2 | 5/4/4 | 69.2% |
| 25 | 1000 | 2/0/1 | 2/1/1 | 0/2/0 | 1/0/3 | 5/3/5 | 61.5% |
| **50** | **100** | **2/1/0** | **3/1/0** | **0/2/0** | **2/1/1** | **7/5/1** | **92.3%** |
| 50 | 250 | 2/1/0 | 3/1/0 | 0/2/0 | 2/1/1 | 7/5/1 | 92.3% |
| 50 | 500 | 2/0/1 | 3/1/0 | 0/2/0 | 2/1/1 | 7/4/2 | 84.6% |
| 50 | 1000 | 2/0/1 | 3/1/0 | 0/2/0 | 2/0/2 | 7/3/3 | 76.9% |
| 75 | 100 | 2/1/0 | 3/1/0 | 0/2/0 | 3/1/0 | 8/5/0 | 100.0% |
| 75 | 250 | 2/1/0 | 3/1/0 | 0/2/0 | 3/1/0 | 8/5/0 | 100.0% |
| 75 | 500 | 2/0/1 | 3/1/0 | 0/2/0 | 3/1/0 | 8/4/1 | 92.3% |
| 75 | 1000 | 2/0/1 | 3/1/0 | 0/2/0 | 3/0/1 | 8/3/2 | 84.6% |

#### Cliff analysis

The following requested grid gates fall within 20% of an adopted measured Ki:

- **N=25:** CGS21680/hA2A = 27 nM. As N rises across 27 nM, the label changes **middle -> positive**.
- **N=75:** CGS21680/hA3 = 67 nM. As N rises across 67 nM, the label changes **middle -> positive**.
- **M=250:** CGS21680/hA1 = 289 nM. As M rises across 289 nM, the label changes **negative -> middle**.

No adopted measured Ki lies within 20% of either frozen gate:

- **N=50 nM**
- **M=100 nM**

The censored CGS21680/hA2B `>10,000 nM` value is not treated as a numerical cliff.

### Robustness rationale

`N=50 nM` and `M=100 nM` were selected because the reference cell lies in a stable region of the frozen affinity table.

Moving M from 100 to 250 changes no labels. The nearest grid cliffs occur at N=25, N=75, and M=250 rather than at the frozen gates.

The frozen rule grades **92.3%** of adopted entries while retaining an explicit middle band rather than forcing every observation into a binary class.

The gates are therefore frozen as a global calibration contract, not optimized per receptor or target.

### Fail-loudly behavior

N and M are mandatory frozen configuration values.

If either threshold is:

- absent;
- null;
- malformed;
- inconsistent with `N < M`; or
- not traceable to the frozen D016 configuration,

the calibration is **UNEVALUABLE** and execution must fail loudly.

No executable code may supply default values for N or M.

Missing affinity measurements must remain missing. They must not be imputed, converted to middle-band observations, or included in denominators.

Censored measurements must remain censored.

### Configuration provenance

D016 must have its **own frozen configuration artifact**, separate from D015 and all target-specific configuration.

That artifact must encode at minimum:

- decision identifier `D016`;
- schema version;
- `N = 50`;
- `M = 100`;
- units `nM`;
- strict positive comparison `< N`;
- strict negative comparison `> M`;
- middle-band treatment `probe-only`;
- missing-value treatment;
- frozen affinity-table identity.

The configuration's SHA-256 must be recorded after the exact config file is materialized.

**Frozen D016 config SHA-256:** `PENDING MATERIALIZATION`

### Governing principle

**Binding labels are global calibration evidence, not target-specific tuning parameters.**

The middle band preserves uncertainty; it is not a reservoir from which convenient positive or negative labels may be selected.

### Lessons

An earlier sensitivity grid ran on reconstructed NECA values (14/20/25 nM) of unknown provenance and was caught and superseded; all calibration inputs must therefore come exclusively from the adopted frozen affinity table.

### Revisit when

- new primary human adenosine-receptor affinity data materially challenge the frozen 13-entry calibration table;
- an independent laboratory produces functionally equivalent parallel binding measurements that resolve the Gao et al. 2004 single-lab limitation;
- evidence shows that either frozen gate (`N = 50 nM` or `M = 100 nM`) lies near a reproducible assay-dependent classification cliff;
- the documented assay-context effect is shown to be materially larger than the approximately four-fold effect considered during calibration;
- additional qualified calibration data materially reduce or eliminate the separation between the positive and negative classes;
- the middle band proves too narrow or too broad to preserve genuinely ambiguous measurements as probe-only;
- a frozen gate causes systematic receptor-, ligand-, or assay-specific misclassification that cannot be addressed through provenance labeling alone;
- the Level-2 homolog structural calibration demonstrates that the frozen binding labels do not provide a usable known-answer reference for `pocket_sequence_identity` and `pocket_superposition_rmsd`;
- a change to the binding-label contract is scientifically justified by new evidence and is recorded prospectively rather than introduced as target-specific tuning.
## D017 — Structural homolog-pocket correspondence measurement for Level-2

**Decision date:** 2026-09-10

**Status:** ACTIVE — FROZEN / EXECUTABLE

### Decision

The Level-2 homolog branch will measure structural correspondence between an experimentally ligand-bound homolog pocket and the corresponding target pocket using a fixed, auditable structural-alignment and residue-mapping procedure.

D017 freezes the **measurement definition only**.

It does **not** define:

- the `pocket_sequence_identity` threshold;
- the `pocket_superposition_rmsd` threshold;
- the minimum mapped-residue requirement;
- the minimum pocket-coverage requirement;
- the Boolean definition of `pocket_conserved`.

Those remain explicitly **UNSET** and require a subsequent decision after the frozen D017 calibration measurements exist.

### Scope

D017 applies only to the **D008 Level-2 homolog-supported branch**.

The homolog site is derived from an experimentally ligand-occupied homolog structure.

No de novo pocket predictor is used to define the homolog site for this branch.

D017 does not modify D015. D015 governs the separate Level-3 P2Rank predicted-pocket contract.

D016 governs the separate frozen binding-affinity labels used as known answers for homolog calibration.

The D015, D016, and D017 contracts are separate and must not be merged.

### Structural aligner

The target and ligand-bound homolog structures are aligned with:

**US-align, version 20220227**

US-align provides pairwise structural alignment through optimization of a TM-score objective and produces the residue correspondence required by the D017 procedure.

Reference:

Zhang C, Shine M, Pyle AM, Zhang Y. **US-align: universal structure alignments of proteins, nucleic acids, and macromolecular complexes.** *Nature Methods.* 2022;19:1109–1115. DOI: `10.1038/s41592-022-01585-1`. PMID: 36038728.

The alignment is performed as a protein-chain structural alignment.

The D017 US-align invocation is frozen as:

`USalign target_chain.pdb homolog_chain.pdb -mol prot -mm 0 -ter 2 -atom " CA " -m {matrix_output} -o {superposition_prefix}`

The input contract requires **single-chain PDB files** for both target and homolog.

The exact biological chain represented by each input file must be recorded for every run.

The frozen alignment parameters are:

- molecule type: `prot`;
- multimer mode: `0`;
- chain mode: `2`;
- representative protein atom: `CA`;
- input representation: single-chain PDB;
- sequence-independent structural alignment;
- transformation-matrix output enabled;
- US-align superposition-artifact output enabled.

No undocumented alignment parameter changes are permitted.

Loop regions, including extracellular loops such as ECL2 where relevant to adenosine receptors, must not be manually remapped or edited after inspection of pocket similarity.

The complete per-residue correspondence produced from the alignment must be retained so that loop-region assignments, gaps, and disputed correspondences remain auditable.

### Configuration provenance

The frozen generic D017 instrument configuration is:

`references/stage5/d017/usalign_20220227_config.json`

**Frozen D017 US-align config SHA-256:**

`c4420efec72ca257d5c13c786fa90bcd435c0aa2a410ea06438fc383df68fa23`

The configuration-materialization record is:

`references/stage5/d017/materialization_20260910.txt`

**D017 configuration-materialization log SHA-256:**

`07e4e115d9fd81c4d4bdb520f87956edf000e3e8bbf342df24600750261c91b3`

The frozen US-align software provenance is:

- US-align version: `20220227`;
- source archive SHA-256: `3c6348e7d45105ade2f0fe80437a36b4e7bfdb92cdb6872a6f4912dcd24d0f8d`;
- `USalign.cpp` SHA-256: `4518d1e85bfccea3ff40de8fbf0b248faf8ebe4695d0d8b6f15f3625593c4427`;
- compiled executable SHA-256: `26ba8b626cf2600321941f0a138ada60505626e858948b5285c66f33097ee55f`;
- compiler: Apple clang 17.0.0 (`clang-1700.6.3.2`);
- build architecture: `arm64-apple-darwin25.5.0`.

The archived US-align distribution was qualified using its bundled `PDB1.pdb` and `PDB2.pdb` structures as software-only smoke fixtures.

The qualification run:

- returned exit code `0`;
- reported aligned length of 119 residues;
- reported global alignment RMSD of 2.20 Å;
- reported sequence identity of 0.824 over aligned residues;
- produced the requested rotation/translation matrix;
- produced the documented `-o` superposition and PyMOL artifacts.

No D017 calibration row was executed during software qualification.

### Pocket residue definition

The homolog pocket is defined from the experimentally bound ligand in the ligand-bound homolog structure.

A homolog residue belongs to the pocket when **any residue heavy atom lies within 4.5 Å of any ligand heavy atom**.

The 4.5 Å cutoff is applied before structural correspondence is evaluated and is applied identically across all calibration rows.

Hydrogen atoms do not define pocket membership under this rule.

The resulting homolog pocket residue set must be recorded explicitly.

The corresponding target pocket is obtained only by mapping those homolog pocket residues through the frozen target/homolog structural alignment.

No target-side de novo pocket prediction may redefine or expand the transferred homolog site.

### Structure selection rule

For each calibration comparison, use the **highest-resolution experimentally determined ligand-bound structure that satisfies the required receptor, ligand, and conformational-state criteria**.

The exact PDB identifier and biological chain used for every target and homolog structure must be recorded in the calibration artifact.

Where the exact ligand-bound homolog structure does not exist, a documented agonist proxy may define the site only where the frozen calibration record permits that proxy.

Proxy use must be recorded explicitly.

Where no usable ligand-bound homolog structure or permitted proxy exists, the calibration row is **UNRUNNABLE** and is dropped rather than patched.

No structure may be substituted after inspection of the resulting D017 measurements merely because another structure produces a more favorable correspondence.

### State assignment

Each target and homolog structure receives one conformational-state label:

- `ACTIVE`;
- `INACTIVE`;
- `UNKNOWN`.

State assignment authority is the **primary structural publication together with the corresponding PDB-entry annotation**.

When the primary structural publication explicitly assigns the deposited receptor to an active or inactive conformational state, that assignment is used.

Where the publication and PDB annotation do not support a defensible state assignment, the structure is labeled:

`UNKNOWN`

No state is inferred solely from ligand identity or agonist/antagonist naming.

The default for an unassigned structure is therefore **UNKNOWN**.

The target and homolog state assignments and their supporting provenance must be retained.

### State matching

Where possible, target and homolog structures must be compared within the same conformational state.

Every result must record:

- `target_state`;
- `homolog_state`;
- `state_match`.

If the assigned states differ:

`state_match = false`

and the comparison is labeled:

**STATE-MIXED**

The structural measurements may still be calculated and retained, but a state-mixed RMSD must not be interpreted as a pure measure of homolog-pocket conservation.

If positive and negative calibration classes separate partly according to conformational-state composition, D018 must identify that confound rather than attributing the separation entirely to pocket sequence or geometry.

Relevant primary structural evidence includes:

Oshima HS, Ogawa A, Sano FK, Akasaka H, Kawakami T, Iwama A, Okamoto HH, Nagiri C, Wei FY, Shihoya W, Nureki O. **Structural insights into the agonist selectivity of the adenosine A3 receptor.** *Nature Communications.* 2024;15:9294. DOI: `10.1038/s41467-024-53473-1`. PMID: 39511145.

### Pocket residue correspondence

US-align establishes the structural correspondence between the frozen target and homolog chains.

For each ligand-defined homolog pocket residue, the corresponding aligned target residue is identified when one exists.

Each homolog pocket residue is recorded as either:

- **mapped** to a target residue; or
- **unmapped**.

Unmapped residues remain explicit in the record and are never imputed.

The complete per-residue mapping must be retained as an audit artifact.

This requirement is particularly important for flexible or structurally divergent regions where different alignment procedures may assign different correspondences.

### Pocket sequence identity

Define:

`pocket_sequence_identity = identical mapped pocket-residue pairs / total mapped pocket-residue pairs`

Only mapped pocket-residue pairs enter this numerator and denominator.

The following must all be reported:

- number of identical mapped residue pairs;
- total number of mapped pocket-residue pairs;
- resulting `pocket_sequence_identity`.

Homolog pocket residues without a target correspondence do not enter the identity denominator, but remain explicitly represented in the mandatory coverage measurement.

No global target/homolog sequence identity may substitute for this local pocket measurement.

### Pocket superposition RMSD

`pocket_superposition_rmsd` is calculated over the **mapped pocket Cα pairs after optimal local superposition of those mapped Cα atoms**.

The RMSD is therefore measured in the locally optimized pocket-superposition frame.

It is **not** calculated as displacement of the mapped pocket atoms in the global US-align coordinate frame.

The exact mapped Cα pair set used for the calculation must be retained.

The optimal local-superposition transformation must also be retained in the calculation artifact.

No side-chain atoms or ligand atoms enter the primary D017 RMSD metric.

The use of residue-level local pocket correspondence and Cα geometry has precedent in local binding-site alignment methodology:

Brylinski M. **eMatchSite: sequence order-independent structure alignments of ligand binding pockets in protein models.** *PLoS Computational Biology.* 2014;10(9):e1003829. DOI: `10.1371/journal.pcbi.1003829`. PMID: 25232727. PMCID: PMC4168975.

D017 does not adopt eMatchSite itself; it remains an unrejected alternative local-site correspondence method.

### Mandatory coverage output

Every D017 correspondence result must report:

- total homolog pocket residues;
- mapped pocket residues;
- unmapped pocket residues;
- mapping coverage;
- identical mapped residue pairs;
- `pocket_sequence_identity`;
- `pocket_superposition_rmsd`.

Define:

`mapping_coverage = mapped homolog pocket residues / total homolog pocket residues`

Coverage must always be reported jointly with sequence identity and RMSD.

Sequence identity calculated only over mapped residues can be artificially inflated when correspondence is lossy.

RMSD can likewise appear artificially favorable if poorly corresponding pocket residues fail to map and disappear from the calculation.

Coverage is therefore a mandatory measurement output, not an optional diagnostic.

D017 does not freeze a minimum acceptable coverage.

### Visual review artifacts

Every D017 correspondence run must retain human-review visualization artifacts in addition to the numerical measurements.

US-align's frozen `-o` output is retained unchanged as the raw visualization artifact.

The frozen review renderer is:

**PyMOL 3.1.0**

PyMOL is used only to render the already-generated structural superposition for human review.

The review artifact set must include:

- the raw US-align superposed structure;
- the raw US-align PyMOL scripts;
- a whole-structure superposition image;
- a pocket-focused superposition image.

The pocket-focused image must make the ligand-defined homolog pocket and its mapped target residues visually inspectable.

The review rendering should distinguish the two structures sufficiently to expose local deviations and loop-region correspondence rather than allowing one opaque structure to completely occlude the other.

The visualization is **review-only and non-gating**.

A rendered image must never:

- define residue correspondence;
- alter `pocket_sequence_identity`;
- alter `pocket_superposition_rmsd`;
- alter mapping coverage;
- determine `pocket_conserved`;
- rescue or reject a calibration result.

The quantitative D017 measurements remain authoritative.

### Required raw artifacts

Each D017 correspondence run must retain:

- target structure identity;
- target structure SHA-256;
- homolog structure identity;
- homolog structure SHA-256;
- target PDB identifier and chain;
- homolog PDB identifier and chain;
- target-state assignment and provenance;
- homolog-state assignment and provenance;
- `state_match`;
- ligand identity;
- exact-ligand or proxy status;
- ligand-defined homolog pocket residue list;
- 4.5 Å pocket-definition parameters;
- US-align version;
- frozen US-align configuration identity and SHA-256;
- complete US-align stdout;
- US-align transformation-matrix output;
- raw US-align superposition artifacts;
- raw US-align PyMOL scripts;
- whole-structure review image;
- pocket-focused review image;
- complete per-residue correspondence mapping;
- mapped pocket residues;
- unmapped pocket residues;
- mapped Cα pair set;
- optimal local-superposition transformation;
- total homolog pocket residues;
- mapped pocket residues;
- unmapped pocket residues;
- mapping coverage;
- identical mapped residue pairs;
- `pocket_sequence_identity`;
- `pocket_superposition_rmsd`.

Intermediate and validation artifacts are retained until the relevant Stage-5 work is finalized and frozen.

### Conservation gate separation

D017 does not assign `pocket_conserved`.

Until D018 freezes the required structural thresholds and any required minimum mapping/coverage criteria:

`pocket_conserved = UNEVALUABLE`

is the only valid state.

No executable code may supply default values for:

- sequence-identity threshold;
- RMSD threshold;
- minimum mapped-residue count;
- minimum coverage.

No placeholder values such as 0.7 sequence identity or 2.0 Å RMSD may appear as executable defaults.

An implementation attempting to produce Boolean `pocket_conserved` without the D018 criteria must fail loudly.

### Relationship to D008

The frozen D017 measurements provide the structural evidence required by the existing D008 Level-2 homolog route.

The relevant outputs are:

- `pocket_sequence_identity`;
- `pocket_superposition_rmsd`;
- mapping coverage and its raw counts;
- state-match provenance.

The existing D008 field:

`pocket_conserved`

may only become Boolean after D018 freezes the conservation rule.

While `pocket_conserved` remains `UNEVALUABLE`, the D008 router must refuse to classify the homolog-supported case as Level 2.

It must not silently interpret an unset value as either conserved or non-conserved.

### Alternative methods

Local pocket-alignment methods remain serious alternatives to the D017 global-alignment-plus-local-measurement procedure.

eMatchSite remains **UNREJECTED**.

Brylinski M. **eMatchSite: sequence order-independent structure alignments of ligand binding pockets in protein models.** *PLoS Computational Biology.* 2014;10(9):e1003829. DOI: `10.1371/journal.pcbi.1003829`. PMID: 25232727. PMCID: PMC4168975.

eMatchSite constructs sequence-order-independent local binding-site alignments and provides an alternative framework for local site correspondence.

D017 selects US-align for the frozen target/homolog chain correspondence because the present Level-2 procedure requires an explicit, auditable target/homolog residue mapping from which the already-defined D008 measurements can be derived.

This decision does **not** establish that US-align is scientifically superior to eMatchSite or other established local-site comparison methods.

Any future replacement of the D017 correspondence procedure requires its own documented decision.

### Conformational-state confounding

Adenosine-receptor binding pockets can differ between receptor conformational states.

The calibration must therefore preserve conformational-state provenance rather than allowing active/inactive structural differences to be silently absorbed into `pocket_superposition_rmsd`.

Relevant primary structural evidence includes:

Oshima HS, Ogawa A, Sano FK, Akasaka H, Kawakami T, Iwama A, Okamoto HH, Nagiri C, Wei FY, Shihoya W, Nureki O. **Structural insights into the agonist selectivity of the adenosine A3 receptor.** *Nature Communications.* 2024;15:9294. DOI: `10.1038/s41467-024-53473-1`. PMID: 39511145.

If the eventual positive and negative calibration classes separate partly because of active/inactive state composition rather than homolog-pocket conservation, D018 must explicitly identify that confound.

### Governing principle

**Measure local pocket correspondence first; decide what counts as conserved separately.**

The D017 measurement procedure must remain independent of the D016 binding answer used to calibrate it.

D018 may inspect the frozen D017 measurements together with the frozen D016 known-answer labels.

D017 itself may not be altered after inspecting which measurement definition best separates those labels.

### 2026-09-10 structure-selection amendment

D017 was revisited under its existing trigger:

**a new experimentally determined structure materially changes the available same-state calibration structure set.**

The 2025 human A3 structural series materially changed the available Level-2 homolog calibration structures. The previously considered A3 structures 8YH0 and 8YH2 were verified as *Ovis aries* rather than human and are excluded from the frozen calibration manifest.

This revisit changes **structure selection and provenance only**. The frozen D017 alignment, pocket-definition, residue-mapping, coverage, sequence-identity, and local Cα RMSD measurement procedures are unchanged.

#### Proxy rule

Where the exact ligand-bound homolog structure is unavailable, a documented proxy ligand of the **same pharmacological class as the calibration ligand** is permitted when it provides a state-matched structure:

- agonist calibration ligand → agonist proxy;
- antagonist calibration ligand → antagonist proxy.

Every proxy must be recorded explicitly as a proxy.

A proxy may not be selected after inspection of D017 measurements because it produces more favorable correspondence.

#### Structure selection

For exact-ligand rows, use the highest-resolution experimentally determined structure containing the required receptor and ligand and satisfying the required conformational-state criteria.

For permitted proxy rows, use the highest-resolution experimentally determined structure containing the approved proxy ligand and satisfying the required receptor and conformational-state criteria.

Where no qualifying exact structure or permitted proxy exists, the row is `UNRUNNABLE` and is dropped rather than patched.

#### State annotation

The frozen state enum remains:

- `ACTIVE`;
- `INACTIVE`;
- `UNKNOWN`.

Publication-specific wording is retained separately in the provenance annotation.

Accordingly, 4UG2 is normalized to:

`ACTIVE`

while the publication wording:

`active-like`

is retained verbatim in its state-annotation field.

No fourth conformational-state category is introduced.

#### Species provenance

Every D017 structure manifest entry must record species at the **gene-source level**.

Human structures are expected for the frozen adenosine-receptor calibration.

If a future comparison necessarily contains different gene-source species, it must be labeled:

`SPECIES-MIXED`

Species mismatch is treated as an explicit structural-calibration confound on the same footing as `STATE-MIXED`.

A non-human structure must never be silently represented as human.

#### A3 manifest correction

The previously considered 8YH0 and 8YH2 A3 structures are excluded because their receptor gene source is *Ovis aries*.

For P3, the human A3 adenosine-bound structure 9EBH replaces 8YH0 as the same-class agonist proxy.

For N3, the human A3 antagonist-bound structure 9EHS replaces 8YH2 as the same-class antagonist proxy.

N3 therefore changes from the previously contemplated state-mixed comparison to an inactive/inactive, human/human comparison.

This correction occurred **before any D017 calibration structure was downloaded or measured** and therefore does not constitute outcome-driven structure selection.

### 2026-09-11 construct-boundary and manifest amendment

D017 was revisited following the completed read-only construct-boundary audit.

The amendment changes only the definition and provenance of the derived receptor-only alignment inputs. The US-align procedure, 4.5 Å pocket definition, residue correspondence, coverage, sequence-identity, and local Cα RMSD measurement procedures remain unchanged.

#### Equivalent-chain selection

Where multiple equivalent receptor chains satisfy all frozen structure, species, ligand, and state requirements, select the **lexicographically first author chain ID**.

For 4UG2, receptor chains A and B both contain the exact calibration ligand CGS21680. Chain A is therefore selected deterministically.

The alternative eligible chain and ligand instance remain recorded in the manifest provenance.

#### Canonical-mapped residue rule

A coordinate-bearing deposited residue enters the D017 receptor-alignment input when its **position maps uniquely to the frozen canonical human receptor sequence**.

Mapping is **position-only**.

The deposited amino-acid identity does not need to match the canonical identity for retention.

Therefore:

- a coordinate-bearing residue with a unique canonical position is retained even when its deposited identity differs from canonical;
- the retained residue receives a **mutation flag** when deposited identity differs from canonical;
- engineered insertions and other coordinate-bearing residues without a unique canonical position are excluded from the D017 receptor-alignment input;
- excluded engineered/noncanonical coordinates remain in the authoritative raw mmCIF artifact.

No coordinate or atom identity is altered during extraction.

#### Pocket mutation provenance

For every retained residue, the derived mapping records:

- deposited author residue identifier;
- deposited residue identity;
- canonical receptor position;
- canonical residue identity;
- mutation flag.

If an identity mismatch occurs for a residue belonging to the D017 ligand-defined pocket under the frozen 4.5 Å heavy-atom rule, the mismatch must be explicitly called out in the D017 revisit log for the affected calibration row in addition to being retained in the derived mapping artifact.

#### Derived author-to-canonical residue map

The author-to-canonical residue map is a **derived frozen artifact** and is part of the provenance required to reproduce the D017 receptor-alignment inputs.

The mapping artifact must record, at minimum:

- source structure identity and SHA-256;
- selected author chain;
- canonical sequence identity and SHA-256;
- deposited author residue identifiers;
- canonical positions;
- deposited and canonical residue identities;
- mutation flags;
- excluded coordinate-bearing residues;
- mapping status.

The mapping artifact must be hashed and its SHA-256 recorded alongside the frozen calibration-structure manifest hash before any D017 alignment is executed.

**Mapping-artifact SHA-256:** `PENDING MATERIALIZATION`

No D017 alignment may run until this mapping artifact has been materialized, validated, hashed, and recorded here.

#### Frozen manifest and canonical-sequence provenance

The fully verified D017 calibration-structure manifest is:

`references/stage5/d017/calibration_structure_manifest.json`

**Manifest SHA-256:**

`f3b477b23c0505845367cb28383ca024e5692ec8a13f2696de3c04fef8b77b5d`

The frozen canonical human receptor sequences are:

- **ADORA2A / UniProt P29274**  
  SHA-256: `fa327e00c2245b9aa5aa65816f078bdd5664de1531fb8404c2b5f60d8e96f239`
- **ADORA2B / UniProt P29275**  
  SHA-256: `4a6c391c07cdd34d0050367c9312638f37a74fa2215f1a01fb7dc63073c15b77`
- **ADORA3 / UniProt P0DMS8**  
  SHA-256: `b117a029664c0025d6b833df72fef925dbd4f70936ee9a04ec09254edd59af92`

The frozen D017 measurement configuration remains:

`c4420efec72ca257d5c13c786fa90bcd435c0aa2a410ea06438fc383df68fa23`

The materialization record remains:

`07e4e115d9fd81c4d4bdb520f87956edf000e3e8bbf342df24600750261c91b3`

### 2026-09-11 alignment-input representation amendment

D017 was revisited after implementation exposed a conflict between the frozen exact-coordinate requirement and standard PDB fixed-width coordinate precision.

The 9EHS deposited coordinates contain values exceeding the precision representable without alteration in standard PDB coordinate fields. Converting these coordinates to standard PDB format would therefore require rounding or another coordinate-changing transformation.

Because D017 requires exact preservation of deposited coordinates, **standard PDB is not an acceptable scientific alignment-input representation**.

This amendment changes only the derived alignment-input representation. The structural measurement definitions remain unchanged.

#### Alignment input format

The D017 alignment input contract is changed from:

`single_chain_pdb`

to:

`single_chain_pdbx_mmcif`

The derived receptor-only alignment input must therefore be a **single-chain PDBx/mmCIF file** containing only the canonical-mapped receptor coordinates required by D017.

The authoritative raw deposited mmCIF remains unchanged.

The derived single-chain mmCIF must preserve:

- deposited atom coordinates exactly;
- deposited atom identity;
- deposited residue identity;
- author chain identifier;
- author residue number;
- insertion code;
- atom naming and ordering insofar as supported by the mmCIF representation.

No coordinate rounding, truncation, reparameterization, or coordinate-space transformation is permitted during extraction.

US-align 20220227 accepts PDBx/mmCIF input directly, so this amendment does not change the frozen alignment software or alignment method.

#### PDB compatibility

Standard PDB files may still be generated as **secondary human-review artifacts** where useful, but they are not the authoritative D017 alignment inputs and must never replace the exact-coordinate mmCIF inputs.

Any PDB rendering or visualization artifact must remain explicitly downstream of the exact-coordinate alignment input.

A PDB conversion that changes coordinate values must be recorded as a derived visualization artifact and must not be used as the scientific source for D017 measurements.

#### Configuration provenance

The previous D017 configuration identified the input contract as:

`single_chain_pdb`

That configuration is superseded by this amendment.

A new D017 configuration must be materialized with the input contract:

`single_chain_pdbx_mmcif`

and its SHA-256 must replace the prior D017 configuration hash before any calibration alignment is executed.

The previous configuration and hash remain retained as historical provenance.

#### Measurement invariance

This amendment does not change:

- target/homolog structure selection;
- equivalent-chain selection;
- species/state requirements;
- canonical position-only residue mapping;
- mutation-flag behavior;
- 4.5 Å homolog-pocket definition;
- per-residue correspondence;
- mapping coverage;
- `pocket_sequence_identity`;
- local Cα superposition;
- `pocket_superposition_rmsd`;
- visual-review role.

The amendment exists solely to ensure that the frozen measurement procedure operates on exact deposited coordinates.

Completed the frozen 4.5 Å mutation-pocket audit.

Added:

- [audit implementation](/Users/mileshuang/Desktop/sbdd-project/evaluation/d017_mutation_pocket_audit.py)
- [materialization script](/Users/mileshuang/Desktop/sbdd-project/scripts/stage5/audit_d017_mutation_pockets.py)
- [updated focused tests](/Users/mileshuang/Desktop/sbdd-project/tests/test_d017_construct_audit.py)
- [machine-readable audit artifact](/Users/mileshuang/Desktop/sbdd-project/references/stage5/d017/receptor_inputs/mutation_pocket_audit.json)

Artifact SHA-256: `63a723e48b99231277a8402f428b1814888020b940570d4a8c3c0e1b6acb3bb0`

| Structure / mutation | Pocket? | Min distance | Minimizing raw atom pair |
|---|---:|---:|---|
| 2YDV A48 `ALA → L` | No | 13.591461 Å | `O` [348] → `NEC C52` [2459] |
| 2YDV A54 `LEU → A` | No | 11.103732 Å | `O` [384] → `NEC O2'` [2465] |
| 2YDV A65 `ALA → T` | No | 9.654675 Å | `C` [461] → `NEC C2` [2474] |
| 2YDV A89 `ALA → Q` | Yes | 3.972587 Å | `N` [628] → `NEC C52` [2459] |
| 2YDV A154 `ALA → N` | No | 17.560295 Å | `N` [1122] → `NEC N1` [2473] |
| 4UG2 A48 `ALA → L` | No | 13.338007 Å | `O` [328] → `NGI C1` [4430] |
| 4UG2 A54 `LEU → A` | No | 10.892390 Å | `O` [364] → `NGI O4` [4441] |
| 4UG2 A65 `ALA → T` | No | 7.661646 Å | `O` [442] → `NGI C12` [4454] |
| 4UG2 A89 `ALA → Q` | Yes | 3.879394 Å | `N` [608] → `NGI C1` [4430] |
| 4UG2 A154 `ALA → N` | No | 12.966958 Å | `N` [1102] → `NGI C18` [4460] |
| 9EHS R97 `ARG → S` | No | 8.437770 Å | `NH2` [4886] → `A1BII C1` [7181] |
| 9EHS R160 `ALA → N` | No | 20.480164 Å | `C` [5403] → `A1BII C16` [7185] |

The artifact records the full `_atom_site` source IDs plus author and label identifiers, coordinates, mapping provenance, raw-structure hashes, and frozen manifest/mapping-artifact hashes.

Tests: focused suite 11 passed; full suite 45 passed. No ambiguity found. No US-align or D017 calibration was run, no D018 threshold was introduced, and no frozen artifact was modified.

### Governing principle

**Measure local pocket correspondence from reproducible receptor inputs; do not let engineered construct sequence or post hoc structural choices define the correspondence.**

The receptor alignment input is determined mechanically from the frozen canonical position map. Deposited residue identity is preserved and flagged when it differs from canonical; engineered or otherwise noncanonical positions remain excluded from the alignment input but preserved in the raw source artifact.

### Revisit when

- US-align produces unstable or materially non-reproducible pocket mappings for the frozen calibration set;
- loop-region correspondence, including ECL2 where relevant, materially determines calibration outcomes in a way that makes the frozen chain-alignment procedure unsuitable;
- state-mixed comparisons materially confound the calibration;
- eMatchSite or another qualified local pocket-alignment method demonstrates materially better validated correspondence for this exact task;
- a new experimentally determined structure materially changes the available same-state calibration structure set;
- the 4.5 Å ligand-contact pocket definition proves inadequate for the target family;
- D018 demonstrates that the frozen D017 measurements cannot support a defensible conservation rule;
- new evidence shows that mapped Cα local RMSD is insufficient for the intended Level-2 characterization claim;
- a change to the measurement contract is scientifically justified and recorded prospectively rather than introduced after inspection of favorable calibration outcomes.
# D018 — Level-2 Homolog-Pocket Conservation Verdict

**Decision date:** 2026-09-13

**Status:** APPROVED

## Decision

D018 defines the rule by which the quantitative D017 homolog-pocket measurements are converted into the Level-2 target-arm field `pocket_conserved`.

D018 does **not** alter the D017 measurement procedure. The following remain fixed:

- homolog pocket definition;
- US-align 20220227;
- position-only receptor mapping;
- exact-coordinate receptor inputs;
- mapping coverage definition;
- pocket sequence-identity definition;
- local mapped-pocket Cα RMSD definition;
- required state/species provenance.

D018 must establish explicit acceptance criteria for:

1. mapping coverage;
2. pocket sequence identity;
3. local pocket Cα RMSD;
4. any required minimum mapped-pocket-residue count or equivalent completeness condition.

These criteria must be selected from the frozen D017 calibration panel rather than introduced as arbitrary target-specific cutoffs.

`pocket_conserved` is now evaluable for cases that satisfy the D018 eligibility conditions.

## Calibration role

The frozen D017 structure panel contains:

- **P1:** A2A → A1, agonist/agonist context;
- **P3:** A2A → A3, agonist/agonist context;
- **N1:** A2A → A1, structural agonist context;
- **N2:** A2A → A2B, active/active context;
- **N3:** A2A → A3, inactive/inactive context.

D018 shall use the completed D017 measurements from this frozen calibration panel to determine whether a single fixed rule can distinguish the intended positive and negative calibration cases without target-specific tuning.

No threshold may be chosen merely because it makes an individual calibration case pass.

## Calibration discrimination requirement

Before D018 approval, completed D017 measurements must be attached for P1, P3, N1, N2, and N3, with per-case pass/fail shown under every proposed conservation rule.

P3 and N3 are the same receptor pair (A2A→A3) represented in different structural states. Sequence identity and mapping coverage therefore cannot be assumed to discriminate them. The D018 analysis must identify which frozen D017 measurement, if any, separates P3 from N3 and show the measured values explicitly.

If no frozen D017 measurement separates P3 from N3 under the proposed rule, the calibration panel does not constrain a discriminating conservation rule. D018 must state that limitation and must not freeze thresholds that the panel cannot falsify.

**State is provenance, not a criterion.**

## P1 calibration observation

The completed P1 measurement currently provides:

- total homolog-pocket residues = 14;
- mapped = 14;
- unmapped = 0;
- mapping coverage = 1.0;
- identical mapped residue pairs = 13/14;
- pocket sequence identity = 0.9285714285714286;
- local pocket Cα RMSD = 0.4398073045565676 Å.

These are observations from D017 and are **not themselves D018 thresholds**.

## Conservation verdict

The D018 verdict must remain a separate classification layer above the three D017 measurements.

The intended semantic distinction is:

> **D017 measures homolog-pocket correspondence. D018 decides whether that measured correspondence is sufficient to treat the homolog pocket as conserved for the Level-2 target arm.**

D018 must not allow the visualization artifacts, US-align exit status, global whole-structure RMSD, or any Level-3 pocket characterization to rescue a failed Level-2 conservation decision.


## Final D018 Rule

D018 is approved as the complete fixed Level-2 homolog-pocket conservation rule.

### Eligibility

A case is eligible for the Level-2 conservation verdict only when both conditions hold:

- mapping coverage = **1.0**;
- mapped homolog-pocket residue count >= **11**.

These are completeness conditions for the experimentally ligand-defined homolog pocket. They are not class-discriminating scores.

### Structural-conservation verdict

For an eligible case:

> `pocket_conserved = TRUE` iff local mapped-pocket C-alpha RMSD <= **0.5370920576693073 Å**.

The cutoff is the midpoint between the largest positive-calibration pocket RMSD and the smallest negative-calibration pocket RMSD:

- largest positive RMSD = **0.4398073045565676 Å**;
- smallest negative RMSD = **0.634376810782047 Å**;
- midpoint = **0.5370920576693073 Å**.

### Pocket sequence identity

**Pocket sequence identity carries no weight in the Level-2 verdict.**

The rebuilt calibration panel demonstrated why: P3 is positive with pocket sequence identity **0.8333333333333334**, while 5UEN B is a structurally negative case with higher pocket sequence identity **0.85**. Therefore sequence identity cannot support a fixed discriminator consistent with the intended panel labels, whereas local pocket RMSD does.

This preserves the semantic boundary of Level 2: the verdict is based on demonstrated local pocket structural conservation, not residue-identity similarity by itself.

### Rebuilt calibration panel — final pass/fail

| Calibration row | Intended class | Mapped residues | Coverage | Pocket sequence identity | Pocket C-alpha RMSD (Å) | Eligibility | `pocket_conserved` |
|---|---|---:|---:|---:|---:|---|---|
| P1 | Positive | 14 | 1.0 | 0.9285714285714286 | 0.4398073045565676 | PASS | **PASS** |
| P3 | Positive | 12 | 1.0 | 0.8333333333333334 | 0.4365457976453139 | PASS | **PASS** |
| N3 / 9EHS R | Negative | 11 | 1.0 | 0.6363636363636364 | 1.5790088912154592 | PASS | **FAIL** |
| NEG_A_9EBI_R | Negative | 22 | 1.0 | 0.5454545454545454 | 0.634376810782047 | PASS | **FAIL** |
| NEG_B_5UEN_B | Negative | 20 | 1.0 | 0.85 | 1.6228560849340186 | PASS | **FAIL** |

The rebuilt panel therefore reproduces the intended calibration labels under the single fixed RMSD rule.

### 5UEN chain-B provenance

**The 5UEN mmCIF contains coordinate-bearing receptor copies on auth chains A and B, each paired with DU1 1201; the approved candidate is the B-copy (`5UEN B` with `DU1 B 1201`). The prior chain-A description was the erroneous provenance statement.**

### Panel amendment

The approved rebuilt panel is:

- P1 — positive;
- P3 — positive;
- N3 / 9EHS R — existing preregistered structural negative;
- NEG_A_9EBI_R / 9EBI R — replacement A3 structural negative;
- NEG_B_5UEN_B / 5UEN B — replacement A1 structural negative.

N1 and N2 are excluded from the structural-conservation calibration because their negative status is based on ligand assignment/context, which is outside the frozen D017 structural measurements. 7LD4 R is excluded because it failed its preregistered negative-direction screen.

The D017 measurement contract itself remains unchanged.


## Claim boundary

If the frozen D018 criteria are satisfied, the authorized Level-2 target-arm claim is limited to:

> **The target pocket is conserved by the frozen D018 homolog-pocket correspondence criterion.**

This does **not** by itself establish:

- ligand compatibility;
- target-ligand interaction reproduction;
- docking success;
- Level-3 predicted-pocket validity;
- generated-molecule binding;
- biological efficacy.

Those remain separate claim layers.

### Governing principle

D018 must convert the frozen D017 measurements into a deterministic, generator-independent Level-2 target-arm verdict without changing the underlying measurements or introducing target-specific tuning.

### Revisit when

Revisit D018 only if the frozen calibration panel, D017 measurement definitions, or Stage-5 Level-2 claim boundary is formally amended.
