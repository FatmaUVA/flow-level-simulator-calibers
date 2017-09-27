network=$1 #'G-scale' linear one-link or esnet
avg_rate=$2
for sched in 'new-global'  #'new-local'
do
    for algo in 'sjf' 'ljf' 
    do
        for ver in 1 #2
        do
            python run-simulation.py $network $sched $algo $ver $avg_rate &
        done
    done
done
#python run-simulation.py $network 'naive' $algo $ver &
wait
