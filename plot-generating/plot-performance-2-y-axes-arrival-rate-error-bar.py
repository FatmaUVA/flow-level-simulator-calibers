# This is the script I used for the latest version of FGCS paper 

import numpy as np
import matplotlib.pyplot as plt
import sys

ver = 1 #sys.argv[1]
network = 'G-scale' #sys.argv[2] #G-scale or esnet
avg_rate = 100 #sys.argv[3]
epoch = 180 #80 #3 minutes
log_dir="/Users/fatmaalali/flow-level-simulator-calibers/FGCS-results/avg-transfer-exp-"+str(avg_rate)

arrival_rate = np.loadtxt(log_dir+"/results-new-global-sjf-ver-"+str(ver)+"/new-arrival-"+network+"-avg-transfer-epoch-"+str(epoch)+"-sim-time-86400-td-3600-run-1.csv",delimiter=',',usecols=(0,),unpack=True)

print "arrival rate = ",1/arrival_rate
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
            #print "MEAN = ",np.mean(eval(temp1, axis=0)
            #print globals()[temp2_mean]


perf_global_sjf = (1-rej_global_sjf_mean)/(1-util_global_sjf_mean)
perf_global_ljf = (1-rej_global_ljf_mean)/(1-util_global_ljf_mean)
perf_local_sjf = (1-rej_local_sjf_mean)/(1-util_local_sjf_mean)
perf_local_ljf = (1-rej_local_ljf_mean)/(1-util_local_ljf_mean)
perf_fixed =  (1-rej_fixed_sjf_mean)/(1-util_fixed_sjf_mean)

print "perf_global_sjf", perf_global_sjf
print "perf_global_ljf", perf_global_ljf
print "perf_local_sjf", perf_local_sjf
print "perf_local_ljf", perf_local_ljf
print "perf_fixed", perf_fixed

print "performance improvement local vs gloabl LJF", (perf_global_ljf-perf_local_ljf)/perf_local_ljf
print "mean ",np.mean((perf_global_ljf-perf_local_ljf)/perf_local_ljf)
arrival_rate = 1/ arrival_rate

log_dir="/Users/fatmaalali/flow-level-simulator-calibers/FGCS-results/plots/"

plt.figure(0)
plt.plot(arrival_rate,perf_global_sjf,'bo-', linewidth=2.0, label = 'global-SJF',markersize=10)
plt.plot(arrival_rate,perf_global_ljf,'gv-',linewidth=2.0,label = 'global-LJF',markersize=10)
plt.plot(arrival_rate,perf_local_sjf,'r*-',linewidth=2.0,label = 'local-SJF',markersize=10)
plt.plot(arrival_rate,perf_local_ljf,'mx-',linewidth=2.0,label = 'local-LJF',markersize=10)
plt.plot(arrival_rate,perf_fixed,'ks-',linewidth=2.0,label = 'fixed',markersize=10)
plt.tick_params(axis='both', which='major', labelsize=14)
plt.ylabel('Performance: success rate / (1 - utilization)',fontsize=14)
plt.xlabel(r'Request arrival rate ($\lambda$)',fontsize=14)

#plt.legend(title = "Algorithm:",loc='lower right')
plt.legend(loc='upper left',ncol=3,bbox_to_anchor=(0.1,1.15))
file_name="new-ver-"+str(ver)+"-Performance3-new-arrival-"+network+"-avg-transfer-"+str(avg_rate)+"-epoch-"+str(epoch)+"-sim-time-86400-td-3600-error-bar"
plt.savefig(log_dir+file_name+'.svg', bbox_inches='tight',format="svg")



#--------- rej and utilization plot--------------------
fig, ax1 = plt.subplots(1)
ax1.set_xlabel(r'Request arrival rate ($\lambda$)',fontsize=14)
ax1.set_ylabel('Reject rate (%)')
ax1.plot(arrival_rate,rej_global_sjf_mean*100,'bo-',linewidth=2.0,label = 'global-SJF')
ax1.plot(arrival_rate,rej_global_ljf_mean*100,'gv-',linewidth=2.0,label = 'global-LJF')
ax1.plot(arrival_rate,rej_local_sjf_mean*100,'r*-',linewidth=2.0,label = 'local-SJF')
ax1.plot(arrival_rate,rej_local_ljf_mean*100,'mx-',linewidth=2.0,label = 'local-LJF')
ax1.plot(arrival_rate,rej_fixed_sjf_mean*100,'ks-',linewidth=2.0,label = 'fixed')
ax1.annotate('Reject rate', xy=(8, 36), xytext=(8, 35),arrowprops=dict(facecolor='black', shrink=0.05))
ax1.tick_params(axis='both', which='major', labelsize=14)
ax1.set_ylim(30,50)
ax1.legend(loc='upper left',ncol=3,bbox_to_anchor=(0.1,1.15))

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
ax2.set_ylabel('Utilization (%)')  # we already handled the x-label with ax1
ax2.plot(arrival_rate,util_global_sjf_mean*100,'bo--',linewidth=2.0)
ax2.plot(arrival_rate,util_global_ljf_mean*100,'gv--',linewidth=2.0)
ax2.plot(arrival_rate,util_local_sjf_mean*100,'r*--',linewidth=2.0)
ax2.plot(arrival_rate,util_local_ljf_mean*100,'mx--',linewidth=2.0)
ax2.plot(arrival_rate,util_fixed_sjf_mean*100,'ks--',linewidth=2.0)
ax2.annotate('Utilization', xy=(4, 46), xytext=(4, 42),arrowprops=dict(facecolor='black', shrink=0.05))
ax2.tick_params(axis='both', which='major', labelsize=14)
ax2.set_ylim(50,75)
#fig.tight_layout()  # otherwise the right y-label is slightly clipped

#add arrows
#ax1.annotate('Reject rate', xy=(8, 37), xytext=(8, 35),arrowprops=dict(facecolor='black', shrink=0.05))
#ax2.annotate('Utilization', xy=(4, 46), xytext=(4, 42),arrowprops=dict(facecolor='black', shrink=0.05))

file_name="fff-new-ver-"+str(ver)+"-reject-utilization-new-arrival-"+network+"-avg-transfer-"+str(avg_rate)+"-epoch-"+str(epoch)+"-sim-time-86400-td-3600-eroor-bar"
plt.savefig(log_dir+file_name+'.svg',format="svg", bbox_inches='tight')

# Shrink current axis by 30%
#box = plt.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])

# Put a legend to the right of the current axis
#plt.legend(title = "Algorithm:",loc='upper right')#, bbox_to_anchor=(1.1, 0))
