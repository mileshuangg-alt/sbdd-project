# Session 015 — Original-ASKCOS Planner Execution Qualification

**Date:** 2026-10-09

**Paused:** 2026-10-16

**Status:** CLOSED FOR HANDOFF TO ADMET — Stage 6 execution qualification incomplete

## Session objective

Continue Stage 6 — Synthetic Feasibility from the qualified original-ASKCOS SIF produced in Session 014.

Session 014 closed after qualifying the immutable original-ASKCOS Docker/SIF representation runtime but before actual retrosynthesis planner deployment.

The Session-015 objective was therefore to identify and qualify the smallest non-web original-ASKCOS execution surface capable of:

1. accepting a represented target molecule;
2. running the native retrosynthetic search machinery;
3. preserving native planner behavior;
4. distinguishing completed search, search-budget expiration, and execution failure;
5. exposing sufficient execution evidence to map planner behavior into the already-frozen D030 Stage-6 outcome taxonomy.

The session does not reopen D028, D029, the D030 identity/routing architecture, the native-runtime representation amendment, or the qualified original-ASKCOS SIF.

---

## Starting state

At Session 015 start:

- D028, D029, and D030 are frozen;
- the D026 full 27-character InChIKey remains the molecular-identity authority;
- the D030 routing population remains exactly the frozen Candidate-B-failing source spellings;
- the original-ASKCOS witness image is frozen at `askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0`;
- Docker image ID is `sha256:551d90c9bf090e992fb971daf95e0cd5f38baf75d4938a4188d25e8de4383f91`;
- the frozen runtime is Python 3.5.9, RDKit 2019.03.4, linux/amd64;
- the qualified CoreHPC SIF is `/mnt/fac/CX900004_DS117/sbdd-project/stage6/images/askcos_d030_85ae3c1b.sif`;
- canonical SIF SHA-256 is `93ccedc2365dbed9231e999b06959e72f790b2971178d028edda8faff8dc6196`;
- FAC is the persistent Stage-6 storage authority;
- node-local `/tmp` is transient execution workspace;
- actual original-ASKCOS retrosynthesis execution remains unqualified.

---

## 1. Minimal original-ASKCOS execution surface

The frozen original-ASKCOS source was inspected read-only before execution-layer modification.

The inspection covered the API and application entry points, MCTS construction, local multiprocessing and Celery execution, worker dispatch, result collection, template application, template prioritization, fast filtering, pricer/buyables behavior, tree status, termination behavior, and result structures.

The goal was not to redesign the planner. The goal was to determine whether the native local `MCTS(celery=False)` path could serve as the minimal non-web execution surface while preserving the frozen planner's scientific behavior.

The local MCTS path was selected for qualification rather than launching the complete legacy web/Celery stack.

---

## 2. Derived execution-layer boundary

Source inspection established that the execution evidence required by D030 could not be recovered safely from the unmodified local path without a small derived execution layer.

The canonical digest-pinned original-ASKCOS Docker/SIF remains immutable.

A separately versioned derived `tree_builder.py` was therefore developed with a strict scope:

> execution instrumentation and bookkeeping only

The derived layer is not authorized to alter molecular representation, RDKit behavior, rdchiral behavior, template libraries or selection, template relevance predictions, precursor generation, fast filtering, MCTS/UCB selection, buyability determination, stock semantics, depth or branching limits, search-time limits, route extraction, route ranking, or other scientific search behavior.

The original frozen SIF remains the provenance anchor.

---

## 3. Execution-semantics problems identified

### 3.1 Local exhaustion bookkeeping

The original exhaustion condition relied on Celery-oriented `pending_results`, which does not represent outstanding local multiprocessing work.

For `celery=False`, native local bookkeeping already maintains `active_pathways_pending`, incremented when a local expansion is submitted and decremented when its result returns.

The derived layer therefore records local exhaustion only when:

```text
every active_pathway is empty
AND
every active_pathways_pending counter is zero
```

This records exhaustion of the configured ASKCOS search process. It does not assert universal absence of a synthetic route.

### 3.2 Worker exceptions versus zero-precursor chemistry

The original local worker caught template-expansion exceptions and converted them into an ordinary result shaped like a zero-precursor template application.

This made execution failure observationally indistinguishable from a legitimate successful template application producing no precursors.

The derived layer preserves worker exceptions as a distinct structured `worker_error` envelope containing pathway ID, SMILES, template index, exception type, and exception message.

The coordinator records such a result as `termination_reason = planner_error` with structured `execution_error` metadata.

A legitimate successful zero-precursor template application retains its original chemical-negative behavior and is not an execution error.

### 3.3 Explicit termination provenance

The native coordination loop has distinct stopping mechanisms that were not exposed as a stable run-status signal.

The derived layer records:

```text
planner_error
return_first
exhausted
time_limit
```

Natural expiration of the existing `expansion_time` budget is recorded as `time_limit`. The search-time limit itself is not changed.

---

## 4. Local-worker template-prioritizer repair

During execution qualification, the local worker path was found to call template application using an unresolved/free `template_prioritizer` name rather than the configured instance state.

The derived local worker call was repaired to use:

```python
template_prioritizer=self.template_prioritizer
```

This restores the configured instance dependency for the local execution path. It does not select a new prioritizer or alter the frozen prioritization methodology.

---

## 5. Derived-source provenance

Original frozen `tree_builder.py` SHA-256:

`9b7803e1cbb278e2defbbe5fc73623cdbb7bc095ace924e1fd05244f6f136952`

Problem-1 checkpoint SHA-256:

`5703344a0c06391cc9d4bf3adc8ea1e2700e92cd4048e0baee02617262e1a484`

Problems-1-and-2 checkpoint SHA-256:

`be52d843816103f0fd9687fc10e6e00c395822289c53672f459627c65718abf6`

Final derived `tree_builder.py` SHA-256:

`18c77a5576fdc1dcb68dd5ec0d6248a5d890d5892c4a785c2e697e22e6db8615`

The final delta from the Problems-1-and-2 checkpoint was only the local-worker template-prioritizer correction.

The frozen patch archive was:

`stage6_askcos_d030_execution_patch_2026-10-10.tar.gz`

Archive SHA-256:

`659fd61bf207f2cb357d0cfc1926994c260cebf1e46a02a34be91c61ccebcd06`

---

## 6. CoreHPC/FAC transfer and verification

The frozen execution-layer archive was transferred from epyc2 to CoreHPC through the established ProxyJump route, with the CoreHPC bastion used as transit only.

Persistent destination:

`/mnt/fac/CX900004_DS117/sbdd-project/stage6/images/provenance/d030_execution_patch_2026-10-10/`

The transferred archive reproduced the frozen epyc2 SHA-256 exactly and passed an archive read test.

After extraction, every entry in the internal `SHA256SUMS` manifest passed.

The extracted final `tree_builder.py` remained:

`18c77a5576fdc1dcb68dd5ec0d6248a5d890d5892c4a785c2e697e22e6db8615`

The canonical SIF was independently rehashed before qualification and remained:

`93ccedc2365dbed9231e999b06959e72f790b2971178d028edda8faff8dc6196`

---

## 7. Deterministic qualification

The derived execution layer was not granted authority merely because it compiled.

A deterministic qualification harness was developed against the frozen SIF plus bind-mounted derived `tree_builder.py`.

The deterministic tests were:

```text
Test A:
worker execution error -> coordinator planner_error

Test B:
legitimate successful zero-precursor result
-> native invalid-CTA behavior
-> NOT planner_error

Test C:
local exhaustion bookkeeping predicate
```

The SIF, derived source, and harness were staged from FAC to node-local `/tmp` and hash-verified before execution. Results and logs were copied back to FAC inside the Slurm job.

---

## 8. Test-B fixture qualification

Two qualification-development jobs failed because the initial Test-B fixture omitted native pre-result state.

### Job 2208255

- Slurm result: FAILED, ExitCode 1:0.
- Test A passed.
- Test B reached the normal-result path but failed with `KeyError: 'CC'` because the fixture had not reproduced the target `Chemical` created by `build_tree()` before `coordinate()`.
- This was a fixture failure, not a derived-ASKCOS failure.

### Job 2208287

- Slurm result: FAILED, ExitCode 1:0.
- Test A passed again.
- Test B advanced farther but failed with `KeyError: 7` because the fixture had not reproduced the `ChemicalTemplateApplication` created by native `select_leaf()` before worker dispatch.
- This was also a fixture failure.

Further fixture changes were stopped until the native source was traced completely.

Source review established:

```text
ChemicalTemplateApplication.__init__:
    waiting = True
    valid = True

build_tree():
    creates the target Chemical before select_leaf()

select_leaf():
    creates the CTA before dispatch

local expand():
    status = WAITING
    pending += 1

normal result processing:
    pending -= 1
    status = DONE
    CTA.waiting = False

zero-precursor result:
    CTA.valid = False
```

The final Test-B fixture therefore reproduced exactly the state encountered by a real returned local-worker result rather than trying to recreate `build_tree()` from inside `coordinate()`.

---

## 9. Authoritative deterministic qualification run

Final source-backed harness SHA-256:

`7d8420c3647ed5f0248214471eeeb10d968dd75aea69981ff6071f52a4cfcdcc`

Final qualification sbatch SHA-256:

`19d5f7d50f26098fe8641d1b7e77ea430f444113c32111fb21e8391a10b5c622`

Authoritative successful Slurm job:

`2209595`

Result:

```text
State:     COMPLETED
ExitCode:  0:0
Elapsed:   00:00:12
```

Preserved exit code: `0`.

Executed frozen inputs:

```text
SIF:
93ccedc2365dbed9231e999b06959e72f790b2971178d028edda8faff8dc6196

derived tree_builder.py:
18c77a5576fdc1dcb68dd5ec0d6248a5d890d5892c4a785c2e697e22e6db8615

qualification harness:
7d8420c3647ed5f0248214471eeeb10d968dd75aea69981ff6071f52a4cfcdcc
```

Observed markers:

```text
TEST_A_COORDINATOR_ERROR=PASS
TEST_B_ZERO_PRECURSOR=PASS
TEST_C_EXHAUSTION_BOOKKEEPING=PASS
D030_DETERMINISTIC_INSTRUMENTATION_TESTS=PASS
QUALIFICATION_ASSERTIONS=PASS
```

---

## 10. Qualified deterministic behaviors

### Test A — coordinator execution-error propagation

**Status:** QUALIFIED

A structured worker-error envelope was consumed by the patched coordinator. The worker failure remained execution-error evidence and produced `termination_reason = planner_error`; it did not masquerade as a legitimate zero-precursor result.

### Test B — legitimate zero-precursor distinction

**Status:** QUALIFIED

The final fixture reproduced the source-confirmed returned-worker state.

After `coordinate()` consumed a successful zero-precursor result:

```text
pending:       1 -> 0
status:        WAITING -> DONE
CTA.waiting:   True -> False
CTA.valid:     True -> False
execution_error: None
termination_reason: not planner_error
```

The fixture subsequently reached `exhausted` because `select_leaf()` was deliberately stubbed to return no further pathway.

That establishes reachability of the patched exhaustion branch under controlled reselection. It does not establish native MCTS selector exhaustion.

### Test C — local exhaustion bookkeeping

**Status:** QUALIFIED

The deterministic bookkeeping test established:

```text
no active pathway + pending = 0
    -> exhaustion eligible

no active pathway + pending > 0
    -> NOT exhaustion eligible

active pathway + pending = 0
    -> NOT exhaustion eligible
```

This qualifies the repaired local outstanding-work predicate. It does not independently qualify native selector exhaustion.

---

## 11. Successful-run evidence

Persistent successful-run directory:

`/mnt/fac/CX900004_DS117/sbdd-project/stage6/images/provenance/d030_execution_patch_2026-10-10/qualification/runs/d030_qual_2209595/`

Evidence SHA-256:

```text
qualification.log
46cf12e03d601ad1e76af3dc95a9bbfe938adebb98f914f70e6d6f21e94fd4b2

input_hashes.txt
018a8a2f0c44392ce734a9f41697e69e324e219d43967999e089ef1e64fff11f

exit_code.txt
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa
```

The qualification-status record was updated append-only after the successful run.

Updated `QUALIFICATION_STATUS.md` SHA-256:

`e1891feb98c363bd7592f937d71c6f7d57fd9430a7bf6ea64976dd3e21ec1895`

The original transferred bundle manifest was not silently regenerated.

---

## 12. Test D — natural `time_limit` behavior

**Status:** DESIGNED / SOURCE-REVIEWED / NOT IMPLEMENTED / NOT RUN

The next qualification item is natural expiration of the existing ASKCOS `expansion_time` budget.

Source inspection established that `coordinate()` measures elapsed wall time, refreshes it inside the coordination loop, and records `time_limit` when the loop ends naturally without another explicit termination reason.

The intended deterministic Test-D fixture was designed to use a controlled clock so that:

```text
initial elapsed = 0
    ->
coordinate loop executes at least one iteration
    ->
active pathway remains unresolved
    ->
outstanding work remains pending
    ->
no worker result arrives
    ->
no planner_error
    ->
no return_first
    ->
not exhausted
    ->
clock advances beyond expansion_time
    ->
while condition becomes false naturally
    ->
termination_reason = time_limit
```

The source review also established that `tree_builder.py` uses module-level `import time` and that a new `Chemical` has `price = -1`, allowing the deterministic fixture to prevent the first-path/`return_first` branch without changing scientific behavior.

The proposed Test D was not added to the harness. No Test-D Slurm job was submitted. No Test-D result exists.

---

## 13. D030 interpretation of `time_limit`

The purpose of Test D is to qualify the execution signal used to distinguish search-budget expiration from completed search.

The intended semantic boundary is:

```text
search remains unresolved
+
configured expansion_time expires
    ->
termination_reason = time_limit
    ->
D030 search state = search_incomplete
```

`time_limit` is distinct from `exhausted`, `planner_error`, and `return_first`.

A `time_limit` result is indeterminate and must not be converted into `no_route_complete`.

Test D remains required before this execution signal receives qualification authority.

---

## 14. Stage-6 pause

Stage 6 was intentionally paused on **2026-10-16** to begin the ADMET workstream.

At the pause point:

```text
Tests A-C:
QUALIFIED

authoritative qualification job:
2209595

Test D:
source-reviewed and designed
NOT implemented
NOT run

ordinary real original-ASKCOS local retrosynthesis smoke execution:
NOT yet qualified

Stage-6 production authority for the derived execution layer:
NOT granted
```

No Stage-6 result for the production molecular population is inferred from the deterministic instrumentation qualification.

---

## 15. Infrastructure state at pause

Current Stage-6/D030 work is on CoreHPC.

Persistent authority:

`/mnt/fac/CX900004_DS117/sbdd-project/stage6/`

Node-local `/tmp` remains transient execution space only.

epyc2 entered a planned brown-out period. During the brown-out, new Stage-6 work should remain on CoreHPC/FAC. The brown-out is not permanent retirement of epyc2.

The necessary active D030 qualification artifacts had already been transferred and verified on FAC before the pause.

---

## 16. Session close

**Status:** CLOSED FOR HANDOFF TO ADMET

Session 015 established and qualified:

```text
minimal local original-ASKCOS execution surface
derived execution-instrumentation boundary
local exhaustion bookkeeping repair
worker-error preservation
explicit termination provenance
local-worker template-prioritizer repair
complete source-delta provenance
epyc2 -> CoreHPC/FAC artifact transfer
FAC archive/internal-manifest verification
source-backed Test-B fixture
Test A qualification
Test B qualification
Test C qualification
authoritative deterministic run 2209595
```

Session 015 does not establish:

```text
Test-D natural time_limit qualification
native MCTS selector exhaustion
ordinary real retrosynthesis smoke execution
production resource envelope
production ASKCOS reliability
route existence for any production molecule
absence of a route for any production molecule
no_route_complete for any production molecule
Stage-6 production authority for the derived execution layer
```

---

## 17. Stage-6 resume point

When Stage 6 resumes, do not reopen deterministic Tests A-C unless their frozen revisit conditions are triggered.

Resume at:

> **Test D — natural `time_limit` behavior**

After Test D, continue the remaining execution qualification required before production authority, including ordinary real original-ASKCOS local retrosynthesis smoke execution.

The frozen scientific planner behavior remains unchanged.

---

## 18. Next session

Session 016 begins the ADMET stage/workstream.

The Stage-6/D030 thread remains paused at Test D and should be resumed from the CoreHPC/FAC artifacts rather than reconstructed from epyc2 or rerun from earlier qualification steps.
