#based on slack on pace and most-bottleneck-link fist in reshape
import time
import random
from math import *
import numpy as np
import operator
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
        self.pace_threshold = 100000
        count_f =0 # counter for the number of flows involved in pacing
        for i in p:
            l = self.topo.Link_set[i]
            avail_rate = [] # at each link
            temp_flows = [] # flows at each link
            involved_flows = [] # flows that will be paced down
            for f in l.flows:
                temp_flows.append(self.flows[f]) # we need the flow object to sort
            #sort by slack value
            temp_flows.sort(key=lambda x: x.slack, reverse=True)
            found_R = False
            #first before chacking the flows slack, check ressidual bw in the link, in case a flow was paced and now more bandwidth is available
            temp_sum = 0
            for f in temp_flows:
                temp_sum = temp_sum + self.flows[f.flow_id].Ralloc
            temp_Rresid = C - temp_sum
            if temp_Rresid < 0: #this is due to floating point rounding
                temp_Rresid = 0

            if new_f.Rmin <= temp_Rresid:
                # no need to pace othe flows
                avail_rate.append(temp_Rresid)
                found_R = True
            else:
                temp_sum = 0
                for f in temp_flows:
                    count_f = count_f + 1
                    if count_f <= self.pace_threshold:
                        involved_flows.append(self.flows[f.flow_id]) # keep the flow original info
                        temp_sum = temp_sum + self.flows[f.flow_id].slack
                        if self.debug == True:
                            print "before pacing: flow :",f,"Ralloc and  slack = ",self.flows[f.flow_id].Ralloc," ", self.flows[f.flow_id].slack," te ",self.flows[f.flow_id].te
                        if temp_sum+temp_Rresid >= new_f.Rmin:
                            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin + ((temp_sum +temp_Rresid) - new_f.Rmin)
                            self.flows[f.flow_id].te = self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch)
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td: #this is due to floating point op I'll have a file explaining
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if  self.flows[f.flow_id].te == self.t_now:
                                self.flows[f.flow_id].te = self.flows[f.flow_id].te + 1
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
                            if self.debug == True:
                                print "after pacing: flow :",f.flow_id," Ralloc: ",self.flows[f.flow_id].Ralloc," te ",self.flows[f.flow_id].te
                            avail_rate.append(new_f.Rmin)
                            found_R = True
                            break
                        else:
                            #update flow Ralloc te slack
                            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin
                            self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch))
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td: #this is due to floating point op
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if  self.flows[f.flow_id].te == int(self.t_now):
                                self.flows[f.flow_id].te = self.flows[f.flow_id].te + 1
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
                    else:
                        if self.debug == True:
                            print "Reject, cannot pace more than 100 flows"
                        self.reject_count = self.reject_count + 1
                        self.revert_flow_changes(involved_flows)
                        return 0
                if found_R == False:
                    if self.debug == True:
                        print "Reject, no available bandwidth in link ",l.link_id," even with pacing"
                    self.reject_count = self.reject_count + 1
                    self.revert_flow_changes(involved_flows)
                    return 0

        self.success_count = self.success_count + 1
        new_f.Ralloc = new_f.Rmin
        new_f.te = int(self.t_now + ceil( ((new_f.size)/(new_f.Ralloc*1.0))/epoch))
        if new_f.te > new_f.td: #this is due to floating point op
            new_f.te = new_f.td
        if int(new_f.te) == int(self.t_now):
            new_f.te = new_f.te + 1
        new_f.slack = new_f.Ralloc - new_f.Rmin
        self.flows[new_f.flow_id] = new_f
        if self.debug == True:
            print "Success, the flow was assigned rate of ", new_f.Ralloc," Rmin ",new_f.Rmin," te ",new_f.te
        #update links with the new flow
        for i in p:
            l = self.topo.Link_set[i]
            l.flows.append(new_f.flow_id)		
		 
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
        self.reshape(involved_links,involved_flows)

    #when a flow finishes or a new flow comes, how to redistribute the slack capacity, is what this function do
    def reshape(self,involved_links,involved_flows):
        global C

        #assign Rmin to all involved flows
        for f in involved_flows:
            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin

        #sort links by most-bottleneck link
        max_te_link = dict()
        for i in involved_links: # go through each link (i holds link id)
            l = self.topo.Link_set[i]
            max_te = 0
            for j in l.flows:
                if self.flows[j].te > max_te:
                    max_te = self.flows[j].te
            max_te_link[l.link_id] = max_te

        # now distribute residual rate
        # start with link that will stay busy the longest
        # sort by te (we cannot sort a dictionary so sort the dict by te and add the sorted value to a list
        sorted_te = sorted(max_te_link.items(), key=operator.itemgetter(1),reverse=True)
        # sorted_te structure is as follows: [(link_id,max_te), (link_id,max_te)]
        for j in sorted_te:
            l = self.topo.Link_set[j[0]] # j[count][0] return the the link_id which we need to ge the other link info
            involved_flows = []
            for f in l.flows:
                involved_flows.append(self.flows[f])
            #sort by remain_data
            if self.algo == 'sjf':
                involved_flows.sort(key=lambda x: x.remain_data, reverse=False)
            elif self.algo == 'ljf':
                involved_flows.sort(key=lambda x: x.remain_data, reverse=True)
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
                self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch))
                if int(self.flows[f.flow_id].te) > int(self.flows[f.flow_id].td):
                    self.flows[f.flow_id].te = self.flows[f.flow_id].td
                if self.debug == True:
                    print "flow",f.flow_id ,"reshaped. Ralloc = ",self.flows[f.flow_id].Ralloc," te = ",self.flows[f.flow_id].te

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
                print "new request id: ",new_f.flow_id," size ",req.size," td ", req.td," src,dst ",req.src,req.dst, "path is ",p

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
		if new_f.te > new_f.td:
		    new_f.te = new_f.td
                if int(new_f.te) == int(self.t_now):
                    print "te = t_now inside ceil",((new_f.size)/new_f.Ralloc)/epoch,"result of ceil",ceil( ((new_f.size)/new_f.Ralloc)/epoch )
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
#            x = (self.sim_time/epoch) -1
#            if (self.t_now == x) :
#                self.avg_utiliz.append(np.mean(l.utiliz))

    def stop_simulation(self):
        for i in self.topo.links:
            l = self.topo.Link_set[i]
            self.avg_utiliz.append(np.mean(l.utiliz))

