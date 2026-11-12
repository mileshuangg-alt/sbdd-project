# LigGate ADMET source input bundle - manifest
Prepared 2026-11-03 PST. Source-level downloads and counts only. No cleaning, no model fits, no label decisions. Files below are untouched originals unless marked.

## A. Recovered cohort originals (cohort-originals/) - delivered to Miles Oct 30; re-recovered from the same iMessage attachment URLs
| File | Rows/sheets | sha256 |
|---|---|---|
| dilirank2_current.xlsx | sheets "version 2" (1338 rows incl. header lines) and "version 1" (1038); header says FDA DILIrank Dataset Ver 2.0 | 1ca1352f...4993 |
| per_drug_research_join_with_reviewed_overlay.csv | 1336 drugs | 9810cd5e...a6dbd |
| reviewed_date_exceptions.csv | 10 rows | c3ff10d2...f857 |
| clinical_automatic_screening_map.csv | 1336 rows, candidate InChIKeys only, not a finalized structure cohort | 7e132acd...ceae4 |
Classification: dilirank2_current.xlsx = DILIrank2 labels (FDA workbook). The other three are RESEARCH-DERIVED overlays (reviewed approval-date overlay, date exceptions, automatic candidate key map). Not publisher dates. Full sha256 in SHA256SUMS.txt.

## B. Approved external sources downloaded (sources/) - untouched originals
| Helper | File | Source URL | Verified counts | Rights |
|---|---|---|---|---|
| AnimalA lesion matrix | animalA_tx500501h_si_002.xlsx | https://acs.figshare.com/articles/dataset/Predicting_Hepatotoxicity_Using_ToxCast_i_in_Vitro_i_Bioactivity_and_Chemical_Structure/2175301 (file ndownloader.figshare.com/files/3809227) | 677 chemicals; lesion union (Hypertrophy/Injury/Proliferative) positive 214; Negative flag 463 | figshare license: CC BY-NC 4.0 |
| Preclinical | preclinical_tx5b00465_si_003.zip, preclin/Public_compounds_heptox_classification.sdf | https://acs.figshare.com/articles/dataset/Computational_Models_for_Human_and_Animal_Hepatotoxicity_with_a_Global_Application_Scope/3124657 (files/4861786) | 3712 SDF records; PC_HT_class present on 3250 (1: 2464, 0: 786); 462 without the field = unknown, not negative | CC BY-NC 4.0 |
| Reactive | reactgall_PMC6278469_supplementary.zip, rg/Table_S1.xlsx, Table_S2.xlsx | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6278469/supplementaryFiles | ReactGAll 977 molecules: 217 positive, 760 negative (matches approved counts) | Molecules 2018 supplement; license not independently checked |
| Reactive structures (candidate supplier only) | metaqm_PM7_opt_structures.mol2 | https://ndownloader.figshare.com/files/47408503 | 2054 molecules in mol2 | CC BY 4.0 per earlier record; name matches are leads, not identity |
| Mito | mito_Training_dataset_31072019.sdf | https://github.com/PharminfoVienna/Mitochondrial-Toxicity (raw: https://raw.githubusercontent.com/PharminfoVienna/Mitochondrial-Toxicity/master/datasets/Training_dataset_31072019.sdf) | 5761 records; Activity Inactive 4936, Active 824, "Inactive, Active" 1; quarantined key YUTJCNNFTOIOGT-UHFFFAOYSA-N present | repository license not checked here |
| BSEP | chembl_status_snapshot_2026-11-03.json (release marker only) | https://www.ebi.ac.uk/chembl/api/data/status.json | ChEMBL_37, released 2026-05-01 | measurement-level snapshot NOT yet built |

## B2. Added in second pass (sources/dili, sources/bsep)
| Item | File | Source | Verified | License as observed |
|---|---|---|---|---|
| DILIPredictor Cmax training input | dili/Cmax_processed.csv (identical copy at data/Cmax_processed.csv in repo) | https://github.com/srijitseal/DILI at pinned commit 98b7a1b7fba4547cefe936b9890b44baab10e490 (committed 2025-08-15) | 727 rows; total plasma pMolar 718 non-empty; unbound plasma pMolar 515 non-empty; column protonated_Standardized_SMILES. Notebook 03a reads it, writes it from Cmax_processed_old.csv.gz (that upstream file is NOT in the repo tree at this commit) and trains two RF regressors (total, unbound), Morgan r2/2048 + MACCS + descriptors + Mordred, 85/15 split seed 42 | Repo code license: MIT (LICENSE saved). Data license not separately stated by the repo. |
| Same data, publisher form | dili/media-2.xlsx sheet S2 (Cmax, 729 rows incl. 2 header lines) | Europe PMC supplementary files for PMC11185581 (bioRxiv 2024.01.10.575128) | sheets S1-S8 present | Europe PMC reports license "cc by"; PMC page links creativecommons.org/licenses/by/4.0/. (Not CC BY-NC.) |
| Publisher S1 structures (AnimalA/others) | dili/media-2.xlsx sheet S1 (20990 rows): Animal hepatotoxicity A 668 rows with names, labels, SMILES (no CAS); Animal hepatotoxicity B 809 with SMILES+CAS; Reactive Metabolite 977 names+labels, no structures; BESP 1780; Mitotox 6459; DILIrank 382; DILIst 1154 | same | counts from file | same as above |
| Publisher supplement doc | dili/media-1.docx | same | not opened | same |
| BSEP ChEMBL 37 raw snapshot | bsep/activities_CHEMBL6020_all_raw.json (2349 activities, all types, target CHEMBL6020 human BSEP), assays_CHEMBL6020_raw.json (85 assays), documents_raw.json | https://www.ebi.ac.uk/chembl/api/data/ (ChEMBL_37, release 2026-05-01), fetched 2026-11-03 | IC50 rows 1717, all nM; relations > 955, = 625, < 137 | ChEMBL license not re-checked here (ChEMBL documents CC BY-SA 3.0; confirm before relying) |
| BSEP subset table | bsep/bsep_family_rows_raw_selected_columns.csv | derived filter of the raw JSON, flagged columns only; NOT a label table | see C | derivative of above |
| AnimalA original paper SI (not a structure source) | animalA_S1/tx500501h_si_001.pdf (16 pages) | figshare 2175307 (files/3809230) | its Table S1 lists 145 liver endpoints and lesion categories, not structures | CC BY-NC 4.0 per figshare |

AnimalA S1 structures (candidate, identity NOT verified): sheet S1 of the publisher workbook has 668 'Animal hepatotoxicity A' rows (name, label, SMILES, no CAS). It is a different file from the approved 677-row lesion matrix. Name-only cross-check (normalized exact names, no identifier or structure check): 668 of 677 matrix names appear in S1, 0 S1 names absent from the matrix, and on those 668 the S1 label equals the matrix union-lesion label (213 positive, 455 negative; matrix has 214 positive overall). The 9 matrix rows without an S1 entry: PharmaCode_0119307, PharmaGSID_48512, Fla (206-44-0), Dipropylene glycol, Propanol 1(or 2)-(2-methoxymethylethoxy)- (34590-94-8), PharmaCode_0343701, 1,2-Benzenedicarboxylic acid di-C9-11-branched alkyl esters (68515-49-1), Silica (7631-86-9), PharmaCode_0200347. S1 labels are not treated as equivalent to the lesion matrix; structures stay candidates until identity alignment is verified. The ToxCast paper's own SI file 1 (figshare 2175307) is a lesion-endpoint table, not structures.

## C. BSEP: raw snapshot kept as downloaded; family question evidence
All 2349 activities and 85 assays for CHEMBL6020 are in bsep/ unfiltered. bsep_family_rows_raw_selected_columns.csv is a convenience view only, not a selection.

Accepted wording (user messages 2026-10-30 14:16-14:29, agent text he approved): "reconstruct the labels from the underlying assay measurements in a fixed ChEMBL 37 snapshot"; "keep the same narrow assay scope"; scope = "the existing human-BSEP radiolabeled taurocholate vesicle-transport family as candidates, not every assay mentioning BSEP or every new 2026 measurement"; "start by recovering original assays/definitions"; other families and undocumented thresholds deferred. The "10 assays / 1535 rows / 1069 IDs" figure was a candidate inventory: assays of records matched to the old 1120 molecule IDs, described as "10 pre-2019 human-BSEP radiolabeled taurocholate vesicle assays", "NOT eligibility or usable labels". So the 10 were found by old-ID matching; the wording itself is a description-defined family. Full-snapshot rows in those 10 assays: 1626 (1535 is the old-ID-matched subset).

Five extra assays selected by the same description wording (pre-2019 document year, membrane vesicle, [3H]-taurocholate, human BSEP) but with no old-ID match:
| Assay | Document (year, journal) | Rows and type | Assay type / metadata | Reading |
|---|---|---|---|---|
| CHEMBL3811149 | CHEMBL3808386, 2016, J Med Chem, MK2 inhibitor review (10.1021/acs.jmedchem.5b01457) | 2 IC50 = 7000 nM | B, Homo sapiens, Sf9, confidence 9; "human BSEP ... Sf9 membrane vesicles ... [3H]-taurocholate transport ... ATP or AMP" | Matches wording. New entities only. |
| CHEMBL4151281 | CHEMBL4145665, 2018, ACS Med Chem Lett, GPR40 AgoPAM (10.1021/acsmedchemlett.8b00149) | 4 IC50 = (1400, 300, 3500, 3200 nM) | A, Sf9, confidence 9; "ATP-dependent [3H]-taurocholic acid uptake" | Matches wording. 2018, so pre-ChEMBL 25 (March 2019) plausibly but not verified. |
| CHEMBL4428921 | CHEMBL4428053, 2016, J Med Chem, NaV1.7 biaryl acyl sulfonamides (10.1021/acs.jmedchem.6b00425) | 1 IC50 = 13300 nM | B, Homo sapiens, no expression system stated; "plasma membrane vesicles ... [3H]-taurocholate ... topcount" | Matches wording; expression system and species detail thinner. |
| CHEMBL4011665 | CHEMBL4011581, 2010, Toxicol Sci (same paper as CHEMBL4011663, 10.1093/toxsci/kfq269) | 1 Imax = 40 % (CHEMBL806) at 100 uM | A | Same assay family but endpoint is Imax %, not IC50. Outside the "IC50 records" scope. |
| CHEMBL4011666 | same | 1 Imax = 50 % (CHEMBL806) at 133 uM | A | Same: Imax, not IC50. |
So: 3 extra assays add 7 IC50 rows (new compounds from three medicinal chemistry counter-screens); 2 assays add 2 Imax rows from the Toxicol Sci 2010 paper already in the set.

Also excluded under either reading: hepatocyte/lysate assays (CHEMBL4011667, 4011668), 2019+ assays and NBD/fluorescent substrates, cell-uptake assays, CHEMBL3707554 (patent, Solvo vesicle assay, substrate not stated; confidence 8, ChEMBL data validity comment H).

Recommendation (one): define the family by the accepted description criteria, not by old-ID matching, and by endpoint IC50. That gives 13 assays and 1633 IC50 rows (1626 + 7). Keep the three newly qualifying assays flagged "wording-qualified, no old-ID evidence" so the per-assay documented-definition review decides each one; keep the 2 Imax rows outside. Reason: the user accepted description wording, not an ID list, and old-ID matching depends on the legacy table, which is itself an audit reference. If the user instead wants strict continuity with the legacy inventory, use the 10. No threshold, relation handling or dedup is applied either way.

## D. PK endpoint sources (added 2026-11-05, sources/pk/ per-file detail in pk/README_PK.md)
| Endpoint | File | Source | Verified | License |
|---|---|---|---|---|
| Lipophilicity logD7.4 | pk/logd74_az.tab | TDC Dataverse doi:10.7910/DVN/21LKWG file 4259595 | 4,200 rows | CC0-1.0 (dataset record) |
| Solubility logS0 | pk/logS0_zenodo4008331.csv | https://zenodo.org/records/4008331 | 829 rows | CC BY 4.0 |
| PAMPA (characterization only) | pk/pampa_ncats.tab | TDC Dataverse doi:10.7910/DVN/21LKWG file 6695858 | 2,035 rows; 1: 1,740 / 0: 295 | CC0-1.0 (dataset record) |
| pKa primary | pk/iupac_pka_v2.4a.csv | https://github.com/IUPAC/Dissociation-Constants pinned v2.4a | 24,211 data rows | CC BY-NC 4.0 (noncommercial scope accepted) |
| pKa validation slice | pk/datawarrior_pka.tsv | pKahub mirror of the DataWarrior set, https://pkahub.ttk.hu/datasets | 7,495 points / 6,050 molecules | UNVERIFIED - validation-slice role only, no training use |
| fu (PPBR) | pk/ppbr_az.tab | TDC Dataverse file 6413140 | 2,828 rows all-species; human 1,614 | CC0-1.0 (dataset record) |
| Clearance (microsome) | pk/clmicro.tab + pk/micro_provenance_crosswalk.csv | AZ clearance set via TDC + ChEMBL 3301361 owner records | 1,101 matched; 1 off-source excluded | CC0-1.0 (dataset record) |
| Clearance (hepatocyte, human) | pk/human_hepa_owner_408.csv + pk/hepa_provenance_crosswalk.csv | owner assay-record snapshot (ChEMBL deposit 3301361), authoritative over TDC clhepa.tab (4 of 408 absent there) | 408 owner-verified human records with relation flags | ChEMBL CC BY-SA 3.0 (records) |
| pKa method codes | pk/method_translation.csv | IUPAC repo /main | O6/O7 regime definitions | CC BY-NC 4.0 |
| Clearance raw assay JSON | pk/chembl_clearance_raw/, pk/az_clearance_assay_records_snapshot.json | https://www.ebi.ac.uk/chembl/api/data/ | unfiltered originals | ChEMBL CC BY-SA 3.0 |


## E. Rights per artifact, exact observed text
- DILIPredictor publisher workbook: the PMC record PMC11185581 is the bioRxiv preprint v2 (2024-06-08). Its page says: "This work is licensed under a Creative Commons Attribution 4.0 International License, which allows reusers to distribute, remix, adapt, and build upon the material in any medium or format, so long as attribution is given to the creator. The license allows for commercial use." Link: https://creativecommons.org/licenses/by/4.0/ . Europe PMC license field: "cc by". Supplements listed there: media-1.docx, media-2.xlsx (the files saved here); no separate license text for the supplements was found on the page.
- Peer-reviewed version (Chem Res Toxicol 2024, PMC11337212, doi 10.1021/acs.chemrestox.4c00015): page text "Published by American Chemical Society Permits the broadest form of re-use including for commercial purposes, provided that author attribution and integrity are maintained (https://creativecommons.org/licenses/by/4.0/)". Crossref license entry: https://creativecommons.org/licenses/by/4.0/ (vor, 2024-07-09). Its SI files (tx4c00015_si_001.pdf, tx4c00015_si_002.xlsx) were not downloaded or compared with media-2.xlsx; no separate SI license text seen.
- Earlier "CC BY-NC 4.0" claim for the publisher workbook: no evidence found for it. The only CC BY-NC 4.0 text observed this session is the figshare license field on AnimalA (2175301, 2175307) and preclinical (3124657). The earlier statement was wrong or unsupported for this workbook.
- DILI repo srijitseal/DILI: MIT (LICENSE file saved, GitHub API spdx MIT) covers code; repo data license not stated.
- FDA DILIrank 2.0 workbook: no license text found on the FDA page; page asks downloaders to notify NCTRBioinformaticsSupport@fda.hhs.gov. License unknown.
- Three overlay/exception/map CSVs: research-derived; inherit unknown.
- AnimalA matrix and preclinical SDF and AnimalA paper SI: figshare field "CC BY-NC 4.0" (https://creativecommons.org/licenses/by-nc/4.0/).
- ReactGAll supplement (PMC6278469, Molecules 2018): Europe PMC license "cc by"; supplement-specific text not separately seen.
- MetaQM figshare 24574495 v1: "CC BY 4.0". Mito repo: MIT (GitHub API). ChEMBL: not re-checked.

## F. Data flags (no transformation applied)
- AnimalA xlsx: 3 CASRN cells are Excel dates: CODE C8018017 (Mancozeb) shows 8018-01-7, C1918021 (Picloram) 1918-02-1, C6893023 (3,5,3'-Triiodothyronine) 6893-02-3. Each CODE equals "C" plus the CAS digits without hyphens; the Animal B sheet in the publisher S1 independently lists mancozeb as 8018-01-7. The cell value should be reconciled against source/code at audit; nothing was changed.
- Mito SDF: one record Activity "Inactive, Active"; quarantined key YUTJCNNFTOIOGT present.
- Preclinical SDF: 462 records without PC_HT_class = unknown.
- Cmax_processed.csv lineage: derived from an upstream file not in the repo.

## hERG addendum (3 Nov 11:57)
See sources/herg/README_PROVENANCE.md

## D. PK endpoint sources (added 2026-11-05, sources/pk/ per-file detail in pk/README_PK.md)
| Endpoint | File | Source | Verified | License |
|---|---|---|---|---|
| Lipophilicity logD7.4 | pk/logd74_az.tab | TDC Dataverse doi:10.7910/DVN/21LKWG file 4259595 | 4,200 rows | CC0-1.0 (dataset record) |
| Solubility logS0 | pk/logS0_zenodo4008331.csv | https://zenodo.org/records/4008331 | 829 rows | CC BY 4.0 |
| PAMPA (characterization only) | pk/pampa_ncats.tab | TDC Dataverse doi:10.7910/DVN/21LKWG file 6695858 | 2,035 rows; 1: 1,740 / 0: 295 | CC0-1.0 (dataset record) |
| pKa primary | pk/iupac_pka_v2.4a.csv | https://github.com/IUPAC/Dissociation-Constants pinned v2.4a | 24,211 data rows | CC BY-NC 4.0 (noncommercial scope accepted) |
| pKa validation slice | pk/datawarrior_pka.tsv | pKahub mirror of the DataWarrior set, https://pkahub.ttk.hu/datasets | 7,495 points / 6,050 molecules | UNVERIFIED - validation-slice role only, no training use |
| fu (PPBR) | pk/ppbr_az.tab | TDC Dataverse file 6413140 | 2,828 rows all-species; human 1,614 | CC0-1.0 (dataset record) |
| Clearance (microsome) | pk/clmicro.tab + pk/micro_provenance_crosswalk.csv | AZ clearance set via TDC + ChEMBL 3301361 owner records | 1,101 matched; 1 off-source excluded | CC0-1.0 (dataset record) |
| Clearance (hepatocyte, human) | pk/human_hepa_owner_408.csv + pk/hepa_provenance_crosswalk.csv | owner assay-record snapshot (ChEMBL deposit 3301361), authoritative over TDC clhepa.tab (4 of 408 absent there) | 408 owner-verified human records with relation flags | ChEMBL CC BY-SA 3.0 (records) |
| pKa method codes | pk/method_translation.csv | IUPAC repo /main | O6/O7 regime definitions | CC BY-NC 4.0 |
| Clearance raw assay JSON | pk/chembl_clearance_raw/, pk/az_clearance_assay_records_snapshot.json | https://www.ebi.ac.uk/chembl/api/data/ | unfiltered originals | ChEMBL CC BY-SA 3.0 |

