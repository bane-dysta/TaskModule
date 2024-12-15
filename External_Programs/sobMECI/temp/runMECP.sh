#! /bin/csh -f

@ natom = numatom

ls | grep 'ProgFile' >& /dev/null
if ($status == 0) then
        echo 'ProgFile Exists - OK'
else
        echo 'ProgFile missing'
        exit
endif
ls | grep 'Job0_A.gjf' >& /dev/null
if ($status == 0) then
	echo 'First Input OK'
else
	echo 'First Input Missing'
	exit
endif
ls | grep 'JOBS' >& /dev/null
if ($status != 0) then
	mkdir JOBS
endif
#ls | grep 'ReportFile' >& /dev/null
#if ($status == 0) then
#	cat ReportFile >> reportfile_old
#endif
#date > ReportFile
rm -f traj.xyz
@ num = 0
while ($num < 100)
	echo numatom >> traj.xyz
	echo Step $num >> traj.xyz
	#Remove space lines
	awk 'NF' geom >> traj.xyz
	csh -f sub_script 'Job'$num $natom
	mv -f 'Job'$num'_A.gjf' 'Job'$num'_A.log' JOBS/
	mv -f 'Job'$num'_B.gjf' 'Job'$num'_B.log' JOBS/
	grep 'CONVERGED' < ReportFile >& /dev/null
	if ($status == 0) then
		echo 'MECP optimization has converged at Step'$num
                date >> ReportFile
		exit
	else
		echo 'Step Number '$num' -- MECP not yet converged'
	endif
	grep 'ERROR' < ReportFile >& /dev/null
	if ($status == 0) then
		echo 'An error has occurred, possibly in the Gaussian Job'
		exit
	endif
	@ num ++
	cat Input_Header_A geom Input_Tail > 'Job'$num'_A.gjf'
	cat Input_Header_B geom Input_Tail > 'Job'$num'_B.gjf'
end

