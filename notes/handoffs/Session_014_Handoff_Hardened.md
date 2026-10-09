# Session 014 Handoff — Build Stage-6 planner stocks, freeze instruments, and run validation if time permits

**Date prepared:** 2026-09-30  
**Purpose:** Start Session 014 at the exact point where Session 013/013.5 ended, without repository deep-diving, cluster archaeology, D026 environment reconstruction, source-stock rediscovery, or repetition of frozen Stage-6 methodology work.

## 0. Standing rule

The handoff is the audit.

Start at the first unresolved scientific/execution step in Section 10.

Do **not** begin Session 014 with:

- repository inventory;
- broad `find`, `grep`, or filesystem archaeology;
- searching for historical ZINC stock again;
- rediscovering D024–D027;
- recreating the D026 Docker image/container;
- rerunning the 100-record pilot;
- rerunning the seven-record stereo audit;
- rerunning Candidate-B filtering;
- recomputing the completed 24,249,767-record D026/D027 batch;
- asking the user to locate artifacts already named here.

If execution exposes a specific missing/corrupt artifact, identify the exact artifact and the exact frozen decision/work package it blocks. Do not turn a concrete missing-file problem into a general discovery phase.

Session 013 and Session 013.5 are closed.

Session 014 is for:

1. defining the frozen planner-stock normalization/ingestion contract;
2. building the AiZynthFinder stock representation;
3. building the ASKCOS buyables representation;
4. proving complete cross-representation identity;
5. freezing the exact AiZynthFinder primary instrument;
6. freezing the exact ASKCOS witness instrument;
7. freezing the prospective Stage-6 validation panel/quantities/threshold;
8. time permitting, executing the frozen validation.

Do **not** run DiffSBDD molecules `0`, `3`, or `18` until the frozen validation passes.

---

## 1. Critical boundary

Session 013 closed the Stage-6 shared molecular-universe problem.

The authoritative post-D026/D027 stock contains:

```text
24,238,632 final identity records
```

derived from:

```text
24,249,767 Candidate-B inputs
10,491 Q1/Q2 quarantines
644 D027 exclude_continue discrepancies
```

All 644 D027 discrepancies independently reproduced the D026 connectivity layer:

```text
D026-side:   644
ZINC-side:     0
neither:       0
```

Final accepted-stock connectivity result:

```text
24,238,632 connectivity matches
0 connectivity mismatches
connectivity concordance = 1.0
```

Full-key result:

```text
23,792,769 full-key matches
445,863 full-key mismatches
full-key concordance = 0.9816052737629748
```

Exact bounded claim:

> The complete frozen Candidate-B input was transformed under D026/D027. The resulting frozen Stage-6 identity stock contains 24,238,632 records. It is the authoritative shared molecular universe from which both planner-specific terminal-stock representations must be constructed. This result does **not** establish route-search success, Stage-6 validation authority, practical syntheses, or intrinsic synthesizability/unsynthesizability.

Do not reopen:

- Candidate A historical-stock recovery;
- D025 first-party source selection;
- Candidate-B predicate;
- D026 identity authority;
- connectivity-only historical-ZINC waiver;
- Q1/Q2;
- proposed Q3 `[C]`;
- D027 three-branch adjudication;
- completed full transform.

---

## 2. What Session 013/013.5 achieved

### 2.1 D024 — Stage-6 architecture

Frozen planner roles:

```text
AiZynthFinder = primary planner
ASKCOS         = independent witness
```

Frozen union-with-provenance gate:

```text
AiZynthFinder route found
    -> PASS
    -> provenance = primary-found
    -> ASKCOS not required

AiZynthFinder no route
+ ASKCOS route found
    -> PASS
    -> provenance = witness-only
    -> witness-only flag retained

AiZynthFinder no route
+ ASKCOS no route
    -> HARD ATTRITION
    -> provenance = double-blind
    -> double_blind = TRUE
```

The witness is lazy: ASKCOS runs only after an AiZynthFinder no-route result because only that branch can alter final Stage-6 disposition.

Hard attrition is a project allocation rule after validation authority is established. It is **not** a chemistry verdict.

No-route means only:

> the frozen planner under the frozen model/template, stock, search algorithm, budget, and stopping rules did not find a route.

It does not mean “unsynthesizable.”

### 2.2 Reporting-only human-chemist flag

A double-blind molecule whose binding score is in the top decile of the Phase-1 cohort receives:

```text
human_chemist_review = TRUE
```

This is reporting-only.

It does not:

- rescue progression;
- alter the gate;
- alter validation;
- retune either planner;
- create limbo;
- authorize an automatic additional synthesis search.

Any future rescue experiment requires separate methodology.

### 2.3 D025 — frozen first-party source

Frozen first-party source:

```text
/nfs/exl/zinc20/2D/for-sale-25Q2.smi
```

Source provenance:

```text
records: 1,907,324,517
size:    113,043,807,549 bytes
SHA-256:
9b5c02767c56282c7704ce039e6176d986cf9e2e386a9ae46d1538600125c336
```

The historical public AiZynthFinder stock:

```text
zinc_stock_17_04_20.hdf5
17,422,831 InChIKey rows
```

was preserved as literature/provenance material but is **not** the operative Stage-6 stock.

Candidate A historical structure recovery is closed as:

```text
UNRECOVERED, not failed
```

Do not resume that search.

### 2.4 Candidate-B filter

Authoritative stored-metadata predicate:

```text
mwt <= 250.0
logp <= 3.5
reactive in {30, 50}
purchasable >= 10
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

Enumeration:

```text
4,275 source .txt files
140 eligible execution-prefilter files
4,135 excluded
0 malformed/unexpected
4,275 / 4,275 unique basenames
```

Enumeration-manifest SHA-256:

```text
0ed2151aa6d2d687f3e0c025cd2f7e8a1efe3a15ffdf89291fd0d18704403b86
```

Filtering result:

```text
input:       24,249,818
accepted:    24,249,767
rejected:            51
malformed:            0
```

The accepted Candidate-B population contained:

```text
24,249,767 unique ZINC IDs
```

### 2.5 D026 — identity authority

Frozen identity authority:

```text
D026-generated InChIKey
```

Downstream structure-consuming work continues to use the original frozen SMILES.

Required historical-ZINC agreement layer:

```text
connectivity layer = first 14 InChIKey characters
```

Full historical ZINC InChIKey equality is **not** required.

100-record pilot:

```text
93 / 100 full-key concordance
100 / 100 connectivity concordance
```

Seven-record stereo audit:

```text
records:                 7
connectivity matches:    7
full-key matches:        0
source explicit stereo:  7
source bond stereo:      7
source atom stereo:      4
oxime-like:              5
```

Case split:

```text
A_input_stereo_present_but_D026_key_empty_stereo_layer: 3
B_input_stereo_absent_but_ZINC_key_has_stereo:          0
C_both_keys_have_stereo_but_stereo_layer_differs:       4
```

### 2.6 D026 preserved pilot artifacts

These were a previous handoff failure point. Their paths and hashes are established; do **not** rediscover them.

Seven-record audit:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_pilot/stereo_audit_7_mismatches.tsv

SHA-256:
0fd004af4052729dc14c196833fea823d26dfbc6498aea6fd39a8b96bfb900f6
```

Associated summary:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_pilot/stereo_audit_summary.json

SHA-256:
a8e7bd2eace3f111f646d63b16c67becb732056b9a3e78c2a846b0f39bd10632
```

These are historical D026 qualification evidence. Session 014 does not need them to begin planner-stock construction.

### 2.7 D026 Q1/Q2

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

No Q3 `[C]` class exists.

### 2.8 D027 discrepancy adjudication

Frozen branches:

```text
local reproduces D026
    -> exclude_continue
    -> reproduced_side = d026
    -> record excluded
    -> run continues
```

```text
local reproduces ZINC over D026
    -> stopped_d026_processing_failure
    -> nonzero hard halt
```

```text
local reproduces neither
    -> adjudication_inconclusive
    -> reproduced_side = neither
    -> nonzero halt for human review
```

Final focused D027 suite:

```text
23 passed
```

Commit establishing the reviewed D027 implementation:

```text
7856595 Implement D027 discrepancy adjudication
```

At verification time this commit was present on:

```text
origin/main
github/main
```

---

## 3. Frozen archive — use these exact paths

### 3.1 Authoritative host-visible run directory

**Session 014 does not need the D026 Docker container.**

The completed run is already persisted on NFS.

Host-visible directory on `epyc2`:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/
```

This is the same persisted data that appeared inside the old D026 container as:

```text
/output/d026_full_2026-09-30/
```

For Session 014, prefer the **host-visible NFS path** above.

Do not recreate or restart `d026-batch-run` merely to access these files.

### 3.2 Authoritative planner-stock input

The single authoritative input for planner-stock construction is:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_identity.tsv
```

SHA-256:

```text
d15f14acd097dfb89a788c2cd07bd304f60245a18f6b6701c8f53350340bd1d0
```

Data records:

```text
24,238,632
```

The header is already established from the frozen D026 implementation:

```text
smiles
zinc_id
zinc_inchikey
d026_inchikey
full_key_match
connectivity_match
source_file
source_line_number
```

In TSV order:

```text
smiles	zinc_id	zinc_inchikey	d026_inchikey	full_key_match	connectivity_match	source_file	source_line_number
```

Scientific interpretation:

- `smiles` = original frozen structure string used for structure-consuming downstream transformations;
- `d026_inchikey` = frozen identity authority;
- `zinc_inchikey` = historical source key retained for provenance/comparison;
- `full_key_match` = historical full-key comparison only;
- `connectivity_match` = historical connectivity comparison;
- source fields preserve original lineage.

Do not reconstruct this dataset from the original 1.9B-record ZINC source in Session 014.

### 3.3 Other frozen full-run artifacts

Quarantine:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_quarantine.tsv

SHA-256:
59214dc57b4b474c6a9aa1abf6436c7d9f52892a4df3590b9702830807af317e

data records:
10,491
```

D027 discrepancy archive:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_discrepancy.tsv

SHA-256:
7900f64b6528227aeb8f2ec2c6f95b420eddd7a944c61afc3c9d5638eb313ae8

data records:
644
```

Summary:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_identity_summary.json

SHA-256:
30b6192a67d1581487444240b3a4ff2e8c1e2aafe57e05a87a08c3692550d8e6
```

Runtime log:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_run.log

SHA-256:
30b6192a67d1581487444240b3a4ff2e8c1e2aafe57e05a87a08c3692550d8e6
```

Exact runtime script:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/d026_batch_identity_runtime.py

SHA-256:
6a0c802a05f91a657e2f77a6773ac8c9e1dced1989ab62a1693f6cf1dd8a46c6
```

Frozen input to the full D026/D027 transform:

```text
/nfs/home/mhuang/stage6_candidate_b_frozen/filtered_records.tsv
```

SHA-256 recorded by the completed transform:

```text
5704a764984131f1165a5de0c24fa8967eebbdd55d4fe2fd9f16b70c2740ed03
```

This pre-D026 file is provenance, not the starting point for Session 014 planner-stock construction.

### 3.4 Full-run final accounting

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

Independent discrepancy audit:

```text
discrepancy_records: 644
adjudications: {'exclude_continue': 644}
reproduced_sides: {'d026': 644}
```

Persistent-copy verification:

```text
ALL_MATCH = True
```

### 3.5 Version-controlled freeze manifest

Local repository artifact:

```text
references/stage6/d026_full_2026-09-30/manifest.json
```

Validation result:

```text
FREEZE_MANIFEST_ACCOUNTING_OK
```

Treat this manifest as the concise Git-side audit record for the frozen full run.

---

## 4. Documentation completed

The authoritative methodology/decision record is:

```text
notes/Decisions.md
```

Session 013 final log:

```text
notes/Session_013.md
```

This Session 014 handoff should be stored as:

```text
notes/handoffs/Session_014_Handoff.md
```

Older handoffs, especially the Session 013.5 handoff, describe intermediate state and must not override this document.

---

## 5. Git state — enough to resume, no deep dive required

Local repository:

```text
~/Desktop/sbdd-project
```

Branch:

```text
main
```

Known reviewed D027 code commit:

```text
7856595 Implement D027 discrepancy adjudication
```

The subsequent D026/D027 freeze-manifest commit was pushed to both remotes.

The finalized Session 013 log is being committed/pushed at session close.

The exact post-close HEAD SHA is execution state, not a missing scientific artifact. Session 014 does **not** need to begin with repository archaeology.

If a Session-014 provenance record actually needs the exact current commit SHA, the only required command is:

```bash
cd ~/Desktop/sbdd-project
git log -1 --oneline --decorate
```

Do not follow this with broad history inspection unless a concrete discrepancy appears.

Remotes:

```text
origin  = UCSF Git
github  = alternate GitHub account
```

Push intended commits to both.

Known unrelated modified/untracked preservation material existed during Session 013, including Stage-5 backups/debug artifacts, development notes, older handoffs, D025 source preservation material, and `notes/Future_Implementations.md`.

Do not:

```text
git clean
git add .
```

Stage only Session-014 intended files.

---

## 6. Environments and access — what exists and what does not need recreation

### 6.1 Mac

Repository:

```text
~/Desktop/sbdd-project
```

Conda environment used for project-side evaluation work:

```text
sbdd-eval
```

Activate only if local Python/project code requires it:

```bash
conda activate sbdd-eval
cd ~/Desktop/sbdd-project
```

There is no requirement to recreate any Session-013 local environment before beginning Session 014.

### 6.2 `epyc2`

Session 013 successfully executed on host:

```text
epyc2
```

Observed shell identity:

```text
[mhuang@epyc2 ~]$
```

Mac-to-`epyc2` transfer during Session 013 used the already-established SSH tunnel through:

```text
localhost:2222
```

Do not spend Session 014 rediscovering the D026 container environment.

### 6.3 Old D026 Docker runtime — historical only

Historical qualified runtime:

```text
container: d026-batch-run
image: sbdd-d026:2026-09-28

environment ID:
sha256:020a8c810e5f4285fe4479c6d6aa6bc987393834480a24dd9a513631668851b4
```

This container produced the frozen stock.

**Session 014 does not need it.**

Do not restart, rebuild, or qualify it unless the frozen NFS artifacts are demonstrably inaccessible/corrupt.

### 6.4 Planner environments

AiZynthFinder and ASKCOS planner environments are **not yet frozen**.

That is legitimate Session-014 methodology work, not missing Session-013 setup.

Do not claim a specific version/build/model/template/search budget is already selected unless Session 014 explicitly freezes it.

---

## 7. Decisions now in force

### 7.1 D024 — primary/witness architecture

Frozen:

```text
primary = AiZynthFinder
witness = ASKCOS
```

Frozen execution semantics:

```text
primary route found
    -> pass
    -> witness not run

primary no route
    -> run witness

witness route found
    -> witness-only pass

witness no route
    -> double-blind hard attrition
    -> only after validation authority exists
```

ASKCOS does not redefine or recalibrate the primary.

### 7.2 D025 — identical terminal molecule universe

Both planner-specific stock representations must derive from the same frozen 24,238,632-record D026/D027 identity population.

Before either planner is used for Stage-6 route search, preserve:

1. source-record count;
2. source SHA-256;
3. unique-molecule count after the frozen normalization contract;
4. AiZynthFinder ingested-stock molecule count;
5. ASKCOS ingested-stock molecule count;
6. deterministic hash of the normalized canonical-SMILES molecule set;
7. complete cross-representation identity proof;
8. transformation logs;
9. software versions/configuration;
10. all rejected/failed source records;
11. all normalization collisions.

A sampled proof is insufficient.

### 7.3 D026/D027 — accepted shared-stock source

Authoritative planner-stock source:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_identity.tsv
```

Expected accepted input count:

```text
24,238,632
```

Session 014 may define the planner-specific normalization needed to ingest this stock, but it may not silently change the underlying accepted molecule universe.

Any loss/collision/rejection created during planner-stock construction is a measured transformation result that must be explicit.

### 7.4 Prospective validation authority

Before hard attrition can operate, Session 014 must freeze and then test:

- exact positive-control membership;
- control-stratum construction;
- measured validation quantities;
- prospective route-found sensitivity threshold.

Control strata already fixed at the framework level:

```text
vendor-catalog / in-stock compounds
marketed drugs
literature compounds with established synthesis or experimental use
```

Generated molecules are evaluation inputs, not validation positives.

There is no defensible ground-truth “known unsynthesizable” negative class.

Therefore Stage-6 validation may establish sensitivity for recovering routes to known-synthesizable compounds; it may not establish conventional specificity for intrinsic nonsynthesizability.

### 7.5 Generator protection / anti-tuning

Phase-1 DiffSBDD Stage-6 cohort:

```text
0
3
18
```

These molecules must not influence:

- planner selection;
- planner version;
- model/template choice;
- stock normalization;
- search algorithm;
- search budget;
- stopping conditions;
- validation membership;
- validation quantities;
- sensitivity threshold;
- gate semantics.

Later FLOWR must use the identical finalized Stage-6 pathway.

---

## 8. Claim authority

### Authorized

The following may be stated:

- D024 fixes AiZynthFinder primary / ASKCOS witness architecture.
- D025 fixes a common shared molecular-universe requirement.
- Candidate B originally contained 24,249,767 accepted source records.
- D026/D027 completed over the entire Candidate-B population.
- 10,491 Q1/Q2 records were quarantined.
- 644 connectivity discrepancies were excluded under D027 after local generation reproduced D026 in all 644 cases.
- no D027 discrepancy reproduced ZINC over D026;
- no D027 discrepancy produced an inconclusive local adjudication;
- the frozen accepted identity stock contains 24,238,632 records;
- those accepted identity records had 100% historical-ZINC connectivity concordance;
- the frozen planner-stock source is the host-visible `candidate_b_d026_identity.tsv` path in Section 3.

### Prohibited

Do not state:

- Stage 6 is already validated for hard attrition;
- an AiZynthFinder planner stock already exists;
- an ASKCOS buyables representation already exists;
- exact AiZynthFinder/ASKCOS versions or search settings are already frozen;
- the historical 17,422,831-row AiZynthFinder stock is operative;
- no-route proves unsynthesizability;
- a found route proves practical experimental feasibility;
- the 644 D027 exclusions are chemically invalid;
- Q1/Q2 records are intrinsically unsynthesizable;
- the Phase-1 molecules have been run through Stage 6.

---

## 9. Do NOT reopen

Closed work:

- Stage-5 validation;
- Stage-5 cohort disposition;
- Graves/DOCK null ladder;
- Candidate A historical-stock recovery;
- historical AiZynthFinder stock as operative-stock candidate;
- D025 first-party source choice;
- Candidate-B predicate;
- tranche prefilter/enumeration;
- Candidate-B 24,249,767-record filter result;
- D026 100-record pilot;
- seven-record stereo audit;
- connectivity-only waiver;
- Q1/Q2 definitions;
- Q3 `[C]` proposal;
- D027 discrepancy semantics;
- old pre-amendment stop at 5,334;
- old post-Q1/Q2 stop at 8,829;
- full D026/D027 production run;
- frozen 24,238,632-record identity stock;
- D026 runtime qualification.

If a future execution uncovers a real frozen-artifact defect, name it narrowly and identify what it blocks before proposing any reopen.

---

## 10. Session 014 exact starting point

### 10.1 Start here — scientific question

The first unresolved scientific question is:

> What exact normalization/ingestion contract should convert each record of the frozen 24,238,632-record D026/D027 identity stock into (a) the AiZynthFinder stock representation and (b) the ASKCOS buyables representation, such that both terminal stocks can be proven to represent the same normalized molecular set?

This is not a source-discovery question.

The source is already frozen.

### 10.2 Exact input

Use:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_identity.tsv
```

Expected data records:

```text
24,238,632
```

Expected columns:

```text
smiles
zinc_id
zinc_inchikey
d026_inchikey
full_key_match
connectivity_match
source_file
source_line_number
```

### 10.3 First work package

The first work package is **planner-stock construction design + implementation**, not planner validation.

Before coding scientifically consequential normalization, Session 014 should:

1. identify the exact stock input/lookup requirements of the selected AiZynthFinder build;
2. identify the exact buyables input/lookup requirements of the selected ASKCOS build;
3. perform the required literature/implementation alternatives check for any normalization choice that could change molecule identity;
4. draft the shared normalization/identity contract;
5. obtain user approval;
6. implement/test the transformation function-by-function;
7. build both full planner representations;
8. run complete cross-representation identity proof;
9. freeze the resulting artifacts/configuration.

This is the correct place for targeted inspection of planner documentation/source.

It is **not** permission for broad repository or cluster archaeology.

### 10.4 First work-package done condition

Do not call planner-stock construction complete until all are frozen:

```text
authoritative source count = 24,238,632

shared normalization contract
+
unique normalized molecule count

AiZynthFinder stock artifact
+
AiZynthFinder ingested count

ASKCOS buyables artifact
+
ASKCOS ingested count

all parser failures
+
all normalization failures
+
all collisions
+
all representation losses

deterministic normalized-molecule-set hash

complete AiZynthFinder-vs-ASKCOS molecule-set identity proof
```

The identity proof must be complete, not sampled.

### 10.5 After planner-stock identity passes

Then freeze the **AiZynthFinder instrument**:

```text
exact version/build
expansion policy/model
reaction-template set
stock artifact/hash
search algorithm
search settings
search budget
stopping conditions
route-return semantics
success semantics
other endpoint-defining settings
```

Then freeze the **ASKCOS witness**:

```text
exact version/build
retrosynthesis model/template configuration
buyables artifact/hash
search algorithm
search settings
search budget
stopping conditions
route-return semantics
success semantics
other adjudication-defining settings
```

No validation run before both instruments are frozen.

### 10.6 Then freeze validation

Prospectively freeze:

```text
exact positive-control membership
control stratum for each record
independent evidence supporting known synthesizability/availability
measured quantities
route-found sensitivity formula
required sensitivity threshold
failure semantics
```

The threshold must be fixed before observing validation results.

If validation passes:

```text
hard attrition authority is activated
```

If validation fails:

```text
Stage-6 results remain characterization-only
no Phase-1 Stage-6 rejection is authorized
```

### 10.7 Only after validation passes

Run:

```text
DiffSBDD molecule 0
DiffSBDD molecule 3
DiffSBDD molecule 18
```

under the exact validated frozen instrument.

Do not inspect these Stage-6 outcomes earlier.

---

## 11. Minimal resume commands — no archaeology

### Mac repository work

```bash
conda activate sbdd-eval
cd ~/Desktop/sbdd-project
```

That is enough to resume local scientific-core work.

Do not start with broad Git/file discovery.

### `epyc2` planner-stock input

Once on `epyc2`, use the frozen host-visible source directly:

```bash
FROZEN_D026_STOCK=/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_identity.tsv
```

No D026 container is required.

If a script needs the input path, pass `$FROZEN_D026_STOCK`.

### Optional one-line integrity check only if execution requires it

The frozen artifact is already qualified. Do not rehash 2.9 GB merely as ceremony.

If a downstream step reports an input-integrity problem and a hash check becomes necessary, the expected SHA-256 is:

```text
d15f14acd097dfb89a788c2cd07bd304f60245a18f6b6701c8f53350340bd1d0
```

---

## 12. Process rules in force

- **No rediscovery:** use this handoff and the frozen artifacts before asking the user to locate anything.
- **Validation-requirement rule:** every new mandatory validation requirement must trace to the frozen framework. Otherwise label it proposed and obtain approval.
- **Alternatives-pass rule:** before adopting a new model/package/scoring/planner component, enumerate serious cited alternatives, explain what each enables, assess dependencies/compute/scope, and trace rejection to an existing frozen requirement. If no documented rejection exists, label it unrejected.
- **Scientific-core rule:** scientifically consequential transformations are authored/reviewed collaboratively, function-by-function.
- For each scientific-core function:
  - explain what it does;
  - explain why it is scientifically relevant;
  - distinguish measurement/transformation from later decision logic;
  - state what the test is expected to establish before running it;
  - distinguish exact expected values from qualitative invariants;
  - define what counts as failure;
  - provide a terminal-wrapped runnable check.
- **Partial edits:** provide exact terminal patches rather than asking the user to edit lines manually.
- **Result dictionaries:** result-producing functions assign to `result` and then `return result`.
- **Script close:** after a scientific-core script is complete, summarize each function and the script's scientific role.
- **Implementation assistant:** OpenCode may do plumbing, tests, manifests/hashes, orchestration, repetitive execution, and mechanical refactoring only after scientific behavior is understood/frozen.
- **No target-specific hardcoding:** target-specific constants remain in config/artifacts.
- **Preservation:** retain intermediate, failed, validation, and diagnostic artifacts until the stage is finalized.
- **No success-by-exit-code:** inspect scientific outputs.
- **No invented provenance:** never invent file paths, hashes, versions, or Git state.
- **Git:** stage intended files only; do not `git add .`; do not `git clean`; push intended commits to both remotes.

---

## 13. Preservation rule

Preserve read-only Session-013 evidence:

- `notes/Decisions.md`;
- `notes/Session_013.md`;
- `references/stage6/d026_full_2026-09-30/manifest.json`;
- D025 provenance artifacts;
- Candidate-B enumeration/filter manifests;
- frozen pre-D026 Candidate-B input;
- D026 pilot and seven-record audit;
- Q1/Q2 diagnostics;
- D027 discrepancy diagnostics;
- all old stopped-run artifacts;
- the complete NFS directory:
  `/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/`.

Preserve new Session-014 evidence as it is created:

- normalization contract/config;
- stock-builder code/tests;
- full transformation logs;
- all parser failures;
- all collisions;
- all rejected molecules;
- AiZynthFinder stock artifact/hash/count;
- ASKCOS buyables artifact/hash/count;
- normalized molecule-set hash;
- full cross-representation identity proof;
- exact primary planner environment/build/config;
- exact witness environment/build/config;
- control-panel source evidence;
- frozen validation config/threshold;
- all validation results, including failures and disagreements.

Do not delete failed branches merely because they are not part of the final production pathway.

---

## 14. Known unknowns — legitimate Session-014 work, not missing handoff information

The following are intentionally **not** supplied because Session 013 did not freeze them:

### AiZynthFinder

- exact version/build;
- exact policy/model;
- exact template set;
- exact stock-construction mechanism for this new frozen stock;
- exact search algorithm/settings;
- exact budget/stopping rules;
- exact route-success semantics.

### ASKCOS

- exact version/build;
- exact model/template configuration;
- exact buyables ingestion mechanism for this new frozen stock;
- exact search algorithm/settings;
- exact budget/stopping rules;
- exact route-success semantics.

### Shared planner-stock normalization

- exact canonicalization/normalization operation used to prove identical molecule sets across the two planner representations.

This must be designed and frozen prospectively in Session 014 because it is scientifically consequential.

### Validation

- exact positive-control members;
- exact panel size;
- exact prospective route-found sensitivity threshold.

These must also be frozen prospectively before observing validation outcomes.

These are the work of Session 014. They are **not** reasons to inspect old Session-013 environments.

---

## 15. Session-014 intended completion state

Minimum target:

```text
planner-stock normalization contract frozen
+
AiZynthFinder stock built
+
ASKCOS buyables built
+
complete cross-representation identity PASS
+
AiZynthFinder exact instrument frozen
+
ASKCOS exact instrument frozen
+
validation panel/quantities/threshold frozen
```

Time permitting:

```text
frozen validation executed
+
validation result recorded
```

Only if validation passes and time remains:

```text
authorize, then execute Stage 6 on 0 / 3 / 18
```

The project sequencing after Stage 6 is:

```text
finish Stage 6
-> begin Tripwire, CYP-first
```

Do not split attention into Tripwire before the bounded Stage-6 work above is closed unless the user explicitly changes the plan.
