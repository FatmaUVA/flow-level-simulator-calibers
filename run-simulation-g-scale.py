# the input are: 1) average transfer size
#                2) algorithm: global-sjf, global-ljf, local-sjf, local-ljf

import sys
import numpy as np
import networkx as nx
import core
import global_sched_ver_1
import global_sched_ver_2
import local_sched_ver_1
import local_sched_ver_2
import matplotlib.pyplot as plt

G=nx.Graph()
nodes=range(1,13) #12 nodes
G.add_nodes_from(nodes)
edges=[(1,2),(1,3),(2,5),(3,4),(3,6),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,11),(7,8),(8,10),(9,10),(9,11),(10,11),(10,12),(11,12)]
G.add_edges_from(edges)
p=nx.shortest_path(G)
#nx.draw(G)
#plt.savefig('G-scale-topology.png', bbox_inches='tight')

#create a dictionary that includes paths for all src,dst pairs
p_len=len(p)
paths=dict() #dictionary for the paths based on (source,dst) tuple
for i in p:
    for j in xrange(1,p_len+1):
        if i != j:
            temp=p[i][j]
            z=len(p[i][j])
            sub_path=[]
            for k in range(z-1):
                if k != k-1:
                    sub_path.append((temp[k],temp[k+1]))

            paths[(temp[0],temp[z-1])]=sub_path

links=[]
for e in edges:
    links.append((e[1],e[0])) #to consider bi directional links
    links.append(e)

C = 10000 # Mbps
#epoch = int(sys.argv[1]) #100
sim_time = 3600*24

#arrival_rate = [1,2,3,4,5,6,7,8,9,10]
arrival_rate = np.arange(0.1,4,0.15) #lambda, but np.random.exponentional needs (1/lambda)
#arrival_rate = np.arange(2.15,3.35,0.15)
arrival_rate = 1/arrival_rate
td_lambda = 60*60 #1 hour
#s_lambda = int(sys.argv[1]) #200 #500 Mbps average transfer rate
s_lambda = [100,200,300,400,500]
sched = sys.argv[1]
algo = sys.argv[2]
ver = sys.argv[3]
print "sced",sched,"algo",algo,"ver",ver
reject_ratio = []
utilization = []
np.random.seed(3)

for epoch in [1]:#, 5, 10]:
    temp_utilization = []
    temp_reject = []
    for arriv_rate in arrival_rate:
	print "epoch",epoch," arrival_rate",arriv_rate
        tot_req = 0
	t_now = 0 #keep track of slots
        topo = core.Topology(links,paths,C,epoch) #same topology class so it doesn't matter which file to use

        if sched == 'global' and ver == '1':
            s = global_sched_ver_1.Scheduler(topo,sim_time,epoch,algo,log=True,debug=False)
        elif sched == 'global' and int(ver) == 2:
            s = global_sched_ver_2.Scheduler(topo,sim_time,epoch,algo,log=True,debug=False)
        elif sched == 'local' and int(ver) == 1:
            s = local_sched_ver_1.Scheduler(topo,sim_time,epoch,algo,log=True,debug=False)
        elif sched == 'local' and int(ver) == 2:
            s = local_sched_ver_2.Scheduler(topo,sim_time,epoch,algo,log=True,debug=False)
        else:
            print "Invalid algorithm!!!"
            quit()

        epochs = sim_time/epoch
        for i in range(epochs):
            requests = []
	    absolute_t = t_now * epoch
	    inter_arrival = np.random.exponential(arriv_rate)
	    absolute_sum = absolute_t
	    absolute_sum = absolute_sum + inter_arrival
	    while absolute_sum < (t_now+1)*epoch:
                tot_req = tot_req + 1
                td = int(np.random.exponential(td_lambda))
		while td < epoch: 
		    td = int(np.random.exponential(td_lambda))
                avg_rate = np.random.choice(s_lambda)
                size = int((avg_rate * td) / 8) #unit MB
		#size = int((np.random.exponential(s_lambda) * td) / 8)  #unit MB
		#while size < 1 or size*8/td > C:
		#    size = int((np.random.exponential(s_lambda) * td) / 8)
                src = np.random.choice(nodes)
                dst = np.random.choice(nodes)
                while dst == src:
                    dst = np.random.choice(nodes)
                req = core.Request(src,dst,size,0,td)
                requests.append(req)
		inter_arrival = np.random.exponential(arriv_rate)
		absolute_sum = absolute_sum + inter_arrival
            s.sched(requests)
	    t_now = t_now + 1
        if tot_req == 0:
	    reject = 0
            temp_reject.append(0)
        else:
	    reject = float(s.reject_count)/tot_req
            temp_reject.append(float(s.reject_count)/tot_req)
        temp_utilization.append(np.mean(s.avg_utiliz))
        
        print "link utilization ",np.mean(s.avg_utiliz)
        print "reject count = ",s.reject_count, " total requests = ",tot_req, "reject rate = ",reject
    
    #save results    
    log_dir="/users/fha6np/simulator/9-7-code/results-"+sched+"-"+algo+"-ver-"+str(ver)+"/"
    file_name='new-arrival-G-scale-uniform-avg-transfer-'+str(s_lambda)+'-epoch-'+str(epoch)+'-sim-time-'+str(sim_time)+'-td-'+str(td_lambda)
    #f_handle = file(log_dir+file_name+'.csv', 'a')
    #np.savetxt(f_handle, np.transpose((arrival_rate,temp_reject,temp_utilization)), header="arrival_rate,reject_ratio,utilization" ,delimiter=',')
    #f_handle.close()
    np.savetxt(log_dir+file_name+'.csv',np.transpose((arrival_rate,temp_reject,temp_utilization)), header="arrival_rate,reject_ratio,utilization" ,delimiter=',')

