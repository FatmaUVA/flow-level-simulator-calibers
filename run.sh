network='G-scale' #linear one-link or esnet
avg_rate=100 #$2
ver=1
count=0
for run_no in `seq 1 10`
do
for sched in  'new-fixed' #'new-global' 'new-fixed'
do
    for algo in 'sjf' #'ljf' 
    do
    	if [ $sched = 'new-fixed' ] && [ $algo = 'ljf' ]; then
            continue
        else
	    if [ $((count%2)) -eq 0 ]; then
                echo started $network $sched $algo $ver $avg_rate $run_no
                python run-simulation.py $network $sched $algo $ver $avg_rate $run_no &
            else
                echo started $network $sched $algo $ver $avg_rate $run_no
                python run-simulation.py $network $sched $algo $ver $avg_rate $run_no
            fi
            count=$((count+1))
        fi
    done
done
done
wait
