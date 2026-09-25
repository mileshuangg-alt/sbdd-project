# D023 DiffSBDD Stage-5 Disposition

Artifact: `references/stage5/d023_diffsbdd_stage5_disposition_20260925.json`

This is a mechanical disposition artifact assembled from preserved Stage-5 measurements. No scientific rerun was performed.

Frozen criterion:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

Disposition basis: `preserved_measurement`

## Summary

| Quantity | Result |
|---|---:|
| Stage-5 input cohort | 16 |
| Retained through Stage 5 | 3/16 |
| Retained molecule IDs | 0, 3, 18 |
| Attrited from forward cascade progression | 13/16 |
| Phe168 reference feature reproduced | 15/16 |
| Asn253 reference feature reproduced | 4/16 |
| Complete frozen A2A recognition pattern reproduced | 3/16 |

The 13 Stage-5-attrited molecules remain permanently retained as characterization evidence. They are not deleted, hidden, or excluded from the scientific record.

## Per-Molecule Disposition

| Molecule ID | Phe168 classes | Phe168 arm | Asn253 classes | Asn253 arm | Complete pattern | Disposition |
|---:|---|---|---|---|---|---|
| 0 | Hydrophobic; VdWContact | true | HBAcceptor; VdWContact | true | true | RETAINED |
| 1 | Hydrophobic | true | VdWContact | false | false | ATTRITED |
| 2 | Hydrophobic; VdWContact | true | VdWContact | false | false | ATTRITED |
| 3 | Hydrophobic | true | HBAcceptor; VdWContact | true | true | RETAINED |
| 5 | Hydrophobic; VdWContact | true | none | false | false | ATTRITED |
| 6 | none | false | HBAcceptor; VdWContact | true | false | ATTRITED |
| 7 | Hydrophobic; VdWContact | true | VdWContact | false | false | ATTRITED |
| 8 | Hydrophobic | true | none | false | false | ATTRITED |
| 9 | Hydrophobic | true | none | false | false | ATTRITED |
| 10 | Hydrophobic | true | VdWContact | false | false | ATTRITED |
| 11 | Hydrophobic | true | VdWContact | false | false | ATTRITED |
| 12 | Hydrophobic | true | none | false | false | ATTRITED |
| 14 | Hydrophobic | true | none | false | false | ATTRITED |
| 17 | Hydrophobic; VdWContact | true | VdWContact | false | false | ATTRITED |
| 18 | Hydrophobic; VdWContact | true | HBAcceptor; VdWContact | true | true | RETAINED |
| 19 | Hydrophobic | true | none | false | false | ATTRITED |

All 13 attrited molecules remain permanently retained as characterization evidence.

## Provenance

| Source | SHA-256 | Role |
|---|---|---|
| `experiments/phase1_diffsbdd/evaluation/stage5_a2a_reference_pattern.csv` | `602ccee156787855452fd2297e0ffc0c41ef72c17a61ab51f30fda876fd5cc2d` | Authoritative preserved DiffSBDD Stage-5 measurement table |
| `experiments/phase1_diffsbdd/evaluation/stage3_input.sdf` | `1f7a12f6a1d231a08d40e360e6b26e7d522b9149e3904860415d4aeacbb7afb0` | Preserved generator-provided coordinate source |
| `notes/Decisions.md` | `eaf66f71bd15fa5573e983219e403837a10036a6ee79ca28dbf4c0b998f4ab69` | D012 historical characterization provenance and D023 authority decision |

D023 is a post-validation authority decision. The 3/16 DiffSBDD outcome was already known when D023 was approved. D023 changes application authority only; it does not change the frozen criterion or any underlying measurement.

D012 recorded the same 3/16 result as characterization-only. D023 does not invalidate that historical record; it authorizes formal Stage-5 cascade disposition from the same preserved measurements.

Claim boundary: the 13 attrited molecules are not called nonbinders or scientifically invalid. Their status is cascade attrition under the validated molecule-level A2A Stage-5 gate, while their measurements remain permanent characterization evidence.
