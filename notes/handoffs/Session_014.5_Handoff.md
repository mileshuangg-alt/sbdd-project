# Session 014.5 Handoff - Continue D029 Candidate-B compatibility run

**Date prepared:** 2026-10-05  
**Purpose:** Continue the current D029 Candidate-B compatibility work without rediscovering prior artifacts, decisions, source code, runtime qualification, or the completed Candidate-A work.

## 0. Standing rule

This handoff is the audit. Start at the first unresolved execution step.
Do not reopen frozen/completed work. Do not invent artifact paths, hashes, Git state, or preservation state.

The uploaded `Session_013.5_Handoff (2).md` is the template and carries the project's standing rule: the handoff is the audit, start at the first unresolved execution step, and do not invent provenance. fileciteturn66file0L3-L12

## 1. Immediate next step

**Candidate-B continue-and-log run has NOT been run.**

The first task in Session 014.5 is therefore:

1. Use the already inspected real D029 wrapper source as the starting point.
2. Build the Candidate-B wrapper from that verified source.
3. Add only wrapper-level per-record exception capture and logging.
4. Do not alter `candidate_b_normalize()`.
5. Do not alter the scientific definition of Candidate B.
6. Perform a tiny/preflight check before any full 241,148-key normalization run.
7. Then launch the full Candidate-B conflicted-key measurement under the approved D029 runtime, with step-by-step persistent progress and failure logging.

**Important:** the previously proposed `/tmp/run_d029_candidate_b_pinned_final.py` does **not** yet exist merely because it was drafted in chat. Do not assume it exists. Create it from the verified Candidate-A wrapper only after inspecting/applying the exact patch.

## 2. D029 status and approved decisions

### 2.1 D029 runtime-pin amendment — approved

Approved amendment date: **2026-10-04**.

For D029 compatibility measurements the runtime is pinned to:

```text
container:     sbdd-d026:2026-09-28
AiZynthFinder: 4.4.1
RDKit:         2023.09.6
```

The runtime conclusion applies to Candidate A only.

Candidate-A comparison already completed:

| Run | Runtime | Conflicted keys | False merges | False splits | Sample false merges | Overall pass | Record status |
|---|---|---:|---:|---:|---:|---|---|
| Earlier D029 Candidate-A run | RDKit 2026.03.5 | 241,148 | 0 | 241,129 | 0 | false | run-history result, no saved artifact |
| Pinned D026-compatible Candidate-A run | RDKit 2023.09.6 | 241,148 | 0 | 241,129 | 0 | false | saved run artifacts |

The 2023.09.6 Candidate-A run is preserved in:

```text
/nfs/home/mhuang/stage6_d029_compatibility_pinned/d029_candidate_a_pinned_final.progress.json
/nfs/home/mhuang/stage6_d029_compatibility_pinned/d029_candidate_a_pinned_final.json
/nfs/home/mhuang/stage6_d029_compatibility_pinned/d029_candidate_a_pinned_conflict_results.json
/nfs/home/mhuang/stage6_d029_compatibility_pinned/d029_candidate_a_pinned_sample_results.json
/nfs/home/mhuang/stage6_d029_compatibility_pinned/d029_candidate_a_pinned_final.log
```

The earlier 2026.03.5 result is retained as run-history evidence only; no saved artifact containing that result was located.

### 2.2 D029 Candidate-B failure amendment — approved

Approved amendment date: **2026-10-04**.

This amendment **replaces the earlier Candidate-B failure-semantics draft**.

Operative rule:

```text
Any Candidate-B normalization failure
OR
any failed D029 pass criterion
    -> B does not pass as the sole identity step
    -> D030 is considered
```

A Candidate-B normalization failure is either:

- an exception raised during the frozen Candidate-B normalization pipeline; or
- failure to produce a Candidate-B identity.

Every failure is logged with at minimum:

```text
D026 full InChIKey
source SMILES
candidate
exception type
exception message
RDKit version
```

The failure's error, SMILES, and key are **diagnostic only**. The cause does not change the trigger.

Report raw failure counts and denominators separately over:

```text
conflicted-key population
source-spelling population
```

No numeric threshold. No relevance exclusion. No “real compound” exclusion. No chemical-class/source-status exception.

Failures are **not** false merges or false splits. Successful Candidate-B identities still feed the existing false-merge/false-split metrics.

The amendment adds the previously open pass/fail consequence: a Candidate-B failure means B cannot be the sole identity step and D030 is considered.

## 3. Frozen D029 inputs

### 3.1 Frozen D026 stock

Authoritative planner-stock source:

```text
/nfs/home/mhuang/stage6_candidate_b_d026_run/d026_full_2026-09-30/candidate_b_d026_identity.tsv
```

Expected/frozen records:

```text
24,238,632
```

Frozen stock SHA-256:

```text
d15f14acd097dfb89a788c2cd07bd304f60245a18f6b6701c8f53350340bd1d0
```

Columns confirmed from the actual file header:

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

### 3.2 Persisted distinct-key manifest

Already created so the 2.9 GB stock does not need to be rescanned merely to rediscover the key universe:

```text
/nfs/home/mhuang/stage6_d029_compatibility_pinned/d029_distinct_d026_keys.tsv
```

Distinct keys:

```text
23,660,155
```

Manifest SHA-256:

```text
d8a94e5135acadd0c4360d0d4336ebbbf320b52214d4f5529f55d185e4a570cd
```

A 1000-row shell/Python ordering check already established:

```text
shell_unique: 955
python_unique: 955
ORDER_MATCH: True
```

The ordering was `LC_ALL=C sort -u`, matching the lexicographic ordering used by D029's `select_sampled_keys`.

### 3.3 D029 conflicted population

The conflict artifact used by the real D029 runner is inside the D029 container mount:

```text
/tmp/stage6_planner_stock_work_20261001/
stage6_planner_stock_build_db342e6310954bdeb056a687fad930c8/
source_identity_representation_conflicts.tsv
```

Host-side equivalent is available through the Docker bind mount, not as a directly present host path.

Verified SHA-256:

```text
8d6c460592e1e2757e1ff95608733b1cdefabdc50d81066237ef0461f73e7e90
```

Conflict rows:

```text
318,033
```

Distinct conflicted D026 keys:

```text
241,148
```

### 3.4 Candidate-B crash already observed

Original Candidate-B D029 run under RDKit 2023.09.6 aborted at:

```text
D026 key:
KDKCOUBAKDHIMF-UHFFFAOYSA-N

source SMILES:
CN1NOC(=O)/C1=C/N=O

exception:
RuntimeError: Invariant Violation
could not find atom2
```

The failure occurred inside:

```text
MolStandardize.CanonicalTautomer(cleaned, params)
```

The crash happened while traversing the sorted conflicted-key population.

A read-only rank check established that this key is:

```text
TARGET_RANK: 90775
TOTAL_DISTINCT_CONFLICTED_KEYS: 241148
RANK_FRACTION: 90775 / 241148
```

So the first observed crash occurred at rank 90,775 / 241,148 = approximately 37.65% of the sorted conflicted-key population.

This **does not** establish the total number of Candidate-B failures. It only establishes where the first observed crash occurred. The old implementation aborted on the first exception.

## 4. Real D029 source code already inspected

### 4.1 Source module

```text
/tmp/stage6_d026_normalization_compatibility.py
```

Confirmed functions used by the real wrapper include:

```text
validate_full_d026_key
build_conflict_source_smiles_by_key
select_sampled_keys
construct_adjacent_pairs_after_lexicographic_sort
candidate_a_normalize
candidate_b_normalize
normalize_source_smiles_by_key
build_candidate_report
detect_false_split_keys
detect_false_merge_pairs
detect_false_merge_pairs_for_sample
key_result_to_json
```

Candidate-B source definition is already known and must remain unchanged:

```python
candidate_b_normalize(smiles, rdkit_version=None)
```

It does:

```text
MolFromSmiles
CleanupParameters()
MolStandardize.Cleanup
MolStandardize.CanonicalTautomer
MolToSmiles(canonical=True, isomericSmiles=True)
```

### 4.2 Existing real wrapper

Verified wrapper:

```text
/tmp/run_d029_candidate_a_pinned_final.py
```

The wrapper:

- loads the real D029 source dynamically;
- verifies required functions exist;
- loads the persisted 23,660,155-key manifest without scanning the stock for the key universe;
- calls the real `select_sampled_keys()`;
- constructs 10,000 adjacent sample pairs;
- loads the preserved conflict artifact;
- performs one full stock pass only to collect source SMILES for the 20,000 selected sample keys;
- writes progress JSON as it runs;
- then normalizes the conflict population and sample using the selected normalizer.

The actual wrapper's Candidate-A execution block was inspected. It calls:

```python
conflict_results = d029.normalize_source_smiles_by_key(
    conflict_source_smiles_by_key,
    d029.candidate_a_normalize,
    rdkit_version,
)
```

and likewise calls the same shared function for the sample.

**Do not invent a new wrapper architecture.** The Candidate-B wrapper should minimally adapt this verified wrapper while adding the approved continue-and-log failure handling.

## 5. Candidate-B wrapper requirements for Session 014.5

The new wrapper should be a separate file so the completed Candidate-A wrapper remains untouched:

```text
/tmp/run_d029_candidate_b_pinned_final.py
```

However, at handoff time this file has **not been run and should not be assumed to exist**.

Scientific behavior required:

1. Use `d029.candidate_b_normalize` unchanged.
2. Wrap each individual source-SMILES normalization call in an exception handler.
3. On exception, synthesize a `NormalizationResult` with failure status and no identity, preserving the exact exception type/message.
4. Log immediately to disk:
   - D026 full InChIKey
   - source SMILES
   - candidate = `candidate_b`
   - exception type
   - exception message
   - RDKit version
5. Continue to the next source spelling.
6. Retain successful identities exactly as the existing D029 code does.
7. Do not classify failures as false merges or false splits.
8. Compute:
   - failed conflicted keys / total conflicted keys;
   - failed conflicted source spellings / total conflicted source spellings;
   - sample failure counts separately.
9. Persist progress while running so the user can step away safely.
10. Do not alter `candidate_b_normalize()`.

### Failure counting semantics

For the conflicted-key population:

```text
failed_key_count = number of D026 keys with >= 1 failed source spelling
failed_spelling_count = number of failed source spellings
key_denominator = number of conflicted D026 keys
spelling_denominator = total distinct source spellings across conflicted keys
```

The presence of both success and failure under the same D026 key does **not** create a false split merely because of the failure; only successful identities enter false-split logic.

## 6. D029 sample definition is frozen

Use the exact D029 functions:

```python
selected_keys = d029.select_sampled_keys(
    stock_keys,
    selected_key_count=20000,
)

sampled_pairs = d029.construct_adjacent_pairs_after_lexicographic_sort(
    selected_keys
)
```

Expected:

```text
selected keys: 20,000
sample pairs: 10,000
```

No new sampling rule.

## 7. D030 status

**D030 is parked and unapproved.**

D030 presupposes the D029 consequence that B cannot be the sole identity step without a fallback.

Current open D030 options:

```text
keep-all-forms
one-representative
```

The one-representative option currently means one planner-ingested representative per planner, while retaining alternatives/failures as provenance/audit information.

ASKCOS representative concept:

```text
exact canonical SMILES emitted by the frozen ASKCOS-side RDKit canonicalizer
```

Open D030 items:

1. Verify the real ASKCOS image's RDKit version and verify that its canonicalizer matches the project's `canonicalize_askcos_smiles`.
2. Determine what the real AiZynthFinder stock ingestion/matching mechanism matches on, with a source.
3. Decide whether D030 uses `keep-all-forms` or `one-representative`.
4. Name/select the fallback mechanism.

Do not act on D030 merely because Candidate B fails. D029 determines that D030 is **considered**, not that D030 is automatically adopted.

## 8. D026 frozen identity authority

D026 remains untouched.

Recorded D026 text:

> **D026 therefore established the D026-generated InChIKey as the operative identity authority.**
>
> **Downstream structure-consuming stages continue to use the original frozen SMILES.**

The actual project identity primitive is:

```python
from aizynthfinder.chem import Molecule

molecule = Molecule(smiles=smiles, sanitize=True)
inchikey = molecule.inchi_key
```

D026 runtime qualification:

```text
container: sbdd-d026:2026-09-28
AiZynthFinder: 4.4.1
RDKit: 2023.09.6
Python: 3.11.11
```

The frozen D026 key is not to be rewritten by D029 or D030 unless a future explicit superseding decision authorizes that.

## 9. D025 / planner-stock contract still in force

Both planner-specific stock representations must derive from the same frozen 24,238,632-record D026/D027 identity population.

Before either planner is used, preserve and report:

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
all normalization collisions
```

A sampled identity proof is insufficient. The underlying Session-013/014 handoff explicitly says any normalization collision, parser loss, failed transformation, or planner-representation disagreement must be explicit. fileciteturn66file0L4-L12

## 10. Provenance and source-population context

Frozen first-party ZINC source:

```text
/nfs/exl/zinc20/2D/for-sale-25Q2.smi
```

Stored-metadata Candidate-B predicate:

```text
mwt <= 250.0
logp <= 3.5
reactive in {30, 50}
purchasable >= 10
```

The project record does not define what `purchasable >= 10` means in ZINC's operational terms. Do not infer in-stock vs make-on-demand vs another tier.

The stock is a filtered first-party ZINC for-sale population, not an enumeration/generation population.

No Stage-6 per-molecule retrosynthesis result set exists in the project record for the frozen D026 stock.

## 11. Preservation rules

Preserve all D029 Candidate-A artifacts and all failed/intermediate Candidate-B artifacts.

Do not delete:

- original Candidate-B crash artifacts;
- Candidate-A pinned artifacts;
- the D029 manifest;
- the stock distinct-key manifest;
- the conflict artifact;
- any partial Candidate-B failure log;
- any partial JSONL/progress output.

The project's preservation rule requires intermediate, failed, validation, and diagnostic artifacts to remain available until the relevant stage is finalized.

## 12. No-run-before-check rule for Session 014.5

Before launching the full Candidate-B normalization run:

1. Confirm the new wrapper source is exactly the intended patch to the real verified Candidate-A wrapper.
2. Confirm no change was made to `candidate_b_normalize()`.
3. Confirm the failure log schema.
4. Run a tiny fixture using a few source spellings, including a deliberately exception-producing stub if needed for the wrapper-level mechanics.
5. Confirm a single failure is logged and the loop continues.
6. Confirm a successful identity still contributes to identity metrics.
7. Confirm output is written incrementally.
8. Only then launch the 241,148-key conflicted population.

The tiny fixture is a mechanical plumbing test, not a scientific result and must not be conflated with D029.

## 13. Expected first full-run scope

Once the preflight passes:

```text
runtime:      sbdd-d026:2026-09-28
RDKit:        2023.09.6
population:   241,148 conflicted D026 keys
source spellings: all spellings attached to those keys
sample:       20,000 D026 keys / 10,000 pairs
```

This run answers the unresolved question:

> How many Candidate-B normalization failures actually occur across the full D029 conflicted-key population under the approved D026-compatible runtime?

It is the first complete measurement of Candidate-B failure prevalence. The earlier crash established only the existence and rank of the first observed failure.

## 14. Session-014.5 completion condition

Session 014.5 may close the Candidate-B execution subtask only after:

- complete Candidate-B conflicted-key run finishes or is explicitly stopped by a documented execution failure;
- raw failure count is known;
- failed-key and failed-spelling denominators are known;
- every failure is logged with key, source SMILES, candidate, exception type/message, and RDKit version;
- false-merge and false-split metrics from successful identities are computed;
- D029 overall consequence is recorded as required by the approved amendment;
- all new diagnostic artifacts are preserved;
- no D030 methodology is silently adopted.

## 15. Process rules in force

- Use existing session artifacts and source before asking the user to rediscover anything.
- Never invent paths, hashes, versions, or results.
- Scientific-core transformations remain deliberately reviewed.
- New mandatory validation rules require traceability to frozen methodology and user approval.
- Preserve all intermediate/failed artifacts.
- Never infer scientific success from a process exit code.
- Candidate B implementation itself is frozen; wrapper-level error handling may change execution accounting under the approved D029 amendment.
- D026 remains frozen.
- D030 remains parked.

**Session 014.5 first action:** continue from the verified real wrapper source and build/test the Candidate-B continue-and-log wrapper. Do not rerun or recreate earlier D029 work.
