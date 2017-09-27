import numpy as np
import matplotlib.pyplot as plt
import sys

ver = sys.argv[1]
network = sys.argv[2] #G-scale or esnet
avg_rate = sys.argv[3]

log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-global-sjf-ver-"+str(ver)+"/"
arrival_rate,rej1,util1 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-global-ljf-ver-"+str(ver)+"/"
arrival_rate,rej2,util2 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-local-ljf-ver-"+str(ver)+"/"
arrival_rate,rej3,util3 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-local-sjf-ver-"+str(ver)+"/"
arrival_rate,rej4,util4 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)

perf_sjf = 1- (rej1/util1)
perf_ljf = 1- (rej2/util2)
perf_mblf_sjf = 1- (rej3/util3)
perf_mblf_ljf = 1- (rej3/util4)

perf2_sjf = (1-rej1)*util1
perf2_ljf = (1-rej2)*util2
perf2_mblf_ljf = (1-rej3)*util3
perf2_mblf_sjf = (1-rej4)*util4

#rej1 = np.round(rej1,3)
#rej2 = np.round(rej2,3)
#rej3 = np.round(rej3,3)
#rej4 = np.round(rej4,3)
#util1 = np.round(util1,3)
#util2 = np.round(util2,3)
#util3 = np.round(util3,3)
#util4 = np.round(util4,3)

#perf3_sjf = (1-rej1)/(1-util1)
#perf3_ljf = (1-rej2)/(1-util2)
#perf3_mblf_ljf = (1-rej3)/(1-util3)
#perf3_mblf_sjf = (1-rej4)/(1-util4)
#perf3_naive =  (1-rej5)/(1-util5)

perf2_sjf = abs(rej1-util1)
perf2_ljf = abs(rej2-util2)
perf2_mblf_ljf = abs(rej3-util3)
perf2_mblf_sjf = abs(rej4-util4)

arrival_rate = 1/ arrival_rate
#arrival_rate = np.log(arrival_rate)

log_dir="/users/fha6np/simulator/9-7-code/9-17-results/plots/"
plt.figure(1)
plt.subplot(211)
plt.plot(arrival_rate,perf2_sjf,'bo-', linewidth=2.0, label = 'global-SJF')
plt.plot(arrival_rate,perf2_ljf,'gv-',linewidth=2.0,label = 'global-LJF')
plt.plot(arrival_rate,perf2_mblf_ljf,'r*-',linewidth=2.0,label = 'local-LJF')
plt.plot(arrival_rate,perf2_mblf_sjf,'mx-',linewidth=2.0,label = 'local-SJF')
#plt.plot(arrival_rate,perf3_naive,'ko-',label = 'naive')
#plt.plot(arrival_rate,perf3_mblf_sjf_3,'ko-',label = 'MBLF-SJF-3')
#plt.ylabel('Performance (1-(rejct/utilization))')
#plt.ylabel('Performance (1-rejct)/(1-utilization')
plt.tick_params(axis='both', which='major', labelsize=14)
plt.ylabel('Performance: utilization - reject rate',fontsize=14)
plt.xlabel('Request arrival rate',fontsize=14)
axes = plt.gca()
axes.set_ylim([0,0.5])
#plt.legend(title = "Algorithm:",loc='lower right')
#file_name="new-ver-"+str(ver)+"-Performance2-new-arrival-"+network+"-avg-transfer-"+str(avg_rate)+"-epoch-1-sim-time-86400-td-3600"
#plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

plt.subplot(212)
plt.plot(arrival_rate,rej1*100,'bo-',linewidth=2.0,label = 'global-SJF')
plt.plot(arrival_rate,rej2*100,'gv-',linewidth=2.0,label = 'global-LJF')
plt.plot(arrival_rate,rej3*100,'r*-',linewidth=2.0,label = 'local-LJF')
plt.plot(arrival_rate,rej4*100,'mx-',linewidth=2.0,label = 'local-SJF')
plt.plot(arrival_rate,util1*100,'bo--',linewidth=2.0)
plt.plot(arrival_rate,util2*100,'gv--',linewidth=2.0)
plt.plot(arrival_rate,util3*100,'r*--',linewidth=2.0)
plt.plot(arrival_rate,util4*100,'mx--',linewidth=2.0)
plt.tick_params(axis='both', which='major', labelsize=14)
plt.ylabel('Rate %',fontsize=14) #('exp', color='b')
plt.xlabel('Request arrival rate',fontsize=14)
axes = plt.gca()
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2),
          fancybox=True, shadow=True, ncol=4)
#axes.set_ylim([0,1])
#plt.legend(title = "Algorithm:",loc='lower right')
#file_name="new-ver-"+str(ver)+"-reject-utilization-new-arrival-"+network+"--avg-transfer-"+str(avg_rate)+"-epoch-1-sim-time-86400-td-3600"
file_name="one-plot-ver-"+str(ver)+"-reject-utilization-new-arrival-"+network+"--avg-transfer-"+str(avg_rate)+"-epoch-1-sim-time-86400-td-3600"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

# Shrink current axis by 30%
#box = plt.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])

# Put a legend to the right of the current axis
#plt.legend(title = "Algorithm:",loc='upper right')#, bbox_to_anchor=(1.1, 0))
