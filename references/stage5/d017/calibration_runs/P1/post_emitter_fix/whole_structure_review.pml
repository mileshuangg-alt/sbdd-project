reinitialize

load references/stage5/d017/calibration_runs/P1/post_emitter_fix/usalign_superposition.cif, structure1
load references/stage5/d017/receptor_inputs/6D9H_R.cif, structure2

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

zoom polymer and ((structure1 and chain A) or (structure2 and chain R)), 8

ray 1800, 1800
png references/stage5/d017/calibration_runs/P1/post_emitter_fix/whole_structure_review.png, dpi=300

quit
