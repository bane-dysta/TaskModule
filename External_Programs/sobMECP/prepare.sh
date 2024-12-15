natm=`awk NF geom | wc -l`

cp temp/MECP.f MECP.f
sed -i "s/numatom/$natm/g" MECP.f
gfortran MECP.f -O -ffixed-line-length-none -o MECP.x
#ifort MECP.f -diag-disable 8290 -extend-source 132 -o MECP.x

rm -f MECP.f

cp -f temp/ProgFile ProgFile
sed -i "s/numatom/$natm/g" ProgFile
cat geom >> ProgFile

cp -f temp/runMECP.sh runMECP.sh
sed -i "s/numatom/$natm/g" runMECP.sh

rm -f ab_initio ReportFile *.chk *.gjf *.log traj.xyz
rm -rf JOBS
