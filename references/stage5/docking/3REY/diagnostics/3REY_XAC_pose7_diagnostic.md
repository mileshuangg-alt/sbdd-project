# 3REY / XAC Pose 7 Diagnostic

## Classification

**B — Globally close but locally flipped/shifted so the pharmacophore is misregistered.**

## Supporting distances

- Global pose-7 RMSD to crystallographic XAC: **1.826 Å**
- Native Phe168 nearest aromatic/core contact: ligand atom 25:N to Phe168 CE2 = **3.004 Å**
- Pose-7 nearest aromatic/core contact: ligand atom 25:C to Phe168 CD2 = **3.518 Å**
- Corresponding native Phe-nearest atom mapped into pose 7: native 25:N → pose 4:N; nearest Phe168 CE2 distance = **3.635 Å**
- Native Asn253 anchor carbonyl: ligand atom 24:O to Asn253 ND2 = **2.868 Å**
- Pose-7 corresponding carbonyl: native 24:O → pose 6:O
- Pose-7 corresponding carbonyl to Asn253 ND2 = **4.180 Å**
- Pose-7 corresponding carbonyl to Asn253 OD1 = **3.657 Å**

## Native vs. pose-7 anchor geometry

The native XAC pose places the Asn253 anchoring carbonyl at hydrogen-bond distance from Asn253 ND2 (**2.868 Å**). Pose 7 keeps the same heavy-atom chemistry but shifts the corresponding carbonyl away from Asn253 ND2 to **4.180 Å**; its closest Asn253-sidechain approach is to OD1 at **3.657 Å**, which is not compatible with the native H-bond geometry.

The Phe168 core contact is also locally changed. The native nearest aromatic/core contact is ligand atom 25:N to Phe168 CE2 at **3.004 Å**, while pose 7's nearest aromatic/core contact is ligand atom 25:C to Phe168 CD2 at **3.518 Å**, and the mapped native Phe-contact atom is at **3.635 Å**.

## Interpretation

Pose 7 can have **1.826 Å global symmetry-aware heavy-atom RMSD** yet fail both anchors because global RMSD averages displacement over the whole ligand and can remain acceptable when the molecule is locally shifted or misregistered in the binding site.

The heavy-atom SMILES is unchanged, so this is not a protonation-state artifact. Instead, the native Asn253 carbonyl pharmacophore is displaced out of native hydrogen-bond geometry and the Phe168 core-contact atom identity/geometry changes.

Therefore pose 7 is globally close but locally pharmacophore-misregistered, consistent with **Classification B** rather than a valid near-native anchor-recovering pose.

## Decision artifact

See:

`3REY_XAC_pose7_native_overlay.png`

The overlay is rendered in the fixed 3REY receptor coordinate frame without fitting pose 7 onto the native ligand.
