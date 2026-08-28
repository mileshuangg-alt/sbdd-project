# OpenCode Handoff — Stage 5 DOCK 3.8.5 3REY/XAC

## Current Objective

Continue Stage 5 DOCK 3.8.5 work for the 3REY/XAC adversarial-decoy line. The immediate goal is to complete a single XAC DOCK search using the corrected 3REY DOCK preparation, then report the full pose ensemble with DOCK scores, rank, and symmetry-aware heavy-atom RMSD to crystallographic XAC.

Do not run any decoy generation or panel work yet.

## Latest VDW-Bump Diagnosis

The all-orientations-`bump` blocker is caused by a VDW-grid coordinate-frame mismatch, not by XAC DB2 conformer generation or orientation enumeration.

Remote `gpu-dev1` inspection found `rec.crg.pdb`, `vdw.bmp`, `vdw.vdw`, and `INDOCK` are byte-identical across `blastermaster_completed`, `blastermaster_corrected`, and `xac_dock_search`. The receptor is in crystallographic 3REY coordinates (`rec.crg.pdb` bbox approximately x `-3.264..66.260`, y `-2.476..54.387`, z `5.437..51.737`), but `vdw.bmp` has header:

```text
bump map
0.200 -10.000 -10.000 -10.000 102 102 102
```

That grid covers only approximately `[-10.0, 10.2]` on each axis. Native/corrected XAC heavy atoms are around x `46.268..51.984`, y `18.350..25.934`, z `27.091..37.365`, so crystallographic XAC itself is outside the existing VDW grid. A fixed-grid diagnostic mapped native XAC atom coordinates to out-of-range grid indices such as `(302, 161, 236)` for a `102^3` grid. Therefore native XAC would fail the same VDW bump criterion with the existing grid.

Do not rerun docking, regenerate DB2, alter bump thresholds, or create search variants to work around this. The next scientific/infrastructure decision is how to correct the receptor/grid preparation provenance while preserving the frozen failed artifacts as evidence.

## Corrected VDW Grid Regeneration

The exact staging failure has been established and corrected. The original completed prep had no usable matching-sphere coordinate records because of the earlier `pdbtosph` failure. `makebox` therefore generated a default origin-centered box (`-10..10`, center `0,0,0`), and `chemgrid` generated `vdw.bmp`/`vdw.vdw` around that box. Later, the corrected matching spheres were substituted into `blastermaster_corrected`, but dependent `box`, `vdw.bmp`, and `vdw.vdw` were not regenerated.

Minimal fix performed on `gpu-dev1`:

```text
makebox.smallokay.pl matching_spheres.sph rec.crg.pdb box 10
chemgrid with unchanged INCHEM parameters and unchanged vdw.parms.amb.mindock
```

Only affected files were replaced, with stale copies preserved using `.stale_origin_grid` suffixes:

```text
references/stage5/dock385/3REY/blastermaster_corrected/working/box
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/vdw.bmp
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/vdw.vdw
references/stage5/dock385/3REY/xac_dock_search/dockfiles/vdw.bmp
references/stage5/dock385/3REY/xac_dock_search/dockfiles/vdw.vdw
```

Verification:

```text
XAC bounds: x 46.268..53.469, y 18.350..25.965, z 27.091..45.217
new vdw.bmp: 0.200  36.268   8.351  17.091 138 140 192
new grid bounds: x 36.268..63.868, y 8.351..36.351, z 17.091..55.491
contains native XAC: True
```

No docking was rerun, no DB2 was regenerated, no bump/scoring parameters were changed, and XAC was not translated to fit the old grid. Stop here unless the next task explicitly asks to run a new single XAC DOCK search using the corrected grids.

## Matching-Sphere Metadata Correction

The normal matching/orientation blocker after same-frame grid correction was traced to `matching_spheres.sph` metadata. The corrected sphere file had exact crystallographic coordinates, but all sphere colors were `0`, while the existing XAC DB2 `R` matching points use colors `[1, 3, 6, 7]`. The DB2 `R` points matched sphere coordinates exactly, but without compatible colors the native identity correspondence was unavailable to normal colored matching.

Metadata-only correction performed on `gpu-dev1`:

```text
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/matching_spheres.sph
references/stage5/dock385/3REY/blastermaster_corrected/working/matching_spheres.sph
references/stage5/dock385/3REY/xac_dock_search_sameframe_original/dockfiles/matching_spheres.sph
```

The all-zero-color artifacts were preserved beside each file with `.all_zero_color` suffixes. Only the sphere color field was updated by exact coordinate matching to `input/xac.db2.gz` DB2 `R` records. Sphere IDs, coordinates, radii, atom-number field, and critical-sphere field were preserved.

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

No docking was rerun after this correction. The next safe step, if requested, is a single direct or wrapper-run XAC search using the corrected same-frame grids and color-compatible matching spheres, without changing DB2, grids, thresholds, or other scientific parameters.

## pdbtosph Runtime Diagnosis

The original `pdbtosph` line-40 failure has been resolved diagnostically. The XAC crystallographic PDB contains 31 ligand atoms. The installed `pdbtosph` binary wrote the 31-sphere header but failed reading back its Fortran scratch unit because libgfortran opened scratch files under `/tmp`, and `/tmp` on `gpu-dev1` was full. `strace` showed scratch writes returning `ENOSPC`, followed by the line-40 EOF/NUL readback failure.

Minimal runtime correction:

```bash
GFORTRAN_TMPDIR=$PWD/gfortran_tmp pdbtosph original_xtal-lig.hetatm_renamed.pdb gfortran_tmp_original.sph
```

This produced all 31 XAC sphere coordinate records with exact coordinate/radius/atom-number agreement to the source-defined format. No source patch was required; no Fortran compiler was available in the active environment for recompilation. Preserved artifacts:

```text
references/stage5/dock385/3REY/pdbtosph_runtime_diagnostic/xtal-lig.match.pdbtosph_gfortran_tmpdir.sph
references/stage5/dock385/3REY/pdbtosph_runtime_diagnostic/pdbtosph_runtime_fix_provenance.md
references/stage5/dock385/3REY/pdbtosph_runtime_diagnostic/pdbtosph_runtime_fix.patch
```

## Fresh Canonical GFORTRAN_TMPDIR Preparation

A fresh isolated 3REY/XAC crystallographic DOCK preparation was rebuilt through `pdbtosph`, `makespheres3`, `makebox`, and `chemgrid` using the original pinned component tools and `GFORTRAN_TMPDIR` set to project-local storage. It did not reuse manually reconstructed matching spheres or patched downstream preparation artifacts.

Path:

```text
references/stage5/dock385/3REY/blastermaster_canonical_gfortran_tmpdir/
```

Validated outputs:

```text
PDBTOSPH_RECORDS 31
INPUT_ATOMS 31
MAX_DELTA 0.0
MATCHING_SPHERES_RECORDS 31
VDW_BMP_HEADER 0.200  36.268   8.351  17.091 138 140 192
GRID_BOUNDS x 36.268..63.868, y 8.351..36.351, z 17.091..55.491
XAC_BOUNDS  x 46.268..53.469, y 18.350..25.965, z 27.091..45.217
CONTAINS_XAC True
```

Key hashes:

```text
xtal-lig.match.sph     sha16 389c068aeba98c36
matching_spheres.sph   sha16 a82d5e06e10b95d8
box                    sha16 04d403334ab27529
vdw.bmp                sha16 27dd5e72ce12825d
vdw.vdw                sha16 99fdc674719402d6
```

No docking was run from this canonical prep. No DB2, grids outside this isolated prep, or search/scoring/bump parameters were changed.

## Direct Search After Sphere-Color Correction

One direct pinned `dock64` run was executed after the metadata-only sphere-color correction, bypassing SUBDOCK/GNU parallel/job-controller machinery:

```text
references/stage5/dock385/3REY/xac_dock_search_sameframe_original/working_direct_colorcorrected/
```

It used the existing DB2, corrected same-frame grids, corrected color-compatible `matching_spheres.sph`, and original unchanged DOCK/search/scoring parameters. The direct-run `INDOCK` copy changed only `ligand_atom_file` to stdin and `output_file_prefix` to `test.`.

Result:

```text
dock64 exit status: 0
OUTDOCK: present
test.mol2.gz: present, 20 bytes, zero MOL2 molecules
mol# 1 l3d_mapped_heavy    4150          0    0.02 bump
total number of orients (matches):          4150
```

No scored pose ensemble was produced. RMSD, P2, and P4 remain not assessable from this run. Stop here unless the next task explicitly asks for a new, bounded diagnosis of why all color-corrected matched orientations still fail the rigid VDW bump test.

## Direct Search From Fresh Canonical Prep

One direct pinned `dock64` XAC search was run from the fresh canonical `GFORTRAN_TMPDIR` preparation:

```text
references/stage5/dock385/3REY/blastermaster_canonical_gfortran_tmpdir/working_direct_xac/
```

It used the existing crystallographic 3D XAC DB2 and canonical same-frame prep. The direct-run `INDOCK` copy changed only `ligand_atom_file` to stdin and `output_file_prefix` to `test.`; original DOCK/search/scoring/bump parameters were otherwise unchanged.

Result:

```text
dock64 exit status: 0
OUTDOCK: present
test.mol2.gz: present, 20 bytes, zero MOL2 molecules
mol# 1 l3d_mapped_heavy    4150          0    0.02 bump
total number of orients (matches):          4150
```

No scored pose ensemble was produced. RMSD, P2, and P4 are not assessable from this canonical direct run. Stop here unless the next task explicitly asks for a bounded diagnosis of why canonical matching still rejects every orientation as `bump`.

## Completed / Frozen Work

- Stage 5 native-reader proof of life passed 3/3.
- Candidate-1 Vina self-redocking failed at 3REY/XAC under corrected native-pattern anchor recovery.
- Candidate-2 AM1-BCC was eliminated before execution because Vina scoring ignores ligand partial charges.
- Candidate-3 smina/Vinardo failed at 3REY/XAC.
- Candidate-4 GNINA was defined and corrected for GNINA v1.3.3 implementation compatibility, but not executed here.
- The current DOCK lineage work uses UCSF DOCK 3.8.5 on `gpu-dev1`.
- DOCK engine bundled qualification was already completed and must not be repeated unless a concrete engine failure requires it.

## Current Corrected DOCK Artifact Paths

Remote project root:

```text
/mnt/nfs/CX900004_DS117/sbdd-project
```

Corrected 3REY DOCK prep copy:

```text
references/stage5/dock385/3REY/blastermaster_corrected/
```

Key corrected files:

```text
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/INDOCK
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/matching_spheres.sph
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/vdw.vdw
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/vdw.bmp
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/trim.electrostatics.phi
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/ligand.desolv.heavy
references/stage5/dock385/3REY/blastermaster_corrected/dockfiles/ligand.desolv.hydrogen
references/stage5/dock385/3REY/blastermaster_corrected/visualization/matching_spheres.pdb
```

Corrected sphere diagnostic artifacts:

```text
references/stage5/dock385/3REY/pdbtosph_diagnostic/xtal-lig.match.corrected.sph
references/stage5/dock385/3REY/pdbtosph_diagnostic/matching_spheres.corrected.sph
references/stage5/dock385/3REY/pdbtosph_diagnostic/matching_spheres_corrected.pdb
```

Diagnostic report:

```text
references/stage5/dock385/3REY/pdbtosph_xac_diagnostic_report.md
```

Local visualization copy for PyMOL:

```text
/Users/mileshuang/Desktop/3REY_DOCK_view/3REY_receptor_raw.pdb
/Users/mileshuang/Desktop/3REY_DOCK_view/3REY_XAC_native_raw.pdb
/Users/mileshuang/Desktop/3REY_DOCK_view/matching_spheres.pdb
```

## pdbtosph Diagnosis Summary

Original failure:

```text
pdbtosph xtal-lig.hetatm_renamed.pdb xtal-lig.match.sph
At line 40 of file pdbtosph.f
Fortran runtime error: End of file
```

Observed behavior:

- `pdbtosph` wrote the header `cluster     1   number of spheres in cluster    31`.
- It then failed before valid coordinate records were written.
- Downstream `makespheres3` saw invalid/truncated ligand spheres and produced zero matching spheres.

Source inspected:

```text
/mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/pdbtosph/src/pdbtosph.f
```

Relevant behavior:

- reads PDB lines with fixed format `6x, I5, 19x, 3F8.3`;
- writes source-equivalent records with `I5, 3F10.5, F8.3, I5`;
- fails reading back its scratch unit at line 40.

Tests already done:

- Original XAC input failed at line 40.
- Strict 80-column XAC input preserving atom names/elements/coordinates also failed at line 40.
- Synthetic multi-atom inputs failed or produced invalid coordinate output.
- A one-atom synthetic input exited successfully but wrote a NUL/blank coordinate line instead of a valid coordinate record.
- Long path invocation also exposes `character*60` filename truncation at line 16, but blastermaster itself uses short filenames, so that is separate from the line-40 blocker.

Conclusion: not an XAC PDB formatting problem; minimal observed issue is a broken installed `pdbtosph` binary/runtime scratch-record behavior in this environment.

Minimal fix demonstrated:

- Do not modify pinned DOCK/pydock3 source.
- Generate a source-equivalent sphere file directly from preserved XAC PDB coordinates.
- Preserve original atom serials and coordinates exactly.
- Use radius `0.700`, matching `pdbtosph.f`.

Validation already obtained:

```text
sphere coordinate records: 31
ligand coordinate records: 31
max atom-number/coordinate delta vs xtal-lig.hetatm_renamed.pdb: 0.000000
ligand center: (49.536, 23.215, 34.764)
```

`makespheres3` with the corrected ligand sphere file reported:

```text
There are 31 ligand heavy atoms
Ligand center of coords (x y z): 49.5358064516129 23.2145806451613 34.764064516129
Final number of output spheres is: 31
Final number of spheres that are from crystallographic ligand: 31
```

## XAC to DB2 / Docking Execution State

A single-ligand XAC DB2 conversion attempt was started under:

```text
references/stage5/dock385/3REY/dock_search_diagnostic/xac_db2_attempt/
```

Input copied from Candidate-2 MOL2 prep artifact:

```text
references/stage5/docking/candidate2_am1bcc/3REY/XAC_candidate2_input.mol2
```

The first `mol2db2.py` attempt failed because `name.txt` was malformed.

The second attempt fixed `name.txt` but failed because `db.solv` header was malformed.

The third attempt used a minimal zero-solvation `db.solv` header and atom records. It appeared to produce DB2-format output; visible terminal output showed DB2 atom records such as:

```text
A  40 A040 H      7  7   +0.0000     +0.000     +0.000     +0.000     0.000
```

Need to verify `xac.db2.gz` exists and is valid before trusting this as final input.

A DOCK search run directory was started under:

```text
references/stage5/dock385/3REY/xac_dock_search/
```

The wrapper was invoked:

```text
references/stage5/dock385/3REY/xac_dock_search/run_xac_dock.sh
```

Immediately after launching:

```text
("$RUN/run_xac_dock.sh") > "$RUN/run_xac_dock.stdout" 2> "$RUN/run_xac_dock.stderr"
Connection to gpu-dev1.ic.fac.ucsf.edu closed.
mhuang8@facbastp9004:~$
```

The session drop means the DOCK run status is unknown. Next step must inspect the `xac_dock_search` directory before rerunning anything.

## What Must Not Be Repeated

- Do not rerun DOCK installation or bundled qualification.
- Do not rerun general blastermaster setup from scratch unless a specific downstream artifact is missing and cannot be reconstructed from the corrected copy.
- Do not rerun the broken `pdbtosph` step as part of normal prep; preserve it only as diagnostic evidence.
- Do not overwrite original failed `blastermaster_completed` artifacts.
- Do not start decoy generation.
- Do not run ProLIF/PoseBusters/panel-negative selection for this task.
- Do not use ControlMaster SSH for remote command execution. Remote work must use the persistent Terminal.app session workflow documented in `.opencode/skills/gpu-dev1/SKILL.md`.

## Remote Access Constraint

Remote work must reuse the existing authenticated persistent macOS Terminal tab route:

```text
local Terminal tab -> bastion -> gpu-dev1.ic.fac.ucsf.edu
```

Commands must be injected into that tab with AppleScript. Do not start fresh SSH processes for project commands. If the tab has timed out, follow the skill's idle-timeout handling.

## Next Action

1. Reuse the persistent `gpu-dev1` Terminal session.
2. Inspect `references/stage5/dock385/3REY/xac_dock_search/` to determine whether the previous DOCK run completed, failed, or only partially wrote files.
3. Verify `xac.db2.gz` exists and inspect the run stdout/stderr.
4. If the run failed because of environment/path/DB2 setup, fix only that minimal issue while preserving all current inputs and logs.
5. Once a valid XAC pose ensemble exists, compute rank/score/RMSD classifications:
   - Near native: RMSD < 2.0 A
   - Characterization only: 2.0 <= RMSD <= 3.0 A
   - Alternative: RMSD > 3.0 A
6. Answer:
   - P2: whether the search samples both near-native and alternative poses.
   - P4: whether any alternative pose ranks at or above the near-native pose.
7. Save final report to:

```text
references/stage5/dock385/3REY/3REY_XAC_dock_pose_ensemble_report.md
```

Stop before XAC decoy generation.
