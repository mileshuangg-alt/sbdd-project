reinitialize

load references/stage5/d017/calibration_runs/P3/post_usalign/usalign_superposition.cif, structure1
load references/stage5/d017/receptor_inputs/9EBH_R.cif, structure2
load references/stage5/d017/structures/raw/9EBH.cif, ligand_source

hide everything
set all_states, off

remove structure1 and not chain A
remove structure2 and not chain R
remove ligand_source and not (chain R and resn ADN and resi 401)

show cartoon, structure1 and chain A
show cartoon, structure2 and chain R

color blue, structure1 and chain A
color red, structure2 and chain R

set cartoon_transparency, 0.55, structure1 and chain A
set cartoon_transparency, 0.20, structure2 and chain R

select homolog_pocket, structure2 and ((chain R and resi 90 and resn LEU) or (chain R and resi 91 and resn LEU) or (chain R and resi 94 and resn THR) or (chain R and resi 168 and resn PHE) or (chain R and resi 177 and resn MET) or (chain R and resi 243 and resn TRP) or (chain R and resi 246 and resn LEU) or (chain R and resi 250 and resn ASN) or (chain R and resi 264 and resn LEU) or (chain R and resi 268 and resn ILE) or (chain R and resi 271 and resn SER) or (chain R and resi 272 and resn HIS))
select target_pocket, structure1 and ((chain A and resi 84 and resn VAL) or (chain A and resi 85 and resn LEU) or (chain A and resi 88 and resn THR) or (chain A and resi 168 and resn PHE) or (chain A and resi 177 and resn MET) or (chain A and resi 246 and resn TRP) or (chain A and resi 249 and resn LEU) or (chain A and resi 253 and resn ASN) or (chain A and resi 270 and resn MET) or (chain A and resi 274 and resn ILE) or (chain A and resi 277 and resn SER) or (chain A and resi 278 and resn HIS))
select ligand, ligand_source and chain R and resn ADN and resi 401

show sticks, homolog_pocket
show sticks, target_pocket
show sticks, ligand

color orange, homolog_pocket
color cyan, target_pocket
color yellow, ligand

bg_color white
set ray_shadow, 0
set depth_cue, 0

zoom ligand or homolog_pocket or target_pocket, 8

ray 1800, 1800
png references/stage5/d017/calibration_runs/P3/post_usalign/pocket_review.png, dpi=300

quit
