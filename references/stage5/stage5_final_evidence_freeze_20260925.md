# Stage-5 Final Evidence Freeze

Artifact: `references/stage5/stage5_final_evidence_freeze_20260925.json`

This is a provenance assembly artifact, not a new analysis. No scientific rerun was performed.

Frozen criterion:

```text
(Phe168 Hydrophobic OR PiStacking)
AND
(Asn253 HBAcceptor)
```

## Frozen Results

| Item | Frozen result |
|---|---|
| A2A evidence level | LEVEL 1 |
| Validation positive arm | 3/3 |
| Validation primary-negative arm | 6/6 |
| DiffSBDD Stage-5 disposition | 3/16 retained; 13/16 attrited |
| Phe168 feature | 15/16 |
| Asn253 feature | 4/16 |
| Complete pattern | 3/16 |
| Residue-75 guard, blind negative panel | 6/6 clear |

D023 is a post-validation authority decision. The criterion and preserved measurements were unchanged.

## Evidence Index

| Evidence | Path | SHA-256 |
|---|---|---|
| D022 decision | `notes/Decisions.md` lines 5594-5695 | `eaf66f71bd15fa5573e983219e403837a10036a6ee79ca28dbf4c0b998f4ab69` |
| D023 decision | `notes/Decisions.md` lines 5697-5814 | `eaf66f71bd15fa5573e983219e403837a10036a6ee79ca28dbf4c0b998f4ab69` |
| D012 historical characterization provenance | `notes/Decisions.md` lines 2551-2637 | `eaf66f71bd15fa5573e983219e403837a10036a6ee79ca28dbf4c0b998f4ab69` |
| D019 PLIP decision provenance | `notes/Decisions.md` lines 4481-4560 | `eaf66f71bd15fa5573e983219e403837a10036a6ee79ca28dbf4c0b998f4ab69` |
| D022 positive-arm audit | `references/stage5/d022_positive_arm_audit_20260925.json` | `441fd06afd883637615d33e6a58644cca5fb67d8d373b164584f413217e11e49` |
| Corrected blind negative-panel ProLIF JSON | `references/stage5/negative_panel/panel/blind_negative_panel_prolif_read_20260924T004822Z.json` | `0b230fd7b8e15644760963a85430e58ce97e3cba2acfdb131e75eadafc06a3ee` |
| Blind negative-panel summary | `references/stage5/negative_panel/panel/blind_negative_panel_prolif_read_20260924T004822Z.md` | `7eb6d2cee85aad33df4d4f1ca522dd179b88d69c3c2bed290170a09daf529290` |
| Primary negative-panel manifest | `references/stage5/negative_panel/panel/primary_panel_manifest.json` | `2f958135092c709f57997dfd0b982e94fe6204233db32f3aea6d562633538506` |
| Blind ProLIF input manifest | `references/stage5/negative_panel/panel/blind_prolif_input_manifest.json` | `6e4fd8aefc81693ed497472fdad5caffedd627fdc718134c8dc58b37a41cf3e6` |
| NEG001 MOL2 adapter qualification JSON | `references/stage5/negative_panel/panel/mol2_adapter_qualification/NEG001_mol2_adapter_qualification.json` | `418f5d6cd2f8f280ca7c2e325ce82aea133c39cd7e6d412779ac6f7d8da06d79` |
| NEG001 MOL2 adapter qualification Markdown | `references/stage5/negative_panel/panel/mol2_adapter_qualification/NEG001_mol2_adapter_qualification.md` | `93e719871ee889d6f70d9b0ff903071d46de98d2b53c78ee7d023611d60ca673` |
| Historical frozen ProLIF reader | `scripts/stage5/test_native_reader_controls.py` | `006d0eae192c4776d84d89d3d381c87d289c0fbda749b1ba7c9a93929c07cdf6` |
| Session-011 frozen-bundle reader copy | `references/stage5/negative_panel/session011_frozen_bundle/reader/test_native_reader_controls.py` | `006d0eae192c4776d84d89d3d381c87d289c0fbda749b1ba7c9a93929c07cdf6` |
| PLIP witness configuration | `references/stage5/plip_witness/a2a_witness_config.json` | `4f6deaaf9bf7840263a0f8a9a046126a1c39f6adeb24ca1a538827d1d929b9dd` |
| D019 PLIP positive qualification summary | `references/stage5/plip_witness/qualification/qualification_summary.json` | `08377ea75969b0f996095677ab2340ca19c8ec36025997df3935fe94318d59de` |
| D019 PLIP DiffSBDD cohort concordance summary | `references/stage5/plip_witness/concordance/diffsbdd_stage5_cohort/concordance_summary.json` | `cc2f2f4c1a0e6d7979b66b2e3ccbe7a4f67af30b9897b3802a497fd5d0a3eced` |
| D019 PLIP Session-011 negative-panel concordance summary | `references/stage5/plip_witness/concordance/session011_negative_panel/concordance_summary.json` | `f64d2983b2a396a570466562f6bcfd4bea3d8d262cb0ec5a51155783d298b8c3` |
| Preserved DiffSBDD ProLIF measurement CSV | `experiments/phase1_diffsbdd/evaluation/stage5_a2a_reference_pattern.csv` | `602ccee156787855452fd2297e0ffc0c41ef72c17a61ab51f30fda876fd5cc2d` |
| Preserved DiffSBDD coordinate source | `experiments/phase1_diffsbdd/evaluation/stage3_input.sdf` | `1f7a12f6a1d231a08d40e360e6b26e7d522b9149e3904860415d4aeacbb7afb0` |
| D023 mechanical disposition JSON | `references/stage5/d023_diffsbdd_stage5_disposition_20260925.json` | `929db9d1a1b25d4af109d3e3c328e31c5d1cbf596035fc86941c8c88a906e445` |
| D023 mechanical disposition Markdown | `references/stage5/d023_diffsbdd_stage5_disposition_20260925.md` | `6536c6a3f4aa212253a8a52dbea28c92bf423680685713136c66caac0c898c8d` |

## Missing Provenance

No retained machine-readable native positive ProLIF result object with full per-interaction metadata was found during the D022 positive-arm audit. Preserved class evidence was available and used for D022.

## Claim Boundary

This freeze does not claim pose sensitivity, general or universal specificity, experimental binding, biological efficacy, or transfer of A2A validation authority to another target.

The 13 Stage-5-attrited DiffSBDD molecules are not called nonbinders or scientifically invalid. Their status is cascade attrition under the validated molecule-level A2A Stage-5 gate, while their measurements remain permanent characterization evidence.
