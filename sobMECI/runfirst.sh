cat Input_Header_A geom Input_Tail > Job0_A.gjf
sed -i "s/guess(read)/ /g" Job0_A.gjf
echo Running Job0_A.gjf...
time g16 < Job0_A.gjf > Job0_A.log

cat Input_Header_B geom Input_Tail > Job0_B.gjf
sed -i "s/guess(read)/ /g" Job0_B.gjf
echo Running Job0_B.gjf...
time g16 < Job0_B.gjf > Job0_B.log
