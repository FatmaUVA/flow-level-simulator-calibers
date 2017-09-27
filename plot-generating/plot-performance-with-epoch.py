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
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-global-sjf-ver-"+str(ver)+"/"
arrival_rate,rej3,util3 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-300-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-global-ljf-ver-"+str(ver)+"/"
arrival_rate,rej4,util4 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-300-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-global-sjf-ver-"+str(ver)+"/"
arrival_rate,rej5,util5 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-1200-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
log_dir="/users/fha6np/simulator/9-7-code/9-17-results/avg-transfer-exp-"+str(avg_rate)+"/results-new-global-ljf-ver-"+str(ver)+"/"
arrival_rate,rej6,util6 = np.loadtxt(log_dir+"new-arrival-"+network+"-avg-transfer-epoch-1200-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)

#to plot only specific range of data
#arrival_rate = arrival_rate[11:26]
#rej1 = rej1[11:26]
#util1 = util1[11:26]
#rej2 = rej2[11:26]
#util2 = util2[11:26]
#rej3 = rej3[11:26]
#util3 = util3[11:26]
#rej4 = rej4[11:26]
#util4 = util4[11:26]
#rej5 = rej5[11:26]
#util5 = util5[11:26]

perf_sjf_1 = 1- (rej1/util1)
perf_ljf_1 = 1- (rej2/util2)
perf_sjf_300 = 1- (rej3/util3)
perf_ljf_300 = 1- (rej3/util4)
perf_sjf_600 = 1- (rej5/util5)
perf_ljf_600 = 1- (rej6/util6)

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


perf1_sjf_1 = util1-rej1
perf1_ljf_1 = util2-rej2
perf1_sjf_300 = util3-rej3
perf1_ljf_300 = util4-rej4
perf1_sjf_600 = util5-rej5
perf1_ljf_600 = util6-rej6


arrival_rate = 1/ arrival_rate
#arrival_rate = np.log(arrival_rate)
print"arrival rate", arrival_rate

log_dir="/users/fha6np/simulator/9-7-code/9-17-results/plots/"
#fig, ax1 = plt.subplots()
plt.figure(0)
plt.plot(arrival_rate,perf1_sjf_1,'bo-',linewidth=2.,label = 'SJF-epoch-1sec')
plt.plot(arrival_rate,perf1_ljf_1,'gv-',linewidth=2.0,label = 'LJF-epoch-1sec')
plt.plot(arrival_rate,perf1_sjf_300,'r*-',linewidth=2.0,label = 'SJF-epoch-5min')
plt.plot(arrival_rate,perf1_ljf_300,'mx-',linewidth=2.0,label = 'LJF-epoch-5min')
#plt.plot(arrival_rate,perf1_sjf_600,'k+-',label = 'SJF-epoch-1200')
#plt.plot(arrival_rate,perf1_ljf_600,'y.-',label = 'LJF-epoch-1200')
#plt.ylabel('Performance (1-(rejct/utilization))')
#plt.ylabel('Performance (1-rejct)/(1-utilization')
plt.ylabel('Performance: utilization - rejection')
plt.xlabel('Request arrival rate')
plt.tick_params(axis='both', which='major', labelsize=14)
axes = plt.gca()
axes.set_ylim([0,0.5])
plt.title('new-arrival-avg-transfer-100-epoch-1-sim-time-86400-td-3600',fontsize=14)
plt.legend(title = "Algorithm:",loc='lower right',fontsize=14)
file_name="new-ver-"+str(ver)+"-Performance2-new-arrival-"+network+"-avg-transfer-"+str(avg_rate)+"-epoch-analysis-sim-time-86400-td-3600"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

plt.figure(1)
plt.plot(arrival_rate,rej1*100,'bo-',linewidth=2.0,label = 'SJF-epoch-1sec')
plt.plot(arrival_rate,rej2*100,'gv-',linewidth=2.0,label = 'LJF-epoch-1sec')
plt.plot(arrival_rate,rej3*100,'r*-',linewidth=2.0,label = 'SJF-epoch-5min')
plt.plot(arrival_rate,rej4*100,'mx-',linewidth=2.0,label = 'LJF-epoch-5min')
#plt.plot(arrival_rate,rej5,'k+-',label = 'SJF-epoch-1200')
#plt.plot(arrival_rate,rej6,'y.-',label = 'LJF-epoch-1200')
plt.plot(arrival_rate,util1*100,'bo--',linewidth=2.0)
plt.plot(arrival_rate,util2*100,'gv--',linewidth=2.0)
plt.plot(arrival_rate,util3*100,'r*--',linewidth=2.0)
plt.plot(arrival_rate,util4*100,'mx--',linewidth=2.0)
#plt.plot(arrival_rate,util5,'k+--')
#plt.plot(arrival_rate,util6,'y.--')
plt.ylabel('Rate %',fontsize=14) 
plt.xlabel('Request arrival rate',fontsize=14)
plt.tick_params(axis='both', which='major', labelsize=14)
axes = plt.gca()
#axes.set_ylim([0,1])
plt.legend(title = "Algorithm:",loc='lower right')
file_name="new-ver-"+str(ver)+"-reject-utilization-new-arrival-"+network+"--avg-transfer-"+str(avg_rate)+"-epoch-analysis-sim-time-86400-td-3600"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

# Shrink current axis by 30%
#box = plt.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])

# Put a legend to the right of the current axis
#plt.legend(title = "Algorithm:",loc='upper right')#, bbox_to_anchor=(1.1, 0))
