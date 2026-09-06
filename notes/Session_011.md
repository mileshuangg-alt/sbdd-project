# Session 011 — rDock Negative-Panel Generation and Blind ProLIF POD

**Date:** 2026-09-02 to 2026-09-06  
**Status:** COMPLETE

## Session objective

Close the remaining pre-Stage-5 validation blocker by obtaining and qualifying a second unrelated pose-generation lineage for the experimental negative panel, freezing panel membership before ProLIF exposure, and then performing the blind frozen-ProLIF proof-of-discrimination (POD).

The session objective was deliberately narrow:

1. use rDock as the frozen second unrelated pose-generation lineage;
2. generate one production rDock result for the already-frozen experimental negative P3-002 N6-cyclooctyladenosine;
3. apply the already-frozen PoseBusters 0.6.5 P1 physical-plausibility gate without repair, minimization, or tuning;
4. if a qualifying rDock representative exists, freeze exact negative-panel membership and provenance before ProLIF exposure;
5. perform the blind negative-panel read through the unchanged historical ProLIF 2.2.0 reader;
6. record the resulting claim at its supported size and close Session 011 before beginning Stage 5.

This work remained **pre-Stage-5 validation**. Stage 5 itself had not yet begun.

## Starting state

At Session 011 start:

- the native A2A ProLIF positive arm was already established and frozen;
- ProLIF 2.2.0 was the frozen interaction reader;
- the strict Graves/DOCK geometric-decoy ladder was a completed preregistered null and was closed to further tuning;
- two experimental hA2A-negative candidates had been frozen prospectively from Gao et al. 2003;
- P3-002 N6-cyclooctyladenosine had supplied a P1-qualified DOCK-family negative representative;
- fresh Vina 1.2.7 negative ensembles existed but Vina was a familiar/development lineage and therefore could not satisfy the second-independent-generator requirement;
- FLOWR and DiffSBDD were reserved for the later generator-comparison arm and were excluded from the validation panel;
- ProLIF remained embargoed from all new negative representatives;
- the single remaining blocker was a P1-qualified negative pose from a genuinely second unrelated pose-generation lineage.

Frozen P3-002 identity and biological status:

- compound: N6-cyclooctyladenosine;
- PubChem CID: **54333857**;
- ChEMBL: **CHEMBL2113424**;
- InChIKey: **TUBLKCBQFVQEOG-SCFUHWHPSA-N**;
- formal charge: **0**;
- hA2A `Ki >10,000 nM`;
- hA1 `Ki = 6.4 ± 1.4 nM`.

Existing frozen DOCK-family representative:

- generator lineage: **DOCK 3.8.5**;
- pose: **rank 1**;
- DOCK score: **-27.96**;
- P3: **PASS**;
- P1: **PASS**;
- protein clashes: **0**;
- ProLIF exposure before panel freeze: **NONE**.

## 1. Second-lineage selection and validation scope

rDock was frozen as the second unrelated pose-generation lineage for Session 011.

The role of rDock was limited to **negative-panel diversity across pose-generation lineages**. The session did not treat rDock as a benchmark, reopen receptor-validation questions, revive the completed Graves-decoy program, or attempt to prove general ProLIF invariance.

The approved execution logic was:

- one frozen production rDock run;
- one frozen PoseBusters P1 qualification;
- if no rDock pose passed P1, stop without tuning, rerunning, changing generators, or inspecting ProLIF;
- if at least one pose passed P1, freeze the deterministic highest-ranked P1-passing representative before ProLIF exposure;
- only after panel freeze could the ProLIF embargo be lifted.

No new scientific requirement was allowed to become mandatory unless it was traceable to the frozen framework/session plan or explicitly approved as a new proposal.

## 2. rDock implementation and qualification

### 2.1 Environment

A dedicated user-space Conda environment was used on the UCSF compute environment:

```text
/mnt/nfs/CX900004_DS117/conda-envs/sbdd-rdock
```

Dependencies installed in the isolated environment included:

- popt;
- cppunit;
- tcsh.

No sudo access was required.

Host build tools included:

- Ubuntu x86_64;
- GCC/G++ 11.4.0;
- Make;
- Git 2.34.1.

### 2.2 Source pin

Frozen source provenance:

```text
rDock tag:    v24.04.204-legacy
Git commit:   3c029ecc65898166b234716b1609fb46212cbc6d
Source path:  /mnt/nfs/CX900004_DS117/src/rdock
```

The supported root-level build system was used:

```text
make -j4
```

The deprecated `build/linux-g++-64` path was not used.

### 2.3 Build interruption and recovery

The initial build failed because host `/tmp` was 100% full. The user owned essentially none of the `/tmp` usage.

Compiler temporaries were redirected to:

```text
/mnt/nfs/CX900004_DS117/tmp/rdock-build
```

No source code or scientific parameter was changed.

The build then completed successfully.

### 2.4 Bundled tests

The bundled test suite passed.

Relevant final output:

```text
[OK] coordinates match
[OK] scores match
```

Required binaries and library artifacts were present, including `rbdock`, `rbcavity`, and `lib/libRbt.so`.

### 2.5 Executable metadata discrepancy

The pinned Git checkout and executable metadata did not report the same version label:

```text
Git checkout:       v24.04.204-legacy / commit 3c029ecc...
Executable reports: v26.09-alpha
Library reports:    libRbt.so/26.09/alpha
```

This discrepancy was recorded rather than modified. Exact Git provenance plus passing bundled tests define the implementation provenance for this session.

## 3. Frozen rDock protocol

The pinned checkout supplied the standard protocol:

```text
/mnt/nfs/CX900004_DS117/src/rdock/data/scripts/dock.prm
```

Title:

```text
Free docking (indexed VDW)
```

The protocol was used unmodified.

No pharmacophore constraints, ProLIF-derived restraints, contact restraints, or scoring/search tuning were introduced.

The frozen reference-ligand cavity parameters were:

```text
SITE_MAPPER   RbtLigandSiteMapper
RADIUS        6.0
SMALL_SPHERE  1.0
MIN_VOLUME    100
MAX_CAVITIES  1
VOL_INCR      0.0
GRIDSTEP      0.5
```

## 4. 3REY receptor translation for rDock

rDock required receptor MOL2 input. The already-qualified 3REY receptor therefore underwent a format translation rather than a new receptor-preparation study.

Open Babel 3.2.1 was already available on the Mac base environment:

```text
/opt/homebrew/Caskroom/miniforge/base/bin/obabel
Open Babel 3.2.1
```

The receptor was converted without hydrogen, protonation, charge, or minimization options.

The approved audit compared only:

1. atom count;
2. coordinates;
3. explicit hydrogens.

The translation **PASSED** this audit.

Receptor partial charges were explicitly excluded from the conversion audit because rDock documentation states that its scoring functions do not use receptor partial charges in this role.

The receptor conversion/audit was frozen and not reopened.

## 5. Production rDock setup and cavity generation

Production working directory:

```text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/rdock_session011
```

Frozen production files included:

```text
3REY_rec.mol2
3REY_rec_for_rdock.mol2
3REY_rdock.prm
XAC_reference.sd
P3-002_N6-cyclooctyladenosine.sd
```

The rDock receptor parameter file used:

```text
RBT_PARAMETER_FILE_V1.00
TITLE 3REY rDock Session 011

RECEPTOR_FILE 3REY_rec_for_rdock.mol2
RECEPTOR_FLEX 3.0

SECTION MAPPER
        SITE_MAPPER RbtLigandSiteMapper
        REF_MOL XAC_reference.sd
        RADIUS 6.0
        SMALL_SPHERE 1.0
        MIN_VOLUME 100
        MAX_CAVITIES 1
        VOL_INCR 0.0
        GRIDSTEP 0.5
END_SECTION

SECTION CAVITY
        SCORING_FUNCTION RbtCavityGridSF
        WEIGHT 1.0
END_SECTION
```

### 5.1 Initial cavity failure

The first `rbcavity` invocation was launched from `$HOME/src/rdock` while `RECEPTOR_FILE` and `REF_MOL` were relative paths.

rDock therefore attempted to open:

```text
/mnt/nfs/CX900004_DS117/src/rdock/3REY_rec_for_rdock.mol2
```

and returned:

```text
RBT_FILE_READ_ERROR at src/lib/RbtBaseFileSource.cxx, line 211
Error opening /mnt/nfs/CX900004_DS117/src/rdock/3REY_rec_for_rdock.mol2
```

This was classified as a working-directory/path error only. No scientific state changed and no production pose was generated.

### 5.2 Corrected cavity generation

Running `rbcavity` from the Session-011 production directory succeeded with the frozen parameters.

Observed cavity:

```text
Total volume 2139.75 A^3
Cavity #1
Size = 17118 points
Volume = 2139.75 A^3
Min = (40.5, 14, 22.5)
Max = (59, 31.5, 51)
Center = (50.2752, 23.4218, 37.3767)
Extent = (18.5, 17.5, 28.5)
```

Exactly one cavity was produced.

No cavity parameter was changed after observing the result.

## 6. Single production rDock run

The frozen production run used:

- ligand: existing frozen neutral P3-002 SD representation;
- receptor/cavity: frozen Session-011 3REY setup;
- protocol: unmodified standard `dock.prm`;
- run count: `-n 1`;
- fixed seed: **20260906**.

Command-line provenance reported by rDock:

```text
-i ./P3-002_N6-cyclooctyladenosine.sd
-r ./3REY_rdock.prm
-p /mnt/nfs/CX900004_DS117/src/rdock/data/scripts/dock.prm
-o ./P3-002_N6-cyclooctyladenosine_rdock
-n 1
-s 20260906
```

rDock reported:

```text
NAME: P3-002_N6-cyclooctyladenosine
RANDOM_NUMBER_SEED: 20260906
END OF RUN
```

Production output:

```text
P3-002_N6-cyclooctyladenosine_rdock.sd
```

The output contained exactly **one SD record**.

The sole pose reported:

```text
SCORE              -10.5896
SCORE.INTER         -10.8878
SCORE.INTER.POLAR   -1.06066
SCORE.INTER.REPUL    0.0594597
SCORE.INTER.ROT      4
SCORE.INTER.VDW     -16.9789
SCORE.INTRA          0.109473
SCORE.RESTR          0.00102727
SCORE.SYSTEM         0.18768
SCORE.heavy         27
SCORE.norm          -0.392208
```

The SD record retained the frozen ligand InChIKey:

```text
TUBLKCBQFVQEOG-SCFUHWHPSA-N
```

The pre-existing `ETKDG_SEED = 20260828` field was retained as ligand-preparation provenance and was not interpreted as the rDock random seed. The rDock run itself explicitly reported seed **20260906**.

No rerun or search tuning was performed.

## 7. PoseBusters P1 qualification

### 7.1 Frozen implementation recovered

The Session-010 P1 definition was retained:

- PoseBusters **0.6.5**;
- shipped configuration: `dock.yml`;
- original generated coordinates;
- no repair/minimization;
- `mol_true=None`;
- qualified 3REY receptor as `mol_cond`;
- `full_report=True`.

The established evaluation environment was recovered as:

```text
sbdd-eval
```

Installed PoseBusters API:

```text
PoseBusters version: 0.6.5
```

The shipped configuration was located at:

```text
/opt/homebrew/Caskroom/miniforge/base/envs/sbdd-eval/lib/python3.12/site-packages/posebusters/config/dock.yml
```

The rDock output used the `.sd` extension, which PoseBusters 0.6.5 does not recognize even though the file content is SD/SDF format. A byte-for-byte copy with `.sdf` extension was used only as an extension-compatible PoseBusters input; the authoritative rDock production artifact remained the untouched `.sd` file.

### 7.2 P1 result

The sole rDock pose passed the frozen P1 qualification.

Observed headline checks included:

```text
mol_pred_loaded = True
mol_cond_loaded = True
sanitization = True
inchi_convertible = True
all_atoms_connected = True
no_radicals = True
bond_lengths = True
bond_angles = True
internal_steric_clash = True
aromatic_ring_flatness = True
non-aromatic_ring_non-flatness = True
double_bond_flatness = True
internal_energy = True
protein-ligand_maximum_distance = True
```

Protein-relative results:

```text
smallest_distance_protein = 2.607812 A
num_pairwise_clashes_protein = 0
volume_overlap_protein = 0.009972
```

Result:

**P1 PASS**

Because the production ensemble contained one pose, that sole pose became the deterministic rDock representative.

The full PoseBusters dataframe was printed during execution but was not persisted as a standalone machine-readable artifact. The observed result was retained in the Session-011 record without rerunning P1 solely for archival purposes.

## 8. Negative-panel freeze

The negative panel was frozen before any new negative was exposed to ProLIF.

### 8.1 DOCK-family representative

```text
Candidate: P3-002 N6-cyclooctyladenosine
Generator lineage: DOCK 3.8.5
Representative: rank 1
DOCK score: -27.96
P1: PASS
Protein clashes: 0
ProLIF exposure before freeze: NONE
```

Exact representative path:

```text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/p3_candidates/P3-002_N6-cyclooctyladenosine/p1_posebusters_dock/poses/rank_01.mol2
```

SHA-256:

```text
a232d950008861f3ee87d73e880b9e1627afa06a47182b3a1a249f4cf61eaddf
```

### 8.2 rDock-family representative

```text
Candidate: P3-002 N6-cyclooctyladenosine
Generator lineage: rDock v24.04.204-legacy
Git commit: 3c029ecc65898166b234716b1609fb46212cbc6d
Representative: sole production pose
rDock score: -10.5896
P1: PASS
Protein clashes: 0
ProLIF exposure before freeze: NONE
```

Exact representative path:

```text
/mnt/nfs/CX900004_DS117/sbdd-project/references/stage5/negative_panel/rdock_session011/P3-002_N6-cyclooctyladenosine_rdock.sd
```

SHA-256:

```text
731661a5096209b80a56f6ecd48d520c69c834b949b3d456bd0101a5de48f81a
```

### 8.3 rDock production-input hashes

```text
04cf1e3c931a3f8039b0791da6b477dfc11f1f6ce863df6173ec6b0eab9d8fc7  P3-002_N6-cyclooctyladenosine.sd
f5141e07c86292518d2df30e88e2815ca3d518cbd0ee527e2de8436341b1139c  3REY_rdock.prm
8ab3ac4b1d8e0f383e1026dc62fbeff33d760c9f9c8eb31ee45ee08121f25d20  3REY_rec_for_rdock.mol2
2be99a4a0659c986c9ec4e9789b36ed8b91d82169acd288b433dd8a3efeaf4ef  XAC_reference.sd
```

### 8.4 Panel-freeze manifest

The panel-freeze manifest was written before the blind ProLIF POD:

```text
negative_panel_freeze_session011.txt
```

Manifest SHA-256:

```text
7dcd620b4f4ad428c2375aff6adb308ef23dfb6ba5e069a6dbcdbe7a8b518bef
```

The manifest explicitly recorded that ProLIF had not been used for panel membership selection.

Vina remained outside the independent-family panel and retained its role as a secondary/generalization control only.

## 9. Recovery of the historical ProLIF reader

The exact historical reader implementation was recovered from the retained repository file:

```text
/mnt/nfs/CX900004_DS117/sbdd-project/scripts/stage5/test_native_reader_controls.py
```

The historical receptor-loading route was:

1. use the validated restored receptor PQR;
2. create a temporary MDAnalysis-compatible PQR view without modifying the authoritative receptor;
3. preserve normal biological residue numbering, with temporary remapping only for genuine negative residue numbers where required;
4. load with MDAnalysis;
5. infer elements and bonds;
6. remove impossible inferred H-H bonds;
7. resolve multiple hydrogen parents only when exactly one same-residue heavy-atom parent exists;
8. require every explicit hydrogen to have exactly one heavy-atom parent;
9. audit Phe168 and Asn253 numbering;
10. convert through `plf.Molecule.from_mda()`;
11. run the frozen default `plf.Fingerprint()` through `Fingerprint.generate(..., metadata=True)`.

The historical ligand reader used RDKit on the prepared SDF followed by `plf.Molecule.from_rdkit()`.

The frozen native 3REY/XAC proof-of-life result was:

```text
Phe168:
- Hydrophobic
- VdWContact

Asn253:
- HBAcceptor
- VdWContact

Result: PASS
```

The complete native proof-of-life arm had previously passed **3/3 experimental positive complexes**.

## 10. Receptor-route investigation before blind POD

An attempted new receptor-loading route using MDAnalysis directly on `3REY_rec.crg.pdb` failed before fingerprint generation because the PDB contained no explicit `CONECT` records. MDAnalysis therefore guessed connectivity, and RDKit sanitization failed with a kekulization exception.

No blind negative was successfully passed to ProLIF during this failed setup attempt.

A direct RDKit PDB-loading route was then tested only at the receptor-loading level:

```text
Atoms: 2700
Bonds: 2760
SANITIZATION: PASS
```

The observed residue names were standard protein/AMBER protonation names.

Before adopting that route, a receptor-artifact coordinate comparison was performed between:

```text
references/stage5/native_complexes/3REY/3REY_receptor_pH7.4_restored.pqr
```

and:

```text
3REY_rec.crg.pdb
```

Heavy atoms were matched by residue number plus atom name.

Result:

```text
PQR heavy atoms: 2251
PDB heavy atoms: 2250
Matched heavy atoms: 2250
Only in PQR: 1
Only in PDB: 0
Max absolute coordinate deviation: 2.312129322 A
Mean absolute coordinate deviation: 0.006478297 A
Atom with maximum deviation: residue 75 CD2
PQR-only atom: residue 305 OXT
```

Because the two receptor artifacts were not coordinate-identical, the proposed direct-RDKit route was **not** substituted into the blind POD.

The missing historical XAC prepared SDF prevented a clean positive-control equivalence test across the two receptor artifacts. This affected only the proposed loader-equivalence branch; it did not block use of the original frozen historical reader.

The equivalence branch was therefore abandoned without modifying the instrument.

## 11. Historical proof-of-life input retention defect

The historical native-reader script expects the prepared 3REY/XAC ligand artifact:

```text
references/stage5/native_complexes/3REY/3REY_XAC_native_pH7.4_restored.sdf
```

That exact file was not present in the retained `native_complexes/3REY` directory and was not recovered by an exact-filename repository search during Session 011.

Retained related artifacts included:

```text
3REY_XAC_native_raw.pdb
3REY_receptor_pH7.4.pqr
3REY_receptor_pH7.4_restored.pqr
3REY_receptor_raw.pdb
XAC.cif
build_native_xac.py
extract_native_complex.py
```

The historical proof-of-life itself remains documented and frozen, including its 3/3 positive result and the 3REY/XAC interaction classes. The missing prepared XAC SDF is therefore recorded as an **artifact-retention defect**, not as evidence that the proof-of-life did not occur.

The file was **not regenerated** during Session 011.

This defect reinforces the existing preservation requirement that all intermediate and validation inputs be retained with the corresponding frozen result.

## 12. Blind frozen-ProLIF POD

After panel freeze, the ProLIF embargo was lifted.

The blind negative-panel read used the **unchanged historical reader route** recovered from `test_native_reader_controls.py`:

```text
3REY_receptor_pH7.4_restored.pqr
-> load_protein()
-> MDAnalysis
-> topology cleanup/audit
-> plf.Molecule.from_mda()
-> plf.Fingerprint()
-> Fingerprint.generate(..., metadata=True)
```

No RDKit receptor route was used for the blind POD.

The frozen A2A recognition definition remained:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

`VdWContact` remained characterization evidence only and did not satisfy the frozen Phe168 criterion.

### 12.1 Residue-75 guard

Because the receptor-artifact comparison identified the largest coordinate difference at residue 75 CD2, every blind read was checked for any interaction involving residue 75.

Predeclared execution rule for this read:

- if a blind pose contacted residue 75, flag that pose and stop on it;
- otherwise continue reporting the frozen anchor interactions.

Neither blind pose contacted residue 75.

### 12.2 DOCK-family negative

Blind result:

```text
Phe168: ['VdWContact']
Asn253: []
Residue 75 contacts: NONE
```

Interpretation under the frozen A2A recognition definition:

- Phe168 required feature: **NOT reproduced** because VdWContact alone does not satisfy Hydrophobic OR PiStacking;
- Asn253 HBAcceptor: **NOT reproduced**;
- complete frozen recognition pattern: **NOT reproduced**.

### 12.3 rDock-family negative

Blind result:

```text
Phe168: []
Asn253: []
Residue 75 contacts: NONE
```

Interpretation under the frozen A2A recognition definition:

- Phe168 required feature: **NOT reproduced**;
- Asn253 HBAcceptor: **NOT reproduced**;
- complete frozen recognition pattern: **NOT reproduced**.

## 13. Session-011 claim boundary

The blind POD result supports a deliberately bounded claim.

### Demonstrated

**Molecule-level discrimination was demonstrated for one experimentally established hA2A-negative molecule, P3-002 N6-cyclooctyladenosine, represented by independently generated P1-qualified poses from two docking lineages (DOCK 3.8.5 and rDock). Neither pose reproduced the predeclared A2A recognition pattern.**

The result also shows that the observed negative classification was reproduced across two unrelated pose-generation routes for this same molecule.

### Not demonstrated

Session 011 does **not** establish:

- pose-level sensitivity;
- discrimination across multiple independent negative chemotypes;
- a general negative-class sensitivity/specificity estimate;
- general invariance to arbitrary receptor representations or loading routes;
- rDock benchmark performance;
- a new Graves-style geometric-decoy result.

The two panel members are two docking-route representations of **one experimental negative molecule**, not two independent molecular negatives.

No broader claim should be inferred from the two-pose panel.

## 14. Final Session-011 status

### Completed

- rDock selected and frozen as the second unrelated pose-generation lineage;
- isolated rDock environment established without sudo;
- source tag and Git commit pinned;
- build completed after redirecting compiler temporaries away from full host `/tmp`;
- bundled rDock tests passed;
- executable/library metadata discrepancy recorded without modification;
- standard free-docking protocol inspected and frozen unmodified;
- 3REY receptor PDB-to-MOL2 format translation completed and passed the approved atom-count/coordinate/explicit-H audit;
- frozen reference-ligand cavity generated successfully;
- single preregistered production rDock run completed with seed 20260906;
- sole rDock pose retained with score -10.5896;
- PoseBusters 0.6.5 P1 implementation recovered and applied without repair/minimization;
- rDock representative passed P1 with zero protein clashes;
- exact DOCK and rDock representative paths and SHA-256 hashes frozen;
- negative-panel membership frozen before ProLIF exposure;
- historical ProLIF reader implementation recovered from retained source;
- proposed alternate receptor-loading route was not substituted into the blind read;
- blind POD executed through the unchanged historical ProLIF 2.2.0 route;
- residue-75 guard was clean for both blind poses;
- neither negative pose reproduced the frozen A2A recognition pattern;
- Session-011 discrimination claim bounded to one experimental negative molecule under two docking routes.

### Remaining artifact-archive task at session close

The scientific work of Session 011 is complete. The corresponding frozen archive must retain, together, the exact panel poses, biological/pose-generation inputs, historical ProLIF receptor, reader implementation, P1/POD result records, provenance manifests, and hashes.

The final archive must **copy rather than move** authoritative artifacts so that original project paths remain intact.

The separate Session-011 narrative log is not part of the scientific artifact bundle and remains under the project's existing session-log system.

## Session conclusion

Session 011 closed the final pre-Stage-5 negative-panel blocker.

The project now has:

- an already-established native experimental positive proof-of-life for ProLIF;
- one experimentally established hA2A-negative molecule selected independently of ProLIF;
- P1-qualified representations of that molecule from two unrelated docking lineages;
- a panel frozen before ProLIF exposure;
- a blind read through the unchanged historical ProLIF 2.2.0 implementation;
- failure of both negative poses to reproduce the predeclared A2A recognition pattern;
- an explicitly bounded molecule-level discrimination claim;
- no pose-sensitivity or broad negative-chemotype discrimination claim.

With Session 011 complete, the project may proceed to **Stage 5** under the frozen framework and claim boundaries.

## Do not reopen after Session 011

- the completed Graves/DOCK geometric-decoy ladder;
- rDock cavity/scoring/search tuning for this panel;
- additional rDock reruns for P3-002;
- generator search for the purpose of replacing the frozen Session-011 second lineage;
- Vina as independent generator family #2;
- FLOWR or DiffSBDD as contributors to the validation panel;
- P3-002 identity or experimental-negative eligibility;
- P3-002 reprotonation/recharging for this panel;
- the completed receptor MOL2 translation/audit;
- PoseBusters version/configuration for this qualification;
- ProLIF parameters or historical reader implementation;
- negative-panel membership based on post-freeze ProLIF information;
- a pose-sensitivity claim from the two docking-route observations;
- regeneration of the missing historical XAC proof-of-life SDF merely to make the retention record look complete.

## Preservation requirement

Preserve all Session-011 implementation, validation, and execution artifacts, including successful and failed branches.

At minimum retain:

- rDock source provenance and environment information;
- build/test outputs where available;
- receptor translation inputs/outputs and audit evidence;
- cavity parameter file and cavity result;
- frozen P3-002 rDock input;
- complete rDock output ensemble;
- DOCK rank-1 frozen representative;
- PoseBusters P1 inputs and observed result record;
- panel-freeze manifest;
- historical 3REY restored receptor PQR used by ProLIF;
- `test_native_reader_controls.py` containing the historical `load_protein()` reader;
- blind POD result record;
- all relevant SHA-256 hashes;
- the failed/path-only rbcavity branch and the abandoned alternate receptor-loading investigation as documented provenance;
- the record that the historical prepared XAC proof-of-life SDF was not retained and was not regenerated.

No Session-011 validation artifact should be deleted merely because it is not expected to appear in the final pipeline.

## Frozen Session-011 scientific bundle

The completed Session-011 validation artifacts were archived together under:

`references/stage5/negative_panel/session011_frozen_bundle/`

The bundle preserves the frozen panel representatives, relevant ligand and receptor inputs, the historical ProLIF reader implementation, panel-freeze provenance, and transcribed results from the completed rDock P1 qualification and blind ProLIF POD.

Bundle checksum manifest:

```text
SHA256SUMS.txt
SHA-256 = b209600b19265b6cdd664c6bbb2e7132bedc66d10b17200df1776a8a32493639

```
