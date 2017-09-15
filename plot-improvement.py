import numpy as np
import matplotlib.pyplot as plt
import sys

network = sys.argv[1] #G-scale or esnet

main_dir = "/users/fha6np/simulator/9-7-code/avg-transfer-exp-100/"
plot_dir = "/users/fha6np/simulator/9-7-code/plots-9-13/"
sched_list = ['global','local']
algo_list = ['sjf','ljf']
ver_list = [1,2]
num_files=8
num_arriv_rate = 26
arrival_rate = np.empty([num_files,num_arriv_rate])
rej = np.empty([num_files,num_arriv_rate])
util = np.empty([num_files,num_arriv_rate])
i = 0
for sched in sched_list:
    for algo in algo_list:
        for ver in ver_list:
            log_dir = main_dir+"results-"+sched+"-"+algo+"-ver-"+str(ver)+"/"
            arrival_rate[i],rej[i],util[i] = np.loadtxt(log_dir+"new-arrival-"+network+"-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
            i = i+1

improve_rej_gsjf = (rej[0] - rej[1])/ rej[1]
improve_rej_gljf = (rej[2] - rej[3])/ rej[3]
improve_rej_lsjf = (rej[4] - rej[5])/ rej[5]
improve_rej_lljf = (rej[6] - rej[7])/ rej[7]

improve_util_gsjf = (util[0] - util[1])/ util[1]
improve_util_gljf = (util[2] - util[3])/ util[3]
improve_util_lsjf = (util[4] - util[5])/ util[5]
improve_util_lljf = (util[6] - util[7])/ util[7]

perf = util - rej
improve_perf_gsjf = (perf[0] - perf[1])/ perf[1]
improve_perf_gljf = (perf[2] - perf[3])/ perf[3]
improve_perf_lsjf = (perf[4] - perf[5])/ perf[5]
improve_perf_lljf = (perf[6] - perf[7])/ perf[7]

arrival_rate = 1/ arrival_rate
print"arrival rate", arrival_rate

#fig, ax1 = plt.subplots()
plt.figure(0)
plt.plot(arrival_rate[0],improve_rej_gsjf*100,'bo-',label = 'global-SJF')
plt.plot(arrival_rate[0],improve_rej_gljf*100,'go-',label = 'global-LJF')
plt.plot(arrival_rate[0],improve_rej_lsjf*100,'ro-',label = 'local-SJF')
plt.plot(arrival_rate[0],improve_rej_lljf*100,'mo-',label = 'local-LJF')
plt.ylabel('Reject rate improvement %')
plt.xlabel('Request arrival rate /epoch')
axes = plt.gca()
#axes.set_ylim([0,1])
plt.title('new-arrival-avg-transfer-100-epoch-1-sim-time-86400-td-3600')
plt.legend(title = "Algorithm:",loc='lower right')
file_name="reject-improvement-new-arrival-"+network+"-avg-transfer-100-epoch-1-sim-time-86400-td-3600"
plt.savefig(plot_dir+file_name+'.png', bbox_inches='tight')

plt.figure(1)
plt.plot(arrival_rate[0],improve_util_gsjf*100,'bo-',label = 'global-SJF')
plt.plot(arrival_rate[0],improve_util_gljf*100,'go-',label = 'global-LJF')
plt.plot(arrival_rate[0],improve_util_lsjf*100,'ro-',label = 'local-SJF')
plt.plot(arrival_rate[0],improve_util_lljf*100,'mo-',label = 'local-LJF')
plt.ylabel('utilization improvement %')
plt.xlabel('Request arrival rate /epoch')
axes = plt.gca()
#axes.set_ylim([0,1])
plt.legend(title = "Algorithm:",loc='upper right')
file_name="utilization-improvement-new-arrival-"+network+"--avg-transfer-100-epoch-1-sim-time-86400-td-3600"
plt.savefig(plot_dir+file_name+'.png', bbox_inches='tight')


plt.figure(2)
plt.plot(arrival_rate[0],improve_perf_gsjf*100,'bo-',label = 'global-SJF')
plt.plot(arrival_rate[0],improve_perf_gljf*100,'go-',label = 'global-LJF')
plt.plot(arrival_rate[0],improve_perf_lsjf*100,'ro-',label = 'local-SJF')
plt.plot(arrival_rate[0],improve_perf_lljf*100,'mo-',label = 'local-LJF')
plt.ylabel('Performance improvement %')
plt.xlabel('Request arrival rate /epoch')
axes = plt.gca()
#axes.set_ylim([0,1])
plt.legend(title = "Algorithm:",loc='upper right')
file_name="performance-improvement-new-arrival-"+network+"--avg-transfer-100-epoch-1-sim-time-86400-td-3600"
plt.savefig(plot_dir+file_name+'.png', bbox_inches='tight')

# Shrink current axis by 30%
#box = plt.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])

# Put a legend to the right of the current axis
#plt.legend(title = "Algorithm:",loc='upper right')#, bbox_to_anchor=(1.1, 0))
