# Session 017 — ADMET Split Construction: Duplicate-Tie Refinement, Similarity Freeze and Split-Input Builder

**Date:** Began after the 2026-11-11 Session 016 → Session 017 handoff (exact first active Session-017 date UNKNOWN); ongoing as of 2026-11-14  
**Status:** ONGOING — recovered history captured to 2026-11-14; not closed, finalized or advanced

## 1. Session objective and record provenance

Session 017 continues the ADMET pilot at the first unfinished implementation-plan item: construct and freeze the real 80/20 development/test split and five-fold development CV (Session 016 §10 resume point; governing plan `admet-pilot-gpt-handoff-1.md`).

Recovered governing Task-2 plan wording (quoted identically in both sources below):

> "Prepare both endpoint datasets with the approved filters, build the 80/20 development/test split and the 5-fold development CV with the approved alias grouping (decision 3), freeze them, and report: settled source-ID counts vs expectations, alias group counts recomputed on the pinned RDKit, any canonicalization failures or ambiguous fragments (held and reported, never guessed), and confirmation that the test side was never read."

Both sources say "Task 2" was clarified as implementation-plan bookkeeping, not a scientific or architectural namespace.

This log was created on 2026-11-14 as a recovered-history capture. Miles authorized it in chat: "I approve creating notes/Session_017.md as the first real bookkeeper write. Session 017 is ONGOING. This is recovered history capture, not session closure, advance, or permission to continue scientific work."

Sources and provenance labels used below:

- **[Export]**: GPT export `LigGate_Session_017_Record_So_Far.md` (Mac path `/Users/mileshuang/Downloads/`, 1061 lines, SHA-256 `9b1f372ff198fb31497c20a46d2280c3f728ecb1facaca43882f9beb2740866a`), export date 2026-11-14, supplied by Miles. The export calls itself historical context only and says it does not close or advance the session.
- **[Handoff]**: `liggate-session-017-handoff.md` (Mac path `/Users/mileshuang/Downloads/`, 442 lines, SHA-256 `e39cfa56833b5f3aa241070facc0c52c11c1919d08ed8b3272f112e621085d32`), titled "LigGate / ADMET Session 017 — Mid-Session Migration Handoff", transfer date 2026-11-14, status "MID-SESSION TRANSFER — NOT A CLOSE-OUT". Miles referred to "the original Session 017 mid-session migration handoff". The main conversation identified this file as that document by its title.
- **[gpu-dev1, user-pasted]**: command output that Miles ran on gpu-dev1 (observed host `n4pu04`) and pasted or reported in the original chat, as recorded by [Export] and/or [Handoff].
- **[Mac, user-reported]**: local Mac test results reported by Miles, as recorded by [Export] and/or [Handoff]. These are Mac mechanical smoke tests, not pinned-runtime qualification.
- **[Mac obs 2026-11-14]**: read-only local Mac observations made by the main Claude Code conversation on 2026-11-14. These are not remote-run evidence.

This log captures only what these sources contain. It does not recover history beyond them. The two source-file hashes above were supplied by the main conversation. The bookkeeper did not recompute them.

---

## 2. Entering state: Session 016 pre-amendment baseline

Source: `notes/Session_016.md` §2 (endpoint counts) and §3 (grouping) (committed record), restated in [Export] §3.1 and [Handoff] §8.

- pKa: 6,752 molecule-steps / 5,474 source-ID compounds
- clearance: 408 molecular identities
- combined endpoint-qualified identities: 5,882
- successfully grouped: 5,881
- grouping failures: 1
- distinct family keys: 5,446
- distinct scaffold keys: 893
- MaxTransformsReached tautomer witnesses: 5 of 5,881

Held identity: `clearance:CHEMBL5315124`, `fragment_ambiguity_equal_largest_heavy_atom_count`.

This is valid historical pre-amendment evidence. It is not rewritten by the Session-017 rerun in §8.

---

## 3. Recovered split formulation (carried forward, not reopened)

Source: [Export] §3.2, [Handoff] §1 and §6, both reconciling the Session-016 record.

- Production units are immutable `family_key` families, not diagnostic scaffold-plus-family transitive components.
- Required per-family fields: family identifier; `w_i` = exact number of molecular identities in family i; pKa count; clearance count; complete `S_ij` to every other family.
- Stage A: dev/test = 0.8/0.2, every family assigned exactly once. `epsilon = delta = 0.05` with lower-bound semantics, not a symmetric ±5-point rule:
  - molecular count: `N_s >= int[p_s (1 - epsilon) N]`
  - endpoint count: `C_{s,e} >= p_s (1 - delta) C_e`
- Stage B: five development folds, nominally 0.2 each. [Handoff] §6 says the same epsilon/delta lower-bound semantics apply to fold molecular counts and endpoint coverage. The historical synthetic 80/10/10 Stage-B probe settings are not production authority.
- Frozen leakage objective: `L_cross = sum_{i<j} w_i w_j S_ij 1[z_i != z_j]`. The native Gurobi formulation maximizes the equivalent within-partition weighted similarity.
- Not authorized: pair pruning, thresholding, sampling, coarsening, approximation, changed weighting, objective normalization or a replacement objective.
- [Handoff] §6 also carries forward these Session-016 points: leakage of any returned assignment must be recomputed independently; a time-limited incumbent is eligible only if it independently satisfies every frozen hard constraint; global optimality is not required; and no MIP-gap acceptance threshold is authorized.

---

## 4. Similarity-method reconciliation and molecular-similarity specification

### 4.1 Reconciliation

Source: [Export] §3.3. The available Session-016 record froze complete `S_ij` usage but did not preserve an exact real-structure → molecule similarity → family similarity mapping. [Handoff] §2.1 agrees.

[Export] says an assistant first proposed another alternatives pass and later suggested a grouping-only molecular representation as fingerprint input. The user corrected this: hard family grouping, the soft similarity objective and family-mean/size weighting had already been reasoned through, and a missing final freeze was not a reason to repeat the alternatives pass. [Export] found no later decision superseding the earlier prepared-source-SMILES recommendation. The grouping-only fingerprint-input proposal was withdrawn.

### 4.2 Reported approval

[Export] §3.4 reports this user wording:

> "Approve the proposed Task-2 similarity mapping, incorporating the earlier input contract explicitly: pKa unique_ID and clearance molecule_chembl_id, preserving the same prepared-source SMILES string across steps; Environment A with RDKit 2023.09.6; direct sanitized MolFromSmiles parsing, no family-key normalization or representative substitution. A parse failure halts rather than skipping an identity.
>
> Freeze Morgan radius 2, 2048 bits, chirality enabled, Tanimoto, and the complete family-mean S_ij mapping as proposed. State explicitly that w_i = |F_i| is what makes w_iw_jS_ij equal the sum of the between-family molecular-pair similarities.
>
> Carry all other qualified choices forward unchanged. clearance:CHEMBL5315124 remains held and unresolved. This approval freezes the similarity specification only; it does not authorize fingerprint computation, pair-matrix generation, or split execution."

[Handoff] §1A reports the same content as "explicitly approved by Miles in this chat" but does not quote it.

Specification as recorded in both sources:

- pKa identity `unique_ID`; clearance identity `molecule_chembl_id`
- the same prepared-source SMILES string is preserved across steps
- RDKit 2023.09.6 (pinned preparation/grouping runtime)
- direct sanitized `Chem.MolFromSmiles(prepared_source_smiles)`; no family-key normalization; no representative substitution; a parse failure halts
- Morgan radius 2, 2048 bits, chirality enabled; Tanimoto
- family mean: `S_ij = (1 / (|F_i||F_j|)) * sum_{a in F_i} sum_{b in F_j} s(a,b)`
- `w_i = |F_i|`, so `w_i w_j S_ij = sum_{a in F_i} sum_{b in F_j} s(a,b)`
- complete family-pair similarities are retained, with no thresholding, pruning, approximation, coarsening or representative substitution

Both sources state that this approval froze the specification only. It did not authorize or establish fingerprint computation, pair-matrix generation or split execution.

The approval is recorded here as history reported by these sources. No `notes/Decisions.md` entry was created and no D-number is assigned. [Export] says no D-number is recoverable.

---

## 5. CHEMBL5315124 and the equal-largest duplicate-tie refinement

### 5.1 Source record recovered

[gpu-dev1, user-pasted] per [Export] §3.5. [Export] does not name the host for this particular command.

```text
MATCH_COUNT: 1
molecule_chembl_id: CHEMBL5315124
smiles: C[C@H]1COc2c(N3CCN(C)CC3)c(F)cc3c(=O)c(C(=O)O)cn1c23.C[C@H]1COc2c(N3CCN(C)CC3)c(F)cc3c(=O)c(C(=O)O)cn1c23.O
```

Both sources describe this as two copies of the same large organic fragment plus water. The pre-amendment selector stopped on equal-largest heavy-atom ties, so Session 016 correctly held it under the old rule.

### 5.2 Reported approval

[Export] §3.6 reports this user wording after discussion: "yep approved lets move forward". [Handoff] §1B reports the refinement as "approved in this chat" without quoting wording.

Approved rule as recorded in both sources:

1. When fragments tie for maximum heavy-atom count, compare the tied fragments by canonical isomeric SMILES under RDKit 2023.09.6.
2. One distinct canonical representation means duplicate multiplicity, not molecular ambiguity. The existing downstream family-key computation continues on that structure.
3. Multiple distinct representations, or a parse or canonicalization failure, stay held. Nothing is guessed.
4. The refinement is grouping-only. The preserved prepared-source SMILES and the frozen similarity input are unchanged.
5. A successful resolution is not an ambiguity or problem flag. Audit provenance is kept under the label `duplicate_equal_largest_fragments_resolved`.

[Export] §4 lists as rejected: an arbitrary first/second-fragment tie break, and a one-record-only CHEMBL5315124 exception.

No `notes/Decisions.md` entry was created and no D-number is assigned. [Export] says none is recoverable.

---

## 6. Alias-grouping amendment and Mac test chronology

### 6.1 Pre-amendment source inspected

[Export] §3.7, [Handoff] §2.3. The user supplied `admet/scripts/alias_grouping.py`. It showed `AUTHORITATIVE_RDKIT_BEHAVIOR = "2023.09.6"` and the pre-amendment behavior:

```python
if len(largest) != 1:
    return FragmentSelection(None, None, largest_count, counts, FRAGMENT_AMBIGUITY)
```

The downstream family-key pipeline is unchanged: copy fragment → remove stereochemistry → RDKit Uncharger → tautomer canonicalization → canonical non-isomeric SMILES.

### 6.2 Tie refinement implemented

[Export] §3.8, [Handoff] §2.3. A targeted replacement modified `admet/scripts/alias_grouping.py`. It added `resolution_note` and:

```python
DUPLICATE_EQUAL_LARGEST_RESOLVED = "duplicate_equal_largest_fragments_resolved"
```

[Handoff] says the resolution note is propagated into `AliasGroupingResult.notes`, and that one distinct representation resolves the tie while multiple representations retain `FRAGMENT_AMBIGUITY`. [Handoff] gives the evidence type as "code edits performed by Miles from commands supplied in this chat".

The edit included this backup command ([Export]):

```bash
cp admet/scripts/alias_grouping.py admet/scripts/alias_grouping.py.pre_duplicate_tie_refinement
```

[Export] recorded the backup's existence as UNKNOWN. The 2026-11-14 local observation in §11 now shows the file exists on the Mac.

### 6.3 First test attempt used the wrong environment

User output per [Export] §3.9. [Export] does not name the host.

```text
zsh: command not found: micromamba
RDKit: 2026.03.6
Traceback (most recent call last):
  File "<stdin>", line 11, in <module>
AssertionError
```

The assertion stopped at the RDKit-version check. [Export] classifies this as an environment-selection failure, not a scientific failure. [Handoff] does not record this attempt.

### 6.4 Existing local alias tests

[Mac, user-reported] The existing suite passed with 19 tests ([Export] §3.12: "19 pass"; [Handoff] §2.4: "19 passed"). [Export] calls this a Mac mechanical regression smoke, not authoritative pinned-runtime chemistry qualification.

### 6.5 First focused-test edit failed safely

[Export] §3.13 (user-reported output):

```text
FAIL: alias_grouping import block not found
...................
```

[Export] says the file was not modified by that edit and the original 19 tests still ran. [Handoff] does not record this attempt.

### 6.6 Four focused tests added; NameError failures

[Export] §3.14, [Handoff] §2.4. The edit reported `PASS: four focused duplicate-tie tests added` in `tests/test_admet_alias_grouping.py`. [Handoff] lists their coverage:

- duplicate equal-largest fragments resolve with audit provenance;
- chemically distinct equal-largest fragments stay ambiguous;
- resolution does not depend on fragment order;
- the actual CHEMBL5315124 resolves without its source SMILES being rewritten.

[Mac, user-reported] The first run gave `...................FFFF` and `4 failed, 19 passed`. All four failures were `NameError: name 'build_alias_grouping_result' is not defined`. Both sources classify this as test plumbing or a test import failure; the new tests did not reach grouping logic.

### 6.7 Import fixed; local suite passed

[Mac, user-reported] A targeted import fix added `build_alias_grouping_result`. Both sources report the same result, each in its own words:

- [Export] §3.15: the user reported "all pass". The expected suite size was 23 (19 + 4), and the export says the conversation "treats this as 23/23 passing locally".
- [Handoff] §2.4: "Miles reported: 23 passed".

[Handoff] §2.5 says this 23-test pytest suite ran on the Mac runtime, not on the pinned runtime.

---

## 7. Pinned-runtime qualification on gpu-dev1

### 7.1 ADMET environment recovered and verified

[Export] §3.10, [Handoff] §2.5. ADMET pilot environment: `/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot`. [Handoff] says it must not be conflated with the native-Gurobi environment and storage under `CX900004_DS117`.

[gpu-dev1, user-reported] The pinned-runtime verification reported `pass`. [Export] lists the relevant runtime contract as Python 3.12.x, NumPy 1.26.4 and RDKit 2023.09.6. [Handoff] names only RDKit 2023.09.6. The exact pandas version from that check is UNKNOWN.

### 7.2 CHEMBL5315124 witness

[gpu-dev1, user-reported]. Per [Export] §3.11 only, a direct witness parsed the prepared-source SMILES, split fragments with `Chem.GetMolFrags(..., sanitizeFrags=True)`, selected the tied-largest fragments and canonicalized each with canonical isomeric `Chem.MolToSmiles`. Per both [Export] §3.11 and [Handoff] §2.5, it asserted 3 total fragments, 2 tied-largest fragments, and 1 distinct canonical isomeric representation in the tied pair. Result reported: `pass`.

### 7.3 Implementation qualification with built-in assertions

[Export] §3.16, [Handoff] §3. The reviewed source and test state was staged to `/mnt/nfs/CX900004_DS117/sbdd-project/session017_alias_tie_qualification`. The transfer workflow included SHA-256 verification, but neither source preserves the literal hash strings. Old Session-016 manifest hashes must not be substituted.

[gpu-dev1, user-reported] per [Export] §3.16 and [Handoff] §2.5: "pytest not in the conda environment". The environment was not changed to install pytest. Built-in assertions ran against the actual amended implementation under RDKit 2023.09.6. [Export] says they covered:

- unique-largest behavior;
- duplicate-tie resolution;
- order invariance;
- genuine ambiguity;
- the actual CHEMBL5315124;
- source preservation;
- family-key presence;
- audit/failure state.

Result reported: `all pass`.

Two different checks are involved here. The Mac pytest results in §6 are local smoke tests. The gpu-dev1 qualification used direct assertions under the pinned runtime, not pytest.

---

## 8. Full-population amended grouping rerun (post-amendment)

### 8.1 First attempt blocked by missing staged data

[gpu-dev1, user-pasted] per [Export] §3.17:

```text
NEED_PREPARED_DATA_TRANSFER
admet/data/prepared/pka_v2.4a_session016.csv
admet/data/prepared/human_hepa_408_session016.csv
(/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot) mhuang
```

[Export] calls this a staging issue, not a scientific failure. [Handoff] does not record this attempt.

### 8.2 Prepared data transferred

[Export] §3.18, [Handoff] §2.6 and §3:

- Mac staging: `/tmp/session017_prepared_data` and `/tmp/session017_prepared_data.tar.gz` ([Export] only)
- gpu-dev1 staging: `/mnt/nfs/CX900004_DS117/sbdd-project/session017_prepared_data`

Literal archive and file hashes are not recoverable from either source.

### 8.3 Rerun result

[gpu-dev1, user-pasted] on host `n4pu04`, per [Export] §3.19 and [Handoff] §2.6. The user pasted many RDKit `Can't kekulize mol` warnings and several `Tautomer enumeration stopped ... max transforms reached` messages. None of them became grouping failures, and [Handoff] says no new exclusion was introduced. Final output:

```text
RDKit: 2023.09.6
endpoint_qualified_identities: 5882
successfully_grouped: 5882
grouping_failures: 0
distinct_family_keys: 5447
distinct_scaffold_keys: 894
resolved_duplicate_ties: [('clearance', 'CHEMBL5315124')]
CHEMBL5315124 family_key: CC1COc2c(N3CCN(C)CC3)c(F)cc3c(=O)c(C(=O)O)cn1c23
CHEMBL5315124 notes: ('duplicate_equal_largest_fragments_resolved',)
PASS: amended full-population grouping
(/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot) mhuang8@n4pu04:~/sbdd-project/session017_alias_tie_qualification$
```

Post-amendment state: 5,882 identities / 5,882 grouped / 0 failures / 5,447 family keys / 894 scaffold keys. CHEMBL5315124 is the only recorded duplicate-equal-largest resolution.

Kept separate from §2: the Session-016 pre-amendment result (5,882 / 5,881 / 1 failure / 5,446 / 893, CHEMBL5315124 held) is the historical record. [Handoff] §8 says the post-amendment state is the superseding production grouping state for continuation, and that the Session-016 evidence should stay preserved rather than be rewritten.

---

## 9. Stage-4 primitive reuse and naming

### 9.1 Stage-4 source inspected

[Export] §3.20, [Handoff] §2.7. The user uploaded `novelty.py` in the original chat. It defines `MORGAN_RADIUS = 2`, `MORGAN_FP_SIZE = 2048`, `MORGAN_USE_CHIRALITY = True`, `make_morgan_generator()` (calls `rdFingerprintGenerator.GetMorganGenerator` with those parameters) and `calculate_tanimoto(fingerprint1, fingerprint2)` (wraps `DataStructs.TanimotoSimilarity`). Stage-4 `fingerprint_molecules()` calls `generator.GetFingerprint(mol)` on the RDKit molecules it is given.

### 9.2 Reuse direction

[Export] §3.21 says "Implementation direction accepted in conversation", and [Handoff] §2.7 says "The continuation decision in this chat was". Neither source preserves verbatim user wording for this item. Recorded direction:

- reuse Stage-4 `make_morgan_generator()` and `calculate_tanimoto()`;
- do not duplicate the Morgan/Tanimoto primitive in a new ADMET-specific module;
- do not use Stage-4 collection/evaluation functions (for example `fingerprint_molecules()`, `evaluate_internal_similarity()`) for family aggregation;
- a shared chemistry-module refactor was discussed but is not authorized or currently required.

### 9.3 Naming clarification

[Export] §3.22, [Handoff] §5. An earlier proposal used `build_task2_split_input.py` / `molecular_similarity.py`. The user clarified that Task 2 is a plan step, not a scientific architectural layer, so no `task2_*` scientific APIs or artifacts should be created. Conceptual pipeline: prepared ADMET identities → immutable alias families → molecular similarity (fingerprints / Tanimoto) → complete family-mean `S_ij` → family-level split input → 80/20 dev/test → five-fold development CV. The builder name discussed was `admet/scripts/build_split_input.py`.

No `notes/Decisions.md` entries were created for §9.2 or §9.3.

---

## 10. Split-input builder: last recorded state in the sources

- [Handoff] §5 says work stopped immediately before the builder was implemented. The next action it gives is to determine the actual repository import path of Stage-4 `novelty.py` without guessing, then implement `admet/scripts/build_split_input.py` using `make_morgan_generator()` and `calculate_tanimoto()`. The builder would read both prepared CSVs, apply the §4 identity contract, rebuild or use the amended alias family assignment, assert the measured population (5,882 / 5,882 / 0 / 5,447), parse and fingerprint every prepared-source SMILES under RDKit 2023.09.6 with parse failure halting, compute Tanimoto, group by `family_key`, build complete family-mean `S_ij` with `w_i = |F_i|`, and produce the family-level optimizer representation.
- [Export] §3.23 is later than that point. It records that a command was *proposed* to locate `novelty.py`, derive an import path, and create `admet/scripts/build_split_input.py` with a `SplitIdentity` dataclass, `fingerprint_split_identities()` and `family_mean_similarity()`. The recoverable conversation has no user output confirming the command was run, so [Export] records the file's existence and content and the Stage-4 import path as UNKNOWN.

The local Mac observation in §11 adds newer information on both points.

---

## 11. Local Mac observations, 2026-11-14

[Mac obs 2026-11-14] Read-only observations by the main Claude Code conversation in `/Users/mileshuang/Desktop/sbdd-project`, branch `stage6-wip`, HEAD `f616babe10579b572e64d5175ca5682c63fc79ef`.

```text
$ git status --short
 M admet/scripts/alias_grouping.py
 M tests/test_admet_alias_grouping.py
?? .claude/
?? CLAUDE.md
?? admet/scripts/alias_grouping.py.pre_duplicate_tie_refinement
?? admet/scripts/build_split_input.py
?? tests/test_admet_alias_grouping.py.pre_duplicate_tie_tests
```

| File | SHA-256 | Size (bytes) | mtime |
| --- | --- | --- | --- |
| `admet/scripts/alias_grouping.py` | `dd604914ab88c9fd9e0475f0bbbecbef223b7dfd6667bfa9ebdb810f24dfe9c5` | 15989 | Nov 12 16:26 |
| `tests/test_admet_alias_grouping.py` | `2a11e59f0b672e3792172fd58d4de68da4194b47350c11eadcddfcd0a25b46a1` | 11284 | Nov 13 13:43 |
| `admet/scripts/build_split_input.py` | `b1e96ba18b35391d19a54aa8c5054719642d8251be4054603be335f6de7905ff` | 2589 | Nov 13 14:36 |
| `evaluation/novelty.py` | `ba09443a67eae67ad08211299ea1f3484d9cfeda6676c047a7d159013eec9493` | 18359 | Aug 16 13:54 |
| `admet/scripts/alias_grouping.py.pre_duplicate_tie_refinement` | `9f6be0038274c27c31527d2c45297ae8612b57c5397fdff92d325b686c4836e6` | 14450 | Nov 12 16:26 |
| `tests/test_admet_alias_grouping.py.pre_duplicate_tie_tests` | `3bdaad34c6e1ec186c822373f2d3500b3dba76d9b93a33eac0f594d1066cbd2e` | 9523 | Nov 6 14:20 |

No observed path was missing. `notes/Session_017.md` did not exist when checked.

`admet/scripts/build_split_input.py` (current Mac content, read by the main conversation; nothing in it was run):

- 96 lines; docstring "Build the frozen ADMET family-level split input."
- imports `from rdkit import Chem, rdBase`, `from admet.scripts.alias_grouping import build_alias_grouping_result`, `from evaluation.novelty import calculate_tanimoto, make_morgan_generator`
- constant `AUTHORITATIVE_RDKIT_VERSION = "2023.09.6"`
- frozen dataclass `SplitIdentity(endpoint, identity, source_smiles, family_key)`
- `fingerprint_split_identities()` parses `source_smiles` with `Chem.MolFromSmiles`. It raises `ValueError` on a parse failure or a duplicate `(endpoint, identity)` key, and fingerprints with `make_morgan_generator().GetFingerprint`.
- `family_mean_similarity()` computes the complete mean `calculate_tanimoto` over all family_a × family_b pairs, with an explicit pair-count assertion.
- Draft state: it imports `rdBase` and `build_alias_grouping_result` but does not use them in the content shown. It has no data loading, no call to the version check, no `S_ij` matrix construction and no main entry point. It is untracked and uncommitted.

What these observations add to earlier UNKNOWNs (newer information, not contradictions of [Export] or [Handoff]):

- `admet/scripts/build_split_input.py` now exists locally as the draft described above. The sources do not establish whether it was created by the command proposed in [Export] §3.23 or by some other route.
- In this local draft, the Stage-4 import path is `evaluation.novelty`, and `evaluation/novelty.py` exists locally. The sources do not establish that it is byte-identical to the `novelty.py` uploaded in the original chat, because no hash of the upload was recorded.
- The `alias_grouping.py.pre_duplicate_tie_refinement` backup exists locally. A test backup, `tests/test_admet_alias_grouping.py.pre_duplicate_tie_tests`, also exists locally; neither source records how it was created.
- The amended `alias_grouping.py` and `tests/test_admet_alias_grouping.py` are modified and uncommitted on `stage6-wip` relative to HEAD `f616bab`.
- The current Mac hashes above describe only the local bytes as of 2026-11-14. They do **not** establish that these bytes match what was staged to `/mnt/nfs/CX900004_DS117/sbdd-project/session017_alias_tie_qualification` or what ran on gpu-dev1. The staged hashes are not recoverable from the sources.

---

## 12. Infrastructure and paths (as recorded in the sources)

Source: [Export] §7, [Handoff] §3.

- Mac remotes: `origin git@git.ucsf.edu:Miles-Huang/sbdd-project.git`; `github https://github.com/mileshuangg-alt/sbdd-project.git`
- gpu-dev1 route: `ssh mhuang8@facbastp9004.fac.ucsf.edu`, then `ssh gpu-dev1.ic.fac.ucsf.edu`. Observed host `n4pu04`; [Handoff] says this hostname is execution-state-specific, not a permanent machine identity.
- ADMET environment: `/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot`
- Gurobi environment: `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual` (Python 3.12.16, Gurobi 14.0.0, Academic WLS per [Handoff] §3; [Export] §6 gives "Gurobi 14.0.0 Academic WLS" without a Python version)
- Session-017 qualification paths: `/mnt/nfs/CX900004_DS117/sbdd-project/session017_alias_tie_qualification`, `/mnt/nfs/CX900004_DS117/sbdd-project/session017_prepared_data`. [Handoff] says whether to archive, commit or remove them has not been decided; preserve them for now.
- Transfer routes (Mac → gpu-dev1 via ProxyJump `mhuang8@facbastp9004.fac.ucsf.edu`; Mac → CoreHPC via ProxyJump `mhuang8@chpc-ucsf-bastion-vm1.corehpc.ucsf.edu` to `mhuang8@chpc-ucsf-login-vm1.corehpc.ucsf.edu:/scratch/user/mhuang8/`) are recorded verbatim in both sources. [Handoff] gives the bundle workflow as one tar.gz plus `SHA256SUMS.txt`, with `shasum -a 256` on the Mac and `sha256sum` on the remote side.

---

## 13. Running jobs

Both sources ([Export] §10, [Handoff] §4) report no known running Session-017 job as of their 2026-11-14 state: no fingerprint, family-pair matrix, production Gurobi, Stage-A split or Stage-B CV job, and no Slurm job or background process. Neither source refreshed live status. Historical Session-016 DataSAIL P1 and native N=100/N=500 measurements are engineering probes, not current jobs, and do not establish full-scale production feasibility or performance.

---

## 14. Differences between the sources

Each item is recorded with its source and none is resolved here.

1. **Final local suite result after the import fix.** [Export] §3.15 ("all pass", treated as 23/23) and [Handoff] §2.4 ("Miles reported: 23 passed") report the same local result in different words. The source wording is preserved; this is not a disagreement. Neither gives the raw output beyond these quotations.
2. **Events in [Export] only.** The wrong-environment RDKit 2026.03.6 failure (§6.3), the failed import-block edit (§6.5), `NEED_PREPARED_DATA_TRANSFER` (§8.1), the Mac `/tmp` staging paths (§8.2), the proposed builder-creation command (§10) and the withdrawn grouping-only fingerprint proposal (§4.1). [Handoff] does not mention them. This is an omission, not a contradiction.
3. **Pinned-runtime contract detail.** [Export] lists Python 3.12.x / NumPy 1.26.4 / RDKit 2023.09.6. [Handoff] names only RDKit 2023.09.6. This is not a contradiction.
4. **Last builder state.** [Handoff] stops before builder implementation. [Export] records a later proposed but unconfirmed creation command. The two are consistent as successive states.

---

## 15. Gaps and UNKNOWNs (still open)

- exact first active Session-017 date beyond the 2026-11-11 handoff
- production Gurobi seed / determinism setting: OPEN (do not inherit synthetic seeds)
- production optimization time budget: OPEN (P0 1,800 s / P1 600 s were engineering-probe limits)
- MIP-gap acceptance threshold: none approved
- constrained-random comparison protocol: OPEN (sampling method, constraint handling, seeds, number of allocations, summary statistic per [Handoff] §7.7)
- full-scale production optimization feasibility/performance: unmeasured
- Git commit of Session-017 edits: none established. Local observation shows the amended files as uncommitted and `build_split_input.py` as untracked on `stage6-wip`.
- SHA-256 of the bytes staged to and run on gpu-dev1: not recoverable. Current Mac hashes (§11) do not establish them.
- pandas version from the pinned-runtime check: UNKNOWN
- whether local `evaluation/novelty.py` is identical to the uploaded `novelty.py`: not established
- how and when `build_split_input.py` and the test backup were created: not established by the sources
- real production fingerprints, complete production `S_ij`, family-level optimizer input, 80/20 production split, five-fold development CV: not established as generated or run
- any unreported work after the last recoverable chat state

Missing documentation in these sources is not evidence that something did not happen or was not approved.

---

## 16. Current state (session ongoing)

As of 2026-11-14, from [Export] §9 and §14 and [Handoff] §9, plus [Mac obs 2026-11-14]:

```text
Endpoint preparation:                    complete/frozen from Session 016
Alias-grouping base methodology:         qualified from Session 016
Equal-largest duplicate refinement:      reported approved, implemented, qualified (gpu-dev1 assertions)
Current grouping population:             5882/5882 grouped, 5447 families, 894 scaffold keys, 0 failures (gpu-dev1, user-pasted)
Similarity methodology:                  reported approved/frozen
Stage-4 Morgan/Tanimoto reuse:           reported selected
build_split_input.py:                    local untracked draft exists (Mac obs); incomplete; not run
Stage-4 import path:                     evaluation.novelty in local draft (Mac obs)
Real fingerprints / S_ij / optimizer input: not established as generated
80/20 split / five-fold CV:              not run
Production Gurobi job:                   none known
```

Both source documents say they give no permission to modify code, run jobs or advance the session. Miles's authorization for this log says the same: it is "not session closure, advance, or permission to continue scientific work." Session 017 remains ongoing.

---

## 17. Decision records and review notes, 2026-11-14

Sources for this section: [Mac obs 2026-11-14], a read-only inspection by the main Claude Code conversation, and Miles's chat authorization of 2026-11-14, which begins: "Handle both rounds as one bookkeeping batch. I authorize the factual Session 017 additions and the D033 draft clarifications below, not code changes or execution." That authorization does not amend D032 and gives no permission for code changes or execution. Session 017 remains ongoing.

### 17.1 Decisions recorded

- D031 — "ADMET Production Split Units, Constraints and Leakage Objective (Retrospective Consolidation)" was recorded in `notes/Decisions.md` (lines 8226–8374) on 2026-11-14 on Miles's authorization. Status: FROZEN DESIGN; RECORDED AS RETROSPECTIVE CONSOLIDATION. Original approval date not recovered.
- D032 — "ADMET Alias Grouping: Equal-Largest Duplicate-Fragment Tie Resolution" was recorded in `notes/Decisions.md` (lines 8376–8423) on 2026-11-14 on Miles's authorization. Status: FROZEN; RECORDED RETROSPECTIVELY. Original approval date not recovered; original approval wording export-reported only.
- `notes/Decisions.md` SHA-256 after D032: `ee5c4b009df43e9bd9f3a74426b8ef478026e4ac2650702c6cff7d2fcb29fd6a` [Mac obs 2026-11-14].
- Earlier statements in §4.2, §5.2 and §9.3 that no `notes/Decisions.md` entry was created describe the state when this log was created. For the items covered by D031 and D032, this subsection supersedes them. The molecular-similarity specification (§4) is not yet recorded as a decision.

### 17.2 Implementation review notes (for later code review; no code changed)

From read-only inspection of `git diff -- admet/scripts/alias_grouping.py` against HEAD `f616bab` [Mac obs 2026-11-14]:

- **Failure-label discrepancy.** In the amended `select_unique_largest_fragment()`, a canonicalization exception or an empty canonical SMILES now returns `FRAGMENT_AMBIGUITY` (`fragment_ambiguity_equal_largest_heavy_atom_count`), even when the largest fragment is unique (no tie). Canonicalization failures within a tie get the same label as genuinely distinct-representation ties. The record is still held, so D032 rule 3 is met; only the audit reason can be inaccurate. Per the reported continuation result (0 grouping failures), no current record is affected. Logged for later code review. D032 is not amended and no code was changed.
- **Stereo-only ties.** Tied fragments that differ only in stereochemistry have distinct canonical isomeric SMILES, so they are held under D032 rule 1, even though the family key later removes stereochemistry. This follows from the recorded rule; it has not been newly tested or qualified.

### 17.3 Evidence status

- The continuation grouping counts (5,882 / 5,882 / 0 / 5,447 / 894; §8.3) are console-reported only (user-pasted gpu-dev1 output). No artifact or hash exists for them, unlike the hash-verified Session-016 diagnostic outputs (`notes/Session_016.md` §3).
- `admet/scripts/session016_alias_edge_diagnostic.py` imports the amended module (`from admet.scripts import alias_grouping as aliases`, line 27) and checks fixed Session-016 counts (`EXPECTED_AUDIT_COUNTS`, defined at lines 38–50 and checked at line 675). Run with the amended module, it would not reproduce its own expected counts. The pre-amendment module survives at committed HEAD `f616bab` and in `admet/scripts/alias_grouping.py.pre_duplicate_tie_refinement`. That code alone does not establish that the Session-016 result is reproducible. These historical references are preserved for now.
- The hashes recorded in this log and in D032 §4 identify reference bytes on the Mac. They are not proof of review, and they do not establish what ran on gpu-dev1.

### 17.4 Gates carried forward for the split-input builder

- Existing approval gates remain in force.
- `admet/scripts/build_split_input.py` needs its own code review and identified bytes before any execution. Transfer verification (tar plus `SHA256SUMS.txt`) is not permission to run it.
- The builder proposal must use D032's continuation counts, not the Session-016 diagnostic's historical `EXPECTED_AUDIT_COUNTS`.

### 17.5 D033 recorded

- D033 — "ADMET Molecular-Similarity Specification for Split Construction" was recorded in `notes/Decisions.md` (lines 8425–8494) on 2026-11-14 on Miles's authorization ("Yes, record D033"). Status: FROZEN; RECORDED RETROSPECTIVELY. Original approval date not recovered; original approval wording export-reported only. This supersedes, for the similarity specification, the §17.1 statement that it is not yet recorded.

### 17.6 Split-input builder code edits and Mac tests

[Mac obs 2026-11-14] Code edits made by the main Claude Code conversation on Miles's approval (chat, 2026-11-14, verbatim): "I approve the builder proposal for code edits". The approved proposal covered code edits and Mac tests only; a real-data run on gpu-dev1 still needs separate code review, identified bytes and a measured interactive runtime. Nothing was run on real data and nothing was run on gpu-dev1.

- `admet/scripts/build_split_input.py` completed (600 lines, SHA-256 `35693c4c7c49bef73bc6892eab3704ab3da394dfe8f8e68d89fded4ac399e293`; untracked). It keeps the existing `SplitIdentity`, `fingerprint_split_identities()` and `family_mean_similarity()` and adds: pinned-runtime check (`assert_authoritative_rdkit_runtime()` plus the config's RDKit version); verification of both prepared CSVs against `admet/data/prepared/MANIFEST.sha256`; identity loading that retains only the identity and `smiles` columns and halts on more than one SMILES per identity; D032 grouping via `build_alias_grouping_result()` that halts on any grouping failure; expected-count checks from the config; D033 fingerprints; families ordered by `family_key`; complete upper-triangle `S_ij` for every family pair via `family_mean_similarity()`; outputs `families.csv`, `memberships.csv`, `family_similarity_upper.npy` (float64), `run_metadata.json` (config, input and code hashes, versions, counts, phase timings) and `SHA256SUMS.txt`, refusing to overwrite a non-empty output directory.
- New frozen config `admet/data/splits/split_input_config.json` (SHA-256 `4dd1c1aa2027fe3cbe8de988c2e3153ec5bd6111ad531ea0983e84658e70e9f2`; untracked): endpoint paths, identity and SMILES columns, RDKit 2023.09.6, expected counts (pKa 5,474 and clearance 408 identities from `notes/Session_016.md` §2; D032 continuation counts 5,882 / 5,882 / 0 / 5,447 / 894), output directory `admet/data/splits/split_input_v1`. It does not use the Session-016 diagnostic's `EXPECTED_AUDIT_COUNTS`.
- New tests `tests/test_admet_build_split_input.py` (12 tiny-fixture tests, SHA-256 `5aca2dd246499b9da923a2c494f211f89b35e873cba89ffd38446194762c6f3d`; untracked).
- Mac test result: `python3 -m pytest tests/test_admet_build_split_input.py tests/test_admet_alias_grouping.py -q` → `35 passed in 1.77s` (12 new + 23 existing), under local RDKit 2026.03.6. This is a mechanical smoke test, not pinned-runtime qualification.
- Not done: no code review of the finished bytes yet; no real-data run; no gpu-dev1 staging; no runtime measurement. The builder's runtime guard was not exercised on the Mac. These hashes are reference bytes, not proof of review.

### 17.7 Code review of the split-input builder and fixes

[Mac obs 2026-11-14] The main Claude Code conversation ran `/code-review` (high effort, single-pass, no verify stage) on `admet/scripts/build_split_input.py`, `admet/data/splits/split_input_config.json` and `tests/test_admet_build_split_input.py`, on Miles's instruction (chat, 2026-11-14, verbatim): "Run /code-review first". It reported 9 findings. On Miles's instruction (chat, 2026-11-14, verbatim): "Fix all findings", all 9 were fixed:

1. Provenance code hashes now come from the files of the modules actually imported (`executed_code_sha256`: this module, `admet.scripts.alias_grouping`, `evaluation.novelty`, each with resolved path and SHA-256), not from paths under `--repo-root`.
2. Endpoint names and the per-family endpoint-count columns are taken from the config's `endpoints` instead of hardcoded `pka` / `clearance` (cf. `~/.claude/CLAUDE.md` rule 9). Output column names are unchanged for the current config (`pka_identities`, `clearance_identities`).
3. Outputs are written to a temporary sibling directory and moved into place only after `SHA256SUMS.txt` is written; a failed write removes the temporary directory and leaves no partial output.
4. The complete `S_ij` loop precomputes one fingerprint tuple per family; each molecule pair still uses `calculate_tanimoto()` (D033 §4). No pair is pruned.
5. Added an end-to-end tiny-fixture test of `build_split_input()` (config, manifest check, counts, output files, SHA256SUMS, families columns, `.npy` length, no label columns in memberships, executed-code hash) with the runtime guard bypassed for the Mac.
6. The loader halts with file and line number on a short or blank CSV row.
7. Each input must sit in the manifest's directory, not just match by file name.
8. Removed two checks that could never fail (family-weight sum; pair count inside the mean).
9. Removed the duplicate inner import of `evaluation.novelty`.

Reference bytes after fixes [Mac obs 2026-11-14; reference bytes, not proof of review]:

- `admet/scripts/build_split_input.py`: 631 lines, SHA-256 `970a2c424ea02375ea39915c40c84672e335c2985847e8709af17673b10f773e`
- `tests/test_admet_build_split_input.py`: 318 lines, SHA-256 `ca6ff4f55eccbb24f67b70d8b09a416d562f66e12865f08db58c7a3bf0f12675`
- `admet/data/splits/split_input_config.json`: unchanged, SHA-256 `4dd1c1aa2027fe3cbe8de988c2e3153ec5bd6111ad531ea0983e84658e70e9f2`

The §17.6 hashes for the builder and its tests are superseded by these.

Mac test rerun: `python3 -m pytest tests/test_admet_build_split_input.py tests/test_admet_alias_grouping.py -q` → `39 passed in 1.64s` (16 builder tests + 23 existing alias tests), under local RDKit 2026.03.6. Mechanical smoke test only; not pinned-runtime qualification. No output directory was created under `admet/data/splits/`.

Not done: Miles's own review of the fixed bytes; gpu-dev1 staging; any real-data run or runtime measurement. The code review was a single-pass automated review, not Miles's code review.

### 17.8 Split-input builder staged to gpu-dev1 (transfer verified; not run)

[Mac obs 2026-11-14] The main Claude Code conversation built the staging bundle on the Mac (scratch directory, not the repository): `session017_split_input_builder.tar.gz` (103,482 bytes, SHA-256 `442a649c4e2197e2653a7ac8034a26f3136ee9dfa7baa1736ec57636f14837d2`) with `session017_split_input_builder.SHA256SUMS.txt`. The tarball unpacks to `session017_split_input_builder/` and contains `FILES.sha256` plus:

- `admet/__init__.py`, `admet/scripts/__init__.py`, `evaluation/__init__.py` (all empty)
- `admet/scripts/build_split_input.py` (`970a2c424ea02375ea39915c40c84672e335c2985847e8709af17673b10f773e`)
- `admet/scripts/alias_grouping.py` (`dd604914ab88c9fd9e0475f0bbbecbef223b7dfd6667bfa9ebdb810f24dfe9c5`)
- `evaluation/novelty.py` (`ba09443a67eae67ad08211299ea1f3484d9cfeda6676c047a7d159013eec9493`)
- `admet/data/splits/split_input_config.json` (`4dd1c1aa2027fe3cbe8de988c2e3153ec5bd6111ad531ea0983e84658e70e9f2`)
- `admet/data/prepared/MANIFEST.sha256` (`50284db691bea9de6fa8da720b58ea02693de97c304b7083b2a3608260f2a43b`)
- `admet/data/prepared/pka_v2.4a_session016.csv` (`572fad71dee4cf691f4c413be8295bfa86c0619bcf77ad8055d90df7228ffeba`)
- `admet/data/prepared/human_hepa_408_session016.csv` (`cb3885018ac3aab1c697ed8baa0501d001faae09aaa07cb724687e943d0083d3`)

Tests were not included (pytest is not in the ADMET environment). A Mac-side extraction check verified the tarball hash and all 10 file hashes.

[gpu-dev1, user-pasted] Miles transferred the bundle and reported "all okay" with this output from host `n4pu04` (prompt directory `~/sbdd-project`):

```text
$ test ! -e session017_split_input_builder && echo DESTINATION_ABSENT
DESTINATION_ABSENT
$ sha256sum -c session017_split_input_builder.SHA256SUMS.txt
session017_split_input_builder.tar.gz: OK
$ tar -xzf session017_split_input_builder.tar.gz
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'   (repeated; also 'LIBARCHIVE.xattr.com.apple.macl')
$ cd session017_split_input_builder && sha256sum -c FILES.sha256
admet/__init__.py: OK
admet/scripts/__init__.py: OK
admet/scripts/build_split_input.py: OK
admet/scripts/alias_grouping.py: OK
evaluation/__init__.py: OK
evaluation/novelty.py: OK
admet/data/splits/split_input_config.json: OK
admet/data/prepared/MANIFEST.sha256: OK
admet/data/prepared/pka_v2.4a_session016.csv: OK
admet/data/prepared/human_hepa_408_session016.csv: OK
```

Notes:

- The GNU tar warnings concern macOS extended attributes recorded in the archive headers; they were ignored on extraction, and every extracted file's SHA-256 matched.
- The pasted output does not show the `cd /mnt/nfs/CX900004_DS117/sbdd-project` step; the prompt shows `~/sbdd-project`. That `~/sbdd-project` resolves to `/mnt/nfs/CX900004_DS117/sbdd-project` is consistent with the earlier qualification prompt in §8.3 but is not independently verified here.
- Transfer verification is not run permission (§17.4). The builder has not been run on gpu-dev1 or on real data.

### 17.9 Real-data split-input build on gpu-dev1 (D031–D033 input; no split run)

[gpu-dev1, user-pasted] Miles ran the staged builder interactively (not Slurm) on host `n4pu04`, in `~/sbdd-project/session017_split_input_builder` with the environment `/mnt/nfs/CX900004_DS1/conda-envs/liggate-admet-pilot` active, and pasted this post-run verification on 2026-11-14:

```text
$ cd admet/data/splits/split_input_v1 && sha256sum -c SHA256SUMS.txt && ls -l
families.csv: OK
memberships.csv: OK
family_similarity_upper.npy: OK
run_metadata.json: OK
-rw-rw----+ 1 mhuang8 sec_fac_cx900004_ds117    263696 Nov 14 22:31 families.csv
-rw-rw----+ 1 mhuang8 sec_fac_cx900004_ds117 118657576 Nov 14 22:31 family_similarity_upper.npy
-rw-rw----+ 1 mhuang8 sec_fac_cx900004_ds117    522846 Nov 14 22:31 memberships.csv
-rw-rw----+ 1 mhuang8 sec_fac_cx900004_ds117      2804 Nov 14 22:31 run_metadata.json
-rw-rw----+ 1 mhuang8 sec_fac_cx900004_ds117       339 Nov 14 22:31 SHA256SUMS.txt
```

Recorded in `run_metadata.json` (pasted excerpt):

- Observed counts: pKa identities 5,474; clearance identities 408; endpoint-qualified identities 5,882; successfully grouped 5,882; grouping failures 0; distinct family keys 5,447; distinct scaffold keys 894; family_count 5,447.
- Timings (seconds): load 0.0138; grouping 23.62; fingerprint 0.441; similarity 28.23; total before write 52.31.
- Executed code: `admet/scripts/build_split_input.py` `970a2c424ea02375ea39915c40c84672e335c2985847e8709af17673b10f773e`; `admet/scripts/alias_grouping.py` `dd604914ab88c9fd9e0475f0bbbecbef223b7dfd6667bfa9ebdb810f24dfe9c5`; `evaluation/novelty.py` `ba09443a67eae67ad08211299ea1f3484d9cfeda6676c047a7d159013eec9493`; all three resolved under `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/`.
- Runtime: Python 3.12.15; NumPy 1.26.4; RDKit 2023.09.6; Linux-5.15.0-202-generic-x86_64-with-glibc2.35.

Checks by the main Claude Code conversation against the records [Mac obs 2026-11-14, from the pasted text only]:

- All observed counts equal the frozen config's expected counts (Session 016 §2 endpoint counts; D032 §3 continuation counts). This is the first artifact-backed confirmation of the D032 continuation population noted as pending in §17.3.
- The executed-code hashes equal the reviewed reference bytes in §17.7 and §17.8, and the paths are the staged bundle; `executed_code_sha256` records the modules actually imported.
- `family_similarity_upper.npy` size 118,657,576 bytes equals 14,832,181 float64 values (5,447 × 5,446 / 2 × 8 bytes = 118,657,448) plus the 128-byte `.npy` header, consistent with a complete upper triangle.
- The output SHA256SUMS verified on gpu-dev1, but the output hash values themselves were not pasted and are not recorded here. The run log (`split_input_v1_run.log`) was not pasted.

Scope: this produced D031 optimizer input only. No Stage-A or Stage-B assignment, optimizer run, commit or copy back to the Mac was performed. Outputs remain on gpu-dev1 at `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/admet/data/splits/split_input_v1/`. They are not yet frozen by any decision.

### 17.10 Miles's review of the builder bytes

[Miles, chat, 2026-11-14] Asked whether the executed builder bytes had been reviewed by him (the point flagged against §17.9's wording "reviewed reference bytes"), Miles stated: "I did review them". This records Miles's own review of the bytes listed in §17.7 and §17.8 (`admet/scripts/build_split_input.py` `970a2c424ea02375ea39915c40c84672e335c2985847e8709af17673b10f773e`, with `admet/scripts/alias_grouping.py` and `evaluation/novelty.py` at the hashes in §17.8). It supersedes, for that review, the "Not done" item in §17.7. The statement does not say when the review took place relative to the gpu-dev1 run in §17.9, and no time is inferred here.

### 17.11 D034 recorded

- D034 — "ADMET Production Optimization Settings and Constrained-Random Comparison" was recorded in `notes/Decisions.md` (lines 8496–8557) on 2026-11-14 on Miles's authorization ([Miles, chat, 2026-11-14]: "lets keep the ongoing seed convention, other than that lats authorize d034."). It is a new decision made in Session 017 (not retrospective); it authorizes no run; numeric WorkLimit values (W_A, W_B) remain to be set by the calibration step (D034 §4 step 3).

### 17.12 D034 review and amendment

- [Miles, chat, 2026-11-14] After a structured review of D034, Miles answered "yes to all six. let me commit changes to the rpeo before you propose code".
- D034 Amendment 1 recorded in `notes/Decisions.md` (lines 8559–8586): Stage-A freeze decision before Stage B; calibration reports only and Miles sets W_A, W_B and safety TimeLimits; Stage-B construction measurement; sampling cap of 100,000 attempts and percentile definition.
- Pending (approved, not yet done): Miles to paste the `split_input_v1/SHA256SUMS.txt` values from gpu-dev1, to be recorded as D034's identified input and checked by each optimizer run before it starts. Until then the output hash values remain unrecorded (§17.9).
- Reproducibility scope: D034's reproducibility claims cover only the same Gurobi version, parameters, `Threads` and host CPU. Each run records the host CPU model. The observed hostname (`n4pu04`) is execution-state-specific (§12), so a later run may land on different hardware and produce a different, equally valid result.
- Miles stated he will commit the repository changes himself before code for D034 is proposed.

### 17.13 Commit, and Stage-A construction-measurement code

- [Mac obs 2026-11-14] On Miles's instruction ("Commit the working tree changes with a sensible message."), the main Claude Code conversation committed seven files on `stage6-wip` as `9b0efa7e20e186f7ebf1a726f2c5a2cac540f42a` ("Session 017: record D031-D034 and add ADMET split-input builder"): `notes/Decisions.md`, `notes/Session_017.md`, `admet/scripts/alias_grouping.py`, `tests/test_admet_alias_grouping.py`, `admet/scripts/build_split_input.py`, `tests/test_admet_build_split_input.py`, `admet/data/splits/split_input_config.json`. Left untracked: `CLAUDE.md`, `.claude/agents/bookkeeper.md`, and the two `.pre_*` backups (pre-amendment versions are preserved at `f616bab`). Not pushed.
- [Miles, chat, 2026-11-14] Approval of the construction-measurement proposal, verbatim: "okay, I approve this proposal. I cannot find the shasums.txt file you referred to". The main conversation clarified that `SHA256SUMS.txt` is on gpu-dev1 at `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/admet/data/splits/split_input_v1/SHA256SUMS.txt` (outputs were not copied to the Mac) and gave the command to print all five split-input hashes there.
- [Mac obs 2026-11-14] Code edits made on that approval (D034 §4 step 2; reusable for D034 Amendment 1 A3); untracked, not run on real data:
  - `admet/data/splits/split_optimization_config.json` (SHA-256 `e44f088bdfca270448cff4fe7d3346eac4c69dc577fd64b3e202437ef7f5a275`): split-input path and family/similarity sizes; ε = δ = 0.05; endpoints; Stage A partitions dev 0.8 / test 0.2; Gurobi environment and Seed 20261114; construction sampling interval; output root `admet/artifacts/split_optimization`. The five expected split-input hashes and `rss_cap_bytes` are null (PENDING); the script refuses to run until they are set.
  - `admet/scripts/measure_split_model_construction.py` (484 lines, SHA-256 `afb399ed206031732d075507a1ae3217c7af0a5d653a5e0a5ce91f7684f61055`): verifies split-input hashes; memory-maps the similarity array behind a read-only upper-triangle mapping; lower bounds via `probe.compute_limits()` and `probe.stratification_lower_bounds()`, upper bounds at stage totals; builds the model with the unchanged `equivalence.build_native_gurobi_model()`; samples RSS with an abort at the cap; checks 10,894 binaries, 5,459 linear constraints and 29,664,362 quadratic terms for Stage A and `SolCount == 0`; never calls `optimize()`; writes `construction_report.json` and `SHA256SUMS.txt` atomically under `admet/artifacts/split_optimization/stage_a_construction/`, refusing to overwrite.
  - `tests/test_measure_split_model_construction.py` (204 lines, SHA-256 `c3e9f0d96a1e3d83a296f6974aa4721fa97e8192ae3ee56c1530401bc41e414c`).
- [Mac obs 2026-11-14] `python3 -m pytest tests/test_measure_split_model_construction.py tests/test_admet_build_split_input.py tests/test_admet_alias_grouping.py -q -rs` → `49 passed, 1 skipped in 2.01s`. The skipped test is the tiny Gurobi model build (`gurobipy` is not installed on the Mac). Mechanical smoke test under local RDKit 2026.03.6 only; Gurobi construction is untested.
- Not done: Miles's review of these bytes; recording of the split-input hashes; setting the RSS cap; staging; gpu-dev1 pre-run checks; any run.

### 17.14 Split-input hashes recorded; gpu-dev1 pre-run checks

[gpu-dev1, user-pasted] Miles ran `sha256sum families.csv memberships.csv family_similarity_upper.npy run_metadata.json SHA256SUMS.txt` in `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/admet/data/splits/split_input_v1` on host `n4pu04` and pasted (2026-11-14):

```text
286f5cbdcbd8af10ce845dda1a6a53d40feba93b0214a35300e18efc4d0e3abc  families.csv
95d8318413b9b89294e25ceaded99c251ce1a55fc3c2dd458afe9de1e45c9044  memberships.csv
478daa50f65111b673337805699b086be9451e21eb5caf61ce14d4b137051185  family_similarity_upper.npy
dd6cdcf373db6177844df3413d655a78b2a16219916b79d4c352aedbe347f53a  run_metadata.json
f6081b95fe808125f8f9f90068626541415f5dcb347f7bb20183020d0dee5276  SHA256SUMS.txt
```

These are recorded as D034's identified split input (approved Q1, §17.12) and were entered by the main conversation as `split_input.expected_sha256` in `admet/data/splits/split_optimization_config.json` [Mac obs 2026-11-14]. They close the "output hash values not recorded" gap noted in §17.9.

[gpu-dev1, user-pasted] Pre-run checks on `n4pu04`, 2026-11-14:

- `nproc` → `128`
- `free -g` → Mem total 503, used 7, free 262, buff/cache 233, available 492; Swap total 507, used 0.
- In `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual`: `python -s -c "import numpy, psutil, gurobipy; ..."` → `ModuleNotFoundError: No module named 'numpy'`. numpy is not installed in the qualified Gurobi environment. Whether psutil and gurobipy import there was not reached by this check.

Consequence (main conversation): `admet/scripts/measure_split_model_construction.py` (§17.13) imports numpy at module level and imports `admet/qualification/datasail_scaling/probe.py`, which also imports numpy, so it cannot run in that environment as written. No environment was changed. A fix is pending Miles's choice.

### 17.15 numpy added to the Gurobi environment

- [Miles, chat, 2026-11-14] Offered (A) removing numpy from the construction script or (B) installing numpy into the qualified Gurobi environment, Miles chose, verbatim: "Option B, install numpy". He also pasted `7.2.2 (14, 0, 0)` for `psutil` and `gurobipy` in that environment.
- [gpu-dev1, user-pasted] Environment composition (`conda list -p /mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual`): `python 3.12.16 h5f976f7_0_cpython conda-forge`; `psutil 7.2.2 pypi_0 pypi`; `gurobipy 14.0.0 pypi_0 pypi`. The environment is mixed: Python from conda-forge, add-on packages from PyPI via pip.
- [gpu-dev1, user-pasted] A conda dry run (`conda install -p … numpy=1.26.4 --dry-run`) failed with `LockError: Failed to acquire lock.`; nothing was changed. The pip route was used instead, matching how `psutil` and `gurobipy` were installed: `python -s -m pip install --dry-run numpy==1.26.4` → `Would install numpy-1.26.4`.
- [gpu-dev1, user-pasted] Snapshots saved on gpu-dev1 under `/mnt/nfs/CX900004_DS117/sbdd-project/`: `liggate-gurobi-qual.before_numpy.txt` (conda `--explicit`), `liggate-gurobi-qual.before_numpy.pip.txt` (`pip freeze`), `liggate-gurobi-qual.after_numpy.txt`, `liggate-gurobi-qual.after_numpy.pip.txt`. After the install, `python -s -c "import numpy, psutil, gurobipy; ..."` printed `1.26.4 7.2.2 (14, 0, 0)`, and `diff` of the before/after pip snapshots showed only `> numpy==1.26.4`. The output of the install command itself and a diff of the conda snapshots were not pasted.
- Consequence: the Session-016 Gurobi qualification (`notes/Session_016.md` §5; `session016_native_quadratic_qualification.json`) describes this environment before numpy was added. The environment path in D034 §1 is unchanged. To keep conda and pip from conflicting, further packages, if any, should not be added to this environment with conda.

### 17.16 Memory cap set; construction config complete

- [Miles, chat, 2026-11-14] Asked what memory cap the construction measurement should use (proposed 128 GiB, about a quarter of the 503 GB on `n4pu04`, §17.14), Miles answered, verbatim: "128 GiB".
- [Mac obs 2026-11-14] `admet/data/splits/split_optimization_config.json` now sets `construction_measurement.rss_cap_bytes` = `137438953472` (128 GiB) and carries the five split-input hashes from §17.14. Config SHA-256: `f074888a283a80dbbd13d7571e6698104377749bff169e38ae44ad464dbd73c0`. This supersedes the config hash in §17.13 (`e44f088b…`) and the intermediate hash after the split-input hashes were entered (`bbb54635…`).
- [Mac obs 2026-11-14] One test, `test_measurement_refuses_pending_config`, read the live config and failed once the cap was set; it was changed to null the cap in its own copy of the config. `tests/test_measure_split_model_construction.py` SHA-256 is now `d8059c50c2417d7c6ef9b0b205b1a13422bf85c8f79b6a4179ad0173f00e512b` (supersedes §17.13's `c3e9f0d9…`). `admet/scripts/measure_split_model_construction.py` is unchanged (`afb399ed206031732d075507a1ae3217c7af0a5d653a5e0a5ce91f7684f61055`).
- [Mac obs 2026-11-14] `python3 -m pytest tests/test_measure_split_model_construction.py tests/test_admet_build_split_input.py tests/test_admet_alias_grouping.py -q -rs` → `49 passed, 1 skipped in 1.63s` (the skipped test is the Gurobi model build; `gurobipy` is not on the Mac). Mechanical only.
- Not done: Miles's review of the construction script bytes; staging; any run.

### 17.17 Code review of the construction-measurement script and fixes

[Mac obs 2026-11-14] On Miles's instruction "Run /code-review first", the main Claude Code conversation ran `/code-review` (high effort, single pass, no verify stage) on `admet/scripts/measure_split_model_construction.py`, `admet/data/splits/split_optimization_config.json` and `tests/test_measure_split_model_construction.py`. It reported 6 findings. None affected the bounds, the model-dimension checks or the no-`optimize()` rule. On Miles's instruction "Fix all findings", all 6 were fixed:

1. The run now refuses to start if `<stage>_construction_ABORTED.json` exists from an earlier aborted run, and the abort report records its sample interval and creation time.
2. The memory cap is documented as sample-based (not a hard limit) in the script and in the report (`rss_cap_enforcement`), and the config's sample interval was shortened from 0.5 s to 0.1 s.
3. The abort path (cap exceeded → abort report → exit code 3), normal sampling and the host description are now tested on the Mac, using an injected RSS reader, exit function, memory total and `/proc/cpuinfo` file.
4. The test that reads the live config now locates it relative to the test file, not the working directory.
5. The similarity mapping reuses the offset when the qualified builder checks `pair in mapping` and then reads `mapping[pair]`.
6. `RssSampler` now cross-references `construction_probe.measure_native_construction()`, whose sampling loop it mirrors (the qualified module is left unedited).

Reference bytes after fixes [Mac obs 2026-11-14; reference bytes, not proof of review]:
- `admet/scripts/measure_split_model_construction.py`: 534 lines, SHA-256 `9e114432ff6db8de75c7b21882f11ec3484da57554480a16a601c1e3464987ee` (supersedes `afb399ed…`).
- `admet/data/splits/split_optimization_config.json`: SHA-256 `f20f1d187e90c0bd33576396cc25f78e98d9e3ceae6f12e17c34a577d37f4fd4` (supersedes `f074888a…` in §17.16; only the sample interval changed).
- `tests/test_measure_split_model_construction.py`: 289 lines, SHA-256 `109bef0789ad3c676399f7131058d15eda1e2961f638a2d66251fe49b622e6a8` (supersedes `d8059c50…`).

Mac test results [Mac obs 2026-11-14]: from the repository root, `python3 -m pytest tests/test_measure_split_model_construction.py tests/test_admet_build_split_input.py tests/test_admet_alias_grouping.py -q -rs` → `54 passed, 1 skipped in 1.58s`; from `tests/` with `PYTHONPATH=..`, the construction tests alone → `15 passed, 1 skipped`. The skipped test is the Gurobi model build (`gurobipy` is not on the Mac). Mechanical only.

Not done: Miles's review of the fixed bytes; staging; any run.

### 17.18 Construction script reviewed; second staging bundle built

- [Miles, chat, 2026-11-14] Asked whether he had reviewed the fixed construction-script bytes (§17.17), Miles answered, verbatim: "Reviewed, stage it". This records his review of `admet/scripts/measure_split_model_construction.py` `9e114432ff6db8de75c7b21882f11ec3484da57554480a16a601c1e3464987ee`, config `f20f1d187e90c0bd33576396cc25f78e98d9e3ceae6f12e17c34a577d37f4fd4` and tests `109bef0789ad3c676399f7131058d15eda1e2961f638a2d66251fe49b622e6a8`.
- [Mac obs 2026-11-14] Second staging bundle built in the Mac scratch directory (not the repository): `session017_stage_a_construction.tar.gz` (17,742 bytes, SHA-256 `b73c3bb9d48b610ebce35d80e36c555efd54e0b7a0f69c05a1f5b4bcfef55c8c`) with `session017_stage_a_construction.SHA256SUMS.txt`. It was built with `--no-xattrs --no-mac-metadata` (no `LIBARCHIVE.xattr` headers found in the archive). Its members unpack under `session017_split_input_builder/`, into the existing staged bundle, with `FILES_construction.sha256` listing:
  - `admet/qualification/__init__.py` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty)
  - `admet/qualification/datasail_scaling/__init__.py` `319f1b3b1b85eacce1197a82eb6494e909db71667daa95d57d2a7237c3f7b564` (docstring only)
  - `admet/qualification/datasail_scaling/probe.py` `cc5af684e4c99eb9eeba84e4dc53155402dda5dbff4280b178526bc347ae4410` (unmodified from HEAD; no separately recorded qualified hash for this file was found)
  - `admet/qualification/native_quadratic/__init__.py` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty)
  - `admet/qualification/native_quadratic/equivalence.py` `58c0df783e9222203e2be68ac28b28de5b803e40bae31689bfd8591a64aac133`, equal to the Session-016 qualified hash in `admet/qualification/native_quadratic/artifacts/SHA256SUMS.txt`
  - `admet/scripts/measure_split_model_construction.py` `9e114432ff6db8de75c7b21882f11ec3484da57554480a16a601c1e3464987ee`
  - `admet/data/splits/split_optimization_config.json` `f20f1d187e90c0bd33576396cc25f78e98d9e3ceae6f12e17c34a577d37f4fd4`

  None of these paths exists in the first bundle. A Mac extraction check verified the tarball hash and all 7 file hashes, with no `._*` files.
- Not done: transfer to gpu-dev1; any run. Transfer verification is not run permission.

### 17.19 Second bundle transferred to gpu-dev1 (verified; not run)

[gpu-dev1, user-pasted] Miles transferred `session017_stage_a_construction.tar.gz` and pasted, from host `n4pu04` with `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual` active (2026-11-14):

```text
$ cd session017_split_input_builder && sha256sum -c FILES_construction.sha256 && sha256sum -c FILES.sha256
admet/qualification/__init__.py: OK
admet/qualification/datasail_scaling/__init__.py: OK
admet/qualification/datasail_scaling/probe.py: OK
admet/qualification/native_quadratic/__init__.py: OK
admet/qualification/native_quadratic/equivalence.py: OK
admet/scripts/measure_split_model_construction.py: OK
admet/data/splits/split_optimization_config.json: OK
admet/__init__.py: OK
admet/scripts/__init__.py: OK
admet/scripts/build_split_input.py: OK
admet/scripts/alias_grouping.py: OK
evaluation/__init__.py: OK
evaluation/novelty.py: OK
admet/data/splits/split_input_config.json: OK
admet/data/prepared/MANIFEST.sha256: OK
admet/data/prepared/pka_v2.4a_session016.csv: OK
admet/data/prepared/human_hepa_408_session016.csv: OK
```

- All 7 second-bundle files match `FILES_construction.sha256` (§17.18), and all 10 first-bundle files still match `FILES.sha256` (§17.8), so the first bundle was not altered by the extraction.
- The pasted output starts at the final command. The earlier steps given to Miles (pre-extraction path check, tarball `sha256sum -c`, `tar -xzkf`) were not pasted; the file-level hashes above verify the extracted contents regardless.
- Transfer verification is not run permission. The construction measurement has not been run.

### 17.20 Stage-A construction run halted on the quadratic-term check; cause identified

[gpu-dev1, user-pasted] Miles ran the Stage-A construction measurement (`python -s -m admet.scripts.measure_split_model_construction --config admet/data/splits/split_optimization_config.json --stage stage_a`) in `liggate-gurobi-qual` on `n4pu04` (2026-11-14). It built the model and then halted on its own dimension check:

```text
Restricted license - for non-production use only - expires 2028-11-29
...
AssertionError: quadratic_terms: observed 27815294, expected 29664362
exit=1
```

No report was written and `optimize()` was not called. The script's sampled peak memory and build time were not reported, because the halt came before the report.

Diagnosis [gpu-dev1, user-pasted; analysis by the main Claude Code conversation]:
- Missing terms: 29,664,362 − 27,815,294 = 1,849,068 = 2 × 924,534 (two partitions).
- Zero-similarity pairs in `family_similarity_upper.npy`: `zero_pairs 924534 x2 1849068 nonzero_pairs 13907647 min_nonzero 0.0028169014084507044`. The missing terms equal exactly the zero-similarity family pairs counted over both partitions.
- Minimal Gurobi check (two binary variables, terms 0.0·x·y and 0.5·x·y): `expr_terms 2`, then after `setObjective` and `update()`, `objective_terms 1`.
- Root cause (confirmed): Gurobi keeps a zero-coefficient term in a `QuadExpr` but drops it when the expression is set as the model objective. The script counts `model.getObjective().size()`, while its expected count assumed one term per family pair per partition. The Session-016 synthetic fixtures contained no zero similarities, so the qualified count rule never met one.
- Consequence for the model: a pair with S_ij = 0 has coefficient w_i·w_j·S_ij = 0 and contributes nothing to L_cross in any assignment, so the stored objective is mathematically identical. The split-input artifact still holds the complete S_ij for all 14,832,181 pairs.

Separate finding: the run printed `Restricted license - for non-production use only - expires 2028-11-29`, so this shell used the size-limited licence bundled with pip `gurobipy`, not the Academic WLS licence recorded for the Session-016 qualification. Construction succeeded under it, but optimizing a model of this size would be refused. How the WLS licence was configured for Session 016 is not in the recovered records. Unresolved.

No code has been changed. A fix is pending Miles's approval.

### 17.21 Zero-similarity term-count fix

- [Miles, chat, 2026-11-14] Shown the confirmed root cause (§17.20) and the planned fix, Miles answered, verbatim: "Approve the fix".
- [Mac obs 2026-11-14] Changes to `admet/scripts/measure_split_model_construction.py`:
  - the expected quadratic-term count is now partitions × non-zero similarity pairs (Stage A on `split_input_v1`: 2 × 13,907,647 = 27,815,294); binary-variable and linear-constraint checks are unchanged;
  - the non-zero count is measured from the similarity array at run time;
  - the report records `similarity_pairs` (total, nonzero, zero) with a note that Gurobi does not store zero-coefficient objective terms and that zero-similarity pairs contribute 0 to L_cross in every assignment, plus the expected dimensions next to the observed ones.
- [Mac obs 2026-11-14] Test changes in `tests/test_measure_split_model_construction.py`: the dimension test now uses the real Stage-A counts (27,815,294 expected terms), and the tiny-fixture similarity array now contains one zero pair, so the Gurobi build test expects 10 stored terms (5 non-zero pairs × 2 partitions) rather than 12. That Gurobi test is skipped on the Mac (`gurobipy` not installed) and pytest is not installed in the gpu-dev1 Gurobi environment, so no test runner currently exercises the corrected Gurobi path; the gpu-dev1 construction re-run is the check.
- Reference bytes after the fix [Mac obs 2026-11-14; reference bytes, not proof of review]:
  - `admet/scripts/measure_split_model_construction.py`: 564 lines, SHA-256 `cfb6d08facb9e31d0652e665e4720705dd18cd1ff36653b2cff6a1182377d2e6` (supersedes `9e114432…` in §17.17 and §17.18).
  - `tests/test_measure_split_model_construction.py`: 303 lines, SHA-256 `61bad0eb85179a3dd92dae3715e45b5d2956f5d09b884ed086f9f7e3026f3226` (supersedes `109bef07…`).
  - `admet/data/splits/split_optimization_config.json`: unchanged, `f20f1d187e90c0bd33576396cc25f78e98d9e3ceae6f12e17c34a577d37f4fd4`.
- [Mac obs 2026-11-14] `python3 -m pytest tests/test_measure_split_model_construction.py tests/test_admet_build_split_input.py tests/test_admet_alias_grouping.py -q -rs` → `54 passed, 1 skipped in 2.53s` (skipped: the Gurobi build test). Mechanical only.
- D031 handling: recorded here as a fact, with no amendment to D031. The solver omits only exactly-zero objective terms (smallest non-zero S_ij 0.0028169014084507044, §17.20), the objective is mathematically unchanged, and the complete S_ij for all 14,832,181 pairs remains in the split-input artifact.
- Not done: Miles's review of the fixed bytes; re-staging the changed script; the construction re-run; the WLS licence issue (§17.20), still unresolved.

### 17.22 Fixed construction script reviewed; third staging bundle built

- [Miles, chat, 2026-11-15] Asked whether he had reviewed the fixed construction script (§17.21), Miles answered, verbatim: "Reviewed, stage it". This records his review of `admet/scripts/measure_split_model_construction.py` `cfb6d08facb9e31d0652e665e4720705dd18cd1ff36653b2cff6a1182377d2e6`.
- [Mac obs 2026-11-15] Third staging bundle built in the Mac scratch directory (not the repository): `session017_zero_fix.tar.gz` (6,361 bytes, SHA-256 `8b78cf97775fbcea502489b2c4088820817ffff074e7a138f97725eea5e58c41`) with `session017_zero_fix.SHA256SUMS.txt`, built with `--no-xattrs --no-mac-metadata` (no `LIBARCHIVE.xattr` headers). It unpacks to its own directory `session017_zero_fix/`, containing only `admet/scripts/measure_split_model_construction.py` (`cfb6d08f…`) and `FILES_zero_fix.sha256`. A Mac extraction check verified the file hash.
- Planned replacement on gpu-dev1 (given to Miles, not yet done): verify the tarball, extract to `session017_zero_fix/`, verify the file, keep the staged pre-fix script (`9e114432…`) as `measure_split_model_construction.py.pre_zero_fix`, then copy in the fixed script and verify its hash in place.
- Not done: transfer, replacement, construction re-run; WLS licence issue (§17.20) still unresolved.

### 17.23 Stage-A construction measurement completed (D034 §4 step 2)

[gpu-dev1, user-pasted] On 2026-11-15 Miles reported that the destination check passed and that, before the swap, `admet/artifacts/split_optimization` did not exist and the staged script hash was `9e114432ff6db8de75c7b21882f11ec3484da57554480a16a601c1e3464987ee`. He then swapped in the fixed script (the swap command's output was not pasted; the executed-code hash below confirms the fixed script ran) and re-ran the Stage-A construction measurement in `/mnt/nfs/CX900004_DS117/conda-envs/liggate-gurobi-qual` on `n4pu04`. Pasted result:

- `exit=0`. Report `admet/artifacts/split_optimization/stage_a_construction/construction_report.json`, SHA-256 `5701bc34512232dcf278e9a887423aefe7f8c2249e5f3ffd5f948bbdc8459fe0`; `sha256sum -c SHA256SUMS.txt` → `construction_report.json: OK`.
- Dimensions (observed = expected): binary variables 10,894; variables 10,894; linear constraints 5,459; quadratic terms 27,815,294.
- Similarity pairs: total 14,832,181; non-zero 13,907,647; zero 924,534.
- Construction time 109.53128896607086 s; peak RSS 2,272,206,848 bytes (about 2.12 GiB; cap 128 GiB, sample-based).
- `optimize_called: false`; `solution_count: 0`.
- Host: `n4pu04`; CPU `INTEL(R) XEON(R) GOLD 6548Y+`; 128 logical CPUs; total memory 540,498,747,392 bytes; platform `Linux-5.15.0-202-generic-x86_64-with-glibc2.35`.
- Runtime: Gurobi 14.0.0; NumPy 1.26.4; Python 3.12.16.
- Executed code (all under `/mnt/nfs/CX900004_DS117/sbdd-project/session017_split_input_builder/`): `measure_split_model_construction.py` `cfb6d08facb9e31d0652e665e4720705dd18cd1ff36653b2cff6a1182377d2e6`; `equivalence.py` `58c0df783e9222203e2be68ac28b28de5b803e40bae31689bfd8591a64aac133` (Session-016 qualified hash); `probe.py` `cc5af684e4c99eb9eeba84e4dc53155402dda5dbff4280b178526bc347ae4410`.

Notes (main Claude Code conversation):
- This completes D034 §4 step 2 for Stage A: the full Stage-A model fits easily in memory (about 2.1 GiB peak, against 503 GB on the host). The earlier rough extrapolation of about 10 GB was an overestimate.
- The run log tail was not pasted, so whether the restricted-licence line appeared again is not shown here. The WLS licence issue (§17.20) is unresolved. Under the restricted licence, optimizing a 10,894-variable model would be refused, so D034 §4 step 3 (calibration solve) is blocked until the WLS licence is active.
- Whether `measure_split_model_construction.py.pre_zero_fix` was kept on gpu-dev1 is not shown in the pasted output.
