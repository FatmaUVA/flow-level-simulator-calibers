import numpy as np
import matplotlib.pyplot as plt
import sys

ver = sys.argv[1]

log_dir="/users/fha6np/simulator/9-7-code/results-global-sjf-ver-"+str(ver)+"/"
arrival_rate,rej1,util1 = np.loadtxt(log_dir+"new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/results-global-ljf-ver-"+str(ver)+"/"
arrival_rate,rej2,util2 = np.loadtxt(log_dir+"new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/results-local-ljf-ver-"+str(ver)+"/"
arrival_rate,rej3,util3 = np.loadtxt(log_dir+"new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/results-local-sjf-ver-"+str(ver)+"/"
arrival_rate,rej4,util4 = np.loadtxt(log_dir+"new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)

#to plot only specific range of data
arrival_rate = arrival_rate[0:10]
rej1 = rej1[0:10]
util1 = util1[0:10]
rej2 = rej2[0:10]
util2 = util2[0:10]
rej3 = rej3[0:10]
util3 = util3[0:10]
rej4 = rej4[0:10]
util4 = util4[0:10]

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
perf3_sjf = (1-rej1)/(1-util1)
perf3_ljf = (1-rej2)/(1-util2)
perf3_mblf_ljf = (1-rej3)/(1-util3)
perf3_mblf_sjf = (1-rej4)/(1-util4)

arrival_rate = 1/ arrival_rate
print"arrival rate", arrival_rate

log_dir="/users/fha6np/simulator/9-7-code/plots-9-7/"
#fig, ax1 = plt.subplots()
plt.figure(0)
plt.plot(arrival_rate,perf3_sjf,'bo-',label = 'SJF')
plt.plot(arrival_rate,perf3_ljf,'go-',label = 'LJF')
plt.plot(arrival_rate,perf3_mblf_ljf,'ro-',label = 'MBLF-LJF')
plt.plot(arrival_rate,perf3_mblf_sjf,'mo-',label = 'MBLF-SJF')
#plt.ylabel('Performance (1-(rejct/utilization))')
plt.ylabel('Performance (1-rejct)/(1-utilization')
plt.xlabel('Mean request arrival rate /epoch')
axes = plt.gca()
#axes.set_ylim([0,1])
plt.title('new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600')
plt.legend(title = "Algorithm:",loc='upper left')
file_name="ver-"+str(ver)+"-Performance-new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600-range"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

plt.figure(1)
plt.plot(arrival_rate,rej1,'bo-',label = 'SJF')
plt.plot(arrival_rate,rej2,'go-',label = 'LJF')
plt.plot(arrival_rate,rej3,'ro-',label = 'MBLF-LJF')
plt.plot(arrival_rate,rej4,'mo-',label = 'MBLF-SJF')
plt.plot(arrival_rate,util1,'bo--')
plt.plot(arrival_rate,util2,'go--')
plt.plot(arrival_rate,util3,'ro--')
plt.plot(arrival_rate,util4,'mo--')
plt.ylabel('Reject Ratio') #('exp', color='b')
plt.xlabel('Mean request arrival rate /epoch')
axes = plt.gca()
axes.set_ylim([0,1])
plt.legend(title = "Algorithm:",loc='lower right')
file_name="ver-"+str(ver)+"-reject-utilization-new-arrival-G-scale-uniform-avg-transfer-epoch-1-sim-time-86400-td-3600-range"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

# Shrink current axis by 30%
#box = plt.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])

# Put a legend to the right of the current axis
#plt.legend(title = "Algorithm:",loc='upper right')#, bbox_to_anchor=(1.1, 0))
