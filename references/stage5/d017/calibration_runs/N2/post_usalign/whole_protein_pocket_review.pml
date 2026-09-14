reinitialize

load references/stage5/d017/calibration_runs/N2/post_usalign/usalign_superposition.cif, structure1
load references/stage5/d017/receptor_inputs/7XY7_R.cif, structure2

hide everything
set all_states, off

remove structure1 and not chain A
remove structure2 and not chain R

show cartoon, structure1 and chain A
show cartoon, structure2 and chain R

color blue, structure1 and chain A
color red, structure2 and chain R

set cartoon_transparency, 0.55, structure1 and chain A
set cartoon_transparency, 0.20, structure2 and chain R

bg_color white
set ray_shadow, 0
set depth_cue, 0

load references/stage5/d017/structures/raw/7XY7.cif, ligand_source
remove ligand_source and not (chain R and resn NEC and resi 501)

select homolog_pocket, structure2 and ((chain R and resi 85 and resn VAL) or (chain R and resi 86 and resn LEU) or (chain R and resi 89 and resn THR) or (chain R and resi 90 and resn GLN) or (chain R and resi 93 and resn ILE) or (chain R and resi 173 and resn PHE) or (chain R and resi 182 and resn MET) or (chain R and resi 186 and resn ASN) or (chain R and resi 247 and resn TRP) or (chain R and resi 250 and resn VAL) or (chain R and resi 251 and resn HIS) or (chain R and resi 254 and resn ASN) or (chain R and resi 272 and resn MET) or (chain R and resi 276 and resn ILE) or (chain R and resi 279 and resn SER) or (chain R and resi 280 and resn HIS))
select target_pocket, structure1 and ((chain A and resi 84 and resn VAL) or (chain A and resi 85 and resn LEU) or (chain A and resi 88 and resn THR) or (chain A and resi 89 and resn ALA) or (chain A and resi 92 and resn ILE) or (chain A and resi 168 and resn PHE) or (chain A and resi 177 and resn MET) or (chain A and resi 181 and resn ASN) or (chain A and resi 246 and resn TRP) or (chain A and resi 249 and resn LEU) or (chain A and resi 250 and resn HIS) or (chain A and resi 253 and resn ASN) or (chain A and resi 270 and resn MET) or (chain A and resi 274 and resn ILE) or (chain A and resi 277 and resn SER) or (chain A and resi 278 and resn HIS))
select ligand, ligand_source and chain R and resn NEC and resi 501

show sticks, homolog_pocket
show sticks, target_pocket
show sticks, ligand

color orange, homolog_pocket
color cyan, target_pocket
color yellow, ligand

zoom polymer and ((structure1 and chain A) or (structure2 and chain R)), 8

ray 1800, 1800
png references/stage5/d017/calibration_runs/N2/post_usalign/whole_protein_pocket_review.png, dpi=300

quit
