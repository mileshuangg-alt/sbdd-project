# Session 007 — Stage 5 Target Compatibility

**Date:** 2026-08-16

## Session Goal

Begin implementation and validation of Stage 5 target compatibility under the predeclared D007 methodology.

Stage 5 is distinct from Stage 3B:

- Stage 3B asks whether a generated pose is physically plausible relative to the pocket.
- Stage 5 asks whether that pose expresses credible, target-specific interactions consistent with recognition by the intended binding site.

The final Stage 5 hard gate is **not yet frozen**.

Before any DiffSBDD Stage 5 baseline molecules are evaluated, the methodology must pass the following validation sequence:

1. Interaction-reader proof of life on native experimental A2A complexes.
2. 3/3 cognate self-redocking validation.
3. Common 3RFM positive/negative control experiment.
4. Complete candidate gate-formulation ledger.
5. Freeze the final Stage 5 hard gate.
6. Only then evaluate the 16 DiffSBDD Stage 4 survivors.

## Starting Status

D007 status:

`PENDING VALIDATION`

Predeclared native interaction-reader controls:

- 3REY — XAC
- 5OLH — Vipadenant
- 5OLO — Tozadenant

Core published A2A interaction anchors:

- Phe168 — aromatic / hydrophobic core recognition
- Asn253 — polar hydrogen-bond anchoring

Primary interaction reader:

`ProLIF`

Frozen preparation policy:

- protein: PDB2PQR / PROPKA, pH 7.4
- ligand: Molscrub, pH 7.4, one state per molecule
- experimental protein heavy-atom coordinates preserved
- experimental ligand coordinates preserved during native reader validation
- His250 protonation state explicitly audited

## First Task

Validate the interaction-reader layer using the native 3REY/XAC experimental complex.

ProLIF must recover both Phe168 and Asn253 from the prepared native crystallographic pose before Stage 5 is allowed to proceed to docking validation.

## Stage 5 Environment Setup

The existing `sbdd-eval` environment initially did not contain the Stage 5-specific preparation and interaction-analysis tools.

Existing environment at the start of Session 7:

```text
Python:       3.12.13
RDKit:        2026.03.5
NumPy:        2.5.2
pandas:       3.0.5
BioPython:    1.88
PoseBusters:  0.6.5

### 3REY receptor preparation audit

3REY chain A was prepared using PDB2PQR 3.7.1 / PROPKA 3.5.1 at pH 7.4 with hydrogen-network optimization disabled.

Results:

- deposited receptor heavy atoms: 2,250
- deposited heavy atoms retained: 2,250 / 2,250
- maximum deposited heavy-atom displacement: 0.0 Å
- hydrogens added: 2,317
- one additional heavy atom added: terminal SER305 OXT
- His250 PROPKA pKa: 3.87
- His250 prepared state: ND1-protonated / NE2-unprotonated
- experimental backbone gap between PRO149 and GLY158 retained rather than reconstructed

The preparation therefore preserves the deposited receptor heavy-atom geometry required by D007.

### Native-ligand Molscrub coordinate audit

Initial XAC preparation with Molscrub 0.2.2 demonstrated that `--skip_gen3d` does not preserve deposited coordinates.

With tautomer enumeration enabled, Molscrub produced three +1 XAC states. Adding `--skip_tautomers` correctly reduced this to one pH-7.4 state and preserved the crystallographic XAC tautomer, but the output coordinates were replaced by a 2D depiction.

After graph-based atom correspondence was established across all 31 heavy atoms:

- maximum mapped displacement: 66.20 Å
- mean mapped displacement: 65.17 Å

The Molscrub output coordinates were therefore rejected for native-reader validation.

The frozen implementation policy is now to use Molscrub for single-state pH-7.4 chemistry assignment, restore deposited heavy-atom coordinates by graph mapping, and generate only hydrogen coordinates afterward. Docking inputs do not require coordinate restoration because docking regenerates the pose.

### 3REY / XAC ProLIF reader proof of life

After validating ligand chemistry, pH-7.4 state assignment, native-coordinate restoration, receptor protonation, and receptor topology reconstruction, the native 3REY/XAC complex was evaluated with ProLIF 2.2.0.

Input audit:

- prepared receptor atoms: 4,568
- receptor residues: 291
- prepared XAC atoms including explicit hydrogens: 60
- XAC formal charge: +1
- native heavy-atom geometry preserved

ProLIF recovered both predeclared A2A anchors.

**Asn253**

ProLIF classified the interaction as:

`HBAcceptor`

with:

- donor/acceptor distance: 2.868 Å
- DHA angle: 137.9°

This agrees with the independently measured pre-reader Asn253 polar-contact distance of 2.868 Å.

**Phe168**

ProLIF detected:

- `Hydrophobic` interaction at 3.853 Å
- `VdWContact` at 3.398 Å

Default ProLIF did not classify the XAC/Phe168 interaction as `PiStacking`. This is not treated as failure because D007 predeclared Phe168 as an aromatic / hydrophobic core-recognition anchor rather than requiring one specific ProLIF interaction class.

Additional native-pose contacts detected by ProLIF included Met177, His250, Leu249, Met270, Ile274, Tyr271, Ala81, and Leu267.

**3REY/XAC reader result: PASS**

The interaction reader therefore demonstrates proof of life on the first of three native experimental positive controls.

Reader-validation status:

- 3REY / XAC: PASS
- 5OLH / Vipadenant: PENDING
- 5OLO / Tozadenant: PENDING

The Stage 5 interaction-reader layer remains pending until all 3/3 native experimental complexes pass.

## Native Interaction-Reader Proof of Life

### Outcome

The Stage 5 native interaction-reader proof of life completed successfully.

**Result: 3/3 experimental positive complexes PASS.**

| Complex | Ligand | Phe168 recovery | Asn253 recovery | Result |
|---|---|---|---|---|
| 3REY | XAC | Hydrophobic, VdWContact | HBAcceptor, VdWContact | PASS |
| 5OLH | Vipadenant / 9XT | PiStacking, VdWContact | HBAcceptor, HBDonor, VdWContact | PASS |
| 5OLO | Tozadenant / 9XW | Hydrophobic, PiStacking, VdWContact | HBAcceptor, HBDonor, VdWContact | PASS |

ProLIF therefore demonstrated that it can recover both predeclared A2A anchor residues when supplied with true experimental positive poses.

This satisfies the D007 interaction-reader proof-of-life requirement.

The Stage 5 hard gate remains unfrozen. No generated molecules have been evaluated.

---

## Native Ligand Preparation

Native-reader ligand preparation was completed for all three positive controls:

- 3REY — XAC
- 5OLH — Vipadenant / 9XT
- 5OLO — Tozadenant / 9XW

Molscrub was used for the frozen pH 7.4 state assignment.

An initial test demonstrated that Molscrub could not be trusted to preserve crystallographic coordinates even with `--skip_gen3d`. Therefore, for native-reader proof-of-life controls only:

1. authoritative ligand chemistry is obtained from the RCSB CCD;
2. Molscrub supplies the pH-7.4 state;
3. the prepared state is graph-mapped back to the deposited ligand;
4. deposited heavy-atom coordinates are restored;
5. hydrogens are added while retaining the native heavy-atom geometry.

All three ligands passed graph/chemistry assertions and geometric spot checks against the A2A pocket before ProLIF was run.

This coordinate-restoration path applies to native-reader proof-of-life poses. Docking ligands do not require native-coordinate preservation because docking regenerates their poses.

---

## Native Receptor Preparation

Receptors were prepared with:

- PDB2PQR 3.7.1
- PROPKA 3.5.1
- AMBER force field
- pH 7.4
- `--noopt`
- `--nodebump`

### Alternate-location policy

Native receptor alternate locations are resolved before PDB2PQR using the following deterministic rule:

1. select the highest-occupancy deposited alternate;
2. on an occupancy tie, prefer altloc A;
3. otherwise choose the lexicographically first altloc.

Relevant selections included:

**5OLH**
- TRP29 → B, occupancy 0.55
- LEU78 → B, occupancy 0.92
- ARG199 → B, occupancy 0.51

**5OLO**
- MET174 → A, occupancy 0.76
- THR279 → B, occupancy 0.60
- ASN284 → A, occupancy 0.50

This resolved the initial apparent multi-angstrom 5OLH coordinate changes, which were caused by comparison of different deposited alternate conformations rather than true PDB2PQR movement.

### Heavy-atom restoration policy

PDB2PQR/PROPKA supplies the pH-7.4 protonation-state assignment and generated hydrogens, but deposited receptor heavy-atom geometry remains experimentally authoritative for native-reader controls.

After PDB2PQR preparation:

1. pre-restoration displacement of every deposited heavy atom is measured;
2. every deposited heavy atom is restored to its selected experimental coordinate;
3. hydrogens attached to a restored heavy atom are rigidly translated by the same vector as their parent;
4. post-restoration displacement is measured;
5. the persisted restored receptor is reloaded and audited.

PROPKA assigns protonation states on the pre-restoration geometry. The observed preparation-induced changes were side-chain-scale, so protonation-state assignment is treated as unaffected.

Results:

| Complex | Pre-restoration max displacement | Persisted post-restoration max |
|---|---:|---:|
| 3REY | 0.000000 Å | 0.000000 Å |
| 5OLH | 0.000000 Å | 0.000000 Å |
| 5OLO | 1.354101 Å | 0.000000 Å |

The nontrivial 5OLO movement was localized to ASN284:

- CA: 0.005097 Å
- CB: 0.017722 Å
- CG: 0.020683 Å
- OD1: 1.258351 Å
- ND2: 1.354101 Å

HD21 and HD22 were translated with ND2 during restoration.

His250 was ND1-protonated / NE2-unprotonated in all three prepared receptors.

PROPKA His250 pKa:

- 3REY: 3.87
- 5OLH: 3.71
- 5OLO: 3.81

---

## ProLIF Adapter Validation

The validated restored receptor PQR files remain authoritative and are not modified for ProLIF.

A temporary reader-only adapter was required for MDAnalysis/ProLIF compatibility.

### Residue-number compatibility

5OLH and 5OLO contain a genuine deposited `GLY A -1`.

ProLIF stores residue numbers as unsigned integers and cannot represent `-1`.

Therefore, only in the temporary ProLIF representation:

`GLY A -1 -> GLY A 10001`

The validated receptor artifacts remain unchanged.

Phe168 and Asn253 numbering is explicitly audited after adaptation and remains unchanged.

### Protein connectivity

PQR lacks explicit bond topology, requiring MDAnalysis bond inference.

Two deterministic cleanup rules were required before RDKit/ProLIF conversion:

1. inferred H-H bonds are removed because H-H covalent connectivity is invalid in this receptor representation;
2. if a hydrogen has multiple inferred heavy-atom parents and exactly one candidate is in the hydrogen's own residue, the same-residue parent is retained and false inter-residue candidate bonds are removed.

If a unique same-residue parent cannot be identified, preparation stops as ambiguous.

Observed cleanup:

- 3REY: 0 H-H bonds removed; 0 false inter-residue H bonds removed
- 5OLH: 1 H-H bond removed; 0 false inter-residue H bonds removed
- 5OLO: 1 H-H bond removed; 1 false inter-residue H bond removed

The 5OLO inter-residue case was:

- ASN144 HD22 — ND2 ASN144: 1.001 Å, retained
- ASN144 HD22 — O PRO139: 1.421 Å, rejected as false inferred connectivity

After cleanup, every explicit receptor hydrogen had exactly one heavy-atom parent:

- 3REY: 2,317 / 2,317
- 5OLH: 3,084 / 3,084
- 5OLO: 3,034 / 3,034

---

## Final Reader Results

### 3REY / XAC

Phe168:
- Hydrophobic
- VdWContact

Asn253:
- HBAcceptor
- VdWContact

Result: **PASS**

### 5OLH / Vipadenant

Phe168:
- PiStacking
- VdWContact

Asn253:
- HBDonor
- HBAcceptor
- VdWContact

Result: **PASS**

### 5OLO / Tozadenant

Phe168:
- Hydrophobic
- PiStacking
- VdWContact

Asn253:
- HBDonor
- HBAcceptor
- VdWContact

Result: **PASS**

### Layer-1 decision

**Native interaction-reader proof of life: 3/3 PASS.**

ProLIF is therefore permitted to proceed to the next D007 validation layer.

No Stage 5 gate has been selected or frozen from these results.

---

## End-of-Session Status

D007 remains:

`PENDING VALIDATION`

Validation sequence:

1. Interaction-reader proof of life — **3/3 PASS**
2. Cognate self-redocking — **PENDING**
3. Common-3RFM positive/negative control panel — **PENDING**
4. Candidate gate-formulation ledger — **PENDING**
5. Final Stage 5 gate freeze — **PENDING**
6. 16-molecule DiffSBDD Stage 5 baseline — **BLOCKED until gate freeze**

### Next Session

Begin cognate self-redocking validation under the already pinned docking protocol.

For each of:

- 3REY / XAC
- 5OLH / Vipadenant
- 5OLO / Tozadenant

require:

- frozen crystallographic-ligand-centroid search-box rule;
- 20-pose ensemble;
- successful pose heavy-atom RMSD < 2 Å to the crystallographic pose;
- recovery of Phe168 and Asn253 by the validated ProLIF reader;
- rank of the successful pose recorded within the 20-pose ensemble.

The docking parameters remain locked after the first validation result.