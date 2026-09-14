reinitialize

load references/stage5/d017/calibration_runs/NEG_B_5UEN_B/post_usalign/usalign_superposition.cif, structure1
load references/stage5/d017/receptor_inputs/5UEN_B.cif, structure2

hide everything
set all_states, off

remove structure1 and not chain A
remove structure2 and not chain B

show cartoon, structure1 and chain A
show cartoon, structure2 and chain B

color blue, structure1 and chain A
color red, structure2 and chain B

set cartoon_transparency, 0.55, structure1 and chain A
set cartoon_transparency, 0.20, structure2 and chain B

bg_color white
set ray_shadow, 0
set depth_cue, 0

load references/stage5/d017/structures/raw/5UEN.cif, ligand_source
remove ligand_source and not (chain B and resn DU1 and resi 1201)

select homolog_pocket, structure2 and ((chain B and resi 12 and resn TYR) or (chain B and resi 16 and resn GLU) or (chain B and resi 66 and resn ALA) or (chain B and resi 70 and resn ASN) or (chain B and resi 87 and resn VAL) or (chain B and resi 88 and resn LEU) or (chain B and resi 91 and resn THR) or (chain B and resi 171 and resn PHE) or (chain B and resi 172 and resn GLU) or (chain B and resi 177 and resn MET) or (chain B and resi 180 and resn MET) or (chain B and resi 247 and resn TRP) or (chain B and resi 250 and resn LEU) or (chain B and resi 253 and resn LEU) or (chain B and resi 254 and resn ASN) or (chain B and resi 257 and resn THR) or (chain B and resi 270 and resn THR) or (chain B and resi 271 and resn TYR) or (chain B and resi 274 and resn ILE) or (chain B and resi 278 and resn HIS))
select target_pocket, structure1 and ((chain A and resi 9 and resn TYR) or (chain A and resi 13 and resn GLU) or (chain A and resi 63 and resn ALA) or (chain A and resi 67 and resn SER) or (chain A and resi 84 and resn VAL) or (chain A and resi 85 and resn LEU) or (chain A and resi 88 and resn THR) or (chain A and resi 168 and resn PHE) or (chain A and resi 169 and resn GLU) or (chain A and resi 174 and resn MET) or (chain A and resi 177 and resn MET) or (chain A and resi 246 and resn TRP) or (chain A and resi 249 and resn LEU) or (chain A and resi 252 and resn ILE) or (chain A and resi 253 and resn ASN) or (chain A and resi 256 and resn THR) or (chain A and resi 270 and resn MET) or (chain A and resi 271 and resn TYR) or (chain A and resi 274 and resn ILE) or (chain A and resi 278 and resn HIS))
select ligand, ligand_source and chain B and resn DU1 and resi 1201

show sticks, homolog_pocket
show sticks, target_pocket
show sticks, ligand

color orange, homolog_pocket
color cyan, target_pocket
color yellow, ligand

zoom polymer and ((structure1 and chain A) or (structure2 and chain B)), 8

ray 1800, 1800
png references/stage5/d017/calibration_runs/NEG_B_5UEN_B/post_usalign/whole_protein_pocket_review.png, dpi=300

quit
