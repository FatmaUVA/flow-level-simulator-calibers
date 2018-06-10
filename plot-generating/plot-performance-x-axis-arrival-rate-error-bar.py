import numpy as np
import matplotlib.pyplot as plt
import sys

ver = sys.argv[1]
network = sys.argv[2] #G-scale or esnet
avg_rate = sys.argv[3]
epoch = 180 #3 minutes
log_dir="/Users/fatmaalali/flow-level-simulator-calibers/FGCS-results/avg-transfer-exp-"+str(avg_rate)
arrival_rate,rej1,util1 = np.loadtxt(log_dir+"/results-new-global-sjf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
arrival_rate,rej2,util2 = np.loadtxt(log_dir+"/results-new-global-ljf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
arrival_rate,rej3,util3 = np.loadtxt(log_dir+"/results-new-local-sjf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
arrival_rate,rej4,util4 = np.loadtxt(log_dir+"/results-new-local-ljf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)
arrival_rate,rej5,util5 = np.loadtxt(log_dir+"/results-new-fixed-sjf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600.csv",delimiter=',',usecols=(0, 1,2),unpack=True)

arrival_rate = np.loadtxt(log_dir+"/results-new-global-sjf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600-run-1.csv",delimiter=',',usecols=(0,),unpack=True)

#the size of the data
#m: number of rows, which depends on the number of arrival rate
#n: number of columns, which dependes on the number of runs for each arrival rate
m = len(arrival_rate)
n = 10

for sched in ['local','global','fixed']:
    for order in ['sjf', 'ljf']:
        if sched == 'fixed' and order == 'ljf':
            continue
        else:
            temp1 = "rej_"+sched+"_"+order
            temp2 = "util_"+sched+"_"+order
            globals()[temp1] = np.zeros(shape=[n,m]) #create variable names according to sched
            globals()[temp2] = np.zeros(shape=[n,m])
            print sched," ",order
            #read the data for all the runs
            for i in range(1, n+1):
                #eval function evaluate the name stored in the variable string and use it as the variable name for our array
                eval(temp1)[i-1],eval(temp2)[i-1] = np.loadtxt(log_dir+"/results-new-"+sched+"-"+order+"-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600-run-"+str(i)+".csv",delimiter=',',usecols=(1,2),unpack=True) 
            #use the mean value
            temp1_mean = "rej_"+sched+"_"+order+"_mean"
            temp2_mean = "util_"+sched+"_"+order+"_mean"
            globals()[temp1_mean] = np.mean(eval(temp1), axis=0)
            globals()[temp2_mean] = np.mean(eval(temp2), axis=0)
#            print "MEAN = ",np.mean(eval(temp1), axis=0)


perf_global_sjf = (1-rej_global_sjf_mean)/(1-util_global_sjf_mean)
perf_global_ljf = (1-rej_global_ljf_mean)/(1-util_global_ljf_mean)
perf_local_sjf = (1-rej_local_sjf_mean)/(1-util_local_sjf_mean)
perf_local_ljf = (1-rej_local_ljf_mean)/(1-util_local_ljf_mean)
perf_fixed =  (1-rej_fixed_sjf_mean)/(1-util_fixed_sjf_mean)


arrival_rate = 1/ arrival_rate
#arrival_rate = np.log(arrival_rate)

log_dir="/Users/fatmaalali/flow-level-simulator-calibers/FGCS-results/plots/"
#fig, ax1 = plt.subplots()
plt.figure(0)
plt.plot(arrival_rate,perf_global_sjf,'bo-', linewidth=2.0, label = 'global-SJF')
plt.plot(arrival_rate,perf_global_ljf,'gv-',linewidth=2.0,label = 'global-LJF')
plt.plot(arrival_rate,perf_local_sjf,'r*-',linewidth=2.0,label = 'local-SJF')
plt.plot(arrival_rate,perf_local_ljf,'mx-',linewidth=2.0,label = 'local-LJF')
plt.plot(arrival_rate,perf_fixed,'ko-',linewidth=2.0,label = 'fixed')
plt.tick_params(axis='both', which='major', labelsize=14)
plt.ylabel('Performance: sucess_rate / (1 - utilization)',fontsize=14)
plt.xlabel('Request inter-arrival rate',fontsize=14)
axes = plt.gca()
#axes.set_ylim([0,0.5])
plt.legend(title = "Algorithm:",loc='lower right')
file_name="new-ver-"+str(ver)+"-Performance3-new-arrival-"+network+"-avg-transfer-"+str(avg_rate)+"-epoch-"+str(epoch)+"-sim-time-86400-td-3600-error-bar"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')


plt.figure(1)
plt.plot(arrival_rate,rej_global_sjf_mean*100,'bo-',linewidth=2.0,label = 'global-SJF')
plt.plot(arrival_rate,rej_global_ljf_mean*100,'gv-',linewidth=2.0,label = 'global-LJF')
plt.plot(arrival_rate,rej_local_sjf_mean*100,'r*-',linewidth=2.0,label = 'local-SJF')
plt.plot(arrival_rate,rej_local_ljf_mean*100,'mx-',linewidth=2.0,label = 'local-LJF')
plt.plot(arrival_rate,rej_fixed_sjf_mean*100,'ko-',linewidth=2.0,label = 'fixed')

plt.plot(arrival_rate,util_global_sjf_mean*100,'bo--',linewidth=2.0)
plt.plot(arrival_rate,util_global_ljf_mean*100,'gv--',linewidth=2.0)
plt.plot(arrival_rate,util_local_sjf_mean*100,'r*--',linewidth=2.0)
plt.plot(arrival_rate,util_local_ljf_mean*100,'mx--',linewidth=2.0)
plt.plot(arrival_rate,util_fixed_sjf_mean*100,'k--',linewidth=2.0)
plt.tick_params(axis='both', which='major', labelsize=14)
#plt.plot(arrival_rate,util5,'ko--')
plt.ylabel('Rate %',fontsize=14) #('exp', color='b')
plt.xlabel('Request inter-arrival rate',fontsize=14)
axes = plt.gca()
#axes.set_ylim([0,1])
plt.legend(title = "Algorithm:",loc='lower right')
file_name="new-ver-"+str(ver)+"-reject-utilization-new-arrival-"+network+"-avg-transfer-"+str(avg_rate)+"-epoch-"+str(epoch)+"-sim-time-86400-td-3600-eroor-bar"
#file_name="one-plot-ver-"+str(ver)+"-reject-utilization-new-arrival-"+network+"--avg-transfer-"+str(avg_rate)+"-epoch-1-sim-time-86400-td-3600"
plt.savefig(log_dir+file_name+'.png', bbox_inches='tight')

# Shrink current axis by 30%
#box = plt.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])

# Put a legend to the right of the current axis
#plt.legend(title = "Algorithm:",loc='upper right')#, bbox_to_anchor=(1.1, 0))
