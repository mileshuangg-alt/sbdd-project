# Session 014 — Stage 6 Planner Identity and ASKCOS Qualification
**Date:** 2026-09-30

**Closed:** 2026-10-09

**Status:** CLOSED

## Session objective

Continue Stage 6 — Synthetic Feasibility from the frozen shared molecular universe established in Session 013.

The immediate objective is to resolve the planner-specific identity problem before either retrosynthesis planner is allowed to operate on the frozen Stage-6 molecular universe.

The session therefore addresses:

1. the exact identity contract shared by AiZynthFinder and ASKCOS;
2. compatibility of candidate normalization strategies with the pinned AiZynthFinder runtime;
3. explicit treatment of source spellings that cannot be represented by the primary planner identity layer;
4. preservation of D026 as the sole molecular-identity authority;
5. construction of a frozen fallback architecture for planner-specific representation failures;
6. identification and qualification of the actual ASKCOS witness implementation;
7. deployment of that witness as an immutable CoreHPC execution artifact without changing its native molecular-representation behavior.

No Stage-6 retrosynthesis outcome is presumed from identity or container qualification.

The session does not authorize a representation result to stand in for stock membership, route existence, search completion, or synthesizability.

---

## Starting state

At Session 014 start:

- Stage 5 is complete and frozen;
- Stage 6 is the active baseline stage;
- the Stage-6 framework and claim semantics were established in Session 013;
- AiZynthFinder is the primary retrosynthesis planner;
- ASKCOS is the independent secondary witness;
- the frozen shared molecular universe contains exactly **24,238,632 D026/D027 identity records**;
- D026-generated full 27-character InChIKeys are the authoritative molecular identities;
- downstream structure-consuming stages continue to use the original frozen SMILES;
- the first-party ZINC source, Candidate-B filter, D026 identity transformation, Q1/Q2 quarantine, and D027 discrepancy adjudication are frozen;
- planner-specific stock construction and complete cross-planner identity proof remain unresolved;
- no Stage-6 planner execution against molecules 0, 3, or 18 is authorized merely by the completed identity-stock work.

The session begins at the planner-specific identity boundary left open by Session 013.

---

## 1. D028 — shared planner-stock identity contract

D028 was approved and frozen with two amendments.

The full D026-generated InChIKey remains the authoritative normalized molecular identity.

AiZynthFinder receives the full frozen D026 InChIKeys directly. They are not regenerated from SMILES.

ASKCOS receives planner-specific molecular representations derived from the original frozen source SMILES while retaining the authoritative source D026 identity.

No ASKCOS-side representation is permitted to replace, regenerate, or mutate the D026 identity authority.

The original D028 ASKCOS representation contract requires exact-runtime canonicalization of the original frozen single-component SMILES without:

```text
salt stripping
fragment selection
neutralization
tautomer normalization
stereochemistry removal
other identity-changing standardization
```

Every ASKCOS representation retains its source D026 identity.

Parser failures, representation losses, duplicate identities, and canonical-SMILES collisions must be measured explicitly.

### 1.1 Collision amendment

D028 adopted the existing D027 exclude-and-log precedent.

If the ASKCOS representation of one frozen D026 key collides with the representation of another distinct frozen D026 key:

```text
ambiguous key
    -> excluded from planner stock
    -> logged
    -> retained in frozen molecular universe
```

No new adjudication mechanism is introduced.

### 1.2 Equality-proof amendment

Complete cross-representation equality is required across all **representable** keys rather than absolutely every frozen D026 key.

A frozen D026 key that ASKCOS cannot encode is:

```text
logged as a representation failure
+
exempted from the equality proof
```

The authorized claim is therefore:

> **set equality across all representable keys**

rather than absolute equality across every frozen key.

**Decision changed:** D028 established the full D026 InChIKey as the sole cross-planner identity authority while allowing planner-specific representations to remain explicit, measured derivatives of the frozen source structures.

---

## 2. D029 — Candidate-B compatibility evaluation

The next question was whether Candidate B could serve as the sole planner-stock identity-normalization step under the pinned AiZynthFinder-compatible runtime.

The qualified runtime was:

```text
AiZynthFinder: 4.4.1
RDKit: 2023.09.6
Python: 3.11.11
```

AiZynthFinder 4.4.1 declares an RDKit dependency of:

```text
^2023.9.1
>=2023.9.1,<2024
```

The D026/D029 RDKit `2023.09.6` pin therefore lies within the declared AiZynthFinder compatibility window.

### 2.1 Candidate-B full-population result

The exhaustive Candidate-B evaluation covered:

```text
241,148 conflicted D026 keys
558,907 conflicted source spellings
```

Final result:

```text
false merges:              9,975
false splits:            179,219
failed source spellings:     147
affected D026 keys:            77
overall pass:               false
```

Candidate B therefore failed as the sole identity-normalization step.

The frozen 20,000-key diagnostic sample had zero normalization failures and zero false merges.

That sample remains a separate diagnostic and does not soften or replace the exhaustive full-population result.

**Decision changed:** Candidate B is not authorized as the sole Stage-6 identity step.

---

## 3. D029 failure-log reconciliation

The Candidate-B failure log initially appeared inconsistent with the structured result because raw TSV physical-line counts produced values of:

```text
1,029 / 882
```

These values were investigated rather than treated as failure counts.

The apparent excess arose from serialization of fragmented diagnostic records across multiple physical lines.

Failure-record blocks were therefore delimited by lines whose first field matched a complete 27-character D026 InChIKey.

Continuation or fragment lines within a block were not treated as independent failure records.

Structured reconciliation against the final Candidate-B conflict-results JSON established:

```text
147 failed (D026 key, source SMILES) pairs in JSON
147 corresponding failure-record blocks in TSV
147 unique failure pairs in TSV
0 JSON-only/orphan pairs
0 TSV-only/orphan pairs
77 affected D026 keys
```

The authoritative failure population is therefore:

```text
147 failed source spellings
77 affected D026 keys
```

The raw TSV physical-line counts are serialization artifacts and must not be used as failure counts.

**Decision changed:** Candidate-B failure accounting is closed at 147 unique failed source spellings across 77 D026 keys.

---

## 4. Candidate-B failure characterization

All 147 failed source spellings were replayed against the exact Candidate-B pipeline under RDKit `2023.09.6`.

All:

```text
147 / 147
```

reproduced their first failure at:

```text
CanonicalTautomer
```

The descriptive overlapping chemistry characterization was:

```text
nitroso:      147
nitro:        140
N-O single:   144
nitrile:       34
azide:          4
azo:            4
```

These classifications are diagnostic only.

They do not create:

```text
chemical-class exclusions
failure-mode exceptions
routing exceptions
acceptance thresholds
identity overrides
```

The routing rule must remain independent of the chemistry or prevalence observed after the failures occurred.

---

## 5. RDKit 2026.03.6 diagnostic

The exact 147 Candidate-B-failing source spellings were subsequently re-parsed under RDKit `2026.03.6`.

Result:

```text
147 tested
147 parse successes
0 parse failures
```

This establishes **parse success only**.

It does not establish successful execution of the complete Candidate-B normalization pipeline under RDKit `2026.03.6`.

The result supports interpreting the observed failures as a version artifact of the pinned identity layer rather than evidence of broken chemistry or intrinsically unparseable source spellings.

The D026/AiZynthFinder identity layer is **not** migrated to RDKit `2026.03.6`.

Doing so would move outside AiZynthFinder 4.4.1's declared RDKit compatibility window and reopen the completed D029 compatibility measurements.

---

## 6. D030 — ASKCOS standby routing for Candidate-B identity failures

D030 was developed, reviewed, approved, and frozen during Session 014.

D030 establishes a fallback identity-coverage architecture for frozen source spellings that fail the pinned Candidate-B identity layer.

D030 is not a new molecular-identity authority.

The D026 full 27-character InChIKey remains authoritative.

The frozen source stock remains untouched.

### 6.1 Representation mode — KEEP-ALL-FORMS

The quarantine unit is the:

```text
individual frozen source spelling
```

Each frozen source spelling remains attached to its authoritative D026 key.

A Candidate-B normalization failure quarantines that spelling only.

No representative spelling is selected, substituted, or promoted in its place.

The frozen molecular universe remains unchanged.

### 6.2 ASKCOS routing set

The ASKCOS routing set is exactly:

> **the frozen source spellings that failed AiZynth identity normalization under the pinned RDKit 2023.09.6 identity layer**

The routing rule is outcome-blind.

It does not depend on:

```text
observed failure prevalence
chemistry class
failure mechanism
source status
availability
apparent relevance
downstream planner outcome
```

No numerical failure tolerance is introduced.

### 6.3 ASKCOS status vocabulary

For each routed source spelling, `askcos_status` has exactly one of:

```text
not_attempted
attempted_failed
errored
represented
```

Mappings:

```text
not_attempted
    -> planner_unrepresented

attempted_failed
    -> planner_unrepresented

errored
    -> planner_error

represented
    + no AiZynth identity
    -> witness_only = true
    -> ASKCOS supplies the spelling's planner coverage/outcome
```

`planner_unrepresented` is distinct from `not_in_stock`.

A representation failure cannot be interpreted as a stock result.

An infrastructure or execution error cannot be converted into a representation failure.

### 6.4 `witness_only`

`witness_only` applies only when:

```text
ASKCOS represented the spelling
+
no AiZynth identity exists for that spelling
```

It is a spelling-level state.

ASKCOS then supplies planner coverage and outcome for that spelling.

A key-level witness designation is derived from spelling-level states and is never independently stored.

### 6.5 Stage-6 planner-outcome taxonomy

Every planner result lands in exactly one of:

```text
planner_unrepresented
in_stock
no_route_complete
search_incomplete
planner_error
```

Only:

```text
no_route_complete
```

constitutes a genuine synthesizability negative within the frozen Stage-6 evidence model.

`search_incomplete` is indeterminate.

`planner_error` is indeterminate.

Neither may be pooled with `no_route_complete`.

A spelling that has reached `represented` does not return to `planner_unrepresented`.

### 6.6 Complete-loss and partial-loss keys

The 77 affected D026 keys comprise:

```text
44 complete-loss keys
33 partial-loss keys
```

Failed source spellings:

```text
92 on complete-loss keys
55 on partial-loss keys
147 total
```

For complete-loss keys, no AiZynth identity coverage exists for any affected spelling.

If ASKCOS represents those spellings, ASKCOS supplies their planner coverage.

For partial-loss keys, surviving AiZynth spellings remain on the primary lane while failed spellings may independently receive ASKCOS witness coverage.

A partial-loss key does not receive a blanket witness-only designation merely because one source spelling failed.

### 6.7 Key-level aggregation

Stage-6 outcomes remain spelling-level evidence.

Key-level state is derived deterministically.

A key is stock-covered if at least one represented spelling has:

```text
in_stock
```

A genuine synthesizability negative requires:

```text
at least one represented spelling
+
every represented spelling = no_route_complete
+
no represented spelling = in_stock
+
no represented spelling = search_incomplete
+
no represented spelling = planner_error
```

A key is globally `planner_unrepresented` only when no source spelling has planner representation.

Mixed represented outcomes remain correspondingly mixed or indeterminate and must not be collapsed into a stronger negative.

**Decision changed:** D030 provides a deterministic fallback architecture without altering D026 identity authority or converting planner limitations into chemistry claims.

---

## 7. Original ASKCOS selected as witness implementation

The deployment investigation initially considered ASKCOSv2.

The official ASKCOSv2 source was identified as:

```text
gitlab mlpds_mit/askcosv2
```

with an RDKit `2026.3.6` pin.

However, the deployment direction was subsequently settled on the **original ASKCOS** prebuilt distribution rather than source-building ASKCOSv2.

The selected image repository is:

```text
askcos/askcos
```

Docker Hub identifies this as the old official ASKCOS image repository.

The exact artifact pulled on `epyc2` was:

```text
askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0
```

Docker image ID:

```text
sha256:551d90c9bf090e992fb971daf95e0cd5f38baf75d4938a4188d25e8de4383f91
```

Observed image properties:

```text
created:       2021-02-22
architecture:  linux/amd64
Python:        3.5.9
RDKit:         2019.03.4
Docker size:   3.45 GB
```

The immutable repository digest observed after the pull exactly matched the digest later recorded in the D030 amendment.

---

## 8. Original-ASKCOS representation boundary

Inspection of the frozen original-ASKCOS source established that its native RDKit runtime is part of the actual planner representation path.

The tree-builder API entry performs:

```python
mol = Chem.MolFromSmiles(orig_smiles)

if not mol:
    resp['error'] = 'Cannot parse smiles with rdkit'
    return JsonResponse(resp, status=400)

smiles = Chem.MolToSmiles(mol)
```

The source also contains RDKit parsing/canonicalization throughout the buyables/pricer and retrosynthetic paths.

The pricer performs:

```python
if not alreadyCanonical:
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return 0.
    smiles = Chem.MolToSmiles(
        mol,
        isomericSmiles=isomericSmiles
    )
```

Downstream `alreadyCanonical=True` calls were traced to internal planner representations rather than establishing an opaque external identity boundary.

Therefore the actual original-ASKCOS architecture is:

```text
input source spelling
        ↓
native ASKCOS runtime
        ↓
RDKit 2019.03.4 parsing/canonicalization
        ↓
planner / stock machinery
```

An external RDKit `2026.03.6` representation cannot substitute for successful representation by the actual planner runtime.

---

## 9. D030 native-runtime amendment

The representation-boundary finding exposed a mismatch between the earlier ASKCOSv2-derived RDKit assumption and the selected original-ASKCOS implementation.

Rather than modifying the old image to use a modern RDKit version, D030 was amended.

The amendment was approved and frozen on:

```text
2026-10-09
```

### 9.1 Frozen witness artifact

```text
Image:
askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0

Image ID:
sha256:551d90c9bf090e992fb971daf95e0cd5f38baf75d4938a4188d25e8de4383f91

Python:
3.5.9

RDKit:
2019.03.4

Architecture:
linux/amd64
```

### 9.2 Frozen representation operation

A routed source spelling is represented if the frozen ASKCOS runtime successfully performs:

```python
mol = Chem.MolFromSmiles(source_spelling)
canonical_smiles = Chem.MolToSmiles(mol)
```

No external preprocessing or canonicalization may substitute.

This includes no:

```text
salt stripping
fragment selection
neutralization
tautomer normalization
stereochemistry removal
newer-RDKit canonicalization
```

### 9.3 Default `MolToSmiles` and stereochemical qualification

The planner API entry uses:

```python
Chem.MolToSmiles(mol)
```

with no explicit `isomericSmiles` argument.

The RDKit `2019.03.4` runtime signature showed that `isomericSmiles` defaults to `True`.

This was checked empirically in the same digest-pinned Docker image using:

```text
Input:
C[C@H](O)F
```

Result:

```text
default:
C[C@H](O)F

explicit isomericSmiles=True:
C[C@H](O)F

explicit isomericSmiles=False:
CC(O)F
```

For this frozen runtime and probe, the literal default operation preserved stereochemistry and agreed with explicit `isomericSmiles=True`.

The representation pilot therefore uses the literal planner operation rather than replacing it with an explicitly parameterized variant.

The stereochemical probe is recorded explicitly in the D030 amendment.

It was an interactive qualification check and is not one of the four hashed representation-pilot artifacts.

### 9.4 Amendment scope

The amendment changes only the ASKCOS witness representation implementation.

It does not change:

```text
D026 identity authority
frozen routing population
KEEP-ALL-FORMS
ASKCOS status vocabulary
witness_only semantics
planner_unrepresented semantics
five-class Stage-6 taxonomy
key-level aggregation
outcome-blind routing
flag authority
```

**Decision changed:** representation capability is measured using the molecular-representation machinery actually exercised by the frozen planner runtime.

---

## 10. Native ASKCOS representation pilot

The authoritative D029 conflict-results JSON was used to reconstruct the frozen D030 routing population.

The structured status counts were:

```text
failure: 147
success: 558,760
```

The frozen pilot population was verified before execution as:

```text
147 failure records
147 unique (D026 key, source spelling) pairs
77 distinct D026 keys
```

The 147 source spellings were passed **verbatim** into the frozen ASKCOS Docker image.

No external molecular transformation was performed.

The exact operation was:

```python
mol = Chem.MolFromSmiles(source_spelling)

if mol is not None:
    canonical_smiles = Chem.MolToSmiles(mol)
```

Result:

```text
input records:       147
distinct D026 keys:   77
RDKit:                2019.03.4
represented:          147
attempted_failed:       0
total:                147
```

Therefore:

```text
147 / 147 represented
0 / 147 attempted_failed
representation rate: 100%
```

All 147 Candidate-B-failing source spellings are therefore representable by the frozen native original-ASKCOS runtime.

This establishes **representation only**.

It does not establish:

```text
stock membership
route existence
synthesizability
search completeness
planner success
Stage-6 disposition
```

### 10.1 Preserved pilot artifacts

Persistent location:

```text
/nfs/home/mhuang/stage6_planner_stock_production_2026-10-01/
d030_askcos_native_representation_pilot_2026-10-09/
```

SHA-256:

```text
624e7ebf1b253794b2c0329acc21e7b328ecadc90c2ec286c8dce62a700abaf2  d030_askcos_native_representation_input.json

6aa5e5620a17b5645139b308a0aa9e5eae47110d3f6a132f628190a5dc5024a1  results.json

4993bd6a3d228a88debef1029191dd0acd208e5e838221322628ff2859bea22f  results.tsv

a232312dc1d97bb5cc3c5823893ac7eaf5072ed3b7550d77ae64224c4299e6dd  summary.json
```

All four passed:

```text
sha256sum -c
```

---

## 11. epyc2 Docker-build investigation

Before the prebuilt original-ASKCOS route was settled, an ASKCOSv2 application-image build was attempted on `epyc2`.

The build repeatedly stalled.

Observed host state included very high system load, at times exceeding:

```text
load average > 400
```

However, subsequent diagnosis showed that cluster CPU load alone did not adequately explain the build behavior.

Docker environment:

```text
Docker Engine:   24.0.7
architecture:    linux/amd64
storage driver:  fuse-overlayfs
Docker root:     /local2/docker
```

BuildKit operations stalled.

Legacy Docker builds progressed farther but repeatedly stalled during Micromamba environment installation/linking.

A representative stuck build container was executing:

```text
micromamba install -y python=3.13.15 pip=26.2.1 -c conda-forge
```

The behavior was consistent with the metadata-heavy container filesystem path being problematic under the host's `fuse-overlayfs` configuration.

The source-build route was abandoned rather than continuing to tune an implementation that was no longer required.

Selection of the prebuilt original-ASKCOS image removed the need to source-build ASKCOSv2.

---

## 12. CoreHPC deployment investigation

CoreHPC was selected as the production execution environment for the ASKCOS witness.

Initial access was temporarily unavailable during CoreHPC maintenance.

After service returned, the environment was characterized.

Available tooling:

```text
Apptainer
Singularity
Podman
srun
sbatch
Buildah
```

Observed versions included:

```text
Apptainer: 1.5.4-1.el9
Podman:    5.8.2
architecture: linux/amd64
```

### 12.1 Slurm access

The account association was:

```text
Account: hpc_core
QOS:
cmnt
cmnt_short
cpu
gpu
hpc_core
```

The `community_short` partition rejected the account's default QOS.

The `cpu` partition permits `hpc_core`.

Interactive CPU allocations were therefore obtained using the CPU partition.

---

## 13. CoreHPC network boundary

Compute-node outbound network access was tested directly.

Requests to:

```text
registry.gitlab.com
pypi.org
conda.anaconda.org
deb.debian.org
```

returned Squid:

```text
403 Forbidden
ERR_ACCESS_DENIED
```

Therefore compute-node online registry/package access is unavailable.

This rules out:

```text
online Docker/Podman pulls on compute nodes
online Apptainer registry pulls on compute nodes
online package installation during compute jobs
online source builds requiring external dependencies
```

The CoreHPC login node was tested separately against Docker Hub:

```text
https://registry-1.docker.io/v2/
```

and returned:

```text
HTTP/2 401
```

This is the expected Docker Registry authentication response and establishes registry reachability from the login node.

The final conversion route therefore uses the networked CoreHPC login node to acquire the exact digest-pinned Docker artifact and convert it into an immutable SIF.

---

## 14. CoreHPC storage architecture

Official CoreHPC scratch documentation was incorporated into the Stage-6 deployment plan.

Two scratch classes are available:

```text
global scratch:
    /mnt/scratch/*

node-local scratch:
    /tmp
```

Scratch is for hot data only.

Nothing canonical may depend on either scratch class.

Node-local `/tmp` is wiped at job termination.

Global scratch is purged at least quarterly and may be cleaned at any time.

Approximate node-local capacities are:

```text
core dense CPU:  ~2 TB NVMe
small GPU:       ~6 TB
large GPU:       6–12 TB
pod:             ~12 TB
community CPU:   ~1 TB SAS
```

FAC capacity storage is persistent and backed up and is the canonical storage authority for Stage-6 deployment artifacts.

### 14.1 FAC allocation

Accessible FAC allocations were inspected.

The appropriate user-facing persistent allocation was identified as:

```text
/mnt/fac/CX900004_DS117
```

Observed capacity:

```text
466G total
68G used
399G available
15% used
```

The allocation already contained user-owned project directories and an existing SIF artifact.

The canonical Stage-6 root was established as:

```text
/mnt/fac/CX900004_DS117/sbdd-project/stage6
```

with logical organization:

```text
stage6/
├── images/
│   └── provenance/
├── frozen_inputs/
├── configs/
├── runs/
└── final/
```

### 14.2 Frozen execution architecture

Canonical copies of:

```text
SIF image
frozen Stage-6 input
final results
```

live on FAC.

The production Slurm script must:

```text
1. stage SIF from FAC -> node-local /tmp
2. stage frozen input from FAC -> node-local /tmp
3. run ASKCOS against node-local scratch
4. copy final results/logs back to FAC
5. only then exit
```

The copy-back step must be inside the job script because node-local scratch is wiped at job termination.

No data-transfer node is required.

**Decision changed:** FAC is the Stage-6 persistence authority; node-local `/tmp` is the preferred hot workspace for ASKCOS batch execution.

---

## 15. Docker-to-SIF conversion

The exact frozen original-ASKCOS Docker digest was converted directly with Apptainer.

Source:

```text
docker://askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0
```

The conversion used CoreHPC login-node registry access.

Apptainer temporary/cache work used local `/tmp`.

The completed immutable SIF was written to persistent FAC storage.

Canonical SIF:

```text
/mnt/fac/CX900004_DS117/sbdd-project/stage6/images/
askcos_d030_85ae3c1b.sif
```

Observed size:

```text
~1.7 GB
```

SIF SHA-256:

```text
93ccedc2365dbed9231e999b06959e72f790b2971178d028edda8faff8dc6196
```

Apptainer metadata records:

```text
build architecture:
amd64

Apptainer:
1.5.4-1.el9

bootstrap:
docker

source:
askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0

OCI base digest:
sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0

OCI base name:
docker.io/askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0
```

The conversion therefore records the exact frozen Docker artifact as its source.

---

## 16. SIF runtime qualification

The SIF was not accepted solely because conversion completed.

Its frozen runtime was checked directly.

Inside the SIF:

```text
Python:
3.5.9

RDKit:
2019.03.4
```

PASS.

The same stereochemical probe was repeated inside the SIF:

```text
Input:
C[C@H](O)F

default:
C[C@H](O)F

explicit isomericSmiles=True:
C[C@H](O)F

explicit isomericSmiles=False:
CC(O)F
```

PASS.

The Docker-to-SIF conversion therefore preserved the runtime and the specific default `MolToSmiles` stereochemical behavior used by the frozen D030 representation boundary.

---

## 17. Frozen input transfer to CoreHPC

The exact Docker-pilot input was transferred to CoreHPC.

The correct transfer topology is:

```text
epyc2
    ↓
SSH ProxyJump through CoreHPC bastion
    ↓
CoreHPC login node
    ↓
FAC
```

The bastion is transit only.

A direct initial `scp` to the bastion succeeded but unnecessarily left an intermediate artifact there.

That workflow is not to be repeated.

The correct command pattern is:

```bash
scp -o ProxyJump=mhuang8@chpc-ucsf-bastion-vm1.corehpc.ucsf.edu \
  <SOURCE> \
  mhuang8@chpc-ucsf-login-vm1.corehpc.ucsf.edu:<DESTINATION>
```

The verified frozen input was preserved at:

```text
/mnt/fac/CX900004_DS117/sbdd-project/stage6/frozen_inputs/
d030_askcos_native_representation_input.json
```

SHA-256:

```text
624e7ebf1b253794b2c0329acc21e7b328ecadc90c2ec286c8dce62a700abaf2
```

This exactly matches the Docker-pilot input.

---

## 18. Compute-node staging qualification

A CoreHPC interactive CPU allocation was obtained.

Slurm job:

```text
2181418
```

Compute node:

```text
gcpu2-30
```

The canonical SIF and frozen representation input were staged from FAC to:

```text
/tmp/mhuang8-stage6-2181418/
```

The staged SIF size was approximately:

```text
1.7 GB
```

and the frozen JSON input approximately:

```text
17 KB
```

The frozen input hash was verified after staging.

This demonstrated the intended production storage path:

```text
FAC
    ↓
node-local /tmp
    ↓
execution
```

without depending on global scratch.

---

## 19. SIF native-representation pilot

The same 147-spelling native representation measurement was executed inside the staged SIF.

The operation remained:

```python
mol = Chem.MolFromSmiles(source_spelling)
canonical_smiles = Chem.MolToSmiles(mol)
```

Result:

```text
input records:       147
distinct D026 keys:   77
RDKit:                2019.03.4
represented:          147
attempted_failed:       0
total:                147
```

PASS.

The SIF therefore reproduced the Docker pilot's aggregate result exactly:

```text
147 represented
0 attempted_failed
```

---

## 20. Docker-to-SIF pair-for-pair equivalence

Aggregate equality alone was not treated as sufficient.

The preserved Docker `results.json` was transferred to CoreHPC and verified against its frozen SHA-256:

```text
6aa5e5620a17b5645139b308a0aa9e5eae47110d3f6a132f628190a5dc5024a1
```

Docker and SIF results were then compared for every unique:

```text
(D026 key, source spelling)
```

The compared fields were:

```text
parse_result
askcos_native_canonical_smiles
askcos_status
representation_outcome
rdkit_version
```

Result:

```text
Docker records:       147
SIF records:          147
shared unique pairs:  147
field mismatches:       0
```

PASS.

Therefore:

> **Docker-to-SIF conversion preserved the frozen D030 native molecular-representation behavior exactly for all 147 routed source spellings.**

This is stronger than merely observing 147 successful representations in both environments.

---

## 21. SIF qualification evidence

Persistent qualification directory:

```text
/mnt/fac/CX900004_DS117/sbdd-project/stage6/images/provenance/
sif_qualification_2026-10-09/
```

Observed contents:

```text
SHA256SUMS
docker_results.json
provenance.txt
provenance.txt.sha256
results.json
results.tsv
summary.json
```

Known SHA-256 values:

```text
canonical SIF:
93ccedc2365dbed9231e999b06959e72f790b2971178d028edda8faff8dc6196

Docker qualification results.json:
6aa5e5620a17b5645139b308a0aa9e5eae47110d3f6a132f628190a5dc5024a1

SIF qualification results.json:
24e42556d60eaa4b6f55d27256f9ade4e2bbb21d36921ef4694e9b60f009424a

SIF qualification results.tsv:
c1fa958baea99ed120a9928eb667a870c813cd41039b52503c684e30d6a1869b

SIF qualification summary.json:
9a5dca21124c7fa0e738f5eebd6edcd7a2bd37ae81e95c5838c9db94ce682239
```

`provenance.txt` records:

```text
source Docker repository/digest
Docker image ID
Python/RDKit runtime
architecture
Apptainer version
SIF SHA-256
OCI source metadata
stereochemical probe
frozen input SHA-256
147/0 SIF result
Docker-to-SIF pair equivalence
claim boundary
```

The provenance file was itself hashed and verified with `sha256sum -c`.

---

## 22. Qualified Stage-6 ASKCOS execution artifact

At Session 014 close, the qualified CoreHPC ASKCOS artifact is:

```text
/mnt/fac/CX900004_DS117/sbdd-project/stage6/images/
askcos_d030_85ae3c1b.sif
```

SHA-256:

```text
93ccedc2365dbed9231e999b06959e72f790b2971178d028edda8faff8dc6196
```

Source Docker artifact:

```text
askcos/askcos@sha256:85ae3c1bc0ccaec71b10d157d467763eda0ab604f96565978ddec93a059f03a0
```

Qualification summary:

```text
source digest provenance:       PASS
architecture:                   PASS
Python 3.5.9:                   PASS
RDKit 2019.03.4:                PASS
default MolToSmiles behavior:   PASS
stereochemical probe:           PASS
147/147 representation:         PASS
attempted_failed = 0:           PASS
Docker/SIF unique pairs:        147 / 147
Docker/SIF field mismatches:    0
FAC -> local /tmp staging:      PASS
```

The SIF is therefore qualified as the frozen CoreHPC execution artifact for subsequent D030 implementation.

---

## 23. Qualification claim boundary

The completed Docker and SIF work establishes:

> **preservation of the frozen D030 native molecular-representation behavior across the selected original-ASKCOS Docker runtime and its CoreHPC SIF conversion**

It does **not** establish:

```text
ASKCOS stock membership
route existence
absence of a route
synthesizability
search completeness
search-budget adequacy
planner runtime reliability
production resource requirements
production Stage-6 outcome frequencies
full D030 execution
```

Those are downstream planner-execution questions.

Representation qualification must not be promoted into a retrosynthesis result.

---

## 24. Final Session-014 Stage-6 state

At Session 014 close, the planner-specific identity problem and ASKCOS deployment artifact are resolved, but actual retrosynthesis planner execution remains open.

### 24.1 Frozen and qualified

The following are closed:

```text
D028 shared planner-stock identity contract

D029 Candidate-B exhaustive compatibility result

D029 147-pair / 77-key failure reconciliation

Candidate-B failure-stage characterization

RDKit 2026.03.6 diagnostic parse test

D030 KEEP-ALL-FORMS routing architecture

D030 four-state ASKCOS status model

D030 five-class Stage-6 outcome taxonomy

D030 key-level aggregation

original-ASKCOS witness selection

original-ASKCOS Docker digest

Python/RDKit runtime

native ASKCOS representation boundary

default MolToSmiles stereo behavior

147-spelling Docker representation pilot

CoreHPC FAC persistence architecture

FAC -> node-local /tmp execution pattern

Docker-to-SIF conversion

SIF runtime qualification

SIF stereo qualification

147-spelling SIF representation pilot

Docker-to-SIF pair-for-pair equivalence
```

### 24.2 Still open

The following remain unresolved:

```text
minimal original-ASKCOS planner execution surface

batch/non-web retrosynthesis entry point

required planner services/processes

model/data dependencies

Redis/MongoDB/RabbitMQ/Celery/web-stack requirements, if any

buyables/pricer stock-loading behavior

frozen ASKCOS search parameters

search budget and stopping conditions

completion versus incompletion signals

timeout/expansion-limit behavior

planner-error signals

route-result structures

production CPU/memory/runtime envelope

production sbatch implementation

actual Stage-6 planner execution
```

No open item may be inferred from the successful representation qualification.

---

## 25. Next implementation boundary

The next work is a **read-only inspection of the qualified original-ASKCOS implementation**.

Do not launch the full legacy web stack blindly.

The immediate question is:

> **What is the smallest supported original-ASKCOS execution surface that can take a target SMILES, perform retrosynthetic search against the required models/data and stock endpoint, and expose sufficient route and termination evidence to map execution into the frozen D030 Stage-6 outcome taxonomy?**

The inspection must identify:

```text
candidate batch/CLI entry points
tree-builder/MCTS interfaces
configuration dependencies
model/data dependencies
database/service dependencies
stock/pricer dependencies
search-completion signals
timeout/limit signals
execution-error signals
route/result structures
```

Only after that execution surface is understood should the production ASKCOS run script be designed.

---

## 26. Do-not-reopen list

Unless a frozen revisit condition is actually triggered, subsequent work must not redo or retune:

```text
D028 identity contract

D029 Candidate-B full-population compatibility result

D029 147-pair / 77-key reconciliation

D029 failure-stage characterization

RDKit 2026.03.6 diagnostic

D030 routing architecture

D030 native-runtime amendment

Docker native-representation pilot

frozen original-ASKCOS Docker identity

CoreHPC FAC storage architecture

Docker-to-SIF conversion

SIF runtime/stereochemical qualification

SIF 147-spelling representation pilot

Docker-to-SIF pair-for-pair equivalence
```

The selected ASKCOS witness image/runtime should be revisited only if:

```text
the frozen image changes
the image digest changes
the native representation path changes
or a different planner implementation is proposed
```

---

## 27. Session close

**Status:** CLOSED

Session 014 accomplished:

```text
D028 shared planner identity contract
+
exhaustive D029 Candidate-B compatibility evaluation
+
147-pair / 77-key failure reconciliation
+
failure-stage characterization
+
RDKit 2026.03.6 diagnostic
+
D030 KEEP-ALL-FORMS fallback architecture
+
frozen ASKCOS status and Stage-6 outcome semantics
+
original-ASKCOS witness selection
+
immutable Docker artifact qualification
+
native-runtime D030 amendment
+
147/147 native representation qualification
+
persistent hashed pilot evidence
+
CoreHPC FAC storage architecture
+
CoreHPC network-boundary characterization
+
digest-pinned Docker-to-SIF conversion
+
SIF runtime and stereo qualification
+
147/147 SIF representation qualification
+
zero-mismatch Docker-to-SIF pair equivalence
+
qualified CoreHPC ASKCOS execution artifact
```

The session does **not** claim:

```text
ASKCOS retrosynthesis has been executed

the ASKCOS planner configuration is fully frozen

the ASKCOS stock endpoint has been exercised

a route has been found or not found for any routed molecule

Stage-6 control validation has passed

molecules 0, 3, and 18 have been evaluated through Stage 6

representation success implies synthesizability

planner failure implies chemical unsynthesizability
```

Session 014 closes immediately before actual original-ASKCOS planner deployment.

The next work begins at the qualified SIF and proceeds by identifying the minimal retrosynthesis execution surface and the exact planner termination evidence needed to implement the already-frozen D030 outcome semantics.