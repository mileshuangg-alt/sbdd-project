# Stage 5 Docking-Protocol Candidate 3 --- Vinardo via smina

**Status:** DEFINED --- NOT YET EXECUTED\
**Results available at definition time:** NONE

Candidate 3 is defined only after Candidate 2 was eliminated before
execution on documentation grounds. Candidate 1 remains permanently
recorded as the only executed-and-failed docking-protocol candidate.

## 1. Single Declared Change

Candidate 3 changes exactly one methodological lever relative to
Candidate 1:

**the docking executable + scoring-function implementation is changed
from AutoDock Vina 1.2.7 using the Vina scoring function to smina using
the built-in Vinardo scoring function.**

This executable+scoring swap is treated as one named methodological
lever because Vinardo is implemented as an optional scoring function
within smina.

``` text
Candidate 1:
AutoDock Vina 1.2.7
scoring function = Vina

Candidate 3:
smina
scoring function = Vinardo
```

No other methodological parameter may change.

## 2. Frozen Parameters Inherited from Candidate 1

  -----------------------------------------------------------------------
  Parameter                           Candidate-3 frozen value
  ----------------------------------- -----------------------------------
  Receptor                            rigid

  Protein preparation                 PDB2PQR / PROPKA, pH 7.4;
                                      experimental heavy-atom coordinates
                                      preserved

  Ligand state preparation            Molscrub, pH 7.4, one
                                      protonation/tautomer state;
                                      tautomer enumeration disabled

  Exhaustiveness                      32

  Random seed                         20260816

  Maximum retained poses              20

  Energy range                        5 kcal/mol

  Search-box dimensions               20 Å × 20 Å × 20 Å

  3REY / XAC center                   49.535806, 23.214581, 34.764065

  5OLH / Vipadenant center            −21.614625, 6.759792, 16.878708

  5OLO / Tozadenant center            19.411107, 173.113429, 17.928714

  Receptor flexibility                none

  RMSD evaluation                     symmetry-aware heavy-atom RMSD to
                                      crystallographic cognate pose

  RMSD threshold                      ≤ 2.0 Å

  Anchor evaluation                   validated ProLIF reader

  Anchor recovery                     control-specific experimentally
                                      recovered native interaction
                                      chemistry, including correct
                                      residue, interaction class, and
                                      donor/acceptor direction where
                                      applicable

  Pose success                        same retained pose must satisfy
                                      RMSD and both native anchor
                                      requirements

  Docking score                       descriptive/ranking only; never a
                                      pass/fail criterion

  Gating                              3REY first; failure stops the
                                      candidate; 3REY pass proceeds to
                                      complete 3/3 validation before
                                      Layer 3
  -----------------------------------------------------------------------

The only declared change is the **Vina executable/scoring implementation
→ smina/Vinardo** swap.

## 3. A Priori Scientific Hypothesis

Candidate 1 produced a geometrically near-native XAC pose but locally
misregistered the pharmacophore: pose 7 reached 1.826 Å symmetry-aware
heavy-atom RMSD yet made no ProLIF contact of any class with Phe168 or
Asn253, and the native Asn253 anchoring carbonyl shifted from 2.868 Å to
4.180 Å.

Unlike the eliminated AM1-BCC candidate, changing from Vina scoring to
Vinardo changes terms that the docking engine actually evaluates.

Vinardo was developed from the Vina scoring-function family and retains
steric, hydrophobic, and non-directional hydrogen-bond components, but
it changes their parameterization and behavior. Published differences
include removal of Vina's second long-range Gaussian steric attraction,
modified atomic radii, changed weights/parameters, and a modified
hydrophobic term. These changes alter the energetic ordering of local
protein-ligand registrations rather than changing a field ignored by the
scoring function.

The a priori hypothesis is:

> Candidate 1's local pharmacophore misregistration may reflect the Vina
> scoring landscape rather than failure to sample the broad binding
> region. Vinardo's independently developed steric, hydrophobic, and
> hydrogen-bond parameterization may reorder competing local
> registrations and favor a pose class that reproduces the
> experimentally established A2A anchor chemistry.

This rationale is independent of whether Candidate 3 ultimately passes
3REY.

Vinardo also has published redocking evidence: its original study
evaluated redocking on multiple curated datasets and reported improved
docking performance relative to Vina across the analyzed datasets.

## 4. Predeclared Prediction

Before any Candidate-3 result exists, the following prediction is
recorded:

**Candidate 3 on 3REY/XAC is predicted to reproduce the native pose
class.**

A retained pose counts as successful only if the same pose satisfies:

``` text
symmetry-aware heavy-atom RMSD <= 2.0 Å

AND

Phe168 native-pattern recovery

AND

Asn253 native-pattern recovery
with correct donor/acceptor direction
```

For 3REY/XAC, the validated native pattern is:

``` text
Phe168:
Hydrophobic
+
VdWContact

Asn253:
HBAcceptor
+
VdWContact
```

The Vinardo score itself is not a success criterion.

## 5. Failure-Acceptance Rule

If Candidate 3 fails the same Stage 5 Layer-2 criterion at 3REY/XAC:

-   Candidate 3 is permanently recorded as an executed failed
    docking-protocol candidate.
-   Candidate 1 remains permanently recorded as the original executed
    failure.
-   Candidate 2 remains permanently recorded as eliminated before
    execution.
-   Candidate 3 is not retuned.
-   5OLH and 5OLO are not run under Candidate 3.
-   Layer 3 remains blocked.

No frozen parameter or evaluation criterion may be changed in response
to the result.

## 6. Validation Sequence

Candidate 3 begins from zero.

### Gate 1 --- 3REY / XAC

Run 3REY/XAC first under the fully locked Candidate-3 protocol.

If 3REY fails:

``` text
Candidate 3:
FAIL

→ preserve result permanently
→ stop Candidate 3
→ do not run 5OLH or 5OLO
→ Layer 3 remains blocked
```

If 3REY passes, Candidate 3 proceeds through the full cognate panel from
zero:

1.  3REY / XAC
2.  5OLH / Vipadenant
3.  5OLO / Tozadenant

All three must pass under the identical frozen Candidate-3 protocol.

Only a **3/3 PASS** unblocks Stage 5 Layer 3.

## 7. Pre-Execution Lock Fields

Candidate 3 is **defined but not executable** until all fields below are
resolved and recorded from the actual local installation.

### smina executable

``` text
smina version:
PENDING — record from actual installation

smina executable path:
PENDING — record from actual installation
```

### Scoring-function selection

The exact command must explicitly request:

``` text
--scoring vinardo
```

Before the first docking run, a non-docking CLI/configuration check must
verify that the installed smina build recognizes `vinardo` as a built-in
scoring function.

The first Candidate-3 docking output/log must verify that Vinardo, not
Vina, was selected. If scoring selection cannot be verified, the run is
invalid and cannot be interpreted as Candidate 3.

### Exact frozen command template

``` text
<smina_executable>   --receptor <frozen_receptor.pdbqt>   --ligand <frozen_ligand.pdbqt>   --scoring vinardo   --center_x <frozen_center_x>   --center_y <frozen_center_y>   --center_z <frozen_center_z>   --size_x 20   --size_y 20   --size_z 20   --exhaustiveness 32   --seed 20260816   --num_modes 20   --energy_range 5   --out <candidate3_output.pdbqt>
```

No Candidate-3 docking command may run until the actual installed smina
version, executable path, supported command syntax, and
scoring-selection verification are written into this document.

### Input invariance

Before execution, Candidate-3 receptor and ligand inputs must be audited
against Candidate 1.

The one-variable design requires receptor structure, ligand molecular
state, coordinates, atom typing, torsion representation, search box, and
evaluation to remain frozen. Any smina-specific compatibility conversion
that changes those features blocks execution for review.

## 8. Candidate-3 Lock Status

``` text
Candidate 1:
PERMANENT EXECUTED FAIL
Layer 2 — 3REY/XAC

Candidate 2:
ELIMINATED BEFORE EXECUTION
0 docking runs consumed

Candidate 3:
DEFINED
NOT YET EXECUTED

Single Candidate-3 change:
AutoDock Vina 1.2.7 / Vina scoring
→
smina / Vinardo scoring

smina version:
PENDING

smina executable:
PENDING

Vinardo selection verification:
PENDING

Candidate-3 results:
NONE

Layer 3:
BLOCKED

Final Stage 5 hard gate:
NOT FROZEN

DiffSBDD Stage 5 baseline:
NOT PERMITTED
```

## References

1.  Quiroga R, Villarreal MA. *Vinardo: A Scoring Function Based on
    Autodock Vina Improves Scoring, Docking, and Virtual Screening.*
    PLOS ONE. 2016;11(5):e0155183. doi:10.1371/journal.pone.0155183.
    https://doi.org/10.1371/journal.pone.0155183
2.  smina source/documentation: built-in alternative scoring functions
    include Vinardo via `--scoring`.
    https://github.com/mwojcikowski/smina
3.  AutoDock Vina documentation, scoring and charge behavior.
    https://autodock-vina.readthedocs.io/en/stable/faq.html
