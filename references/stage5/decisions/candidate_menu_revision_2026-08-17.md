# Stage 5 Docking-Protocol Candidate-Menu Revision Memo

**Date:** 2026-08-17\
**Status:** RESEARCH / MENU-REVISION MEMO --- NO EXPERIMENTS EXECUTED IN
THIS PASS

## Purpose

Candidates 1 and 3 have now both failed the validated Stage-5 Layer-2
cognate redocking test, while Candidate 2 was eliminated before
execution because its declared AM1-BCC charge change cannot affect
AutoDock Vina's `vina` scoring function.

The remaining research menu contained two qualitatively different
levers:

1.  limited flexibility of the Asn253 anchor side chain;
2.  a genuinely different docking engine, GNINA.

This memo records the evidence available **after Candidates 1 and 3**
and revises the candidate menu before any further candidate is selected.

No docking run, code change, or candidate-4 execution is authorized by
this memo.

------------------------------------------------------------------------

# 1. Structural check --- Is rigid Asn253 a plausible cause?

## 1.1 What the experimental structures show

The three cognate positive controls all place the A2A orthosteric
recognition site around the same conserved residues, including
Phe168\^5.29 and Asn253\^6.55. A review of A2A receptor structures
specifically identifies Phe168, Met177, Leu249, Asn253, and Ile274 as
residues that interact with all examined agonists/antagonists in the
structural set. \[Source grade: **Published structural review ---
strong**\] (https://pmc.ncbi.nlm.nih.gov/articles/PMC5736361/)

The exact cognate structures are:

-   **3REY / XAC:** X-ray, 3.31 Å
-   **5OLH / Vipadenant:** X-ray, 2.60 Å
-   **5OLO / Tozadenant:** X-ray, 3.10 Å

The RCSB entries confirm these are experimental A2A receptor complexes.
\[Source grades: **Primary PDB records --- very strong**\] (3REY:
https://www.rcsb.org/structure/3REY; 5OLH:
https://www.rcsb.org/structure/5OLH; 5OLO:
https://www.rcsb.org/structure/5OLO)

The 2011 structural study of 3REY/3RFM/3PWH is particularly important.
It reports that XAC makes the same two key interactions as ZM241385:
π-stacking with Phe168 and a hydrogen bond between the xanthine carbonyl
and Asn253\^6.55. It explicitly reports an approximately 2.9 Å
hydrogen-bond distance and says the Asn253 side-chain rotation relative
to another A2A structure allows the donor NH2 group to engage the XAC
carbonyl. \[Source grade: **Primary structural paper --- very strong**\]
(https://pmc.ncbi.nlm.nih.gov/articles/PMC3732996/)

A second structural analysis independently states that the Asn253 side
chain in 3REY is rotated relative to other A2A structures such as 3RFM,
while the same terminal NH2 group still forms the hydrogen bond to the
purinedione carbonyl in the xanthine complexes. \[Source grade:
**Published structural/molecular-modeling paper --- strong**\]
(https://pmc.ncbi.nlm.nih.gov/articles/PMC3757144/)

A later review of A2A antagonist structures likewise describes Phe168
and Asn253 as recurrent key recognition residues in 5OLH and 5OLO, with
hydrogen bonding to Asn253 in both complexes. \[Source grade:
**Published review --- strong**\]
(https://pmc.ncbi.nlm.nih.gov/articles/PMC7558881/)

## 1.2 Native interaction geometry in the project controls

The validated native-reader measurements already recorded for this
project are:

  -----------------------------------------------------------------------
  Complex                             Native Asn253 interaction evidence
  ----------------------------------- -----------------------------------
  3REY / XAC                          HBAcceptor + VdWContact; HBAcceptor
                                      distance 2.868 Å

  5OLH / Vipadenant                   HBAcceptor + HBDonor + VdWContact;
                                      HBAcceptor distance 3.297 Å;
                                      HBDonor distance 2.804 Å

  5OLO / Tozadenant                   HBAcceptor + HBDonor + VdWContact;
                                      HBAcceptor distance 3.017 Å;
                                      HBDonor distance 2.743 Å
  -----------------------------------------------------------------------

Thus, although the exact receptor rotamer is not numerically identical
across the three deposited complexes, the native structures consistently
place Asn253 in a ligand-engaged, hydrogen-bond-capable environment.

The literature also shows that A2A binding sites exhibit some local
induced fit, including an experimentally observed Asn253 rotamer change
in 3REY relative to other structures. \[Source grade: **Primary
structural paper --- very strong**\]

The evidence therefore does **not** support the simpler statement that
"the receptor is rigid in one generic inactive-state rotamer and
therefore blocks Asn253." The 3REY receptor used for Candidate 1 is
itself the **XAC-bound receptor**, and its Asn253 conformation is
already the experimentally observed conformation that supports the XAC
hydrogen bond.

## 1.3 How much motion would Candidate-1 pose 7 need?

For Candidate-1 pose 7:

``` text
native XAC carbonyl → Asn253 ND2:
2.868 Å

pose-7 corresponding carbonyl → Asn253 ND2:
4.180 Å
```

The scalar distance difference is:

``` text
4.180 - 2.868 = 1.312 Å
```

Therefore, even under the most favorable possible interpretation in
which the ligand carbonyl were held completely fixed and only the Asn253
ND2 atom moved directly toward it, the ND2 position would have to move
by **at least 1.312 Å** to reach the native distance.

That is only a lower bound. A real rotameric side-chain movement would
move multiple atoms and would also have to preserve chemically sensible
geometry.

More importantly, the candidate-1 receptor is already the **cognate
XAC-bound receptor**. The experimentally observed Asn253 rotamer is
therefore not an obviously wrong apo-state rotamer waiting to be
corrected.

### Structural conclusion

**Rigid-receptor failure has a real mechanistic possibility in docking
generally, but this particular XAC result does not provide strong
evidence that an incorrect Asn253 receptor rotamer caused Candidate 1's
failure.**

The burden of proof for a flexibility candidate is therefore high.

To make limited Asn253 flexibility compelling, we would need evidence
that:

1.  the deposited 3REY Asn253 conformation is incompatible with the
    ligand-registration produced by the search;
2.  an alternative physically plausible Asn253 rotamer exists that
    restores the native geometry without requiring the ligand to move
    into the native pose;
3.  allowing that rotamer is a plausible failure-mode correction rather
    than simply adding degrees of freedom until the positive control
    passes.

The current evidence establishes none of these three points.

------------------------------------------------------------------------

# 2. Flexibility literature --- what happens in cognate/self-redocking?

The literature gives a mixed but important answer: receptor flexibility
can rescue cases where the deposited receptor conformation is genuinely
wrong for the ligand, but adding flexibility does **not** generally
improve self-docking automatically and can reduce performance by
enlarging the search space and perturbing scoring.

## 2.1 Explicit receptor-flexibility benchmark

A large study of explicit receptor flexibility compared rigid and
flexible treatment across docking scenarios and specifically included
self-docking. It found that when receptor flexibility was used for
self-docking, success decreased from approximately **94% to 88%** at the
stricter 2 Å criterion in the reported analysis, with the authors
attributing the degradation to the increased search space and additional
noise in side-chain energetics. \[Source grade: **Published
benchmark/method paper --- strong**\]
(https://pubs.acs.org/doi/10.1021/acs.jctc.0c01184)

That is directly relevant because our task is **cognate
self-redocking**, not cross-docking.

The same work found that flexibility can be highly valuable when the
initial receptor structure contains an inaccurate side-chain rotamer or
small pocket-clash problem. Among cases where rigid docking failed
despite reasonably accurate backbones, receptor flexibility rescued
about half of the failures. \[Source grade: **Published benchmark/method
paper --- strong**\]

The important qualification is that those improvements were associated
with actual pocket-side-chain errors or clashes, not merely with the
abstract fact that proteins are flexible.

## 2.2 Other docking studies

AutoDock4 introduced selective receptor flexibility and reported a
188-complex redocking benchmark plus a separate cross-docking set. The
redocking study showed that the method could successfully redock many
complexes, but the benchmark was not a clean controlled comparison
proving that flexible receptors systematically outperform rigid
receptors for cognate self-docking. \[Source grade: **Published
benchmark/method paper --- strong**\]
(https://pmc.ncbi.nlm.nih.gov/articles/PMC2760638/)

FlexAID explicitly supports side-chain flexibility and showed strong
advantages when docking into **non-native** receptor conformations,
especially when critical side-chain movements were required. The authors
emphasize that protein flexibility is particularly important when the
holo conformation is unknown. \[Source grade: **Published
benchmark/method paper --- strong**\]
(https://pubs.acs.org/doi/10.1021/acs.jcim.5b00078)

That is a stronger argument for flexibility in **cross-docking** than in
our current **cognate self-docking** problem.

A later flexible-docking benchmark similarly found that flexible
receptor treatment could rescue wrong side-chain conformations, but also
reported that self-docking accuracy decreased when flexibility was
added, again attributing this to increased search-space size and noisier
energetic ranking. \[Source grade: **Published benchmark --- strong**\]
(https://pmc.ncbi.nlm.nih.gov/articles/PMC8218654/)

## 2.3 Flexibility conclusion

The literature does **not** support the premise:

> "The self-redocking failed, therefore make the receptor flexible."

The stronger literature-supported rule is:

> "Use receptor flexibility when there is independent structural
> evidence that the receptor conformation being docked is wrong or
> insufficient for the ligand."

Our 3REY receptor is already the cognate XAC-bound structure and already
contains the experimentally observed Asn253 arrangement that forms the
native H-bond.

Therefore the flexibility lever has not acquired a sufficiently strong
**a priori** rationale from the Candidate-1/Candidate-3 failures.

------------------------------------------------------------------------

# 3. GNINA assessment

## 3.1 Published redocking and cross-docking performance

GNINA 1.0 provides the strongest direct benchmark evidence among the
remaining levers.

In the published GNINA benchmark, when the binding pocket was defined,
the CNN-rescored GNINA pipeline increased Top-1 redocking success from
**58% with Vina scoring to 73% with the GNINA CNN**, and cross-docking
success from **27% to 37%**. With whole-protein docking, the
corresponding changes were 31% → 38% for redocking and 12% → 16% for
cross-docking. \[Source grade: **Published benchmark/method paper ---
very strong**\] (https://pmc.ncbi.nlm.nih.gov/articles/PMC8191141/)

The authors then repeated the comparison on protein-ligand systems
excluded from the CNN training data. On that unseen subset, GNINA
redocking Top-1 remained about **68%**, while Vina was about **57%**;
cross-docking was about **42% for GNINA versus 23% for Vina**. \[Source
grade: **Published benchmark/method paper --- very strong**\]

This is exactly the type of evidence our candidate-menu rule calls for:
an independent engine with documented gains in cognate redocking and
cross-docking rather than a parameter tweak chosen because it might
rescue the failing control.

## 3.2 Why the mechanism is relevant to Asn253

GNINA's CNN scoring functions do not simply modify Vina's numerical
weights.

The model consumes a 3D grid representation of ligand/receptor atom-type
densities and is explicitly trained for pose scoring. In GNINA 1.3, the
pose-score objective classifies whether a pose is **≤2 Å RMSD from the
ground-truth pose**. \[Source grade: **Published method paper --- very
strong**\] (https://pmc.ncbi.nlm.nih.gov/articles/PMC11874439/)

That is materially different from our Candidate-1 → Candidate-3
progression:

``` text
Candidate 1:
Vina empirical scoring

Candidate 3:
Vinardo, modified empirical Vina-family scoring

Potential next engine:
GNINA CNN pose scoring
```

GNINA therefore supplies a new mechanism for recognizing the local 3D
arrangement of atom types associated with a native pose.

This is especially relevant to the Asn253 problem because the native
Asn253 interaction depends on a specific spatial relationship between:

``` text
Asn253 side-chain NH2
        ↕
ligand carbonyl / acceptor geometry
```

A CNN trained to distinguish native-like ≤2 Å poses can learn spatial
interaction patterns that are not represented as a single explicit
Vina/Vinardo term.

This does not prove GNINA will recover Asn253. It provides the
independent mechanistic rationale that the next experiment should test.

## 3.3 GNINA independence and possible target overlap

GNINA 1.0 used several pretrained CNN ensembles with different training
sets, including PDBbind General 2016 and CrossDocked2020. \[Source
grade: **Primary GNINA method paper --- very strong**\]

GNINA 1.3 states that its modern CNN models were retrained on
**CrossDocked2020 v1.3** and on **ReDocked2020**, a redocked subset of
CrossDocked2020. The pose-scoring model is explicitly trained on
ground-truth pose labels. \[Source grade: **Primary GNINA 1.3 method
paper --- very strong**\]

CrossDocked2020 itself contains approximately 22.5 million poses across
13,840 ligands and 2,900 pockets. \[Source grade: **Published dataset
paper --- very strong**\] (https://pubmed.ncbi.nlm.nih.gov/32865404/)

This creates a real independence question for our A2A test.

A public PDBbind+ record confirms that **5OLO is included in PDBbind**
and that related A2A structures occur at very high sequence similarity.
\[Source grade: **Database record --- moderate/strong for PDBbind
membership; not a training-manifest proof**\]
(https://www.pdbbind-plus.org.cn/browse/6aqf)

I did **not** find a public, searchable source that conclusively
establishes whether **3REY, 5OLH, or 5OLO themselves are included in the
exact CrossDocked2020/GNINA training split used by a specific current
GNINA model**, nor a source that establishes exact A2A-antagonist
training overlap for all three structures.

Therefore a GNINA pass on these targets would **not be proven
independent in the same sense as a benchmark test explicitly excluding
the target complexes**.

This does not make GNINA unusable. It changes the interpretation:

> A GNINA pass would be evidence that an independently different
> docking/scoring engine can recover our target under its pretrained
> learned model, but we should not claim that this constitutes an
> untouched external validation of A2A generalization unless the exact
> GNINA model's training membership is independently checked.

This caveat is important enough that any future GNINA candidate
definition must record the exact GNINA model/version and its training
provenance.

------------------------------------------------------------------------

# 4. Recommendation

## Selected next lever: genuinely different engine --- GNINA

The evidence favors **GNINA over limited Asn253 side-chain flexibility**
as the next candidate.

The evidence chain is:

1.  **The cognate receptor already contains the experimentally observed
    XAC Asn253 geometry.** The XAC structure reports the relevant \~2.9
    Å carbonyl--Asn253 hydrogen bond, and the structural literature
    specifically describes the Asn253 rotamer in 3REY as an induced-fit
    conformation supporting XAC. \[Source grade: **Primary structural
    evidence --- very strong**\]

2.  **Candidate 1 failed while finding a globally near-native pose.**
    That means the receptor's bound conformation is capable of
    supporting the target geometry; the failure was in reproducing the
    ligand's local registration under the frozen scoring/search
    protocol.

3.  **Candidate 3 changed the classical scoring landscape but did not
    recover native Asn253 chemistry at all.** Vinardo therefore tested
    one class of scoring variation without solving the discriminating
    interaction.

4.  **The flexibility literature is mixed for self-docking and
    repeatedly warns that added degrees of freedom can reduce cognate
    redocking success.** Flexibility is most strongly supported when
    independent structural evidence indicates an incorrect receptor
    conformation, which is not the situation for the XAC cognate
    receptor. \[Source grade: **Published benchmarks --- strong**\]

5.  **GNINA provides a genuinely different pose-scoring mechanism with
    published cognate-redocking improvement over Vina.** Its CNN
    explicitly learns pose quality from 3D atom-density representations
    and has demonstrated higher Top-1 redocking performance, including
    on systems excluded from training. \[Source grade: **Published
    benchmark/method paper --- very strong**\]

6.  **The specific mechanism directly addresses our remaining
    uncertainty.** If native Asn253 is already correctly positioned but
    empirical Vina/Vinardo ranking repeatedly fails to identify a pose
    containing the correct local carbonyl--Asn253 geometry, a learned 3D
    pose scorer is a more directly motivated next test than allowing
    that already-correct receptor side chain to move.

### Important limitation

This recommendation does **not** claim GNINA is independent of A2A
structural data. The exact training-set membership of our three PDB
complexes is not established from the public sources located in this
research pass. That must be documented before execution and used to
qualify the interpretation of any GNINA result.

The recommended candidate therefore changes **engine/scoring model
only**, while keeping:

``` text
rigid cognate receptor
same ligand state
same box
same center
same search budget
same pose allowance
same energy-range policy where supported
same RMSD criterion
same control-specific interaction criterion
```

No receptor flexibility is introduced simultaneously.

------------------------------------------------------------------------

# 5. Closing rule

**One more selected candidate; if it fails Layer 2, Stage 5 concludes as
a documented negative result on standard tools under the validated
harness, and the project pivots to the reference-pose fallback gate. No
further levers get invented after results.**

------------------------------------------------------------------------

# Source Grades

  ---------------------------------------------------------------------------------
  Source                  Role in memo                   Grade
  ----------------------- ------------------------------ --------------------------
  Dore et al., 2011; 3REY XAC--Asn253 geometry and       **Published primary
  structural paper        receptor-side-chain induced    structural paper --- very
                          fit                            strong**

  Rucktooa et al., 2018 / Cognate Vipadenant and         **Published primary
  RCSB 5OLH and 5OLO      Tozadenant structures          structures / PDB records
                                                         --- very strong**

  A2A receptor structural Cross-complex Phe168/Asn253    **Published review ---
  reviews                 recognition context            strong**

  Force-field             Direct rigid vs flexible       **Published
  optimization /          self-docking evidence          benchmark/method paper ---
  flexible-docking                                       strong**
  benchmark                                              

  AutoDock4 selective     Receptor-flexibility redocking **Published
  receptor-flexibility    precedent                      benchmark/method paper ---
  paper                                                  strong**

  FlexAID 2015            Flexibility benefit in         **Published
                          non-native structures          benchmark/method paper ---
                                                         strong, but more
                                                         cross-docking-oriented**

  GNINA 1.0               Vina vs CNN                    **Published
                          redocking/cross-docking        benchmark/method paper ---
                          performance                    very strong**

  GNINA 1.3               Current                        **Published method paper
                          CrossDocked2020/ReDocked2020   --- very strong**
                          training provenance            

  CrossDocked2020         Training-set scale and         **Published dataset paper
                          construction                   --- very strong**

  PDBbind+                Evidence that 5OLO occurs in   **Database record ---
                          PDBbind                        moderate/strong; not proof
                                                         of GNINA training
                                                         membership**

  Searchable              Not used to justify the        **Informal --- excluded
  blog/commercial         decision                       from decision evidence**
  articles                                               
  ---------------------------------------------------------------------------------

## Decision status

**MENU REVISION:** adopt GNINA as the single remaining next candidate.

**NOT YET DONE:** candidate definition, implementation lock, GNINA
installation/model pinning, or docking.

No Candidate-4 result exists.
