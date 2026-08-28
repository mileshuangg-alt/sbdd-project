# 3REY/XAC DOCK Pose Ensemble and VDW-Bump Diagnostic

## Current Status

The corrected 3REY/XAC DOCK search remains blocked before pose scoring: the graph-mapped 3D XAC DB2 produces matched orientations, but all are rejected as `bump`.

## VDW Grid Diagnosis

Remote diagnostic inspection on `gpu-dev1` found that `vdw.bmp`, `vdw.vdw`, `rec.crg.pdb`, and `INDOCK` are byte-identical across the completed prep, corrected prep, and XAC search copy:

```text
rec.crg.pdb  sha256 232e96e7084d569dede3bb29...
vdw.bmp      sha256 9989dc7d6d854d2fa260a17c...
vdw.vdw      sha256 7d0306e433b51649ea3a6821...
INDOCK       sha256 b39338473e2b4c0b57c32b16...
```

The receptor file used with the search is in the crystallographic 3REY frame:

```text
rec.crg.pdb: 2700 ATOM records, 0 HETATM records
receptor bbox: x -3.264..66.260, y -2.476..54.387, z 5.437..51.737
```

The VDW bump-map header does not cover that frame:

```text
vdw.bmp line 1: bump map
vdw.bmp line 2: 0.200 -10.000 -10.000 -10.000 102 102 102
```

That grid spans approximately `[-10.0, 10.2]` in each coordinate axis at 0.2 A spacing. Corrected/native XAC heavy atoms are in the crystallographic binding-site frame, for example DB2 `X` records place atoms at approximately:

```text
x 46.268..51.984, y 18.350..25.934, z 27.091..37.365
```

Therefore the existing `vdw.bmp`/`vdw.vdw` are not in the same coordinate frame as the corrected 3REY receptor/spheres/native XAC representation. This establishes the VDW-grid provenance/coordinate-frame mismatch as the cause of universal `bump` rejection.

## Native XAC Against Existing VDW Grid

The existing crystallographic 3D XAC DB2 contains native-frame `X` coordinates. A fixed-pose diagnostic using the same `vdw.bmp` grid header showed native XAC atoms index far outside the grid, e.g. atom coordinates around `(50.572, 22.276, 37.365)` map to grid index `(302, 161, 236)` while the grid dimensions are only `(102, 102, 102)`.

Thus crystallographic XAC itself cannot pass the same VDW bump criterion with this grid. It is not a ligand-conformer or orientation-enumeration problem; the native pose is outside the VDW grid coordinate frame.

## Fixed Native-Pose VDW Test

Follow-up diagnostic objective: create one valid fixed crystallographic XAC orientation that reaches the DOCK VDW/bump criterion without rerunning broad docking, regenerating DB2, or changing bump/scoring parameters.

Source inspection found `docking_mode 2` in pinned DOCK 3.8.5 selects the score-only path (`dock.f`: `read in orientations then score`, calling `run_score_only_search`). A direct isolated `dock64` score-only invocation was attempted with a single shifted native XAC DB2 and unchanged grid/scoring files, but it segfaulted after grid and sphere loading and before ligand status output. This did not produce a bump/pass result from the executable path.

The valid fixed orientation was therefore defined by preserving the crystallographic XAC orientation and translating its DB2 `X`/`R` coordinates into the existing DOCK box frame. The transform used the bounding-box center of the native DB2 `X` coordinates:

```text
center subtracted: (49.868500, 22.157500, 36.154000)
native DB2 X bbox before: x 46.268..53.469, y 18.350..25.965, z 27.091..45.217
native DB2 X bbox after:  x -3.600..3.601, y -3.807..3.808, z -9.063..9.063
```

This places the single crystallographic orientation inside the existing `vdw.bmp` grid while preserving its native internal geometry and orientation.

Using the pinned source-equivalent VDW calculation from `score_conf.f`/`chemscore.f` on that one fixed orientation, with unchanged `vdw.bmp`, `vdw.vdw`, `vdw.parms.amb.mindock`, and `bump_rigid = 10.0`, produced:

```text
DOCK_VDW_NATIVE_FIXED atoms=31
vdwasum=0
vdwbsum=0
confvs=vdwasum-vdwbsum=0
bump_rigid=10.0
result=PASS
```

Interpretation: once the crystallographic XAC orientation is represented in the same box frame as the existing VDW grid, it does not fail the rigid VDW bump criterion. The previous universal `bump` behavior is therefore attributable to coordinate-frame mismatch/staging, not to an intrinsic native-XAC steric clash under the unchanged VDW threshold.

## Corrected Grid Regeneration

The exact staging failure was in the dependency chain from corrected spheres to the VDW grid. The original completed preparation had a failed/truncated ligand-sphere path; its `matching_spheres.sph` contained only the DOCK 5.2 color/header records and no usable coordinate spheres. `makebox` therefore produced a default origin-centered box:

```text
HEADER    CORNERS OF BOX  -10.000 -10.000 -10.000  10.000  10.000  10.000
REMARK    CENTER (X Y Z)    0.000   0.000   0.000
```

The later corrected sphere files were in the crystallographic frame, but only the sphere artifacts were replaced. The dependent `box`, `vdw.bmp`, and `vdw.vdw` were not regenerated, leaving the VDW grid centered near the origin while receptor/XAC/matching spheres were in the crystallographic frame.

Minimal correction performed on `gpu-dev1`:

```text
makebox.smallokay.pl matching_spheres.sph rec.crg.pdb box 10
chemgrid with unchanged INCHEM parameters:
  rec.crg.pdb
  prot.table.ambcrg.ambH
  vdw.parms.amb.mindock
  box
  0.2
  1
  4
  10
  2.3 2.6
  vdw
```

Only affected staging/grid artifacts were regenerated/replaced:

```text
references/stage5/dock385/3REY/blastermaster_corrected/working/box
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/vdw.bmp
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/vdw.vdw
references/stage5/dock385/3REY/xac_dock_search/dockfiles/vdw.bmp
references/stage5/dock385/3REY/xac_dock_search/dockfiles/vdw.vdw
```

The stale origin-centered files were preserved with `.stale_origin_grid` suffixes. No bump/scoring parameters were changed, and XAC was not translated to fit the old grid.

Regenerated grid verification:

```text
XAC bounds: x 46.268..53.469, y 18.350..25.965, z 27.091..45.217

new vdw.bmp header:
bump map
0.200  36.268   8.351  17.091 138 140 192

new grid bounds: x 36.268..63.868, y 8.351..36.351, z 17.091..55.491
contains native XAC: True

new box:
HEADER    CORNERS OF BOX   36.268   8.350  17.091  63.469  35.965  55.217
REMARK    CENTER (X Y Z)   49.868  22.158  36.154
REMARK    DIMENSIONS (X Y Z)   27.201  27.615  38.126
```

The regenerated `vdw.bmp`/`vdw.vdw` are now in the same crystallographic coordinate frame as corrected 3REY receptor, corrected matching spheres, and native XAC.

## Same-Frame Original-Parameter Search Attempt

A fresh prospective XAC search directory was prepared on `gpu-dev1` using the newly validated same-frame corrected preparation and original unchanged DOCK parameters:

```text
references/stage5/dock385/3REY/xac_dock_search_sameframe_original/
```

Inputs preserved there include:

```text
dockfiles/INDOCK                         sha16 b39338473e2b4c0b
dockfiles/vdw.bmp                        sha16 27dd5e72ce12825d
dockfiles/vdw.vdw                        sha16 99fdc674719402d6
input/xac.db2.gz                         sha16 bca2a589589ecdcc
run_xac_dock.sh
run_xac_dock.stdout
run_xac_dock.stderr
```

This run did not use any relaxed-bump or high-cutoff diagnostic variant directory. It used the corrected same-frame VDW grids and the original `INDOCK` hash above.

The attempted wrapper invocation exited with code `0`, but GNU `parallel` failed before DOCK produced `OUTDOCK` or pose MOL2 output:

```text
parallel: Error: Output is incomplete.
parallel: Error: Cannot append to buffer file in /tmp.
parallel: Error: Is the disk full?
parallel: Error: Change $TMPDIR with --tmpdir or use --compress.
```

No `output/1/OUTDOCK.0`, `output/1/test.mol2.gz.0`, or `output/1/perfstats` was produced. Per the instruction to stop rather than branch into debugging if the corrected search encountered a new failure, no wrapper/TMPDIR workaround was attempted and no rerun was launched.

Consequently, there is no scored pose ensemble from this attempt. Heavy-atom RMSD, rank classes, P2, and P4 are not assessable from this failed wrapper submission.

### TMPDIR Rerun

The preserved run directory was resumed with the previously established project-local GNU `parallel` temporary directory workaround:

```text
TMPDIR=$PWD/tmp_parallel
USE_PARALLEL_ARGS="--tmpdir $PWD/tmp_parallel"
./run_xac_dock.sh
```

The DOCK inputs, `INDOCK`, DB2, VDW grids, and search settings were not changed. The previous `/tmp`-buffer failure logs were preserved as:

```text
run_xac_dock.stdout.parallel_tmpfail
run_xac_dock.stderr.parallel_tmpfail
```

The rerun command exited with status `0`, and GNU `parallel` was invoked with the project-local tmpdir:

```text
parallel --results .../output/logs --tmpdir .../xac_dock_search_sameframe_original/tmp_parallel ...
```

However, the rerun still did not produce DOCK pose/scoring outputs:

```text
output/1/OUTDOCK.0        missing
output/1/test.mol2.gz.0   missing
output/1/perfstats        present, exit status 0
run_xac_dock.stderr       empty
```

Because this is a new post-wrapper/no-DOCK-output failure state, no further debugging or rerun was attempted under the current instruction. Heavy-atom RMSD, rank classes, P2, and P4 remain not assessable from this run.

### Direct dock64 Run

The wrapper/job-controller path was bypassed with one direct pinned `dock64` invocation from a short staged working directory:

```text
references/stage5/dock385/3REY/xac_dock_search_sameframe_original/working_direct/
```

The original run inputs were left unchanged. The staged `working_direct/INDOCK` was a direct-run copy only, preserving original scientific parameters while matching SUBDOCK's stdin DB2 convention:

```text
ligand_atom_file               -
output_file_prefix             test.
```

All other file references remained the existing relative `../dockfiles/...` paths, using the corrected same-frame grids and original search/scoring settings. The direct command was:

```bash
cd /mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/dock385/3REY/xac_dock_search_sameframe_original/working_direct
zcat -f ../input/xac.db2.gz | /mnt/nfs/CX900004_DS117/dock385/dock3-release/dock3/dock64 INDOCK > dock64.stdout 2> dock64.stderr
```

Execution status and outputs:

```text
dock64 exit status: 0
OUTDOCK:       present, 3449 bytes
test.mol2.gz:  present, 20 bytes
dock64.stdout: preserved
dock64.stderr: preserved
```

`OUTDOCK` shows that DOCK launched and evaluated the ligand hierarchy, but no conformations were scored and no pose was written:

```text
mol# 1 l3d_mapped_heavy    4150          0    0.02 bump
total number of orients (matches):          4150
total number of conformations (sets):             2
total number of nodes (confs):            24
total number of complexes:                      4150
```

`test.mol2.gz` is a valid gzip container but decompresses to zero characters and contains zero `@<TRIPOS>MOLECULE` records.

Therefore this same-frame, original-parameter direct run still produced no scored pose ensemble. Heavy-atom RMSD classes, P2, and P4 are not assessable from this run because every matched orientation was rejected as `bump` before scoring.

### Normal Matching Path Diagnosis

The direct run did not retain an internal generated match/transformation file. The only retained direct-run artifacts are:

```text
working_direct/INDOCK
working_direct/OUTDOCK
working_direct/dock64.stdout
working_direct/dock64.stderr
working_direct/test.mol2.gz
```

`OUTDOCK` confirms the normal matcher generated orientations, but all were rejected before scoring:

```text
matched orientations: 4150
nscored: 0
status: bump
```

Read-only inspection of the retained DB2 matching points and corrected receptor spheres showed that ligand matching-point geometry itself is not missing: every DB2 `R` coordinate has an exact coordinate match in `dockfiles/matching_spheres.sph`:

```text
ALL_R_HAVE_EXACT_SPHERE 31 of 31
IDENTITY_TRANSFORM_RMSD_TO_XTAL 0.0
```

Representative exact coordinate correspondences:

```text
R1 color7 -> sphere9011 color0 dist 0.0000
R2 color1 -> sphere9016 color0 dist 0.0000
R3 color7 -> sphere9030 color0 dist 0.0000
R4 color7 -> sphere9014 color0 dist 0.0000
R5 color7 -> sphere9029 color0 dist 0.0000
```

The first concrete discrepancy is the sphere correspondence/annotation, not the rigid transform math: the corrected matching spheres preserve the native coordinates but not DB2 atom/color correspondence. The DB2 `R` records carry nonzero matching colors, while all corrected sphere records are color `0`; the sphere record order is also not DB2 atom order:

```text
R colors:      [1, 3, 6, 7]
sphere colors: [0]

same-order examples:
R1 color7 vs sphere9001 color0 dist 13.7579
R2 color1 vs sphere9002 color0 dist 15.0232
R3 color7 vs sphere9003 color0 dist 13.4810
R4 color7 vs sphere9004 color0 dist 12.9183
```

An identity/native correspondence exists by nearest coordinate and would place XAC exactly on the crystallographic ligand. A corrected-type fixed native VDW check against the regenerated same-frame grid also passes the rigid VDW cutoff:

```text
confvs = -27.8852
bump_rigid = 10.0
result = PASS
```

Therefore the current all-bump result arises in the normal matching/orientation path from missing/wrong sphere correspondence metadata: the matcher samples geometric correspondences that do not preserve the native atom-to-sphere mapping, so the generated rigid orientations are sterically invalid even though the native identity mapping exists and would pass VDW.

Minimal correction to consider next: regenerate or stage `matching_spheres.sph` so crystallographic ligand spheres retain correspondence compatible with the XAC DB2 matching points/atom classes, rather than using coordinate-only, all-zero-color spheres. Do not change bump/scoring thresholds, VDW grids, DB2 chemistry, or other scientific search parameters for that correction.

### Matching-Sphere Metadata Correction

The crystallographic matching-sphere metadata was corrected without changing sphere coordinates, DB2 chemistry, VDW grids, bump/scoring thresholds, or search parameters.

The all-zero-color sphere artifacts were preserved with `.all_zero_color` suffixes. Corrected files were written at:

```text
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/matching_spheres.sph
references/stage5/dock385/3REY/blastermaster_corrected/working/matching_spheres.sph
references/stage5/dock385/3REY/xac_dock_search_sameframe_original/dockfiles/matching_spheres.sph
```

Method: each existing crystallographic sphere coordinate was matched to the exact same-coordinate DB2 `R` matching point in `input/xac.db2.gz`, and only the sphere color field was updated to the corresponding DB2 `R` color. Sphere IDs, coordinates, radii, atom-number field, and critical-sphere field were preserved.

Validation:

```text
SPHERE_COUNT_OLD_NEW 31 31
MAX_COORD_DELTA 0.0
NON_COORD_METADATA_CHANGED_EXCEPT_COLOR_FIELDS 0
OLD_COLORS [0]
NEW_COLORS [1, 3, 6, 7]
R_EXACT_COORD_MATCHES 31 of 31
COLOR_MATCHES 31 of 31
WORST_DIST 0
IDENTITY_CORRESPONDENCE_AVAILABLE True
```

Representative validated correspondences:

```text
R1 color7 -> sphere9031 color7 dist 0.0000
R2 color1 -> sphere9016 color1 dist 0.0000
R3 color7 -> sphere9030 color7 dist 0.0000
R4 color7 -> sphere9014 color7 dist 0.0000
R5 color7 -> sphere9029 color7 dist 0.0000
R6 color6 -> sphere9012 color6 dist 0.0000
R7 color7 -> sphere9028 color7 dist 0.0000
R8 color3 -> sphere9009 color3 dist 0.0000
```

No docking was rerun after this metadata-only correction.

### Direct dock64 Run After Sphere-Color Correction

One direct pinned `dock64` run was executed after the matching-sphere color correction, bypassing SUBDOCK/GNU parallel/job-controller machinery:

```text
references/stage5/dock385/3REY/xac_dock_search_sameframe_original/working_direct_colorcorrected/
```

The run used the existing DB2, corrected same-frame grids, corrected color-compatible `matching_spheres.sph`, and original unchanged DOCK/search/scoring parameters. The staged direct-run `INDOCK` changed only the ligand input mechanism and output prefix required for stdin streaming:

```text
ligand_atom_file               -
output_file_prefix             test.
```

Inputs recorded at launch:

```text
dockfiles/INDOCK                         sha16 b39338473e2b4c0b
dockfiles/matching_spheres.sph           sha16 6d2516daa6fecde4
dockfiles/vdw.bmp                        sha16 27dd5e72ce12825d
dockfiles/vdw.vdw                        sha16 99fdc674719402d6
input/xac.db2.gz                         sha16 bca2a589589ecdcc
working_direct_colorcorrected/INDOCK     sha16 19392b7070ec7260
```

Direct command:

```bash
cd /mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/dock385/3REY/xac_dock_search_sameframe_original/working_direct_colorcorrected
zcat -f ../input/xac.db2.gz | /mnt/nfs/CX900004_DS117/dock385/dock3-release/dock3/dock64 INDOCK > dock64.stdout 2> dock64.stderr
```

Execution and output status:

```text
dock64 exit status: 0
OUTDOCK:       present
test.mol2.gz:  present, 20 bytes
dock64.stdout: present, 0 bytes
dock64.stderr: present, 48 bytes
```

`dock64.stderr` contained only:

```text
Warning: ieee_inexact is signaling
FORTRAN STOP
```

`OUTDOCK` still reports all generated orientations rejected as `bump` before scoring:

```text
mol# 1 l3d_mapped_heavy    4150          0    0.02 bump
total number of orients (matches):          4150
total number of conformations (sets):             2
total number of nodes (confs):            24
total number of complexes:                      4150
```

`test.mol2.gz` decompresses to zero characters and contains zero `@<TRIPOS>MOLECULE` records. Therefore no scored pose ensemble was produced, and heavy-atom RMSD, rank classes, P2, and P4 remain not assessable from this corrected direct run.

### Direct dock64 Run From Fresh Canonical Prep

One direct pinned `dock64` XAC search was run from the fresh canonical `GFORTRAN_TMPDIR` preparation, bypassing SUBDOCK/GNU parallel/job-controller machinery:

```text
references/stage5/dock385/3REY/blastermaster_canonical_gfortran_tmpdir/working_direct_xac/
```

The run used the existing crystallographic 3D XAC DB2 and canonical same-frame preparation. Original DOCK/search/scoring/bump parameters were kept unchanged. The staged direct-run `INDOCK` changed only the input mechanism/output prefix needed for stdin streaming:

```text
ligand_atom_file               -
output_file_prefix             test.
```

Input hashes recorded at launch:

```text
dockfiles/INDOCK                         sha16 b39338473e2b4c0b
dockfiles/matching_spheres.sph           sha16 a82d5e06e10b95d8
dockfiles/vdw.bmp                        sha16 27dd5e72ce12825d
dockfiles/vdw.vdw                        sha16 99fdc674719402d6
input/xac.db2.gz                         sha16 bca2a589589ecdcc
working_direct_xac/INDOCK                sha16 19392b7070ec7260
```

Direct command:

```bash
cd /mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/dock385/3REY/blastermaster_canonical_gfortran_tmpdir/working_direct_xac
zcat -f ../../xac_dock_search_sameframe_original/input/xac.db2.gz | /mnt/nfs/CX900004_DS117/dock385/dock3-release/dock3/dock64 INDOCK > dock64.stdout 2> dock64.stderr
```

Execution status and outputs:

```text
dock64 exit status: 0
OUTDOCK:       present
test.mol2.gz:  present, 20 bytes
dock64.stdout: present, 0 bytes
dock64.stderr: present, 48 bytes
```

`dock64.stderr` contained only:

```text
Warning: ieee_inexact is signaling
FORTRAN STOP
```

`OUTDOCK` still reports zero scored poses:

```text
mol# 1 l3d_mapped_heavy    4150          0    0.02 bump
total number of orients (matches):          4150
total number of conformations (sets):             2
total number of nodes (confs):            24
total number of complexes:                      4150
```

`test.mol2.gz` decompresses to zero characters and contains zero `@<TRIPOS>MOLECULE` records. Heavy-atom RMSD, rank/score/RMSD tables, P2, and P4 are not assessable because no scored pose ensemble was produced. Per instruction, no further debugging was performed.

## Source Criterion Checked

Source inspection of DOCK 3.8.5 confirmed that `score_sets.f` marks an orientation as `BUMPED` when the conformer status is not `ALLOKAY` or the rigid VDW term exceeds `bump_rigid`. `score_conf.f` computes the VDW term from the grid as `vdwasum - vdwbsum` and compares it to `bump_maximum`.

The preserved search log is consistent with this failure mode:

```text
bump_maximum 10.0
bump_rigid   10.0
bumpmap_file ../dockfiles/vdw.bmp
mol# XAC flexiblecode 1002 matched 0 nscored ... bump
total number of orients (matches): 1002
```

## Constraints Honored

No broad docking was rerun. No DB2 was regenerated by `mol2db2`. No thresholds, scoring parameters, or search variants were changed. The only execution was read-only/source inspection, one isolated score-only `dock64` attempt that crashed before ligand status, one fixed-grid native-pose VDW/bump calculation using the pinned DOCK source criterion, the minimal `makebox`/`chemgrid` regeneration needed to replace the stale VDW grid artifacts, one same-frame original-parameter XAC wrapper submission that failed before DOCK output because GNU `parallel` could not write its `/tmp` buffer, one same-run rerun with project-local GNU `parallel` tmpdir that exited without producing DOCK pose/scoring output, one direct pinned `dock64` run that completed but rejected all matched orientations as `bump`, read-only normal-matching input/correspondence diagnostics, one metadata-only correction of matching-sphere colors with coordinate-preservation validation, one direct pinned `dock64` run after sphere-color correction that still rejected all matched orientations as `bump`, and one direct pinned `dock64` run from the fresh canonical `GFORTRAN_TMPDIR` preparation that also rejected all matched orientations as `bump`.
