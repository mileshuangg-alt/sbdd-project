# Session 013 — Stage 6 Synthetic Feasibility
**Date:** 2026-09-25

**Closed:** 2026-09-30

**Status:** CLOSED


## Session objective
Begin Stage 6 — Synthetic Feasibility from the frozen Phase-1 DiffSBDD baseline.


The immediate objective is deliberately narrow:


1. retrieve the existing project framework and decision material governing Stage 6;

2. determine exactly what Stage 6 is intended to measure;

3. determine the evidence level and claim supported by that measurement;

4. determine whether the existing framework authorizes synthetic feasibility as a hard forward-cascade attrition gate;

5. identify any genuine framework hole before introducing a new criterion, threshold, validation requirement, or software implementation;

6. only after the scientific construct is established, perform the required literature-backed alternatives pass for any unresolved implementation choice.


No Stage-6 package, scoring function, retrosynthesis engine, threshold, or gate is presumed frozen at session start.


Implementation does not begin until the Stage-6 methodology and required authority are clear.


## Starting state
At Session 013 start:


* Stage 5 is complete and frozen;

* the validated A2A Stage-5 gate has been applied to the preserved 16-member Phase-1 DiffSBDD cohort under D023;

* ****3/16**** molecules remain in forward cascade progression;

* the retained molecule IDs are ****0, 3, and 18****;

* ****13/16**** molecules are attrited from forward progression but remain permanently retained as characterization evidence;

* the frozen Stage-5 interaction measurements remain Phe168 feature reproduced in 15/16, Asn253 feature reproduced in 4/16, and the complete A2A pattern reproduced in 3/16;

* the Stage-5 gate, validation evidence, D022 semantics, D023 authority, ProLIF reader, negative panel, and claim boundary are closed to further tuning;

* FLOWR remains deferred until the complete DiffSBDD baseline cascade is implemented and frozen;

* the next baseline stage is ****Stage 6 — Synthetic Feasibility****;

* no specific Stage-6 synthesis package, score, retrosynthesis engine, threshold, or attrition rule is presumed frozen.


The forward cohort entering Stage 6 is therefore:


```text

molecule 0

molecule 3

molecule 18

```


unless the existing Stage-6 framework explicitly establishes a different analysis population.


Last confirmed Stage-5 baseline commit:


```text

2079c0c Close Stage 5 A2A baseline

```


The actual branch/remote state must be treated as execution state and confirmed before the first new Session-013 commit.


### 1.1 Framework retrieval
**Status:** COMPLETE


The authoritative Stage-6 framework was recovered from the original project proposal:


```text

DiffSBDD-proposal-pipelineframing-2026-08-12.pdf

```


The proposal establishes Stage 6 as ****Retrosynthesis / Synthetic Feasibility**** within the committed filter cascade.


The cascade table defines Stage 6 as a filtering stage whose rejection condition is:


```text

molecules with no route found

```


and whose reported result is:


```text

route found / no route found

```


The detailed Stage-6 section specifies ****AiZynthFinder**** as the originally proposed retrosynthesis planner and defines the reported outputs as:


```text

route found / no route found

step count

```


SA score is retained only as a weaker accompanying signal rather than the primary Stage-6 evidence.


The proposal explicitly bounds the interpretation of both outcomes. A `no route found` result does not establish that the molecule cannot be synthesized; it means only that the specified planner, template/policy, stock, and search configuration did not identify a route. Conversely, `route found` establishes successful route search against that configuration, not that a medicinal chemist would execute the proposed synthesis.


The proposal separately identifies ****AiZynthFinder stock and policy configuration**** as an unresolved question because those choices determine what `route found` means.


The recovered framework therefore establishes:


```text

Stage-6 role:                 hard attrition gate

Primary measurement:         retrosynthetic route search

Original proposed planner:   AiZynthFinder

Primary outcome:             route found / no route found

Additional outcome:          step count

SA score:                    weaker accompanying signal

Negative claim:              configuration-bounded planner failure

Intrinsic nonsynthesizability claim: NOT AUTHORIZED

Stock/policy configuration:  unresolved at proposal stage

```


The proposal also establishes the broader three-input control framework: generated molecules, known actives, and known decoys pass through the identical cascade, and filter behavior is interpreted against controls whose status is independently established.


However, the proposal does ****not**** specify a Stage-6 validation protocol sufficient to establish when route-search failure may exercise hard attrition. In particular, it does not define a prospective sensitivity requirement on known-synthesizable compounds or provide a ground-truth negative class of unsynthesizable molecules.


That is the Stage-6 framework hole addressed in Section 2.


The governing Session-013 question is therefore narrowed from whether Stage 6 is intended as a hard gate to:


> ****What validation must the frozen Stage-6 route-search instrument pass before its configuration-bounded `no route found` result is authorized to exercise the proposal's intended hard attrition?****


## 2. Stage-6 authority, negative semantics, and validation protocol
### 2.1 Reconciliation of hard attrition with bounded negative evidence
The original proposal establishes Stage 6 as a ****hard attrition gate****. Molecules for which the frozen retrosynthesis search does not find a route do not advance through the forward cascade.


This is an ****allocation decision within the evaluation pipeline****, not a chemistry verdict.


The Stage-6 disposition language is therefore:


```text

route found

-> eligible to advance beyond Stage 6


no route found

-> attrited from forward cascade progression

```


The corresponding scientific interpretation is deliberately narrower:


```text

no route found

!= molecule is unsynthesizable

```


A Stage-6 negative means only that the ****frozen planner, under the frozen template/policy and stock configuration, did not find a route under the frozen search protocol****.


Therefore:


> ****We do not advance molecules without a found route. This makes no claim that those molecules cannot be made.****


There is no contradiction between hard attrition and the bounded negative. Hard attrition answers the operational question ****“does this molecule receive additional project resources?”**** The route-search result answers the narrower computational question ****“did the frozen planning system find a route under the specified search conditions?”****


This preserves the proposal's explicit warning that planner failure does not establish nonsynthesizability and that even a found route establishes only successful template search against the specified stock rather than practical experimental synthesis.


****Decision changed:**** fixes the Stage-6 disposition semantics. A `no route found` result may eventually cause forward-cascade attrition without being reported as evidence that the molecule is chemically impossible to synthesize.


### 2.2 Validation must precede attrition authority
The proposal requires generated molecules and controls to pass through the same cascade and states that a filter becomes interpretable by observing its behavior on compounds whose status is already settled.


For Stage 6, this principle is instantiated as a prospective control validation ****before the gate is permitted to reject the Phase-1 DiffSBDD survivors****.


The validation population will be stratified by independently settled evidence of real-world availability:


1. ****vendor-catalog, in-stock compounds****;

2. ****marketed drugs****;

3. ****literature actives with established synthesis/experimental use****;

4. ****generated molecules****, which are the eventual evaluation population rather than positive controls.


The first three strata provide increasingly application-relevant examples of molecules known to be synthesizable or physically obtainable independently of the retrosynthesis planner.


Generated molecules do not establish the positive-control truth and cannot be used to calibrate the gate that will subsequently judge them.


All control and generated inputs must be processed under the same frozen Stage-6 configuration relevant to the route-search claim.


****Decision changed:**** defines what evidence must exist before the proposal's route-search stage receives operational authority to attrit generated molecules.


### 2.3 Prospective validation quantities and pass criterion
Before any Stage-6 control run, the validation quantities and the required sensitivity on known-synthesizable compounds must be ****predeclared and frozen****.


At minimum, the validation record must distinguish:


```text

N evaluated

N route found

N no route found

route-found sensitivity on known-synthesizable controls

```


Results must also remain stratified by control source rather than being reported only as a pooled total:


```text

vendor-catalog / in-stock

marketed drugs

literature actives

```


Any additional quantity used to determine whether the gate passes validation must likewise be specified before observing the control results.


The numerical sensitivity requirement is ****not set from the observed validation data****. It must be justified, declared, and frozen prospectively.


No cutoff may be selected or revised because it produces a desirable validation result or favorable retention of molecules 0, 3, or 18.


Until that prospective criterion is frozen and passed, Stage-6 route-search results have ****characterization value only**** and cannot exercise the proposal's intended hard-attrition authority.


****Decision changed:**** establishes the condition that promotes the Stage-6 measurement from characterization-only execution to an authorized hard gate.


### 2.4 The missing specificity rung
Stage-6 validation has an important structural limitation that must remain explicit.


The positive side can be tested against compounds independently known to have been synthesized or obtained.


The corresponding negative side cannot be constructed symmetrically:


> ****There is no ground-truth reference class of molecules known to be unsynthesizable.****


Failure to find a published synthesis, failure of a retrosynthesis planner, absence from vendor catalogs, or failure under another search configuration does not establish that a molecule cannot be synthesized.


Consequently, ****specificity for true nonsynthesizability is structurally unknowable under the available evidence model****.


The validation can therefore establish whether the frozen planner/configuration has acceptable sensitivity for recovering routes to known-synthesizable compounds. It cannot establish a conventional sensitivity/specificity pair for the underlying property “synthesizable versus unsynthesizable.”


This is the missing validation rung and must remain visible in the Stage-6 claim boundary.


It must not be replaced with a constructed pseudo-negative class whose members are merely difficult, unpublished, unavailable commercially, or unsuccessful in another planner.


****Decision changed:**** caps the validation claim and prevents planner failure from being reinterpreted as demonstrated chemical nonsynthesizability.


### 2.5 Frozen planner/configuration defines the instrument
The proposal identifies AiZynthFinder stock and policy configuration as an open question and explicitly states that these choices determine what a route-found result means.


Accordingly, the Stage-6 instrument is not merely:


```text

AiZynthFinder

```


It is the complete frozen search configuration, including the planner and all configuration elements that materially define its search and endpoint, including the template/policy and stock configuration.


Those choices must be resolved and recorded in a new frozen decision record using the next available D-number ****before any validation or generated-molecule run****.


The decision record must define enough configuration provenance that:


1. the validation run can be reproduced;

2. molecules 0, 3, and 18 can later be evaluated under the identical instrument;

3. `route found` and `no route found` retain a stable meaning;

4. later FLOWR evaluation can use the identical frozen Stage-6 implementation rather than a recalibrated one.


No Stage-6 result produced under a different stock/policy configuration inherits the validation authority of the frozen instrument automatically.


****Decision changed:**** defines the unit that is validated and prevents configuration changes from silently changing the meaning of the Stage-6 gate.


### 2.6 Order of operations
The Stage-6 execution order is now constrained as follows:


```text

1. Freeze Stage-6 framework and claim semantics.


2. Perform the required literature-backed alternatives pass

   before final implementation/configuration selection.


3. Select and freeze the planner + template/policy + stock

   configuration in the next D-number decision.


4. Predeclare and freeze the control panel, measured quantities,

   and known-synthesizable sensitivity pass criterion.


5. Run the frozen control validation.


6. If validation passes:

      authorize hard attrition under the frozen configuration.


   If validation fails:

      retain Stage-6 results as characterization only;

      do not reject molecules through Stage 6.


7. Only after successful validation:

      run molecules 0, 3, and 18 through the authorized gate.

```


The outcomes of molecules ****0, 3, and 18 must play no role in selecting the instrument, configuration, validation panel, measured quantities, or pass threshold****.


This preserves prospective validation and prevents the Phase-1 generated cohort from becoming calibration data for its own gate.


****Decision changed:**** fixes when the gate may first touch the frozen Phase-1 forward cohort and prevents outcome-informed calibration.


### 2.7 Immediate Session-013 boundary
No AiZynthFinder production or validation run will be performed at this point.


The next work is methodological:


* complete the Stage-6 framework freeze;

* perform the required literature-backed alternatives pass;

* determine the planner/configuration choice;

* define the prospective positive-control validation and sensitivity criterion;

* draft the corresponding next D-number decision for review.


Only after those elements are frozen may Stage-6 validation execution begin.


Molecules ****0, 3, and 18 remain untouched by Stage 6 until that validation passes****.


****Decision changed:**** blocks premature execution and preserves the independence of Stage-6 validation from the generated-molecule outcomes.


## 3. Stage-6 planner selection and witness architecture
The Stage-6 planner architecture remains:


```text

PRIMARY:

AiZynthFinder


SECONDARY WITNESS:

ASKCOS

```


AiZynthFinder remains the frozen primary planner, and ASKCOS remains the frozen secondary witness.


The union-with-provenance gate remains unchanged:


```text id="g9x8c2"

PRIMARY FOUND

+ WITNESS FOUND

    -> PASS

    -> provenance: primary-found


PRIMARY FOUND

+ WITNESS NOT RUN

    -> PASS

    -> provenance: primary-found


PRIMARY NOT FOUND

+ WITNESS FOUND

    -> PASS

    -> provenance: witness-only

    -> witness-only flag retained


PRIMARY NOT FOUND

+ WITNESS NOT FOUND

    -> HARD ATTRITION

```


There is no clemency, limbo, or discretionary intermediate category.


### 3.1 Double-blind disposition flag
Every molecule reaching the final branch:


```text

AiZynthFinder: no route found

ASKCOS:        no route found

```


receives an explicit:


```text

double-blind = TRUE

```


flag in the Stage-6 record.


This flag is distinct from the ASKCOS witness column.


The witness column records ****execution status/outcome****:


```text

route found

no route found

not run

```


The `double-blind` flag records the ****reason for final attrition****.


The two fields must therefore not be conflated.


The double-blind disposition remains:


```text id="1e6kyj"

double-blind = TRUE

-> HARD ATTRITION

```


The flag does not create a new disposition category and does not alter the gate.


### 3.2 Second-tier human-chemist review flag
A double-blind molecule whose binding score ranks in the ****top decile of the Phase-1 cohort**** receives an additional metadata flag:


```text id="4gy9qk"

human_chemist_review = TRUE

```


This produces a report-level review list of double-blind molecules that combine:


```text

no route found by both frozen planners

+

top-decile binding score

```


The human-chemist review list is ****outside the Stage-6 gate****.


Its purposes are:


* transparent reporting of high-priority attrited molecules;

* preservation of candidates for possible future rescue work;

* identifying molecules that may warrant additional synthesis-oriented investigation if project scope later permits it.


Possible future rescue avenues include:


* a larger retrosynthesis search budget;

* a broader or make-on-demand precursor space;

* additional route-planning methods;

* actual wet-lab or CRO synthesis if such access becomes available.


None of those possibilities changes the Stage-6 disposition established under D024.


### 3.3 Flags do not reopen progression
Neither metadata flag changes the disposition:


```text id="yn9c7b"

double-blind = TRUE

    -> attrited


human_chemist_review = TRUE

    -> still attrited

```


The flags are metadata for reporting, interpretation, and downstream optionality only.


They do not:


* restore a molecule to forward progression;

* suspend attrition;

* create a limbo category;

* override the union gate;

* authorize an additional Stage-6 veto;

* or reopen an already-completed Stage-6 decision.


Any future rescue experiment is a new downstream action and would require its own explicitly authorized methodology.


****Decision changed:**** double-blind attrition now carries an explicit final-disposition flag, with a second reporting-only human-chemist-review flag for double-blind molecules in the cohort's top binding-score decile. The Stage-6 gate and attrition decision remain unchanged.


**---**


## 4. Frozen primary/witness execution and disagreement evidence
The lazy-witness execution protocol remains in force.


AiZynthFinder runs first on the full frozen control panel and Phase-1 cohort.


ASKCOS runs only after an AiZynthFinder `no route found`, because only that branch can change Stage-6 disposition.


### 4.1 Recorded outcomes
For every molecule, the Stage-6 evidence record preserves:


```text id="7j1x4m"

AiZynthFinder outcome


ASKCOS outcome where adjudication is required:

    route found

    no route found

    not run


Stage-6 provenance:

    primary-found

    witness-only

    double-blind


double_blind:

    TRUE / FALSE


human_chemist_review:

    TRUE / FALSE


route information where found

step count where defined


AiZynthFinder configuration provenance

ASKCOS configuration provenance where ASKCOS was run

```


The ASKCOS column retains its three-state execution meaning.


The `double_blind` field is a separate final-disposition field and must remain explicit even though the same state can be derived from the two planner outcomes.


The `human_chemist_review` field records the optional report-level second-tier flag and does not constitute another gate.


### 4.2 Frozen outcome table

| AiZynthFinder primary | ASKCOS witness | Stage-6 disposition | Provenance | Flags |
| --- | --- | --- | --- | --- |
| Route found | **Not run** | **PASS** | Primary-found | None |
| No route found | Route found | **PASS** | Witness-only | Witness-only |
| No route found | No route found | **HARD ATTRITION** | Double-blind | `double_blind = TRUE`; add `human_chemist_review = TRUE` when binding score is top-decile |


Hard attrition in the final row is operative only after the frozen Stage-6 control validation has passed.


The human-chemist-review flag does not alter this table's disposition.


### 4.3 Preserved witness-only rescue measurement
Witness-only rescue remains measured over the ****primary-no-route subset****:


```text id="v6t4fz"

witness-only rescue rate

=

ASKCOS route-found among primary-no-route molecules

/

all primary-no-route molecules submitted to ASKCOS

```


This quantity is reported separately for the controls and Phase-1 cohort.


The reverse-disagreement quantity remains unmeasured because ASKCOS is not run when the primary has already found a route.


### 4.4 Double-blind reporting
The final attrition report distinguishes:


```text id="9y9hj2"

primary-found passes

witness-only passes

double-blind attritions

```


Every double-blind attrition additionally carries its explicit `double_blind` flag.


Within the double-blind group, the report separately identifies the subset carrying:


```text

human_chemist_review = TRUE

```


because their binding score lies in the top decile of the cohort.


This creates a transparent record of high-priority attrited molecules without weakening the gate.


### 4.5 Anti-tuning lock
The top-decile human-chemist-review list is generated ****after the frozen Stage-6 binding-score ranking is available****, but it does not alter the predeclared gate.


The review threshold is a reporting rule for the already-finalized cohort disposition.


Neither the `double_blind` flag nor the `human_chemist_review` flag may be used to:


* restore progression;

* change the primary/witness planners;

* change their configurations;

* modify the validation threshold;

* alter union-gate semantics;

* or create a post hoc rescue criterion.


Any actual rescue attempt is outside the frozen Stage-6 gate and requires a separately authorized methodology.


****Decision changed:**** Section 4 now records double-blind attrition explicitly and adds the top-decile human-chemist-review metadata path. Execution remains lazy-witness; gate semantics remain unchanged; neither flag can reopen progression.

## 5. Shared precursor-stock selection and D025 freeze
Session 013 next resolved the shared precursor universe required by the frozen primary/witness architecture.



The governing constraint was:



```text
AiZynthFinder primary

and

ASKCOS witness

must terminate against the same frozen molecular universe
```



This is necessary because a `route found` or `no route found` result is configuration-bounded and the stock is part of that configuration.



### 5.1 Historical AiZynthFinder stock acquisition
The public AiZynthFinder stock artifact was acquired and preserved as:



```text
references/stage6/d025_shared_stock/source/zinc_stock.hdf5
```



SHA-256:



```text
99d39a6f807c3e815487500bafc2b4a9dc66a31af189e3b1776874fb0d4a188d
```



The artifact corresponds to the historical:



```text
zinc_stock_17_04_20.hdf5
```



and contains:



```text
17,422,831 stored InChIKey rows
```



The artifact is InChIKey-only.



It therefore cannot by itself be transformed into an identical canonical-SMILES ASKCOS buyables representation while preserving direct molecule-set identity.



### 5.2 Candidate A — historical structure-bearing recovery
The first recovery path attempted to identify an authoritative structure-bearing ZINC population corresponding exactly to the historical 17,422,831-row AiZynthFinder stock.



That path was investigated through:



* public AiZynthFinder/Figshare provenance;
* public ZINC archival material;
* first-party BKS filesystem discovery;
* shallow inspection of historical generic ZINC storage trees.



No authoritative first-party structure-bearing artifact representing the exact historical population was recovered.



Candidate A is therefore:



```text
UNRECOVERED
```



not:



```text
FAILED
```



No equality test against a recovered historical structure set was performed.



The historical AiZynthFinder HDF5 remains preserved as provenance and literature-comparison material but is not the operative Stage-6 shared-stock source.



### 5.3 Candidate B — first-party structure-bearing ZINC source
The operative Stage-6 source was frozen as:



```text
/nfs/exl/zinc20/2D/for-sale-25Q2.smi
```



Observed source properties:



```text
size:      113,043,807,549 bytes
records:   1,907,324,517
SHA-256:   9b5c02767c56282c7704ce039e6176d986cf9e2e386a9ae46d1538600125c336
format:    SMILES + ZINC identifier
```



Preserved first-party provenance included:



```text
how2
hownew
newcron2d.csh
zinc_export.py
zinc_substance.py
```



Known source-code hashes:



```text
zinc_export.py
e3fd79d7b5651d81a6dcaaaee98467d917c45b68f63c7beb6a1d8f4511ff56a4

zinc_substance.py
6852b73b1d1a0d2fc148f4cef85f3cb93a2619e17c0d931a57753e23c46ce5c9
```



### 5.4 Frozen Candidate-B selection
The authoritative record-level predicate was frozen as:



```text
mwt <= 250.0
logp <= 3.5
reactive in {30, 50}
purchasable >= 10
```



The pre-`how2` ZINC `.txt` schema was established as:



```text
smiles
zinc_id
inchikey
mwt
logp
reactive
purchasable
tranche_name
features
```



Implementation:



```text
evaluation/stage6_candidate_b_filter.py
tests/test_stage6_candidate_b_filter.py
```



Commit:



```text
ce0e406 Add Stage 6 Candidate B metadata filter
```



The worker is streaming and deterministic and uses the stored first-party ZINC metadata rather than recomputing MW, logP, or reactivity.



The tranche filename mapping permitted an execution preselection:



```text
[AB][A-G][EG][A-E]
```



but this filename filter is not the scientific definition of membership.



The record-level stored-metadata predicate remains authoritative.



Real-tree enumeration:



```text
total .txt files:          4,275
eligible files:              140
excluded files:            4,135
malformed/unexpected:          0
basename uniqueness:      4,275 / 4,275
```



Enumeration manifest SHA-256:



```text
0ed2151aa6d2d687f3e0c025cd2f7e8a1efe3a15ffdf89291fd0d18704403b86
```



Filtering result:



```text
input records:      24,249,818
accepted records:   24,249,767
rejected records:           51
malformed records:           0
```



The accepted population contained:



```text
24,249,767 unique ZINC IDs
```



### 5.5 D025 cross-planner identity requirement
D025 froze the requirement that both planners derive their terminal stock representations from the same frozen structure-bearing source.



Before either representation may be used for planning, the stock-construction process must preserve and report:



```text
source-record count
source SHA-256
unique-molecule count after frozen normalization
AiZynthFinder ingested-stock molecule count
ASKCOS ingested-stock molecule count
deterministic hash of normalized canonical-SMILES set
complete cross-representation identity proof
transformation logs
software versions/configuration
all rejected/failed source records
```



A sampled identity proof is not sufficient.



Any normalization collision, parser loss, failed transformation, or planner-representation disagreement must be explicit.



**Decision changed:** D025 replaced an informal reference to an AiZynthFinder/ZINC stock with a frozen, first-party, structure-bearing molecular universe and a complete cross-planner identity requirement.



---



## 6. D026 molecular-identity transformation and qualification
The Candidate-B source contains both structural records and historical stored ZINC InChIKeys.



A reproducible Stage-6 shared-stock transformation required a frozen molecular-identity authority independent of historical ZINC key-generation differences.



D026 therefore established the D026-generated InChIKey as the operative identity authority.



Downstream structure-consuming stages continue to use the original frozen SMILES.



### 6.1 D026 qualification principle
The approved D026 waiver is:



> **D026 identity concordance is required at the connectivity layer for this source population; full historical ZINC InChIKey concordance is not required. D026 identity authority remains the frozen D026-generated InChIKey. Downstream structure-consuming stages continue to use the original frozen SMILES.**



Connectivity equality is:



```text
zinc_inchikey[:14] == d026_inchikey[:14]
```



Historical full-key disagreement is reported but is not itself a transformation failure.



### 6.2 100-record pilot
The frozen D026 runtime was qualified on a 100-record pilot.



Pilot result:



```text
full-key concordance:       93 / 100
connectivity concordance:  100 / 100
```



The seven full-key mismatches were not silently waived.



They were isolated for a stereo-focused audit.



### 6.3 Seven-record stereo audit
Stereo-audit result:



```text
records:                 7
connectivity matches:    7
full-key matches:        0
source explicit stereo:  7
source bond stereo:      7
source atom stereo:      4
oxime-like:              5
```



The seven records separated into:



```text
A_input_stereo_present_but_D026_key_empty_stereo_layer: 3
B_input_stereo_absent_but_ZINC_key_has_stereo:          0
C_both_keys_have_stereo_but_stereo_layer_differs:       4
```



The four C records remain explicitly distinct from the three A records.



The audit supported the connectivity-layer waiver.



It did not establish that the remaining 24.25 million Candidate-B records would behave identically.



### 6.4 D026 batch implementation
Primary implementation:



```text
evaluation/d026_batch_identity.py
tests/test_d026_batch_identity.py
```



Relevant commits:



```text
e4e94c6 Implement D026 batch identity transform and pilot waiver
2ab4c78 Freeze D026 exotic-valence quarantine amendment
```



The batch implementation:



* streams the Candidate-B input;
* verifies source-file and source-line lineage;
* verifies SMILES lineage;
* verifies ZINC-ID lineage;
* recovers the stored historical ZINC InChIKey;
* computes the D026 InChIKey;
* records full-key and connectivity concordance separately;
* writes deterministic identity, quarantine, discrepancy, and summary artifacts;
* does not silently discard transformation exceptions.



**Decision changed:** D026 established a reproducible identity transformation and made connectivity concordance, rather than historical full-key identity, the required agreement layer for this frozen source population.



---



## 7. Exotic-valence quarantine and D027 discrepancy adjudication
Full-population qualification exposed rare structural representations requiring prospective treatment rather than post hoc exception handling.



### 7.1 D026 Q1/Q2 quarantine amendment
Frozen Q1:



```python
r"\[[Nn]\]"
```



Reason:



```text
D026_EXOTIC_VALENCE_Q1
```



Frozen Q2:



```python
r"\[[Nn][^\]]*\][\\/]\(=O"
```



Reason:



```text
D026_EXOTIC_VALENCE_Q2
```



Q1/Q2 records are removed from the accepted identity stock and preserved in the quarantine artifact.



The motivating Q1 record was:



```text
ZINC 687728612
AAEE.txt:2172
```



with historical source representation:



```text
N=C(NO)N[N]N=C1C=C[N+]\(=O)N=C1
```



The prevalence measurement was provenance only.



Rarity did not itself justify or authorize the quarantine.



### 7.2 `[C]` discrepancy and rejection of Q3
A later connectivity discrepancy occurred at:



```text
ZINC 642869374
AAEE.txt:5675
SMILES:
C[C]1N=C(C2=C=C(N)NN2)C#CN1
```



Historical ZINC key:



```text
NOBHQWDCVRXEIG-UHFFFAOYSA-N
```



D026 key:



```text
OBWAYGZZGSXGKA-UHFFFAOYSA-N
```



Independent local RDKit/InChI generation produced:



```text
OBWAYGZZGSXGKA-UHFFFAOYSA-N
```



and therefore reproduced D026 rather than historical ZINC.



No Q3 `[C]` quarantine class was created.



A bare-carbon prevalence measurement was retained only as provenance and did not confer exception status.



### 7.3 D027 adjudication semantics
D027 replaced the original assumption that every non-waived connectivity mismatch necessarily demonstrated D026 processing failure.



For every non-waived connectivity discrepancy, the local independent generation result is recorded and compared against both connectivity layers.



Frozen branches:



```text
local reproduces D026
    -> adjudication = exclude_continue
    -> reproduced_side = d026
    -> exclude from frozen stock
    -> continue run
```



```text
local reproduces ZINC over D026
    -> hard halt
    -> stopping_status = stopped_d026_processing_failure
```



D027 Rule 6 added the third branch:



```text
local reproduces neither D026 nor ZINC
    -> adjudication = adjudication_inconclusive
    -> reproduced_side = neither
    -> nonzero exit
    -> halt for human review
```



The inconclusive state does not accuse D026 of failure.



It also does not permit continuation because an adjudicator that cannot reproduce either side cannot be treated as authoritative for subsequent discrepancies in that run.



### 7.4 D027 implementation and tests
Commit:



```text
7856595 Implement D027 discrepancy adjudication
```



Final focused test suite:



```text
23 passed
```



The tests covered:



* normal connectivity concordance;
* full-key mismatch with connectivity agreement;
* Q1/Q2 quarantine;
* D026-side discrepancy exclusion and continuation;
* ZINC-side hard halt;
* neither-side `adjudication_inconclusive` halt;
* discrepancy artifact serialization;
* deterministic summary/accounting behavior.



**Decision changed:** non-waived connectivity disagreement became a three-branch adjudicated event rather than an automatic D026 failure, while every discrepant record remained excluded from the accepted stock.



---



## 8. Full Candidate-B D026/D027 execution
After D026/D027 semantics and implementation were frozen, the complete 24,249,767-record Candidate-B population was executed.



### 8.1 Qualified runtime
The full batch ran on:



```text
host: epyc2
container: d026-batch-run
image: sbdd-d026:2026-09-28
```



Frozen container environment ID:



```text
sha256:020a8c810e5f4285fe4479c6d6aa6bc987393834480a24dd9a513631668851b4
```



Relevant mounts:



```text
/input/filtered_records.tsv
    <- /nfs/home/mhuang/stage6_candidate_b_frozen/filtered_records.tsv

/output
    <- /nfs/home/mhuang/stage6_candidate_b_d026_run

/source
    <- /nfs/exl/zinc20/2D
```



The exact runtime script was preserved as:



```text
/output/d026_full_2026-09-30/d026_batch_identity_runtime.py
```



SHA-256:



```text
6a0c802a05f91a657e2f77a6773ac8c9e1dced1989ab62a1693f6cf1dd8a46c6
```



The local committed:



```text
evaluation/d026_batch_identity.py
```



had the identical SHA-256.



At verification time, commit `7856595` was present on both:



```text
origin/main
github/main
```



### 8.2 Final batch result
Completed summary:



```text
input records:                    24,249,767
Q1/Q2 quarantined:                   10,491
processed:                        24,239,276

D027 discrepancies:                     644
exclude_continue:                        644
local reproduced D026:                  644
local reproduced ZINC:                    0
local reproduced neither:                 0

final identity records:           24,238,632

connectivity matches:             24,238,632
connectivity mismatches:                   0
connectivity concordance:                1.0

full-key matches:                 23,792,769
full-key mismatches:                 445,863
full-key concordance:       0.9816052737629748

stopping_status: completed
```



Accounting closed exactly:



```text
24,249,767
=
10,491 quarantined
+
24,239,276 processed
```



and:



```text
24,239,276 processed
=
24,238,632 final identity records
+
644 D027 exclusions
```



The discrepancy artifact independently confirmed:



```text
discrepancy_records: 644
adjudications: {'exclude_continue': 644}
reproduced_sides: {'d026': 644}
```



Therefore the complete run produced:



```text
0 ZINC-side D026 processing failures
0 inconclusive adjudications
```



### 8.3 Frozen D026/D027 archive
Persistent run directory:



```text
/output/d026_full_2026-09-30/
```



Frozen artifacts:



```text
candidate_b_d026_identity.tsv
candidate_b_d026_quarantine.tsv
candidate_b_d026_discrepancy.tsv
candidate_b_d026_identity_summary.json
candidate_b_d026_run.log
d026_batch_identity_runtime.py
```



SHA-256:



```text
candidate_b_d026_identity.tsv
d15f14acd097dfb89a788c2cd07bd304f60245a18f6b6701c8f53350340bd1d0

candidate_b_d026_quarantine.tsv
59214dc57b4b474c6a9aa1abf6436c7d9f52892a4df3590b9702830807af317e

candidate_b_d026_discrepancy.tsv
7900f64b6528227aeb8f2ec2c6f95b420eddd7a944c61afc3c9d5638eb313ae8

candidate_b_d026_identity_summary.json
30b6192a67d1581487444240b3a4ff2e8c1e2aafe57e05a87a08c3692550d8e6

candidate_b_d026_run.log
30b6192a67d1581487444240b3a4ff2e8c1e2aafe57e05a87a08c3692550d8e6

d026_batch_identity_runtime.py
6a0c802a05f91a657e2f77a6773ac8c9e1dced1989ab62a1693f6cf1dd8a46c6
```



The persistent copies were compared against the runtime source files:



```text
ALL_MATCH = True
```



Frozen input artifact SHA-256 recorded by the completed transform:



```text
5704a764984131f1165a5de0c24fa8967eebbdd55d4fe2fd9f16b70c2740ed03
```



### 8.4 Version-controlled freeze manifest
The full-run freeze manifest was created at:



```text
references/stage6/d026_full_2026-09-30/manifest.json
```



It records:



* run ID and freeze date;
* input count and SHA-256;
* container environment ID;
* runtime/committed script hashes;
* D026/D027 counts and adjudication totals;
* artifact paths and SHA-256 values;
* accounting invariants.



Manifest accounting validation:



```text
FREEZE_MANIFEST_ACCOUNTING_OK
```



The freeze-manifest commit was pushed to:



```text
origin/main
github/main
```



The exact SHA of that final freeze-manifest commit was not captured in chat after push.



It must not be invented.



**Decision changed:** the D025/D026/D027 molecular-universe work moved from qualification/proposal state to a completed frozen Stage-6 stock containing exactly 24,238,632 accepted identity records.



---



## 9. Final Session-013 Stage-6 state
At Session 013 close, the Stage-6 architecture and common molecular universe are frozen, but the planner instruments and validation authority are not yet complete.



The frozen input to planner-stock construction is:



```text
24,238,632 D026/D027 identity records
```



The remaining Stage-6 work is now bounded.



### 9.1 AiZynthFinder primary still to freeze
Session 014 must freeze:



```text
exact version/build
expansion policy/model
reaction-template set
planner-specific stock representation
search algorithm
scientifically relevant search settings
search budget/stopping conditions
route-return semantics
success semantics
other settings materially affecting endpoint
```



### 9.2 ASKCOS witness still to freeze
Session 014 must freeze:



```text
exact version/build
retrosynthesis model/template configuration
buyables representation
search algorithm
search budget/stopping conditions
route-return semantics
success semantics
other settings materially affecting witness adjudication
```



### 9.3 Planner-stock identity proof still required
Before either planner may be used for planning, Session 014 must preserve:



```text
source-record count
source SHA-256
unique normalized-molecule count
AiZynthFinder ingested-stock molecule count
ASKCOS ingested-stock molecule count
deterministic normalized canonical-SMILES-set hash
complete cross-representation identity proof
transformation logs
software versions/configuration
all rejected/failed source records
```



The proof is complete-set, not sampled.



### 9.4 Validation still to freeze and execute
Before hard attrition receives authority, Session 014 must freeze prospectively:



```text
exact positive-control membership
control-stratum construction rules
measured validation quantities
known-synthesizable route-found sensitivity threshold
```



The controls remain stratified as:



```text
vendor-catalog / in-stock
marketed drugs
literature compounds with established synthesis/experimental use
```



Generated molecules are not positive controls.



The frozen Phase-1 molecules:



```text
0
3
18
```



must not influence:



```text
planner selection
planner configuration
stock construction
control-panel membership
measured validation quantities
validation threshold
attrition semantics
```



Only after the frozen Stage-6 validation passes may the gate touch those three molecules.



### 9.5 Session 014 execution order
The next session therefore begins:



```text
1. Build AiZynthFinder planner-specific stock from frozen D026/D027 stock.

2. Build ASKCOS buyables representation from the same frozen stock.

3. Account for all losses/collisions/rejections.

4. Complete full cross-representation identity proof.

5. Freeze exact AiZynthFinder instrument.

6. Freeze exact ASKCOS instrument.

7. Freeze positive-control panel, measured quantities, and pass threshold.

8. Time permitting, run the frozen validation.

9. Only after validation passes, run molecules 0, 3, and 18.
```



Tripwire work begins after Stage 6 is finalized rather than interrupting this remaining bounded Stage-6 work.



**Decision changed:** Session 013 closes with the shared Stage-6 molecular universe frozen and the remaining work narrowed to planner-stock construction, exact instrument freeze, prospective validation freeze, and validation execution.



---



## 10. Session close
**Status:** CLOSED



Session 013 and its Session 013.5 continuation together accomplished:



```text
Stage-6 framework retrieval
+
hard-attrition claim boundary
+
prospective validation authority model
+
AiZynthFinder primary / ASKCOS witness architecture
+
lazy witness execution
+
double-blind and human-chemist-review reporting semantics
+
D025 first-party shared-stock source freeze
+
Candidate-B filtering
+
D026 identity qualification
+
connectivity-only historical-ZINC waiver
+
Q1/Q2 exotic-valence quarantine
+
D027 three-branch discrepancy adjudication
+
complete 24,249,767-record batch execution
+
24,238,632-record frozen identity stock
+
persistent artifact archive
+
version-controlled freeze manifest
```



The session does **not** claim:



```text
Stage-6 planner instruments are already frozen
Stage-6 control validation has already passed
molecules 0, 3, and 18 have been evaluated by Stage 6
no-route means chemical unsynthesizability
```



The next session is:



```text
Session 014
```



and starts directly at planner-specific stock construction and complete cross-planner identity proof.



Do not repeat D025 source discovery, Candidate-B filtering, D026 qualification, D027 adjudication design, or the completed full identity transform unless execution exposes a specific technical defect in a frozen artifact that blocks the next authorized operation.


