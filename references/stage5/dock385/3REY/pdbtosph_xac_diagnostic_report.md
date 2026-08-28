# 3REY/XAC DOCK 3.8.5 pdbtosph Diagnostic

## Scope

Diagnostic-only investigation of the 3REY/XAC crystallographic-ligand sphere-preparation blocker.

No XAC docking was run. No decoys were generated. Completed DOCK setup/qualification was not repeated.

## Observed Failure

Existing blastermaster step:

```text
pdbtosph xtal-lig.hetatm_renamed.pdb xtal-lig.match.sph
```

failed with:

```text
At line 40 of file pdbtosph.f
Fortran runtime error: End of file
```

The resulting `xtal-lig.match.sph` contained only:

```text
cluster     1   number of spheres in cluster    31
```

followed by NUL/blank data, with no valid coordinate records.

Downstream `makespheres3` therefore reported:

```text
There are 1 ligand heavy atoms
Ligand center of coords (x y z): 0 0 0
Final number of output spheres is: 0
```

## Parser Source

Pinned DOCK/pydock3 source inspected:

```text
/mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/pdbtosph/src/pdbtosph.f
```

Relevant logic:

```fortran
open (unit=2,  status='scratch')
...
read (pdblin, 1001) atmnum, x, y, z
1001 format (6x, I5, 19x, 3F8.3)
write (2, 1002) atmnum, x, y, z, radius, atmnum
1002 format (I5, 3F10.5, F8.3, I5)
...
rewind (2)
do 600 i=1, count
  read (2,1000) line
  write (3,1000) line
600 continue
```

The runtime failure occurs while reading the Fortran scratch unit back after the atom count has already been written to the output file.

## Root Cause

The failure is not caused by the XAC atom count, XAC coordinates, atom ordering, or nonstandard residue identity.

Input-format tests performed in `references/stage5/dock385/3REY/pdbtosph_diagnostic/` showed:

- The original XAC input fails at line 40 after writing the 31-sphere header.
- A strict 80-column rewritten XAC PDB preserving all atom names, elements, and coordinates also fails at line 40.
- Synthetic multi-atom PDB inputs also fail or produce no valid coordinate records.
- A one-atom synthetic input exits successfully but still writes a NUL/blank coordinate record rather than a valid text sphere coordinate.

Follow-up isolated runtime tracing established the concrete cause of the scratch-record failure. The installed `pdbtosph` binary opens its Fortran scratch file under `/tmp`:

```text
open("/tmp/gfortrantmpo4vgox", O_RDWR|O_CREAT|O_EXCL, 0600) = 4
```

On `gpu-dev1`, `/tmp` was full:

```text
/dev/mapper/vg_ubuntu-lv_tmp  9.8G  9.3G     0 100% /tmp
```

The scratch write then failed with `ENOSPC`, and the later line-40 scratch readback hit EOF/NUL data:

```text
write(4, "    1  48.99900  24.12700  30.36"..., 1519) = -1 ENOSPC (No space left on device)
At line 40 of file pdbtosph.f
Fortran runtime error: End of file
```

Therefore the line-40 failure is an environment/runtime scratch-location problem caused by full `/tmp`, not a fixable XAC PDB formatting problem and not an algorithmic error in the source format itself.

A separate artifact of `pdbtosph` was also observed: because its input/output filename buffers are `character*60`, invoking it with long relative paths fails earlier at line 16 with `No such file or directory`. Blastermaster avoids that by running inside the working directory with short filenames; this is not the line-40 blocker.

## Minimal Runtime Correction

No Fortran compiler was available in the active `dock385` environment (`gfortran`, `ifort`, `ifx`, `flang`, `f77`, and `fort` were not found in `PATH`), so recompilation was not performed. A source patch was not required.

The installed pinned binary runs correctly when libgfortran scratch files are redirected away from full `/tmp` by setting `GFORTRAN_TMPDIR` to writable project-local storage:

```bash
mkdir -p gfortran_tmp
GFORTRAN_TMPDIR=$PWD/gfortran_tmp \
  /mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/pdbtosph/bin/pdbtosph \
  original_xtal-lig.hetatm_renamed.pdb \
  gfortran_tmp_original.sph
```

Runtime tracing showed the corrected invocation opened the scratch file under the project-local diagnostic directory and the scratch write/read succeeded.

The full XAC run produced a canonical 31-record ligand sphere file:

```text
references/stage5/dock385/3REY/pdbtosph_runtime_diagnostic/xtal-lig.match.pdbtosph_gfortran_tmpdir.sph
```

Validation:

```text
SPHERE_RECORDS 31
INPUT_ATOMS 31
MAX_DELTA 0
```

Installed executable provenance:

```text
pdbtosph sha256 9498c3bc875c95ac69cf52d853572e7b9d857e01b51978c324695d3ad68cdcc4
```

Additional preserved diagnostic artifacts:

```text
references/stage5/dock385/3REY/pdbtosph_runtime_diagnostic/pdbtosph_runtime_fix_provenance.md
references/stage5/dock385/3REY/pdbtosph_runtime_diagnostic/pdbtosph_runtime_fix.patch
```

`pdbtosph_runtime_fix.patch` records that no source patch was required; the correction is runtime-only (`GFORTRAN_TMPDIR`).

No pinned DOCK or pydock3 source was modified.

## Fresh Canonical Preparation With Runtime Fix

A fresh isolated 3REY/XAC crystallographic DOCK preparation was rebuilt using the original pinned component tools and `GFORTRAN_TMPDIR` redirected to project-local storage. Existing patched/manual matching-sphere artifacts were not reused.

Isolated prep directory:

```text
references/stage5/dock385/3REY/blastermaster_canonical_gfortran_tmpdir/
```

Canonical component commands run through matching spheres, box, and VDW grids:

```bash
GFORTRAN_TMPDIR=$PWD/gfortran_tmp \
  /mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/pdbtosph/bin/pdbtosph \
  xtal-lig.hetatm_renamed.pdb xtal-lig.match.sph

/mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/makespheres3/makespheres3.cli.pl \
  1.5 0.8 45 xtal-lig.match.sph all_spheres.sph rec.crg.pdb matching_spheres.sph

/mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/makebox/makebox.smallokay.pl \
  matching_spheres.sph rec.crg.pdb box 10

/mnt/nfs/CX900004_DS117/dock385/dock3-release/pydock3/pydock3/blastermaster/programs/chemgrid/bin/chemgrid
```

The `chemgrid` `INCHEM` used the original preserved parameters:

```text
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

Validation:

```text
PDBTOSPH_RECORDS 31
INPUT_ATOMS 31
MAX_DELTA 0.0
MATCHING_SPHERES_RECORDS 31

BOX:
HEADER    CORNERS OF BOX   36.268   8.350  17.091  63.469  35.965  55.217
REMARK    CENTER (X Y Z)   49.868  22.158  36.154
REMARK    DIMENSIONS (X Y Z)   27.201  27.615  38.126

VDW_BMP_HEADER 0.200  36.268   8.351  17.091 138 140 192
GRID_BOUNDS x 36.268..63.868, y 8.351..36.351, z 17.091..55.491
XAC_BOUNDS  x 46.268..53.469, y 18.350..25.965, z 27.091..45.217
CONTAINS_XAC True
```

Key output hashes:

```text
xtal-lig.match.sph     size 2562      sha16 389c068aeba98c36
matching_spheres.sph   size 2480      sha16 a82d5e06e10b95d8
box                    size 834       sha16 04d403334ab27529
vdw.bmp                size 3755871   sha16 27dd5e72ce12825d
vdw.vdw                size 29675536  sha16 99fdc674719402d6
```

No docking was run, no DB2 was regenerated, and no search/scoring/bump parameters were changed.

## Minimal Fix Used For Validation

Because input reformatting did not make the pinned `pdbtosph` binary produce valid sphere records, the retained diagnostic fix is a source-equivalent direct writer that creates the exact sphere-file records `pdbtosph` is intended to write:

```text
cluster     1   number of spheres in cluster    31
<atom serial> <x> <y> <z> 0.700 <atom serial>
```

The writer reads `xtal-lig.hetatm_renamed.pdb`, skips hydrogens by the same atom-name rule, preserves original atom serials and coordinates, and writes radius `0.700` as in `pdbtosph.f`.

The original failing inputs and outputs were preserved.

## Artifacts

Diagnostic directory:

```text
references/stage5/dock385/3REY/pdbtosph_diagnostic/
```

Important files:

```text
original_xtal-lig.hetatm_renamed.pdb
original_short.sph
original_short.stderr
fixed_80col_xtal-lig.pdb
fixed_80col_xtal-lig.sph
synthetic_31.pdb
synthetic_31.sph
write_xac_spheres.py
xtal-lig.match.corrected.sph
makespheres_corrected.stdout
makespheres_corrected.stderr
matching_spheres.corrected.sph
```

Report:

```text
references/stage5/dock385/3REY/pdbtosph_xac_diagnostic_report.md
```

## Validation Results

Corrected crystallographic-ligand sphere file:

```text
references/stage5/dock385/3REY/pdbtosph_diagnostic/xtal-lig.match.corrected.sph
```

Validation:

```text
sphere header: cluster     1   number of spheres in cluster    31
sphere coordinate records: 31
ligand coordinate records: 31
max atom-number/coordinate delta vs xtal-lig.hetatm_renamed.pdb: 0.000000
ligand center: (49.536, 23.215, 34.764)
```

This matches the crystallographic XAC heavy-atom centroid previously frozen for 3REY:

```text
49.535806 23.214581 34.764065
```

`makespheres3` was run against the corrected ligand sphere file and existing all-sphere/receptor artifacts:

```text
makespheres3.cli.pl 1.5 0.8 45 \
  xtal-lig.match.corrected.sph \
  ../blastermaster_completed/working/all_spheres.sph \
  ../blastermaster_completed/working/rec.crg.pdb \
  matching_spheres.corrected.sph
```

Key validation output:

```text
There are 31 ligand heavy atoms
Ligand center of coords (x y z): 49.5358064516129 23.2145806451613 34.764064516129
Using crystallographic ligand as spheres for output
Number of spheres after removing too far (>7 angstroms) and too close to receptor (<1.2 angstroms): 31
Number of spheres after removing spheres too close to each other (approximately <1.5 angstroms): 31
After continuity checking, number of spheres is: 31
Final number of output spheres is: 31
Final number of spheres that are from crystallographic ligand: 31
```

Corrected matching sphere file:

```text
references/stage5/dock385/3REY/pdbtosph_diagnostic/matching_spheres.corrected.sph
```

Parsed matching-sphere coordinate records after the cluster header:

```text
31
```

First corrected matching sphere:

```text
9001 48.999 24.127 30.369 0.0 0
```

Last corrected matching sphere:

```text
9031 50.760 25.370 43.957 0.0 0
```

## Reproducibility Implications

The minimal reproducible correction is not to alter DOCK/pydock3 source or ligand geometry. It is to replace the broken `pdbtosph` sphere-conversion output with an explicitly generated source-equivalent sphere file from the preserved XAC PDB coordinates.

This correction preserves XAC crystallographic geometry exactly and restores a nonzero matching-sphere set for downstream DOCK setup.

Before any actual XAC docking or decoy generation, the DOCK preparation workflow should be made to consume the corrected `xtal-lig.match.corrected.sph` / `matching_spheres.corrected.sph` artifacts or rerun the downstream steps from those corrected files while preserving the original failed artifacts.
