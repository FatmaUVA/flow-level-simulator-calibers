# global SJF in pace and reshape

import time
import random
from math import *
import numpy as np
from core import flow, Link, Topology, Request
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
        self.pace_threshold = 100 # the maximum number of flow you can pace to accept new request
        self.success_count = 0
        self.reject_count = 0
	self.no_request = 0
        self.t_now = -1 # current timeslot (epoch)
        self.flows = dict() #indexed by the flow_id
        self.avg_utiliz = [] #for logging to keep track of link utilization
        
    def pace(self,new_f,p):

        global epoch
        global C
        count_f =0 # counter for the number of flows involved in pacing
        involved_flows = [] #involved flows considered for reshaping
        involved_flows_id = []
        # first for each link find if Rmin is avilable by taking the slack
        for i in p:
            l = self.topo.Link_set[i]
            sum_slack = 0
            if len(l.flows) == 0: # if no flows in the link
                sum_slack = C
            else:
                for f in l.flows: #f holds only the flow id
                    sum_slack = sum_slack + self.flows[f].slack
                    if f not in involved_flows_id:
                        involved_flows_id.append(f)
                        involved_flows.append(self.flows[f])
            if sum_slack < new_f.Rmin: #no enough rate to reach its deadline
                self.reject_count = self.reject_count + 1
                if self.debug == True:
                    print "Reject, no available bandwidth in link ",l.link_id," even with pacing"
                return 0
        
        # Rresid available for the new flow across the entire path
        if self.debug == True:
            print "Success,Rmin is available, reshaping will be done"

        # Rmin found
        # first give it the minimum then redistribute slack rate
        new_f.Ralloc = new_f.Rmin
        new_f.te = int(self.t_now + ceil( (new_f.size/(new_f.Ralloc*1))/epoch))
        if new_f.te > new_f.td:
            new_f.te = new_f.td
        new_f.slack = new_f.Ralloc - new_f.Rmin
        self.flows[new_f.flow_id] = new_f
        self.success_count = self.success_count + 1
        involved_flows.append(new_f)
        involved_flows_id.append(new_f.flow_id)
        #update links with the new flow
        for i in p:
            l = self.topo.Link_set[i]
            l.flows.append(new_f.flow_id)

        #assign Rmin to all involved flows
        for f in involved_flows_id:
            self.flows[f].Ralloc = self.flows[f].Rmin
        # now distribute residual rate
        #sort by te
        if self.algo == 'sjf':
            involved_flows.sort(key=lambda x: x.te, reverse=False)
        elif self.algo == 'ljf':
            involved_flows.sort(key=lambda x: x.te, reverse=True)
        else:
            print "invalid algo"
        
        for f in involved_flows:
            p = self.topo.paths[(f.src,f.dst)]
            path_Rresid = []
            for i in p:
                l = self.topo.Link_set[i]
                temp_sum = 0
                for x in l.flows:
                    temp_sum = temp_sum + self.flows[x].Ralloc 
                l_slack = C - temp_sum # link slack capacity that we want to redistribute
                if l_slack <= 0:
                    path_Rresid.append(0)
                    break #no resid bandwidth in one of the links on the path so break
                path_Rresid.append(l_slack)
            f_max_path_Rresid = min(path_Rresid)
            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin + f_max_path_Rresid
            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
            self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id]    .Ralloc*1.0)) /epoch))
            if int(self.flows[f.flow_id].te) > int(self.flows[f.flow_id].td):
                self.flows[f.flow_id].te = self.flows[f.flow_id].td
            if self.debug == True:
                print "flow",f.flow_id ,"reshaped. Ralloc = ",self.flows[f.flow_id].Ralloc," te = ",self.flows[f.flow_id].te

    def revert_flow_changes(self,involved_flows):
        for f in involved_flows:
            self.flows[f.flow_id] = f 
	    #if self.debug == True:
	   #     print " flow ",f.flow_id," revert changes "

    def update_current_flows(self):
        global epoch
        paths_involved = []
        current_flows = dict() #need to make a copy to delete
        for f in self.flows:
            if int(self.flows[f].te) == self.t_now:
                p = self.topo.paths[(self.flows[f].src, self.flows[f].dst)]
                paths_involved.append(p)
                if self.debug == True:
                    print "flow ",f, " finished"
                #delete the flow id from the links involved
                for i in p:
                    l = self.topo.Link_set[i]
                    l.flows.remove(f)
                    if self.debug == True:
                        print "flow ",f, "deleted from link ",l.link_id
            else:
                current_flows[f] = self.flows[f]
                current_flows[f].update(self.t_now)
        self.flows = current_flows #current_flow does not include the finished flows
        
        #Find the disjoint set of impacted links
        involved_links = []
        involved_flows = []
        involved_flows_id = []
        for p in paths_involved:
            for i in p:
                l = self.topo.Link_set[i]
                if i not in involved_links:
                    involved_links.append(i)
                #find the disjoint set of flows in the impacted paths
                for f in l.flows:
                    if f not in involved_flows_id:
                        involved_flows.append(self.flows[f])
                        involved_flows_id.append(f)
		
            #sort by te
            if self.algo == 'sjf':
                involved_flows.sort(key=lambda x: x.te, reverse=False)
            elif self.algo == 'ljf':
                involved_flows.sort(key=lambda x: x.te, reverse=True)
            else:
                print "invalid algo"
            #create sets to do issubset operation
            involved_links_set = set(involved_links)
            for f in involved_flows:
                pi = self.topo.paths[(f.src,f.dst)]
                p_set = set(pi)
                if p_set.issubset(involved_links_set):
                    # allocate more rate to f
                    path_Rresid = []
                    for i in pi:
                        l = self.topo.Link_set[i]
                        temp_sum = 0
                        for x in l.flows:
                            temp_sum = temp_sum + self.flows[x].Ralloc
                        l.Rresid = C - temp_sum
                        path_Rresid.append(l.Rresid)
                    Rresid = min(path_Rresid)
                    if (f.Ralloc + Rresid) <= f.Rmax and Rresid > 0:
                        self.flows[f.flow_id].Ralloc = f.Ralloc + Rresid
                        self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch)) #TODO check
                        #self.flows[f.flow_id].te = int(self.t_now + (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch)
			if self.flows[f.flow_id].te > self.flows[f.flow_id].td: #this is due to floating point op
			    #print "true te > td, Ralloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data 
			    self.flows[f.flow_id].te = self.flows[f.flow_id].td
                        if self.flows[f.flow_id].te == int(self.t_now):
                            #print "true te = t_now, Ralloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data
                            self.flows[f.flow_id].te = self.flows[f.flow_id].te + 1
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
                            #print "link is ",l.link_id ," error, flow ",f.flow_id,"  size-sent ",self.flows[f.flow_id].size - self.flows[f.flow_id]    .sent_data," Ralloc ",self.flows[f.flow_id].Ralloc,"epoch ",epoch," t_now ",self.t_now," te ",self.flows[f.flow_id].te, " Rmin ",self.flows[f.flow_id].Rmin," flow path is ",p
                    elif (f.Ralloc + Rresid) > f.Rmax and Rresid > 0:
                        self.flows[f.flow_id].Ralloc = f.Rmax
			self.flows[f.flow_id].te = self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch)
                        #self.flows[f.flow_id].te = int(self.t_now + (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch)
			if self.flows[f.flow_id].te > self.flows[f.flow_id].td: #this is due to floating point op
			    #print "true te < td, Ralloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data
			    self.flows[f.flow_id].te = self.flows[f.flow_id].td
                        if self.flows[f.flow_id].te == int(self.t_now):
                            #print "true te = t_now, Ralloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data
                            self.flows[f.flow_id].te = self.flows[f.flow_id].te + 1
			self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin


    def sched(self,requests):
        global epoch
	global C
        self.t_now = self.t_now + 1
        if self.debug == True:
            print "\nt_now = ", self.t_now

        if self.log == True:
            self.log_link_utilization()

        #remove finished flows and update current flow status
        self.update_current_flows()

        if self.debug == True:
	    for f in self.flows:
		p = self.topo.paths[(self.flows[f].src,self.flows[f].dst)]
		print "flow ",f," with links :",p," Ralloc, te: ",self.flows[f].Ralloc, " ", self.flows[f].te

	if len(requests) == 0:
            #no new reuest
            return 0

        for req in requests:
            #find the path
            p = self.topo.paths[(req.src,req.dst)]
	    self.no_request = self.no_request + 1
	    #new_f.flow_id = self.no_request
	    new_f = flow(self.no_request,req.size,req.td,req.src,req.dst,self.t_now) # the new flow to schedul
            if self.debug == True:
                print "new request id: ",new_f.flow_id,"path",p," size ",req.size," td ", req.td," src,dst ",req.src,req.dst

            # find Rresidual bandwidth in the path p
	    avail_rate = []
            for i in p:
                l = self.topo.Link_set[i]
                temp_sum = 0
                if len(l.flows) == 0:
                    avail_rate.append(C)
                else:
                    for f in l.flows:
                        temp_sum = temp_sum + self.flows[f].Ralloc
                    avail_rate.append( (C-temp_sum) )
                    #update link Rresid to use it in pacing if needed (to avoid recomputation)
                    l.Rresid = C - temp_sum

            Rresid = min(avail_rate)
            if(Rresid < new_f.Rmin):
                #print "no enogh bandwidth, need to pace"
                self.pace(new_f,p)
            else:
                new_f.Ralloc = Rresid
                #new_f.update()
                new_f.te = int(self.t_now + ceil( (new_f.size/(new_f.Ralloc*1.0))/epoch ))
                #new_f.te = int(self.t_now +  ((new_f.size*8)/new_f.Ralloc)/epoch )
		if new_f.te > new_f.td:
		    new_f.te = new_f.td
                if int(new_f.te) == int(self.t_now):
                    new_f.te = new_f.te + 1
                new_f.slack = new_f.Ralloc - new_f.Rmin 
                
		self.flows[new_f.flow_id] = new_f
                
                if self.debug == True:
                    print "Success, flow has been scheduled with rate ",new_f.Ralloc," te = ",new_f.te
                self.success_count = self.success_count + 1
                for i in p:
                    l = self.topo.Link_set[i]
                    l.flows.append(new_f.flow_id) 

    def log_link_utilization(self):
	global epoch
        for i in self.topo.links:
            l = self.topo.Link_set[i]
            l.utilization(self.flows)
            x = (self.sim_time/epoch) -1
            avg_utiliz = []
            if (self.t_now == x) :
                self.avg_utiliz.append(np.mean(l.utiliz))

