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