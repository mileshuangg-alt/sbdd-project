# Session 006 — Stage 4 Novelty / Chemical-Space Characterization

## Session Goal

Implement Stage 4 of the generator-agnostic evaluation cascade.

Stage 4 evaluates where surviving generated molecules sit in chemical space without introducing an additional hard attrition gate.

The central Stage 4 questions are:

1. How redundant are the generated molecules with respect to one another?
2. How similar are they to known chemistry associated with the target?
3. How similar are they to established approved-drug chemistry?

Stage 4 therefore consists of:

- **Stage 4A — internal generated-set similarity**
- **Stage 4B — target-ligand-space similarity**
- **Stage 4C — approved-drug-space similarity**

---

## Stage 4 Design Decision

Stage 4 is explicitly **non-attritional**.

Unlike Stages 1–3, Stage 4 does not remove molecules from the cascade based on structural similarity.

Instead, all surviving molecules receive chemical-space similarity measurements that can later be used for ranking, interpretation, and generator comparison.

This avoids imposing an arbitrary universal novelty cutoff.

Therefore:

```text
Stage 4 entering: 16
Stage 4 leaving:  16
Stage 4 attrition: 0
```

Cumulative strict cascade survival remains:

```text
16 / 20 = 80%
```

---

## Shared Molecular Representation

All Stage 4 similarity analyses use the same molecular representation and similarity metric.

### Fingerprint

Morgan fingerprint:

```text
radius = 2
fingerprint size = 2048 bits
chirality = enabled
```

The Morgan radius defines the local atomic environments encoded into the molecular fingerprint.

A radius of 2 means that atomic environments extending up to two bonds from each atom contribute to the representation.

### Similarity Metric

Tanimoto similarity is used to compare Morgan fingerprints.

Conceptually:

```text
molecular structure
      ↓
Morgan fingerprint
      ↓
binary structural representation
      ↓
Tanimoto comparison
      ↓
structural similarity score
```

The same fingerprint definition is used for:

- generated molecules
- known target ligands
- approved drugs

This ensures that differences between Stage 4A, 4B, and 4C arise from the **comparison population**, rather than from changing the molecular representation.

---

## Stage 4 Input

Stage 4 consumes the 16 molecules that passed the combined Stage 3 structural-plausibility gate.

Molecule IDs:

```text
0
1
2
3
5
6
7
8
9
10
11
12
14
17
18
19
```

The Stage 4 molecules are loaded from:

```text
experiments/phase1_diffsbdd/evaluation/stage3_input.sdf
```

rather than reparsing the original generator SDF.

This preserves the upstream evaluation boundary and avoids reconstructing molecules that have already been excluded.

---

# Stage 4A — Internal Generated-Set Similarity

## Goal

Stage 4A measures redundancy within the surviving generated set.

The question is:

> How structurally similar are the generated molecules to one another?

Stage 4A does not classify molecules as novel or non-novel.

Instead, it records the internal similarity distribution and each molecule's nearest generated neighbor.

---

## Pairwise Comparison

With 16 surviving molecules, the number of unique unordered molecule pairs is:

```text
16 × 15 / 2 = 120
```

All 120 unique pairs were evaluated exactly once.

For example:

```text
molecule 0 vs molecule 1
```

is evaluated, while the redundant reverse comparison:

```text
molecule 1 vs molecule 0
```

is not separately stored.

The first manually checked comparison was:

```text
molecule 0 vs molecule 1
Tanimoto = 0.04054054054054054
```

The pairwise evaluator reproduced this value correctly.

---

## Stage 4A Pairwise Results

Full pairwise distribution:

```text
Number of pairs: 120

Mean similarity:
0.08916327987437872

Standard deviation:
0.030563299746668975

Median similarity:
0.08722826086956521

Minimum similarity:
0.014705882352941176

Maximum similarity:
0.19607843137254902
```

Rounded:

```text
Mean:    0.0892
SD:      0.0306
Median:  0.0872
Minimum: 0.0147
Maximum: 0.1961
```

Under the predefined Morgan/Tanimoto representation, the surviving generated set therefore shows low internal fingerprint similarity and no obvious near-duplicate pairs.

No universal diversity threshold is imposed.

---

## Molecule-Level Internal Similarity

For each molecule, the most similar generated neighbor is identified.

The molecule-level output records:

```text
molecule_id
nearest_generated_neighbor_id
nearest_generated_similarity
```

This converts:

```text
120 pairwise comparisons
        ↓
nearest-neighbor search
        ↓
16 molecule-level records
```

Example:

```text
molecule_id = 0
nearest_generated_neighbor_id = 3
nearest_generated_similarity = 0.14583333333333334
```

---

## Stage 4A Artifacts

Detailed pairwise diagnostic:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4a_pairs.csv
```

Dimensions:

```text
120 pairwise rows
+ header
= 121 lines
```

Molecule-level summary:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4a.csv
```

Dimensions:

```text
16 molecule rows
+ header
= 17 lines
```

---

# Stage 4B — Target-Ligand-Space Similarity

## Goal

Stage 4B asks:

> How structurally similar is each generated molecule to known chemistry associated with the target?

For the Phase 1 baseline, the target is the human A2A receptor corresponding to the 3RFM generation experiment.

Rather than querying a changing live database during every evaluation run, a target-specific reference set is constructed once and frozen locally.

---

## ChEMBL Environment

The ChEMBL Python client was added to the generator-independent evaluation environment.

Pinned client:

```text
chembl_webresource_client = 0.10.9
```

Reference database:

```text
ChEMBL 37
```

The client version and database release are distinct:

```text
client version
→ controls how ChEMBL is accessed

ChEMBL release
→ controls which scientific records define the reference set
```

---

## Target Validation

Target ChEMBL ID:

```text
CHEMBL251
```

Resolved target:

```text
Adenosine receptor A2a
Homo sapiens
SINGLE PROTEIN
```

The reference builder validates:

- target ChEMBL ID
- organism
- target type

before constructing the ligand reference.

This prevents accidental construction of a reference set for:

- the wrong species
- a protein family
- a different molecular target

---

## Target Activity Definition

Known target chemistry is defined from qualifying ChEMBL activity records.

Accepted activity types:

```text
Ki
Kd
IC50
EC50
```

Additional requirements:

```text
standard_value is not null
standard_relation ∈ {=, <, <=}
pChEMBL >= 6.0
```

An activity record represents an experimental measurement connecting a molecule to the target.

One molecule can have multiple qualifying activity records.

Therefore, activity records are used as the experimental evidence for inclusion, but the final reference set is deduplicated at the molecular-structure level.

---

## ChEMBL Provenance

For qualifying target ligands, provenance is retained so that the reason a reference molecule entered the set can be reconstructed.

Relevant provenance includes:

- ChEMBL molecule IDs
- parent molecule IDs
- activity IDs
- source document IDs
- pChEMBL values

For example, one reference structure can have multiple qualifying activity records from different source documents.

This preserves the chain:

```text
reference structure
      ↓
ChEMBL molecule record
      ↓
qualifying activity
      ↓
source document
```

---

## Structure-Level Deduplication

Qualifying ChEMBL activity structures are parsed with RDKit.

Structures are then converted to canonical isomeric SMILES.

Deduplication is performed by canonical structure rather than simply by ChEMBL molecule ID.

Therefore:

```text
multiple activity records
and/or
multiple ChEMBL IDs
        ↓
same canonical molecular structure
        ↓
one reference structure
```

All associated provenance is retained.

---

## Frozen A2A Reference Set

The final target reference contains:

```text
5,344 unique structures
```

Audit:

```text
Rows:              5344
Unique structures: 5344
Duplicates:        0
```

Potency audit:

```text
Lowest recorded pChEMBL: 6.0
All retained pChEMBL values >= 6.0: True
```

Artifact:

```text
references/chembl37/ADORA2A_target_ligands.csv
```

The reference is considered **frozen** because future Stage 4B runs consume this local snapshot rather than querying ChEMBL live.

This ensures that future generator comparisons use the identical target-chemistry reference population.

For example:

```text
DiffSBDD ─┐
          ├→ same frozen A2A reference
FLOWR ────┘
```

---

## Target Reference Fingerprints

All 5,344 target-reference structures successfully loaded into RDKit.

They were fingerprinted using the same predefined Morgan generator used for the generated molecules.

Audit:

```text
Reference ligands: 5344
Fingerprints:      5344
Fingerprint size:  2048 bits
```

---

## Stage 4B Comparisons

Each of the 16 generated molecules was compared against all 5,344 known A2A reference structures.

Total comparisons:

```text
16 × 5,344 = 85,504
```

For each generated molecule, Stage 4B records:

- nearest target ligand ID
- nearest target ligand structure
- nearest-target Tanimoto similarity
- mean similarity to the five nearest target ligands
- target reference-set size

The nearest-target similarity answers:

> What known target-associated structure is closest to this generated molecule?

The top-5 mean answers:

> How similar is this generated molecule to its local neighborhood within known target chemistry?

---

## Stage 4B Results

Nearest-target similarity:

```text
Mean:
0.22516831662981335

Standard deviation:
0.05067860345638793

Median:
0.2144005143040823

Minimum:
0.13924050632911392

Maximum:
0.30434782608695654
```

Rounded:

```text
Mean:    0.2252
SD:      0.0507
Median:  0.2144
Minimum: 0.1392
Maximum: 0.3043
```

Top-5 target-ligand similarity:

```text
Mean:
0.20605486491654418

Standard deviation:
0.04366729039981743
```

Rounded:

```text
Mean: 0.2061
SD:   0.0437
```

These scores are retained as target-space characterization.

No target-similarity threshold is used for Stage 4 attrition.

---

## Stage 4B Artifact

Molecule-level output:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4b.csv
```

Dimensions:

```text
16 molecule rows
+ header
= 17 lines
```

Each molecule was compared against:

```text
target_reference_count = 5344
```

---

# Stage 4C — Approved-Drug-Space Similarity

## Goal

Stage 4C asks:

> How structurally similar is each generated molecule to established approved small-molecule chemistry?

Unlike Stage 4B, this reference space is target-independent.

The goal is not to determine whether the generated molecules resemble A2A ligands specifically, but whether they occupy chemistry already represented among approved small-molecule drugs.

---

## Approved-Drug Definition

The approved-drug reference was constructed from ChEMBL 37.

Initial selection:

```text
max_phase = 4
molecule_type = Small molecule
```

`max_phase = 4` identifies marketed/approved drugs in ChEMBL.

The reference is not restricted to FDA approvals specifically.

The intent is to characterize proximity to established approved-drug chemistry broadly.

---

## Parent Normalization

Approved ChEMBL records can represent alternative forms of the same underlying drug chemistry.

Examples include:

- hydrochloride salts
- sodium salts
- phosphate forms
- other alternative forms

Counting every form independently would artificially increase the density of some regions of approved-drug chemical space.

Therefore, approved records are normalized to their ChEMBL parent structures where a parent relationship is available.

Example:

```text
CHEMBL14
CARBACHOL

C[N+](C)(C)CCOC(N)=O.[Cl-]

        ↓ parent normalization

CHEMBL965
CARBAMOYLCHOLINE

C[N+](C)(C)CCOC(N)=O
```

The chloride-containing approved record therefore contributes the parent molecular structure to the similarity reference.

However, the approved record identity is retained as provenance.

---

## Parent-Normalization Logic

The approved-reference builder handles four cases.

### Case 1 — self-parented record

Example:

```text
CHEMBL2 → CHEMBL2
```

The existing approved record already represents the parent.

No additional ChEMBL request is needed.

### Case 2 — alternative form with external parent

Example:

```text
CHEMBL14 → CHEMBL965
```

The external parent molecule is retrieved and its structure is used.

### Case 3 — previously retrieved external parent

External parent records are cached.

If multiple approved forms resolve to the same parent:

```text
approved form A ─┐
approved form B ─┼→ same parent
approved form C ─┘
```

the parent is retrieved only once.

### Case 4 — missing hierarchy

Some approved ChEMBL records have no parent hierarchy.

If the record itself contains a usable structure, its own structure can represent the reference entry.

If neither a parent nor a usable molecular structure can be resolved, the record cannot define a Morgan-fingerprint chemical-space point and is excluded from the structural reference.

---

## Structurally Unresolvable Approved Records

A concrete edge case was:

```text
CHEMBL1200557
MANGANESE SULFATE ANHYDROUS
```

ChEMBL metadata:

```text
max_phase = 4
molecule_type = Small molecule
molecule_hierarchy = None
molecule_structures = None
```

Because no usable molecular structure exists, the record cannot be fingerprinted.

It is therefore excluded from the Stage 4C structural reference rather than causing the reference build to fail.

The number of structurally unresolvable approved records is explicitly counted.

---

## Approved-Reference Construction Performance

The full reference build used progress reporting and parent caching.

Example progress:

```text
Processed 250 approved records; 245 unique structures; 4 external parent lookups.
Processed 500 approved records; 487 unique structures; 15 external parent lookups.
Processed 1000 approved records; 947 unique structures; 66 external parent lookups.
Processed 2000 approved records; 1600 unique structures; 437 external parent lookups.
Processed 3000 approved records; 2031 unique structures; 832 external parent lookups.
Processed 3250 approved records; 2127 unique structures; 954 external parent lookups.
```

The build required substantial time because external parent resolution requires live ChEMBL requests.

This cost is paid only during one-time reference construction.

Normal Stage 4C evaluation consumes the frozen local reference and does not require live ChEMBL access.

---

## Frozen Approved-Drug Reference

Final construction:

```text
158 approved records skipped because no usable structure could be resolved

2,198 unique parent-normalized approved-drug structures
```

Artifact:

```text
references/chembl37/approved_drugs.csv
```

---

## Approved-Reference Audit

File integrity:

```text
2,198 structures
+ header
= 2,199 lines
```

Structural uniqueness:

```text
Rows:              2198
Unique structures: 2198
Duplicates:        0
```

RDKit parsing:

```text
Structures: 2198
Parsed:     2198
Failed:     0
```

RDKit emitted warnings for a small number of unusual hydrogen-containing structures:

```text
WARNING: not removing hydrogen atom without neighbors
```

These were warnings rather than parse failures.

All 2,198 frozen reference structures produced valid RDKit molecules.

---

## Withdrawal Metadata

Withdrawal status was retained as descriptive metadata.

Reference composition:

```text
Total structures: 2198

Associated with at least one withdrawn approved record:
268

Without a withdrawn approved record:
1930
```

Withdrawn drugs remain part of the Stage 4C reference because the scientific question is proximity to **established approved-drug chemistry**, not current market availability.

Withdrawal status does not alter the similarity score and is not used as a filter.

---

## Approval-Year Metadata

First-approval information is also retained as descriptive provenance.

It does not influence:

- reference inclusion
- fingerprint generation
- similarity calculation
- Stage 4 ranking

Some ChEMBL records lack first-approval metadata.

Missing approval-year metadata is preserved as missing data rather than treated as an evaluation failure.

---

## Approved-Drug Fingerprints

All 2,198 approved reference structures were fingerprinted using the same Morgan generator as:

- generated molecules
- A2A target ligands

Audit:

```text
Fingerprints:     2198
All fingerprints: 2048 bits
```

---

## Stage 4C Comparisons

Each of the 16 generated molecules was compared against all 2,198 approved-drug reference structures.

Total comparisons:

```text
16 × 2,198 = 35,168
```

For each generated molecule, Stage 4C records:

- nearest approved parent ChEMBL ID
- nearest approved parent name
- associated approved ChEMBL IDs
- associated approved drug names
- nearest approved structure
- first-approval metadata
- withdrawal metadata
- nearest-approved Tanimoto similarity
- mean similarity to the five nearest approved structures
- approved reference-set size

---

## Stage 4C Example Results

Examples of nearest approved-drug neighbors include:

```text
molecule 0
→ TRANEXAMIC ACID
→ Tanimoto = 0.2500

molecule 3
→ MESALAMINE
→ Tanimoto = 0.3824

molecule 7
→ LORLATINIB
→ Tanimoto = 0.1569

molecule 14
→ HYDRALAZINE
→ Tanimoto = 0.3611
```

Parent normalization is visible in the results.

For example:

```text
molecule 2
→ parent: DOPAMINE
→ approved records:
   DOPAMINE
   DOPAMINE HYDROCHLORIDE
```

These approved forms occupy one parent-normalized reference structure rather than multiple chemical-space points.

---

## Stage 4C Results

Nearest-approved similarity:

```text
Mean:
0.24609454761534533

Standard deviation:
0.06357601605631347

Median:
0.229020979020979

Minimum:
0.1568627450980392

Maximum:
0.38235294117647056
```

Rounded:

```text
Mean:    0.2461
SD:      0.0636
Median:  0.2290
Minimum: 0.1569
Maximum: 0.3824
```

Top-5 approved-drug similarity:

```text
Mean:
0.2183966031108081

Standard deviation:
0.04945683064062478
```

Rounded:

```text
Mean: 0.2184
SD:   0.0495
```

Two nearest-neighbor records lack first-approval metadata.

This reflects missing ChEMBL metadata rather than failed similarity calculations.

---

## Stage 4C Artifact

Molecule-level output:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4c.csv
```

Dimensions:

```text
16 molecule rows
+ header
= 17 lines
```

Each molecule was compared against:

```text
approved_reference_count = 2198
```

---

# Combined Stage 4 Artifact

Stage 4A, 4B, and 4C molecule-level outputs are combined by original `molecule_id`.

Inputs:

```text
novelty_4a.csv
novelty_4b.csv
novelty_4c.csv
```

Combination uses:

```text
outer merge
+
one-to-one molecule-ID validation
```

The outer merge prevents a missing molecule from silently disappearing.

The one-to-one validation prevents duplicate molecule IDs from silently producing duplicated output rows.

---

## Combined Provenance Audit

Combined molecule count:

```text
16
```

Molecule IDs:

```text
0
1
2
3
5
6
7
8
9
10
11
12
14
17
18
19
```

These exactly match the molecules entering Stage 4.

All core Stage 4 similarity fields are populated.

The only missing values are:

```text
nearest_approved_first_approvals: 2
```

These result from unavailable ChEMBL approval-year metadata.

---

## Combined Output Schema

The final Stage 4 artifact contains:

```text
molecule_id

nearest_generated_neighbor_id
nearest_generated_similarity

nearest_target_ligand_ids
nearest_target_ligand_smiles
nearest_target_similarity
target_top5_mean_similarity
target_reference_count

nearest_approved_parent_id
nearest_approved_parent_name
nearest_approved_drug_ids
nearest_approved_drug_names
nearest_approved_drug_smiles
nearest_approved_first_approvals
nearest_approved_withdrawn_flags
nearest_approved_similarity
approved_top5_mean_similarity
approved_reference_count
```

Final artifact:

```text
experiments/phase1_diffsbdd/evaluation/novelty.csv
```

---

# Stage 4 Summary

The three Stage 4 analyses answer different chemical-space questions.

| Substage | Comparison | Question |
|---|---|---|
| Stage 4A | generated vs generated | How redundant is the generated set? |
| Stage 4B | generated vs known target ligands | How close is each molecule to known target chemistry? |
| Stage 4C | generated vs approved drugs | How close is each molecule to established approved-drug chemistry? |

Summary statistics:

```text
Stage 4A — generated vs generated

Pairwise mean:
0.0892

Pairwise SD:
0.0306

Pairwise median:
0.0872

Pairwise range:
0.0147–0.1961
```

```text
Stage 4B — generated vs known A2A ligands

Mean nearest:
0.2252

SD nearest:
0.0507

Median nearest:
0.2144

Nearest range:
0.1392–0.3043

Mean top-5:
0.2061
```

```text
Stage 4C — generated vs approved drugs

Mean nearest:
0.2461

SD nearest:
0.0636

Median nearest:
0.2290

Nearest range:
0.1569–0.3824

Mean top-5:
0.2184
```

---

# Interpretation

Under the predefined Morgan radius-2 / 2048-bit / chirality-aware representation, the surviving DiffSBDD molecules show low internal fingerprint similarity.

The generated set therefore does not contain obvious highly redundant or near-duplicate structures among the 16 Stage 3 survivors.

The molecules occupy measurable but generally modest similarity neighborhoods within both:

- known human A2A ligand space
- approved small-molecule drug space

Some generated molecules are closer to known external chemistry than the generated molecules are to one another.

However, similarity values across Stage 4A, Stage 4B, and Stage 4C should not be interpreted as directly equivalent novelty thresholds.

The comparison populations differ substantially:

```text
Stage 4A:
16 generated molecules

Stage 4B:
5,344 known target ligands

Stage 4C:
2,198 approved-drug structures
```

Nearest-neighbor similarity depends on both the fingerprint definition and the size/composition of the comparison population.

Therefore, Stage 4 retains these values as descriptive and ranking measurements rather than converting them into universal pass/fail novelty criteria.

---

# Stage 4 Attrition

Stage 4 is intentionally non-attritional.

```text
Stage 4 entering: 16
Stage 4 leaving:  16

Stage 4 survival:
16 / 16 = 100%

Stage 4 attrition:
0
```

The cumulative strict cascade therefore remains:

```text
20 generated
    ↓
19 Stage 1 chemically valid
    ↓
18 Stage 2 strict Rule-of-Five survivors
    ↓
16 Stage 3 structural-plausibility survivors
    ↓
16 Stage 4 chemically characterized
```

Cumulative strict cascade survival:

```text
16 / 20 = 80%
```

Stage 4 adds chemical-space ranking and context without changing cumulative survival.

---

# Implementation Artifacts

Stage 4 evaluator:

```text
evaluation/novelty.py
```

ChEMBL reference builder:

```text
scripts/build_chembl_reference.py
```

Frozen target reference:

```text
references/chembl37/ADORA2A_target_ligands.csv
```

Frozen approved-drug reference:

```text
references/chembl37/approved_drugs.csv
```

Stage 4A pairwise output:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4a_pairs.csv
```

Stage 4A molecule-level output:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4a.csv
```

Stage 4B molecule-level output:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4b.csv
```

Stage 4C molecule-level output:

```text
experiments/phase1_diffsbdd/evaluation/novelty_4c.csv
```

Combined Stage 4 output:

```text
experiments/phase1_diffsbdd/evaluation/novelty.csv
```

---

# Architecture Decisions Reinforced This Session

## 1. Novelty is characterization, not attrition

Stage 4 does not remove molecules.

Similarity measurements are retained for ranking and interpretation.

## 2. Molecular representation is fixed across comparison spaces

All Stage 4 comparisons use the same Morgan/Tanimoto definition.

Only the reference population changes.

## 3. Reference construction is separated from evaluation

Live ChEMBL access occurs only during reference-data construction.

The evaluator consumes frozen local files.

This prevents:

- network availability from affecting normal evaluation
- database updates from silently changing generator comparisons
- ChEMBL-specific logic from leaking into the generator-independent evaluator

## 4. Reference sets are versioned scientific inputs

The current references are tied to:

```text
ChEMBL 37
```

Future ChEMBL releases should create new reference versions rather than silently replacing the current files.

## 5. Parent normalization prevents artificial chemical-space density

Approved salts and alternative forms are normalized to parent structures.

This prevents multiple formulations of one active chemistry from being counted as separate reference points.

## 6. Provenance is retained through deduplication

Deduplicating structures does not mean discarding their source identities.

Reference structures retain the ChEMBL records and experimental or approval metadata that caused them to enter the reference set.

## 7. Missing reference metadata is not an evaluation failure

Missing first-approval information remains missing.

It does not invalidate an otherwise usable molecular reference structure.

## 8. Structurally unevaluable reference records are explicitly counted

Approved records without any resolvable molecular structure cannot participate in fingerprint-based chemical-space analysis.

These are excluded from the reference set and counted explicitly rather than silently disappearing.

---

# Session Outcome

Stage 4 novelty / chemical-space characterization is implemented for the Phase 1 DiffSBDD baseline.

Completed:

```text
Stage 4A
Internal generated-set similarity
✓

Stage 4B
Target-ligand-space similarity
✓

Stage 4C
Approved-drug-space similarity
✓

Combined Stage 4 artifact
✓
```

Final Stage 4 population:

```text
16 molecules entering
16 molecules leaving
0 molecules removed
```

Current cumulative strict cascade survival:

```text
16 / 20 = 80%
```

Stage 4 now provides a generator-independent framework for comparing generated molecules across:

- internal redundancy
- known target chemistry
- approved-drug chemistry

while preserving molecule-level provenance and avoiding arbitrary novelty attrition thresholds.