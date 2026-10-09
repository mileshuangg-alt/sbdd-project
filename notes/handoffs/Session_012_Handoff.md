# Session 012 Handoff --- Stage 5 Begins After Session 011 Validation Closure

**Date prepared:** 2026-09-06\
**Purpose:** Start Session 012 without repeating Session 011 setup,
qualification, artifact discovery, receptor preparation, or validation
work.

## 1. Critical boundary

Session 011 completed the pre-Stage-5 A2A ProLIF
discrimination-validation program.

The next chat should **begin Stage 5**. Do not reopen Session 011
validation unless a retained artifact is demonstrably corrupt or missing
in a way that blocks Stage 5.

The Session 011 result must be stated at its true size:

> **Molecule-level discrimination was demonstrated for one
> experimentally established human-A2A-negative molecule, P3-002
> N6-cyclooctyladenosine, represented under two independent docking
> routes (DOCK and rDock). Neither pose reproduced the frozen A2A
> recognition pattern. This does not establish pose sensitivity or
> general discrimination across negative chemotypes.**

Do not inflate this into a claim of general negative-chemotype
discrimination or pose sensitivity.

------------------------------------------------------------------------

## 2. What Session 011 achieved

### 2.1 Second unrelated negative pose-generation lineage

rDock was selected and qualified as the second unrelated pose-generation
lineage for the frozen negative panel.

Frozen source provenance:

``` text
rDock tag:    v24.04.204-legacy
Git commit:   3c029ecc65898166b234716b1609fb46212cbc6d
Source path:  /mnt/nfs/CX900004_DS117/src/rdock
```

Observed executable/library metadata:

``` text
Executable: rbdock / rbcavity v26.09-alpha
Library:    libRbt.so/26.09/alpha
```

This metadata discrepancy was recorded rather than modified. Git
provenance plus passing bundled tests is the implementation provenance.

Bundled rDock tests passed:

``` text
[OK] coordinates match
[OK] scores match
```

### 2.2 rDock build/runtime environment

Dedicated server environment:

``` text
/mnt/nfs/CX900004_DS117/conda-envs/sbdd-rdock
```

Host used during production:

``` text
n4pu04
```

Relevant dependencies in the isolated environment:

-   popt
-   cppunit
-   tcsh

Compiler/build environment:

-   Ubuntu x86_64
-   GCC/G++ 11.4.0
-   Make
-   Git 2.34.1

The initial build failed because host `/tmp` was full. Compiler
temporaries were redirected to:

``` text
/mnt/nfs/CX900004_DS117/tmp/rdock-build
```

No source or scientific parameters were changed.

If a fresh shell ever needs the already-built rDock environment, restore
only:

``` bash
conda activate "$HOME/conda-envs/sbdd-rdock"

export RBT_ROOT="$HOME/src/rdock"
export PATH="$RBT_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$RBT_ROOT/lib:$CONDA_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

export TMPDIR="$HOME/tmp/rdock-build"
export TMP="$TMPDIR"
export TEMP="$TMPDIR"
```

**Do not rebuild or rerun qualification tests unless there is evidence
that the installation changed.**

### 2.3 Frozen rDock production protocol

The unmodified standard protocol was used:

``` text
$HOME/src/rdock/data/scripts/dock.prm
Title: Free docking (indexed VDW)
```

Cavity mapper settings:

``` text
SITE_MAPPER  RbtLigandSiteMapper
RADIUS       6.0
SMALL_SPHERE 1.0
MIN_VOLUME   100
MAX_CAVITIES 1
VOL_INCR     0.0
GRIDSTEP     0.5
```

Successful production cavity:

``` text
Total volume: 2139.75 A^3
Cavity count: 1
Center:       (50.2752, 23.4218, 37.3767)
Extent:       (18.5, 17.5, 28.5)
```

The first `rbcavity` failure was only a working-directory/relative-path
error. The corrected invocation from the Session-011 working directory
succeeded. No scientific parameters were changed.

### 2.4 Receptor translation

The qualified 3REY receptor PDB-to-MOL2 translation was completed before
production and passed the approved audit.

Audit dimensions:

1.  atom count;
2.  coordinates;
3.  explicit hydrogens.

Result:

``` text
PASS
```

Receptor partial charges were explicitly outside this conversion audit
because rDock does not use receptor partial charges in the relevant
scoring functions.

Do not redo this conversion/audit.

### 2.5 Frozen experimental negative

The Session-011 rDock ligand was:

``` text
P3-002 — N6-cyclooctyladenosine
PubChem CID: 54333857
ChEMBL:      CHEMBL2113424
InChIKey:    TUBLKCBQFVQEOG-SCFUHWHPSA-N
hA2A Ki:     >10,000 nM
hA1 Ki:      6.4 +/- 1.4 nM
formal charge: 0
```

The existing frozen neutral SDF was used. No reprotonation, recharge, or
new ligand identity/state was introduced.

### 2.6 Single production rDock run

Working directory:

``` text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/rdock_session011
```

Production run used:

``` text
input:    P3-002_N6-cyclooctyladenosine.sd
receptor: 3REY_rdock.prm
protocol: $HOME/src/rdock/data/scripts/dock.prm
runs:     1
seed:     20260906
```

The run completed with `END OF RUN` and wrote one SD record:

``` text
P3-002_N6-cyclooctyladenosine_rdock.sd
```

Observed rDock score:

``` text
SCORE = -10.5896
SCORE.INTER = -10.8878
SCORE.INTRA = 0.109473
```

The one-record output is an observed result of the single production
run. Do not reinterpret `-n 1` as a preregistered requirement to produce
exactly one pose.

### 2.7 Frozen PoseBusters P1 result

PoseBusters environment on the Mac:

``` text
Conda environment: sbdd-eval
PoseBusters:       0.6.5
```

Shipped configuration:

``` text
/opt/homebrew/Caskroom/miniforge/base/envs/sbdd-eval/lib/python3.12/site-packages/posebusters/config/dock.yml
```

Frozen procedure:

-   PoseBusters 0.6.5;
-   shipped `dock.yml`;
-   original generated coordinates;
-   no repair/minimization;
-   `mol_true=None`;
-   qualified 3REY receptor as `mol_cond`;
-   `full_report=True`.

The rDock `.sd` output was copied byte-for-byte to a `.sdf` filename
solely because PoseBusters 0.6.5 rejects the `.sd` extension. The
generated coordinates were not changed.

Observed rDock P1 result:

``` text
P1: PASS
smallest_distance_protein = 2.607812 A
num_pairwise_clashes_protein = 0
volume_overlap_protein = 0.009972
```

Do not rerun P1 merely to recreate the dataframe. The archival bundle
contains a result record explicitly labeled as a transcription of the
completed terminal run.

### 2.8 Frozen negative panel

The panel was frozen before ProLIF exposure.

#### DOCK representative

``` text
Candidate: P3-002 N6-cyclooctyladenosine
Generator: DOCK 3.8.5 lineage
Pose:      rank 1
Score:     -27.96
P1:        PASS
Protein clashes: 0
```

Authoritative representative:

``` text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/p3_candidates/P3-002_N6-cyclooctyladenosine/p1_posebusters_dock/poses/rank_01.mol2
```

SHA-256:

``` text
a232d950008861f3ee87d73e880b9e1627afa06a47182b3a1a249f4cf61eaddf
```

#### rDock representative

``` text
Candidate: P3-002 N6-cyclooctyladenosine
Generator: rDock
Pose:      sole production pose
Score:     -10.5896
P1:        PASS
Protein clashes: 0
```

Authoritative representative:

``` text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/rdock_session011/P3-002_N6-cyclooctyladenosine_rdock.sd
```

SHA-256:

``` text
731661a5096209b80a56f6ecd48d520c69c834b949b3d456bd0101a5de48f81a
```

Additional rDock provenance hashes:

``` text
04cf1e3c931a3f8039b0791da6b477dfc11f1f6ce863df6173ec6b0eab9d8fc7
P3-002_N6-cyclooctyladenosine.sd

f5141e07c86292518d2df30e88e2815ca3d518cbd0ee527e2de8436341b1139c
3REY_rdock.prm

8ab3ac4b1d8e0f383e1026dc62fbeff33d760c9f9c8eb31ee45ee08121f25d20
3REY_rec_for_rdock.mol2

2be99a4a0659c986c9ec4e9789b36ed8b91d82169acd288b433dd8a3efeaf4ef
XAC_reference.sd
```

Panel-freeze manifest:

``` text
negative_panel_freeze_session011.txt
SHA-256:
7dcd620b4f4ad428c2375aff6adb308ef23dfb6ba5e069a6dbcdbe7a8b518bef
```

### 2.9 Historical ProLIF reader recovered

The actual historical proof-of-life implementation was recovered from:

``` text
scripts/stage5/test_native_reader_controls.py
```

The frozen receptor route is:

``` text
validated restored receptor PQR
-> make_mdanalysis_compatible_pqr()
-> MDAnalysis
-> inferred topology
-> deterministic H-H / hydrogen-parent cleanup
-> plf.Molecule.from_mda()
-> plf.Fingerprint()
-> Fingerprint.generate(..., metadata=True)
```

The key callable is:

``` python
load_protein(path)
```

The frozen reader uses default:

``` python
plf.Fingerprint()
```

and:

``` python
fingerprint.generate(
    ligand,
    protein,
    metadata=True,
)
```

Do not replace this with the experimental direct-RDKit receptor route
for the frozen A2A POD/Stage-5 implementation.

### 2.10 Historical positive proof of life remains established

The native ProLIF proof of life was completed previously:

``` text
3REY / XAC:          PASS
5OLH / Vipadenant:   PASS
5OLO / Tozadenant:   PASS

Native reader proof of life: 3/3 PASS
```

For 3REY/XAC, the frozen result was:

``` text
Phe168:
- Hydrophobic
- VdWContact

Asn253:
- HBAcceptor
- VdWContact
```

The original prepared XAC SDF expected by the historical script:

``` text
3REY_XAC_native_pH7.4_restored.sdf
```

was not recovered from the retained filesystem during Session 011. This
is a preservation defect. It was **not regenerated**.

This missing historical positive input does not block the completed
blind POD because the POD used the original historical receptor/reader
route and the already-frozen negative poses.

### 2.11 Receptor-artifact comparison / abandoned RDKit branch

A temporary question arose about using `3REY_rec.crg.pdb` directly
through RDKit. Before any blind negative read, the historical PQR and
`rec.crg.pdb` receptor artifacts were compared by residue number + atom
name.

Observed:

``` text
PQR heavy atoms:     2251
PDB heavy atoms:     2250
Matched heavy atoms: 2250
Only in PQR:         SER305 OXT
Only in PDB:         none

Mean coordinate deviation: 0.006478297 A
Maximum deviation:         2.312129322 A
Maximum-deviation atom:    residue 75 CD2
```

Because the artifacts were not coordinate-identical, the proposed
direct-RDKit equivalence branch would have required a positive
side-by-side. The missing historical XAC SDF blocked that optional
equivalence test.

The direct-RDKit route was therefore **not used for the blind POD**.

Do not reopen this branch for Stage 5 unless a future documented
decision explicitly requires it.

### 2.12 Blind frozen-ProLIF POD result

The blind POD used the **unchanged historical ProLIF 2.2.0 route** with:

``` text
receptor:
references/stage5/native_complexes/3REY/3REY_receptor_pH7.4_restored.pqr

reader:
scripts/stage5/test_native_reader_controls.py
load_protein()
plf.Molecule.from_mda()
plf.Fingerprint().generate(..., metadata=True)
```

Frozen A2A recognition definition:

``` text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

VdWContact is characterization only and does not satisfy the required
Phe168 feature.

A residue-75 guard was applied because of the receptor-artifact
deviation. Neither negative contacted residue 75.

#### DOCK negative

``` text
Phe168: ['VdWContact']
Asn253: []
Residue 75 contacts: NONE
Frozen A2A recognition pattern: NOT REPRODUCED
```

#### rDock negative

``` text
Phe168: []
Asn253: []
Residue 75 contacts: NONE
Frozen A2A recognition pattern: NOT REPRODUCED
```

Frozen claim:

> **Molecule-level discrimination was demonstrated for one
> experimentally established human-A2A-negative molecule represented
> under two docking routes. No pose-sensitivity claim is made. No
> general negative-chemotype discrimination claim is made.**

------------------------------------------------------------------------

## 3. Frozen Session-011 scientific archive

The scientific archive was assembled separately from the session-log
system.

Local Git-repository path:

``` text
references/stage5/negative_panel/session011_frozen_bundle/
```

It contains:

``` text
inputs/
panel/
provenance/
reader/
results/
SHA256SUMS.txt
```

The bundle preserves:

-   DOCK and rDock frozen panel representatives;
-   relevant P3-002 inputs;
-   rDock receptor/parameter/reference inputs;
-   historical restored 3REY PQR used by the blind ProLIF reader;
-   `test_native_reader_controls.py`;
-   panel-freeze provenance;
-   transcribed completed rDock P1 result;
-   transcribed completed blind ProLIF POD result;
-   SHA-256 inventory.

The result text files are explicitly labeled as transcriptions of
completed terminal runs. PoseBusters and ProLIF were **not rerun**
merely to create archival result files.

Bundle checksum manifest hash:

``` text
SHA256SUMS.txt
SHA-256:
b209600b19265b6cdd664c6bbb2e7132bedc66d10b17200df1776a8a32493639
```

The empty `rdock/` directory seen locally is a leftover from an earlier
draft and is not tracked by Git. Do not alter the hashed bundle merely
to remove an empty directory.

------------------------------------------------------------------------

## 4. Documentation completed in Session 011

The local Git repository is:

``` text
/Users/mileshuang/Desktop/sbdd-project
```

The documentation system uses:

``` text
notes/Session_011.md
notes/project_log.md
notes/Decisions.md
```

Session 011 was added to the project log.

D011 was added to `notes/Decisions.md` with the bounded discrimination
claim.

Do not create root-level duplicates such as:

``` text
./Session_011.md
./project_log.md
./Decisions.md
```

The correct tracked locations are under `notes/`.

------------------------------------------------------------------------

## 5. Git state at Session-011 close

### Local repository

``` text
/Users/mileshuang/Desktop/sbdd-project
```

Local branch after integrating the UCSF-side project-log commit:

``` text
main
HEAD = 2774032
```

Recent history:

``` text
2774032 Merge remote-tracking branch 'origin/main'
eade3c1 Close Session 011 blind ProLIF validation
9ec8cef Update project_log.md
```

### Personal GitHub remote

Configured remote:

``` text
github  https://github.com/mileshuangg-alt/sbdd-project.git
```

The merged Session-011 history was successfully pushed to personal
GitHub:

``` text
github/main = 2774032
```

### UCSF remote

Original/normal UCSF URL:

``` text
https://git.ucsf.edu/Miles-Huang/sbdd-project.git
```

During troubleshooting it was temporarily changed to SSH and then
restored to HTTPS. The HTTPS push returned:

``` text
Password authentication is not available for Git operations.
You must use a personal access token or SSH key.
HTTP 403
```

The existing Mac SSH key is:

``` text
~/.ssh/id_ed25519
```

Direct SSH authentication test succeeded:

``` text
ssh -T git@git.ucsf.edu

Hi Miles-Huang! You've successfully authenticated, but GitHub does not provide shell access.
```

At the last confirmed point in this chat, the user had **not yet
reported a successful UCSF push of `2774032`**.

Therefore, unless the user completed it after this handoff was written:

``` text
local main:   2774032
github/main:  2774032
origin/main:  last confirmed at 9ec8cef
```

Do not assume UCSF is synchronized without checking.

If UCSF mirroring is revisited, do not redo commits, merges, or
Session-011 work. The desired history is already local and on personal
GitHub.

### Intentionally untracked local artifacts

At the last `git status --short`, these remained intentionally
unstaged/untracked:

``` text
local_dock_debug/

references/stage5/dock385/3REY/xac_canonical_db2/amsol_runtime/
  compat-libf2c-34-3.4.6-32.el7.x86_64.rpm
  extracted/
```

Do not delete these merely to obtain a clean Git status. The project
preservation rule remains in force.

------------------------------------------------------------------------

## 6. Current Mac evaluation environment

For PoseBusters / ProLIF evaluation:

``` text
Conda environment: sbdd-eval
```

Confirmed versions:

``` text
PoseBusters 0.6.5
ProLIF      2.2.0
```

PoseBusters shipped `dock.yml`:

``` text
/opt/homebrew/Caskroom/miniforge/base/envs/sbdd-eval/lib/python3.12/site-packages/posebusters/config/dock.yml
```

Relevant local Session-011 working directory used during validation:

``` text
~/sbdd-project/session011/rdock_receptor
```

This is **not the Git repository**.

The actual local Git repository is:

``` text
~/Desktop/sbdd-project
```

Do not confuse these paths again.

------------------------------------------------------------------------

## 7. Current server environment

Established SSH route from the Mac:

``` bash
ssh mhuang8@facbastp9004.fac.ucsf.edu
ssh gpu-dev1.ic.fac.ucsf.edu
```

The rDock production work was performed on:

``` text
n4pu04
```

Server project/work path:

``` text
/mnt/nfs/CX900004_DS117/sbdd-project
```

rDock Session-011 production directory:

``` text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/rdock_session011
```

rDock frozen bundle source directory:

``` text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/session011_frozen_bundle
```

Do not redo environment setup, rDock build, rDock tests, receptor
conversion, cavity generation, production docking, PoseBusters P1, panel
freeze, or blind ProLIF POD.

------------------------------------------------------------------------

## 8. Decisions now in force

### D011 claim boundary

Session 011 supports:

``` text
one experimentally established A2A-negative molecule
+
two independent docking routes (DOCK and rDock)
+
both fail frozen A2A recognition pattern
=
bounded molecule-level discrimination evidence
```

It does **not** support:

``` text
pose sensitivity
general negative-chemotype discrimination
universal ProLIF specificity
universal target-transfer claims
```

### Stage-5 reader

ProLIF 2.2.0 remains the frozen interaction reader.

The historical `load_protein()` route remains the frozen A2A
implementation.

### Generator parity

DiffSBDD and FLOWR must continue through the identical
generator-independent evaluation pathway. FLOWR remains reserved for the
later comparator arm.

### Witness work

PLIP or another qualified independent witness remains
**post-validation** and separate from the frozen ProLIF verdict. Do not
insert witness qualification ahead of Stage 5 unless the frozen
framework/session plan explicitly requires it.

### Validation-requirement rule

Before adding any new validation requirement:

1.  trace it to the frozen framework/session plan;
2.  identify the evidence requiring it;
3.  if it is not already frozen, label it as a proposed new requirement;
4.  obtain user approval before treating it as mandatory.

Do not create another validation rabbit hole.

### Alternatives-pass rule

Before adopting a new model, package, scoring function, reader,
generator, or comparable component, perform the literature-backed
alternatives pass first:

-   enumerate serious cited alternatives;
-   state what each enables;
-   assess compute/dependencies/scope;
-   trace rejection to an existing frozen requirement;
-   label alternatives `unrejected` if no documented rejection exists.

Do not defend a candidate by default.

------------------------------------------------------------------------

## 9. Things Session 012 must NOT reopen

-   Graves/DOCK geometric-decoy ladder.
-   XAC/3REY or 9XT/5OLH DOCK tuning.
-   rDock qualification/build/tests.
-   rDock receptor conversion/audit.
-   rDock cavity parameters.
-   rDock production run.
-   rDock P1 qualification.
-   negative-panel membership.
-   ProLIF blindness/panel freeze.
-   blind negative POD.
-   direct-RDKit receptor equivalence branch.
-   historical XAC SDF regeneration.
-   Vina as independent generator family #2.
-   FLOWR as a validation negative generator.
-   ProLIF parameters.
-   frozen A2A recognition definition.
-   broadening D011 beyond its one-molecule/two-route evidence scope.

------------------------------------------------------------------------

## 10. Session 012 starting point

**Session 011 validation is scientifically complete.**

Session 012 should begin at **Stage 5**, using the now-frozen A2A
interaction framework and reader.

Before proposing Stage-5 implementation work, first inspect the frozen
Stage-5 framework and existing Stage-5 evaluator/artifacts. Do not
assume that Session 012 requires a new model, reader, scoring function,
receptor preparation, or validation experiment.

The first Session-012 question should be:

> **Given the now-completed Session-011 bounded discrimination
> validation, what exact Stage-5 operation is authorized by the frozen
> D008/D011 framework, and what existing evaluator/artifacts already
> implement it?**

Use the retained session logs, decisions, project log, and Git-tracked
artifacts before asking the user to run exploratory commands.

------------------------------------------------------------------------

## 11. Preservation rule

Preserve all Session-011 artifacts, including failed branches and
implementation diagnostics, until the relevant stage is finalized and
frozen.

In particular, do not delete:

-   rDock build/runtime artifacts merely because production is complete;
-   the first path-only `rbcavity` failure record;
-   receptor conversion/audit artifacts;
-   P1 artifacts;
-   panel-freeze artifacts;
-   blind POD records;
-   the frozen scientific bundle;
-   the intentionally untracked DOCK/AMSOL runtime artifacts;
-   documentation of the missing historical XAC proof-of-life SDF.

The missing historical XAC SDF must remain documented as a retention
defect. Do not silently regenerate it and represent the regenerated file
as the historical artifact.
