# PK source inputs - provenance (assembled 2026-11-05)

Scope: source artifacts for the PK model work, with per-file provenance. The decision record (which datasets, filters, metrics, and protocol were chosen, and by whom) lives in the agreed-plan File dated 5 Nov 2026; this README documents the artifacts only. Nothing here is a training run or a cleaning decision beyond the filters recorded in that plan. Filter-derived counts below are EXPECTED values for version v2.4a under the recorded filter stack - a build should compute and report its own counts and flag deviations, not adjust filters to hit these numbers.

## Files in this directory

| File | What it is | Source / license | Verified facts |
|---|---|---|---|
| iupac_pka_v2.4a.csv | IUPAC Digitized pKa compilation, pinned version 2.4a, sha256 in SHA256SUMS.txt | https://github.com/IUPAC/Dissociation-Constants - CC BY-NC 4.0, noncommercial scope | 24,211 data rows (24,632 physical lines; some quoted fields contain embedded newlines). Expected counts under the recorded filter stack (R+A grades; medium rule; O6/O7 excluded; 25C-else-20-30C; median per molecule-step): 6,784 molecule-steps over 5,496 compounds (530 with both sides); acid steps 2,650/505/100/38/8/2 (steps 1-6), base steps 3,172/265/34/8/2 (steps 1-5). Medium field semantics: "solvent information, if parsable from the remarks column" - blank is unrecorded, not confirmed water. original_T marks 289 "25 (assumed)" + 60 approximate rows. |
| method_translation.csv | IUPAC method-code definitions (O6/O7 = Hammett H0 mineral-acid/alkali regime) | same repo, /main/method_translation.csv | code-to-description mapping for the O6/O7 exclusion |
| datawarrior_pka.tsv | DataWarrior drug-like pKa slice (held out for validation, not training) | pKahub mirror https://pkahub.ttk.hu/datasets (file /static/home/flatfiles/Datawarrior.tsv), primary source "Datawarrior website" (https://openmolecules.org/datawarrior/) | 7,495 points / 6,050 molecules. LICENSE UNVERIFIED - this was the recorded status when the slice role was chosen; treat accordingly. Site assignment columns (assignment_method/assignment_error) are the source's own Epik-based calls, as noted in the decision record. |
| logd74_az.tab | AstraZeneca logD7.4 lipophilicity (endpoint source) | TDC, Harvard Dataverse dataset doi:10.7910/DVN/21LKWG file lipophilicity_astrazeneca.tab (id 4259595); dataset license CC0-1.0 as recorded on the Dataverse record | 4,200 rows, columns Drug_ID / Drug (SMILES) / Y (logD7.4) |
| logS0_zenodo4008331.csv | Intrinsic aqueous solubility logS0 (endpoint source) | https://zenodo.org/records/4008331 - "829 drug-like molecules intrinsic solubility dataset", CC BY 4.0 | 829 rows, columns smiles / logS0 / random / diversity (the record also ships fingerprints.csv and descriptors.csv, not staged - derived features, not labels) |
| pampa_ncats.tab | PAMPA permeability, binary (characterization only) | TDC, same Dataverse dataset, file pampa_ncats.tab (id 6695858); CC0-1.0 | 2,035 rows; labels 1: 1,740 / 0: 295 |
| ppbr_az.tab | Plasma protein binding (fu) source, human-only 1,614 after filtering | TDC, same Dataverse dataset, file ppbr_az.tab (id 6413140); CC0-1.0 | 2,828 rows all-species; fu target per the plan |
| clmicro.tab | Microsomal clearance source | AstraZeneca clearance set via TDC | 1,101 rows matched to owner assay records; 1 off-source row excluded and logged |
| clhepa.tab | Hepatocyte clearance source (mixed species as shipped) | AstraZeneca clearance set via TDC | NOT endpoint-usable as shipped - 2/3 rat. Use human_hepa_owner_408.csv |
| human_hepa_owner_408.csv | Human-hepatocyte-only clearance with owner relation flags | Built directly from the owner assay-record snapshot (az_clearance_assay_records_snapshot.json; ChEMBL deposit https://doi.org/10.6019/chembl3301361). 4 of the 408 records are absent from the TDC clhepa.tab file; the owner records are authoritative | 408 owner-verified human records; censoring keys on the owner relation flags, never bare values |
| micro_provenance_crosswalk.csv, hepa_provenance_crosswalk.csv | row-to-source crosswalks for the clearance sets | derived | provenance joins |
| az_clearance_assay_records_snapshot.json | owner assay-record snapshot used for verification | ChEMBL deposit https://doi.org/10.6019/chembl3301361 | assays 3301370/3301371/3301372 |
| chembl_clearance_raw/ | raw ChEMBL activity/assay JSON pulls for those assays | https://www.ebi.ac.uk/chembl/api/data/ | unfiltered originals |

## Modeling implementation reference (not data)

Chemprop v2.3.1 pinned tag https://github.com/chemprop/chemprop/tree/v2.3.1 - the search space recorded in the plan is its built-in hpopt space, unchanged; masked multi-task loss, bounded loss (bounded-mse), Noam-like LR schedule and the early-stopping flags (--tracking-metric/--patience/--min-delta) were verified against the tagged source on 2026-11-05.
