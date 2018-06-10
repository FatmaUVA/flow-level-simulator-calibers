# this implement TCP fair share where all the flows get a fair share of their bottleneck link

import time
import random
from math import *
import numpy as np
from core import flow, Link, Topology, Request
import operator

epoch = 100.0 #300.0 #1 #timeslot, periodic sceduling, unit seconds
C = int(10000 * 1e6) #160000 # link capaacity in bps

class Scheduler:
    global C #link capacity
    global epoch
    
    def __init__ (self,topo,sim_time,epochx,algo,log,debug = False):
	global epoch
        self.topo = topo
        self.no_accepted_flows = 0
        self.log = log
        self.debug = debug
        self.sim_time = sim_time
        self.algo = algo
        epoch = float(epochx)
        self.pace_threshold = 1000 # the maximum number of flow you can pace to accept new request
        self.success_count = 0
        self.reject_count = 0
        self.no_request = 0
        self.t_now = -1 # current timeslot (epoch)
        self.flows = dict() #indexed by the flow_id
        self.avg_utiliz = [] #for logging to keep track of link utilization    
        self.missed_td = 0

        # these two paramters are for TCP, for every epoch the list is initialized to 0
        self.involved_links = []
        self.invoved_flows = []



    #f is the flow id
    def add_flow(self,f):
        # fro each link in the path of f
        p = self.topo.paths[(self.flows[f].src,self.flows[f].dst)]
        for i in p:
            l = self.topo.Link_set[i]
            if l not in invololved_links:
                self.involved_links.append(l)
                #loop through flows spanning link l
                for f in l.flows:
                    if f not in involved_flows:
                        self.involved_flows.append(f)
                        #recursive call of the function to add all involved flows
                        self.add_flow(f.flow_id)


    # This function implement TCP behaviour of sharing bandwidth between flows
    # new_flows: list of the new flows which holds the new flows IDs
    def find_max_rate_per_flow(self,new_flows):
        global C
        done_flows = [] #list of flows received the max rate in their bottleneck link

        # Find the set of involved_flows and involved_links to find rate perf flow based on each flow bottleneck link rate
        # TODO: remove involved_flows, not needed, only involved_links is needed
        self.involved_links = [] #holds link IDs
        self.involved_flows = [] #holds flows IDs
        for f in new_flows:
            self.add_flow(f)


        #Sort links by the number of flows spanning the links
        #create a list for links that hold the pair of [link_id, no. of flows spanning the link]
        links_id_no_flows_pair = []
        for i in involved_links: #i has link id
            l = self.topo.Link_set[i]
            temp = [l.link_id,len(l.flows)] # create the pair
            links_id_no_flows_pair.append(temp)  #append to the list
        #sort the list by the 2nd value 
        links_id_no_flows_pair.sort(key=lambda x: x[1], reverse=True)
        sorted_links = links_id_no_flows_pair


        # create a dictionary for links info and initialize it
        # dict details{ link_id: [total_flows,rate_per_flow,used_bw,done_flows]}
        # the dictionary is used to make sure flows reach the maximum possible rate, if link has 4 flows
        # then each flow should get C/4, however, one or many of the flows cannot reach C/4 because
        # of other bottleneck link in the path at it can only reach a rate less than C/4,
        # hence, the other flows in the link should get more than C/4
        links_dict = dict()
        #initialize the dictionary
        for i in involved_links:
            l = self.topo.Link_set[i]
            if len(l.flows) > 0:
                temp = [len(l.flows), C/(len(l.flows)*1.0), 0 ,0 ];
            else:
                temp = [len(l.flows), 0, 0 ,0 ];
            links_dict[l.link_id] = temp
    

        # assign rate to flows based on bottleneck link rate
        #loop through links in sorted list and loop through flows to assign rates
        for pair in sorted_links:
            l = self.topo.Link_set[pair[0]] #the first value in the pair is id, second is no of flows spanning the link
            temp = [] #list of max rate can be assigned for a flow in each link
            #assign max rate available for each flow
            for f in l.flows:
                if f not in done_flows:
                    p = self.topo.paths[(self.flows[f].src,self.flows[f].dst)]
                    for i in p:
                        x = self.topo.Link_set[i]
                        link_info = links_dict[x.link_id] #this return a list 
                        temp.append(link_info[1]) #read rate_per_flow files
                    self.flows[f].Ralloc = min(temp) #assign it the bottleneck rate
                    #selflf.flows[f].slack = self.flows[f].Ralloc - self.flows[f].Rmin
                    self.flows[f].te = self.t_now + (self.flows[f].remain_data/(self.flows[f].Ralloc*1.0))
                    if self.debug == True:
                        print "flow",self.flows[f].flow_id ," Ralloc = ",self.flows[f].Ralloc," te = ",self.flows[f].te


            #update link dict to reflect the rate that has already been assigned to the flows
            for f in l.flows:
                if f not in done_flows:
                    done_flows.append(f)
                    p = self.topo.paths[(self.flows[f].src,self.flows[f].dst)]
                    #for each link in the path of f
                    for i in p:
                        x = self.topo.Link_set[i]#get the link object
                        temp = links_dict[x.link_id] #this return a list
                        temp[2] = temp[2] + (C - self.flows[f].Ralloc) #temp[2] is used_bw
                        temp[3] = temp[3] + 1 #done flows
                        if (temp[3] - temp[0]) > 0: #if there are remaining flows didn't get rate assigned
                            temp[1] = (C-temp[2])/temp[1] #update rate_per_flow
                        links_dict[x.link_id] = temp #update links info
        

    def delete_completed_flows(self):
        global epoch
        self.t_now = self.t_now + 1
        current_flows = dict() #need to make a copy to delete
        paths_involved = [] #when a flow completed
        for f in self.flows:
            if self.flows[f].te <= int(self.t_now):
                p = self.topo.paths[(self.flows[f].src, self.flows[f].dst)]
                paths_involved.append(p)
                if self.debug == True:
                    print "flow",f, " finished at epoch = ",self.flows[f].te," deadline = ",self.flows[f].td
                if self.flows[f].te > self.flows[f].td:
                    self.missed_td = self.missed_td + 1
                #delete the flow id from the links involved
                for i in p:
                    l = self.topo.Link_set[i]
                    l.flows.remove(f)
                    if self.debug == True:
                        print "flow",f, "deleted from link ",l.link_id
            else:
                current_flows[f] = self.flows[f]
                current_flows[f].update_tcp(self.t_now)
        self.flows = current_flows #current_flow does not include the finished flows

        self.find_max_rate_per_flow()

 
    def sched(self,requests):
        global epoch
        global C
        #self.t_now = self.t_now + 1
        if self.debug == True:
            print "\nt_now = ", self.t_now

        if self.debug == True:
	        for f in self.flows:
		        p = self.topo.paths[(self.flows[f].src,self.flows[f].dst)]
		        print "flow",f," with links :",p," Ralloc, te: ",self.flows[f].Ralloc, " ", self.flows[f].te

	if len(requests) == 0:
            #no new reuest
            return 0


        involved_paths = []
        involved_flows_id = []
        involved_links_id = []
        for req in requests:
            #find the path
            p = self.topo.paths[(req.src,req.dst)]
            self.no_request = self.no_request + 1
            involved_paths.append(p)
            new_f = flow(self.no_request,req.size,req.td,req.src,req.dst,self.t_now) # the new flow to schedul
            self.flows[new_f.flow_id] = new_f
            if self.debug == True:
                print "new request: flow",new_f.flow_id," size ",req.size," td ", req.td," src,dst ",req.src,req.dst
            self.success_count = self.success_count + 1
            for i in p:
                l = self.topo.Link_set[i]
                l.flows.append(new_f.flow_id)



        self.find_max_rate_per_flow()


    def log_link_utilization(self):
	global epoch
        for i in self.topo.links:
            l = self.topo.Link_set[i]
            l.utilization(self.flows)
#            x = (self.sim_time/epoch) -1
#            if (self.t_now == x) :
#                self.avg_utiliz.append(np.mean(l.utiliz))

    def stop_simulation(self):
        for i in self.topo.links:
            l = self.topo.Link_set[i]
            self.avg_utiliz.append(np.mean(l.utiliz))
