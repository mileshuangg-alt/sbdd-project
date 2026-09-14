#!/usr/bin/env pymol
cmd.load("references/stage5/d017/calibration_runs/N2/post_usalign/usalign_superposition.cif", "structure1")
cmd.load("references/stage5/d017/receptor_inputs/7XY7_R.cif", "structure2")
hide all
set all_states, off
show cartoon, structure1
show cartoon, structure2
show stick, not polymer
show sphere, not polymer
color blue, structure1
color red, structure2
set ribbon_width, 6
set stick_radius, 0.3
set sphere_scale, 0.25
set ray_shadow, 0
bg_color white
set transparency=0.2
zoom polymer and ((structure1 and c. A) or (structure2 and c. R))

