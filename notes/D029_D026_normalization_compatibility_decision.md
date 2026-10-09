# D029 — D026-Compatible Planner-Stock Normalization
**Decision date:** 2026-10-02  

**Status:** FROZEN


## Decision
Before any compatibility experiment is run, the following acceptance test and decision rule are frozen.


### 1. Acceptance test
A candidate normalization rule is compatible with frozen D026 only if, measured against the **full 27-character D026 InChIKey**:


1\. it never collapses a pair of structures that D026 keeps distinct (**false merge = 0**); and

2\. it never preserves a distinction that D026 collapses (**false split = 0**).


The first 14-character connectivity layer is insufficient for this acceptance test. The full D026 InChIKey remains the reference identity.


### 2. Comparison identity
The **candidate normalized identity** is exactly:


\`\`\`text

(RDKit version, canonical isomeric SMILES)

\`\`\`


where the canonical isomeric SMILES is emitted by:


\`\`\`python

MolToSmiles(

    normalized_molecule,

    canonical=True,

    isomericSmiles=True,

)

\`\`\`


The RDKit version is part of the candidate identity because canonical-SMILES serialization can change between RDKit versions.


The D026 full 27-character InChIKey remains the reference identity.


Definitions:


\`\`\`text

FALSE MERGE

distinct D026 keys

but identical candidate identities


FALSE SPLIT

same D026 key

but distinct candidate identities

\`\`\`


### 3. Prospective test set
#### Exhaustive conflicted-key test
Use **all 241,148 conflicted full D026 keys** identified in the preserved Stage-6 ASKCOS representation-conflict artifact.


This is the primary compatibility test and measures both false merges and false splits.


#### Different-key control sample
Construct exactly **10,000 unordered pairs** from **20,000 distinct full 27-character D026 keys**.


Sampling is frozen as:


\`\`\`text

population:

    frozen distinct-key D026 population


population identity:

    full 27-character D026 InChIKey


sample size:

    20,000 distinct keys

    -> 10,000 unordered pairs


selection:

    deterministic SHA-256 hash-priority sampling


seed:

    20261002


pairing:

    selected keys sorted ascending by full D026 key

    adjacent keys paired sequentially


row-order dependence:

    forbidden

\`\`\`


The sampled different-key arm measures false merges only.


### 4. Candidate normalization rules
At minimum, evaluate exactly these two candidates:


#### Candidate A — InChI-consistent treatment
Use the fixed pipeline defined prospectively for the compatibility experiment:


\`\`\`text

frozen source SMILES

→ RDKit MolFromSmiles

→ Standard InChI via MolToInchi() with no non-standard options

→ RDKit MolFromInchi(Standard InChI)

→ MolToSmiles(

      normalized_molecule,

      canonical=True,

      isomericSmiles=True,

  )

\`\`\`


#### Candidate B — RDKit MolStandardize canonical-tautomer treatment
Use the fixed pipeline defined prospectively for the compatibility experiment:


\`\`\`text

frozen source SMILES

→ RDKit MolFromSmiles

→ MolStandardize.CleanupParameters()

→ MolStandardize.cleanup(mol, params)

→ MolStandardize.canonicalTautomer(cleaned, params)

→ MolToSmiles(

      normalized_molecule,

      canonical=True,

      isomericSmiles=True,

  )

\`\`\`


The exact runtime RDKit version used for the experiment must be recorded in the run header and is part of candidate identity.


No additional candidate may replace either preregistered candidate without a separately approved methodology amendment.


### 5. Pass bar
A candidate passes only if:


- **false merges = 0** and **false splits = 0** across all 241,148 conflicted keys; and

- **false merges = 0** across the 10,000-pair different-key sample.


There is no tolerance band.


There is no post hoc adjustment.


### 6. Candidate selection rule
- **Both candidates pass:** select the **InChI-consistent treatment**, because D026's frozen identity authority is an InChIKey generated from InChI semantics.

- **Exactly one candidate passes:** adopt the passing candidate.

- **Both candidates fail:** **stop and redesign**.


The pass threshold may not be loosened, redefined, or otherwise adjusted after observing results.


### 7. Power statement for the sampled control arm
If zero false merges are observed in the 10,000-pair sample, the conventional rule-of-three interpretation gives an approximate upper bound of:


\`\`\`text

3 / 10,000 = 0.0003 = 0.03%

\`\`\`


at approximately 95% confidence for the pairwise false-merge rate.


This bound is reported explicitly and is **not** treated as proof of zero false merges across the full 24,238,632-record frozen population.


The 10,000-pair arm is accepted as adequate only as a **generalization control**. The 241,148 conflicted keys remain the exhaustive primary compatibility test.


A passing result therefore does not support a claim of demonstrated zero false merges across all 24.2 million frozen keys.


### 8. Pre-test freeze
The rules above are frozen before results are observed.


The experiments measure the preregistered rules. They do not define, tune, or amend them.


No production planner-stock run may proceed on the basis of a candidate that has not passed this preregistered compatibility test.


## Scientific rationale
D025 requires both planner-specific terminal-stock representations to derive from the same frozen D026/D027 molecular universe and to be proven identical at the normalized molecular-set level. D026's full 27-character InChIKey is the identity authority. Therefore compatibility must be tested against the full D026 equivalence relation rather than the connectivity-only first 14 characters.


The candidate normalized identity is explicitly version-pinned canonical isomeric SMILES so that the comparison is deterministic and auditable.


## Amendment — Candidate-B Normalization Failure and Sole-Identity Consequence
**Decision date:** 2026-10-04  

**Status:** Approved amendment


#### Decision
For D029, **any Candidate-B normalization failure, or any failure of a frozen D029 pass criterion, means Candidate B does not pass as the sole identity step for the frozen D026 molecular universe, and D030 is considered.**


The trigger is outcome-based:


Candidate-B normalization failure  

**OR**  

any failed D029 pass criterion  

→ Candidate B does not pass as the sole identity step  

→ D030 is considered


The cause of a failure does not affect this trigger.


This amendment replaces the earlier D029 Candidate-B failure-semantics draft. The earlier draft is superseded and shall not be treated as an independent or competing failure rule.


#### Failure definition and diagnostic logging
A Candidate-B normalization failure means either:


- an exception is raised during the frozen Candidate-B normalization pipeline; or

- the normalization completes without producing a Candidate-B identity.


Every failure shall be logged with, at minimum:


- D026 full InChIKey

- source SMILES

- candidate

- exception type

- exception message

- RDKit version


Each failure's key, source SMILES, error type, and error message are retained for diagnosis only. The cause or apparent chemical nature of a failure does not create an exclusion or exception to the D029 trigger.


The complete Candidate-B measurement shall report the raw failure count and denominator separately over:


- the conflicted-key population;

- the source-spelling population.


No numeric failure threshold is introduced.


No relevance-, chemical-class-, source-status-, availability-, or “real compound”-based exclusion is introduced.


#### D029 identity-comparison semantics
A normalization failure does not produce a Candidate-B identity and therefore is not itself classified as a false merge or false split.


The existing D029 false-merge and false-split definitions remain unchanged.


Successful Candidate-B identities continue to feed those metrics exactly as before.


Thus:

normalization failure  

→ logged  

→ counts against B's sole-identity status  

→ not a false merge  

→ not a false split


successful normalization  

→ produces Candidate-B identity  

→ participates in false-merge / false-split measurement


#### D029 pass/fail consequence
The earlier failure-semantics draft established that normalization failures must be measured and preserved separately from false merges and false splits. This amendment adds the previously open **pass/fail consequence**:


\> Any Candidate-B normalization failure, or any failed D029 pass criterion, means Candidate B does not pass as the sole identity step, and D030 is considered.


#### Rationale
The frozen Candidate-B population derives from the first-party ZINC \`for-sale-25Q2.smi\` source and was selected using the stored metadata predicate:


mwt <= 250.0  

logp <= 3.5  

reactive in {30, 50}  

purchasable >= 10


The project record does not document what \`purchasable >= 10\` means in ZINC's own operational terms. It therefore cannot be used as a basis for a post hoc relevance exclusion.


A failure to process a molecule belonging to the frozen evaluated population is therefore a compatibility failure of the defined Candidate-B identity transformation, regardless of why the failure occurred.


The preserved PubChem-bare finding for:


KDKCOUBAKDHIMF-UHFFFAOYSA-N


is contextual diagnostic evidence only. It does not create an exclusion, relevance exception, or alternative pass criterion.


#### Scope
This amendment changes only the decision consequence of Candidate-B failures and failed D029 pass criteria.


It does not change:


- Candidate-A normalization;

- Candidate-B normalization;

- the D029 population;

- the D029 sampling scheme;

- the false-merge definition;

- the false-split definition;

- the treatment of successful Candidate-B identities;

- the preserved diagnostic runs or artifacts.


This decision was made before the continue-and-log Candidate-B run produced any complete failure count.


## Executed Candidate-B outcome — 2026-10-05

**Status:** Outcome recorded; D030 remains closed pending the post-run sequence below.

The full Candidate-B compatibility run was completed under the approved pinned D029 runtime:

- container image: `sbdd-d026:2026-09-28`
- AiZynthFinder: `4.4.1`
- AiZynthFinder commit: `9859f5bc6c04c342b828aff20001504c238d7ac1`
- RDKit: `2023.09.6`
- conflicted D026 keys: `241,148`
- conflicted source spellings: `558,907`

The completed run reported:

- conflicted keys with one or more Candidate-B normalization failures: `77`
- failed conflicted source spellings: `147`
- false merges in the conflicted population: `9,975`
- false splits in the conflicted population: `179,219`
- sample keys: `20,000`
- sample source spellings: `20,328`
- sample keys with normalization failures: `0`
- sample failed source spellings: `0`
- sample false merges: `0`
- Candidate-B sole-identity pass: `false`
- D030 considered: `true`
- overall pass: `false`

The preserved Candidate-B failure log contains `1,029` failure-log records at the time of inspection. This number has **not yet been reconciled** against the `147` failed source-spelling count reported by the final D029 result. The two are therefore recorded as separate observed run artifacts only; neither number may be used interchangeably with the other or used for further prevalence/accounting claims until reconciliation is complete.

### Executed failure handling versus preregistered acceptance criteria

The Candidate-B wrapper used per-record exception capture, immediate failure logging, and continuation so that the full conflicted population could be measured. This was the **failure-handling behavior actually executed by the run**.

A finalized, outcome-blind Candidate-B failure-acceptance rule governing the prevalence or acceptability of failures had **not** been completed before the run. The executed continue-and-log behavior must therefore not be represented retroactively as a preregistered scientific acceptance rule.

The run establishes the observed behavior and measured outcome under the implementation that was executed. The separate failure-acceptance rule remains an open post-run methodological item and must be drafted only after the failure-log reconciliation is complete.

### Required post-run sequence

1. Record the Candidate-B result as an observed D029 outcome.
2. Reconcile the `1,029` failure-log records against the `147` failed source spellings before either number is used for further accounting.
3. After reconciliation, draft a generic, outcome-blind failure-acceptance rule phrased as what would have been preregistered before the Candidate-B result was observed.

**D030 remains closed and unapproved until all three steps are complete.**

#### Failure-log reconciliation

The initial physical line count of the Candidate-B failure TSV was 1,030 lines, corresponding to 1,029 lines after the header. A subsequent structured reconciliation established that the TSV serialization contains repeated/fragmented diagnostic rows and therefore that physical line counts are not a valid failure-record denominator.

The final Candidate-B conflict-results JSON was used as the structured reference. The reconciliation found:

- 147 failed `(D026 full InChIKey, source SMILES)` pairs in the final JSON;
- 147 corresponding failure-record blocks in the TSV;
- 147 unique `(D026 full InChIKey, source SMILES)` pairs in the TSV;
- 0 JSON-only failure pairs;
- 0 TSV-only failure pairs;
- 77 distinct D026 keys containing at least one failed source spelling.

Therefore, the authoritative Candidate-B failure counts are 147 failed source spellings across 77 conflicted D026 keys. The earlier raw TSV line counts of 1,029 and 882 are diagnostic serialization counts and are not used for D029 failure accounting.

### Per-key blast-radius classification

A structured per-key analysis of the completed Candidate-B conflict-results JSON was performed over the 147 failed source spellings and 77 affected D026 keys.

The analysis found:

- 44 of 77 affected D026 keys lost all source spellings to Candidate-B normalization failure;
- 33 of 77 affected keys retained at least one successfully normalized source spelling;
- the 44 all-spellings-lost keys accounted for 92 failed source spellings;
- the 33 partial-loss keys accounted for 55 failed source spellings;
- the 147 failed source spellings therefore reconcile as 92 + 55 = 147;
- the 77 affected keys reconcile as 44 + 33 = 77.

The failure-spelling distribution per affected key was:

- 11 keys with 1 failed spelling;
- 64 keys with 2 failed spellings;
- 2 keys with 4 failed spellings.

This blast-radius analysis is descriptive and is used to size the prospective witness-only population under the ASKCOS standby-routing design direction. It does not define or modify the D029 failure-acceptance rule and does not determine the D030 design direction.

No D026 identity, frozen source stock, or planner stock was modified by this analysis.

### Governing principle
\> For D029 compatibility measurements, failure of the defined Candidate-B identity step on any member of the evaluated population, or failure of any frozen D029 pass criterion, means Candidate B cannot serve as the sole identity step; the failure cause is diagnostic evidence, not a basis for exclusion.


#### Revisit when
Revisit only if a separately approved D029/D030 methodology changes the identity architecture or changes the authority assigned to Candidate-B compatibility failures.
