network='G-scale' #linear one-link or esnet
avg_rate=100 #$2
ver=1
for run_no in `seq 1 10`
do
for sched in  'new-local' 'new-global' 'new-fixed'
do
    for algo in 'sjf' 'ljf' 
    do
    	if [ $sched = 'new-fixed' ] && [ $algo = 'ljf' ]; then
            continue
        else
            python run-simulation.py $network $sched $algo $ver $avg_rate $run_no
        fi
    done
done
done
wait
