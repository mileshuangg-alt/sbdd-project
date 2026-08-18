# Stage 5 Docking-Protocol Candidate 3 Validation Report

**Candidate:** Candidate 3 --- smina / Vinardo scoring\
**Status:** PERMANENT FAIL\
**Validation layer:** Stage 5 Layer 2 --- cognate self-redocking\
**Executed complexes:** 3REY / XAC only

## Result

Candidate 3 was executed on 3REY/XAC under the frozen protocol and
retained **19 poses**.

`num_modes = 20` is a maximum. With the frozen
`energy_range = 5 kcal/mol`, 19 eligible retained modes is legitimate
and is **not a protocol deviation**.

The existing ensemble was evaluated without rerunning docking.

-   Best crystal-reference symmetry-aware heavy-atom RMSD: **4.642 Å**
-   Phe168 native interaction pattern (`Hydrophobic + VdWContact`):
    present in many poses
-   Asn253 native acceptor pattern (`HBAcceptor + VdWContact`): absent
    in every retained pose
-   First successful pose rank: **none**

No retained pose satisfied:

``` text
RMSD <= 2.0 Å
AND
Phe168 native-pattern recovery
AND
Asn253 native-pattern recovery with correct directionality
```

## Verdict

**Candidate 3 --- PERMANENT FAIL**

Vinardo altered the generated ensemble, confirming Candidate 3 was a
real experiment and not a duplicate of Candidate 1, but produced no
retained pose satisfying the complete native-geometry plus native-anchor
criterion.

Per the predeclared lock:

-   5OLH / Vipadenant was not run;
-   5OLO / Tozadenant was not run;
-   both remain locked under Candidate 3;
-   Layer 3 remains blocked;
-   Candidate 3 is not retuned.

## Cross-Candidate Observation

  ---------------------------------------------------------------------------
  Candidate     Scoring                      Best Phe168 native Asn253 native
                                crystal-reference chemistry     chemistry
                                             RMSD               
  ------------- ------------- ------------------- ------------- -------------
  Candidate 1   Vina                      1.826 Å absent in the absent in the
                                                  near-native   near-native
                                                  pose          pose

  Candidate 3   Vinardo                   4.642 Å recovered in  absent in
                                                  many poses    every pose
  ---------------------------------------------------------------------------

Candidate 1 was globally near-native with zero anchor recovery in its
near-native pose. Candidate 3 recovered Phe168 chemistry yet stayed
globally far from the crystal pose.

The native Asn253 acceptor chemistry was never recovered by any
qualifying pose under either executed scoring function. **Asn253 is
therefore the discriminating residue that any future candidate rationale
must specifically address.**

This observation does not define or authorize another candidate.
