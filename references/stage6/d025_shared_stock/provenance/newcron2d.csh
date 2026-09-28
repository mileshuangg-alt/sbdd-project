#!/bin/csh -f 
# cronbuild2d.csh
#
#setenv SQLALCHEMY_DATABASE_URI "postgresql+psycopg2://admin:adminsecret@mem2.cluster.ucsf.bkslab.org:5433/zinc21"
#setenv ZINC_PROTOMER_FILES_ROOT "/nfs/dbraw/zinc"
#setenv ZINC_2D_TRANCHE_FILES_ROOT '/nfs/db/export/2D'
#setenv ZINC_3D_TRANCHE_FILES_ROOT '/nfs/db/export/3D'

#source /nfs/soft/www/apps/zinc15/envs/edge/env.csh
echo starting cronbuild2d
#cd /nfs/export/2D/
# for now we are in /nfs/exe/work/jji 

setenv ZINC_CONFIG_ENV admin

# this loop takes a month to run

setenv i $1
echo $i
foreach j (A B C D E F G H I J K)
	setenv l "${i}${j}"
	setenv k "${l}.d"
	echo i $i j $j k $k l $l
	mkdir $k
	zinc-manage admin export tranches-2d --dir $k $l

	if (-d $l) then
		mv $l $l.old
	endif
	mv $k $l
end
