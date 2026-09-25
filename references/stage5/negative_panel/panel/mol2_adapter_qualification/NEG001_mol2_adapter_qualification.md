# NEG001 MOL2 ProLIF Adapter Qualification

Qualification review status: PENDING_HUMAN_REVIEW

## Adapter

- Path: scripts/stage5/mol2_prolif_adapter.py
- Function: load_mol2_ligand_for_prolif

## Coordinate Preservation

- Atom count: 54
- Has conformer: True
- Maximum absolute coordinate deviation: 0.0
- RMS coordinate deviation: 0.0
- Tolerance: none invented; raw deviations are reported.

## Chemical Perception Records

- 3REY_XAC: 5 descriptive differences
- 5OLH_9XT: 5 descriptive differences
- 5OLO_9XW: 1 descriptive differences

## Protected-File Check

- `scripts/stage5/test_native_reader_controls.py` byte-for-byte unchanged: True

## Scope Confirmation

- NEG001 interaction reader run: not run
- blind six-pose ProLIF POD: not run
