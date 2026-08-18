# Stage 5 Candidate-2 Research Menu

## Status

**Research only — no protocol chosen, no code changed, no docking run.**

Candidate 1 remains permanently failed at Stage 5 Layer 2. The corrected criterion is control-specific native chemistry: correct anchor residue + experimentally recovered ProLIF interaction class + correct donor/acceptor direction where applicable. Candidate 1 failed 3REY/XAC because no retained pose simultaneously achieved crystallographic RMSD <= 2.0 A and the native Phe168/Asn253 interaction patterns.

The purpose of this document is to identify scientifically defensible single-lever alternatives **before any candidate-2 result exists**. Each candidate would require a fresh 3/3 cognate self-redocking validation from zero. Candidate-1 results, including the failure and its diagnostics, remain permanently on record.

## Diagnostic constraint that motivates candidate-2 research

The first Vina run did not simply miss the pocket. Pose 7 was globally close to the crystal pose (1.826 A RMSD) but had no ProLIF interaction with either Phe168 or Asn253. The three poses that previously appeared to recover both residues were 10.3-10.8 A from the crystal and recovered Asn253 through **HBDonor + VdWContact**, whereas native XAC recovers Asn253 through **HBAcceptor + VdWContact**. Thus the corrected result is a genuine pharmacophore-registration failure, not merely a permissive-reader artifact.

This pattern makes four classes of intervention worth researching: ligand electrostatics, scoring function, local receptor flexibility, and a different docking engine.

## Candidate menu — weakest to strongest a priori justification

### 1. Limited receptor side-chain flexibility at the anchor residues

**Proposed single lever:** allow limited, predefined side-chain flexibility at the relevant pocket/anchor residues while holding the ligand preparation, search box, seed, scoring function, and other settings fixed.

**A priori rationale:** rigid-receptor docking can produce false negatives when the receptor conformation is not compatible with the ligand's preferred local interaction geometry. A GPCR docking benchmark found receptor flexibility to be a major determinant of docking performance; allowing receptor side-chain movement improved success, and both large rotations and small side-chain movements were sometimes required to permit the correct ligand pose. citeturn991669search1 A separate GPCR/antitarget study found induced-fit flexibility rescued several experimentally active compounds that were false negatives in rigid-receptor docking. citeturn692516search7

**Why it could address pharmacophore misregistration:** a near-native ligand that is locally unable to realize the correct carbonyl/Phe-core geometry may need a small local receptor accommodation. This lever targets the steric/geometric part of the local energy landscape rather than the ligand graph or interaction reader.

**What we would have to believe:** we would have to believe that a cognate crystal receptor, despite already representing the experimentally bound complex, is still an appropriate starting point for limited induced-fit relaxation; that the relevant side chains are capable of physiologically plausible local motion; and that allowing those motions does not simply manufacture non-native contacts that were not present in the experimental structure. This is the weakest rationale for the present failure because the receptor is the cognate experimental structure rather than a homology model or cross-docking receptor.

**Main methodological risk:** flexibility increases the search space and can create receptor conformations that are useful computationally but are not justified by the experimental complex. A clean candidate would therefore have to predefine exactly which side chains and what flexibility is permitted before rerunning validation.

**Verdict on justification:** defensible, but relatively indirect for this cognate crystal-receptor failure.

### 2. Higher-quality ligand partial charges (AM1-BCC or equivalent)

**Proposed single lever:** replace Meeko's default Gasteiger ligand partial charges with one independently justified higher-quality charge model, such as AM1-BCC, while keeping the molecular state, coordinates, receptor, scoring function, search parameters, and interaction reader fixed.

**A priori rationale:** partial charges directly control the electrostatic contribution to protein-ligand interaction energies. AM1-BCC was designed to reproduce HF/6-31G* electrostatic potentials while remaining practical for organic molecules, and its parameterization/validation paper reports good reproduction of hydrogen-bonded dimer energies and solvation properties. citeturn991669search0turn991669search2 A dedicated docking study comparing multiple electrostatic-charge methods reported the highest pose-prediction success for AM1-BCC among the tested methods. citeturn776158search6 Another study found ligand-charge choice could materially affect docking enrichment and that AM1-BCC performed strongly among tested charge models. citeturn776158search8

**Why it could address pharmacophore misregistration:** XAC carries a formal +1 protonated amine and a carbonyl-rich xanthine core. Changing the ligand partial-charge distribution can change the balance between electrostatics, hydrogen-bond attraction, and competing hydrophobic/steric minima. In principle, that can alter which local ligand registrations are energetically favored without changing the ligand graph or protonation state.

**What we would have to believe:** we would have to believe the observed local misregistration is materially driven by how the ligand's electrostatics are represented, rather than by sampling, sterics, receptor geometry, or the scoring function's other terms. We would also have to justify AM1-BCC as a general charge-model choice for the whole Stage 5 ligand set, not as a charge model selected because it might help XAC.

**Important limitation:** the strongest direct charge-model evidence located here is not Vina-specific. It supports the general scientific proposition that charge representation can alter docking performance, but it does not establish that AM1-BCC will outperform Gasteiger specifically for Vina on A2A ligands.

**Verdict on justification:** reasonably strong and directly connected to a charged ligand's electrostatics, but still mechanistically inferential for this exact failure.

### 3. Vinardo-style scoring-function variant within the Vina/Smina family

**Proposed single lever:** replace Vina's empirical scoring function with the established Vinardo scoring function, while preserving the search region and the rest of the redocking definition.

**A priori rationale:** Vinardo was explicitly developed as a scoring function derived from Vina/Smina with modified steric interactions, atomic radii, weights, and simplified interaction terms. Its developers evaluated docking and redocking performance and reported improved docking, scoring, and ranking performance across the datasets they tested. citeturn976128search0turn976128search1 Smina itself was developed as a Vina fork focused on scoring/minimization and custom scoring functions, and its empirical-scoring work reported better sampling of low-RMSD poses than the default Vina scoring function in cross-docking tests. citeturn776158search0turn776158search2

**Why it could address pharmacophore misregistration:** the current result points at the local energy landscape: the search reaches a globally near-native region but prefers a locally misregistered minimum. A scoring-function change is directly designed to alter how steric, hydrophobic, and hydrogen-bond interactions contribute to pose energy and therefore can change both minimization trajectories and ranking of local minima. Vinardo's changed steric term, atomic radii, and interaction weights give an a priori reason to test whether Vina's local energy ordering is part of the problem. citeturn976128search0

**What we would have to believe:** we would have to believe the present failure reflects deficiencies in Vina's empirical energy surface rather than inadequate sampling. We would also have to accept an implementation consequence: standard Vinardo is exposed through Smina, a Vina fork, so the practical candidate changes the docking executable as well as the scoring function. That should be documented as part of the candidate definition rather than pretending the binary itself is unchanged.

**Important limitation:** the published Vinardo comparison reports broad benchmark improvements, not evidence specific to A2A/3REY or this exact pharmacophore. The rationale is therefore independent of the XAC result but not target-specific.

**Verdict on justification:** strong and unusually well aligned with a suspected energy-landscape problem, with the caveat that the implementation is not a pure one-line Vina scoring toggle.

### 4. Different engine with an independently established pose-scoring/sampling advantage, e.g. GNINA

**Proposed single lever:** replace the Vina docking engine with one independently validated engine such as GNINA, while keeping the receptor preparation, ligand state, box definition, 20-pose allowance, and corrected native-chemistry success criterion fixed.

**A priori rationale:** GNINA integrates convolutional-neural-network scoring into the docking workflow. In its published redocking benchmark, GNINA's CNN scoring improved top-1 <2 A RMSD performance relative to Vina when the binding pocket was explicitly defined; the reported improvement was from 58% to 73% on that benchmark. The authors also reported that the CNN ensemble generalized to held-out proteins/ligands and that CNN score correlated with proximity to the known binding pose. citeturn692516search0turn692516search3 GNINA can use CNN scoring for rescoring, refinement, or throughout the docking process, so it represents a genuinely different pose-selection/scoring mechanism rather than a small parameter adjustment. citeturn976128search3

**Why it could address pharmacophore misregistration:** if the empirical Vina landscape systematically prefers a locally plausible but pharmacophore-misregistered arrangement, a learned pose-quality model gives a fundamentally different representation of protein-ligand geometry for pose ranking/refinement. This is an a priori reason to test whether Vina's scoring model is the limiting component.

**What we would have to believe:** we would have to believe that GNINA's learned scoring generalizes to the A2A/XAC system and that its training data do not give it an inappropriate memorization advantage on these specific structures/chemotypes. We would also have to accept a larger methodological change than a scoring-function swap: GNINA changes the docking implementation and scoring machinery together.

**Main methodological risk:** this is the broadest candidate. Its apparent success could be difficult to attribute to one mechanism, and training-data overlap must be checked before interpreting a successful result as independent methodological corroboration.

**Verdict on justification:** very strong as an independent docking-method alternative, but broadest in scope and therefore the hardest to interpret causally.

## Ranking summary: weakest to strongest justification

| Rank | Lever | A priori justification | Main concern |
|---:|---|---|---|
| 1 | Limited anchor-residue side-chain flexibility | GPCR docking literature directly supports receptor flexibility as a determinant of pose recovery | Cognate crystal receptor is already experimentally bound; flexibility may introduce non-native accommodations |
| 2 | AM1-BCC/equivalent ligand charges | Electrostatics and charge representation directly affect interaction energies; AM1-BCC has established charge-model validation and docking evidence | Evidence is not specifically Vina/A2A; assumes electrostatics drive the misregistration |
| 3 | Vinardo scoring function | Directly targets empirical energy-landscape/scoring behavior and has published improved redocking performance | Practical implementation uses Smina, so executable/scoring-function changes are coupled |
| 4 | Independent engine such as GNINA | Strong published redocking advantage and genuinely different scoring/pose-evaluation machinery | Broadest change; training-data generalization/leakage must be checked |

This ranking is **about strength of independent scientific justification, not an instruction to choose a candidate**.

## Rules for any future candidate-2 test

Every candidate must change exactly one predeclared methodological lever. The rationale must be written before any candidate-2 result exists and may not be "it fixes XAC."

Candidate 1 remains permanently recorded as a failed protocol.

Every candidate-2 variant must restart the complete cognate validation:

```text
3REY / XAC
5OLH / Vipadenant
5OLO / Tozadenant
```

All three must satisfy the corrected native-chemistry criterion before that candidate can proceed to the common 3RFM control panel.

No partial success on XAC is sufficient. No parameter may be adjusted within a candidate after results are observed.

## Decision status

**No candidate 2 selected.**

The purpose of this document is to establish an auditable, result-independent menu of plausible levers. Any future selection should cite this document, explicitly name the single changed lever, and preserve the failed candidate-1 result alongside the new candidate's full 3/3 validation record.

## Sources

1. Jakalian, A., Jack, D.B., Bayly, C.I. (2002). *Fast, efficient generation of high-quality atomic charges. AM1-BCC model: II. Parameterization and validation.* Journal of Computational Chemistry 23(16):1623-1641. DOI: 10.1002/jcc.10128.
2. *The effect of different electrostatic potentials on docking accuracy: a case study using DOCK5.4.* Bioorganic & Medicinal Chemistry Letters 18 (2008):3509-3512. DOI: 10.1016/j.bmcl.2008.05.026.
3. Koes, D.R., Baumgartner, M.P., Camacho, C.J. (2013). *Lessons Learned in Empirical Scoring with smina from the CSAR 2011 Benchmarking Exercise.* Journal of Chemical Information and Modeling 53:1893-1904. DOI: 10.1021/ci300604z.
4. Quiroga, R., Villarreal, M.A. (2016). *Vinardo: A Scoring Function Based on Autodock Vina Improves Scoring, Docking, and Virtual Screening.* PLOS ONE 11(5):e0155183. DOI: 10.1371/journal.pone.0155183.
5. McNutt, A.T. et al. (2021). *GNINA 1.0: molecular docking with deep learning.* Journal of Cheminformatics 13:43. DOI: 10.1186/s13321-021-00522-2.
6. *Evaluating GPCR modeling and docking strategies in the era of deep learning-based protein structure prediction* (2022). This study compared rigid and receptor-flexible docking and found receptor flexibility to be a major determinant of GPCR docking performance, with both large and small side-chain movements sometimes needed for correct poses.
7. *Selectivity Challenges in Docking Screens for GPCR Targets and Antitargets* (2018). This study reported examples where induced-fit receptor relaxation rescued docking false negatives associated with receptor steric conflicts.
