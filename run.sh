network=$1 #'G-scale' linear one-link or esnet
for sched in 'global'  # 'local' 'global'
do
    for algo in 'sjf' 'ljf' 
    do
        for ver in 1 2
        do
            python run-simulation.py $network $sched $algo $ver &
#            python run-simulation-esnet.py $sched $algo $ver &
        done
    done
done
python run-simulation.py $network 'naive' $algo $ver &
wait
