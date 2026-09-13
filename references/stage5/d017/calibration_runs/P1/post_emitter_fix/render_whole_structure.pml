run references/stage5/d017/calibration_runs/P1/post_emitter_fix/usalign_superposition.pml

hide everything
show cartoon, structure1
show cartoon, structure2

color blue, structure1
color red, structure2

set cartoon_transparency, 0.55, structure1
set cartoon_transparency, 0.20, structure2

bg_color white
set ray_shadow, 0
set depth_cue, 0

orient structure1 or structure2
zoom structure1 or structure2, 5

ray 1800, 1800
png references/stage5/d017/calibration_runs/P1/post_emitter_fix/P1_whole_structure_superposition.png, dpi=300

quit
