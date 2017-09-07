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
        count_f =0 # counter for the number of flows involved in pacing
        for i in p:
            l = self.topo.Link_set[i]
            avail_rate = [] # at each link
            temp_flows = [] # flows at each link
            involved_flows = [] # flows that will be paced down
            for f in l.flows:
                temp_flows.append(self.flows[f])
            #sort by slack value
            temp_flows.sort(key=lambda x: x.slack, reverse=True)
            found_R = False
            #first before chacking the flows slack, check ressidual bw in the link, in case a flow was paced and now more bandwidth is available
            temp_sum = 0
            for f in temp_flows:
                temp_sum = temp_sum + f.Ralloc
            temp_Rresid = C - temp_sum
            if temp_Rresid < 0: #this is due to floating point rounding
                temp_Rresid = 0

            if new_f.Rmin <= temp_Rresid:
                avail_rate.append(temp_Rresid)
                found_R = True #TODO check do I need to set it true here
            # no need to pace othe flows
            else:
                temp_sum = 0
                for f in temp_flows:
                    count_f = count_f + 1
                    if count_f <= self.pace_threshold:
                        involved_flows.append(f) # keep the flow original info
                        temp_sum = temp_sum + f.slack
                        if self.debug == True:
                            print "before pacing: flow :",f.flow_id,"Ralloc and  slack = ",f.Ralloc," ", f.slack," te ",self.flows[f.flow_id].te
                        if temp_sum+temp_Rresid >= new_f.Rmin: #TODO not sure if I should add tem_Rresid (done) but should I do =
                            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin + ((temp_sum +temp_Rresid) - new_f.Rmin)
                            self.flows[f.flow_id].te = self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch)
                            #self.flows[f.flow_id].te = int(self.t_now + (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch)
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td: #this is due to floating point op I'll have a file explaining
                                #print "In pacing true te > tdRalloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data,"te =",self.flows[f.flow_id].te,"td =",self.flows[f.flow_id].td
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if  self.flows[f.flow_id].te == int(self.t_now):
                                #print "In pacing true te = t_now Ralloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data,"te =",self.flows[f.flow_id].te,"td =",self.flows[f.flow_id].td
                                self.flows[f.flow_id].te = self.flows[f.flow_id].te + 1
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc -self.flows[f.flow_id].Rmin
                            #self.flows[f.flow_id].update()
                            if self.debug == True:
                                print "after pacing: flow :",f.flow_id," Ralloc: ",self.flows[f.flow_id].Ralloc," te ",self.flows[f.flow_id].te
                            avail_rate.append(new_f.Rmin)
                            found_R = True
                            break
                        else:
                            #update flow Ralloc te slack
                            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin
                            if self.flows[f.flow_id].Ralloc <= 0:
                                print "Ralloc zero ",self.flows[f.flow_id].Ralloc,"size",self.flows[f.flow_id].size,"sent",self.flows[f.flow_id].sent_data
                            self.flows[f.flow_id].te = self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch)
                            #self.flows[f.flow_id].te = int(self.t_now +  (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch)
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td: #this is due to floating point op
                                #print "In pacing true te > tdRalloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if  self.flows[f.flow_id].te == int(self.t_now):
                                #print "In pacing true te = t_now Ralloc =",self.flows[f.flow_id].Ralloc,"remain =",self.flows[f.flow_id].remain_data
                                self.flows[f.flow_id].te = self.flows[f.flow_id].te + 1
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc -self.flows[f.flow_id].Rmin
                            #self.flows[f.flow_id].update()
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
        new_f.te = self.t_now + ceil( ((new_f.size)/(new_f.Ralloc*1.0))/epoch)
        if new_f.te > new_f.td: #this is due to floating point op
            #print "In new flow true te > td Ralloc =",new_f.Ralloc,"remain =",new_f.remain_data,"te=",new_f.te,"td=",new_f.td,"size=",new_f.size,"Rmin=",new_f.Rmin,"t_now=",self.t_now,"inside ceil=", ceil(((new_f.size*8)/new_f.Ralloc)/epoch),
            new_f.te = new_f.td
        if int(new_f.te) == int(self.t_now):
            new_f.te = new_f.te + 1
            #print "In new flow true te =t_now Ralloc =",new_f.Ralloc,"remain =",new_f.remain_data,"te=",new_f.te,"td=",new_f.td,"size=",new_f.size,"Rmin=",new_f.Rmin,"t_now=",self.t_now,"inside ceil=", ceil(((new_f.size*8)/new_f.Ralloc)/epoch),
        new_f.slack = new_f.Ralloc - new_f.Rmin
        #new_f.update()
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

        #sort links by most-bottleneack link
        max_te_link = dict()
        for i in involved_links: # go through each link (i holds link id)
            l = self.topo.Link_set[i]
            max_te = 0
            for j in l.flows:
                if self.flows[j].te > max_te:
                    max_te = self.flows[j].te
            max_te_link[l.link_id] = max_te
        
        sorted_te = sorted(max_te_link.items(), key=operator.itemgetter(1),reverse=True)
        reshaped_flows = [] # list of flows that have been reshaped ( no need to reshape them if found in another link)
        involved_links_set = set(involved_links)
        for j in sorted_te:
            l = self.topo.Link_set[j[0]] # i[count][0] return the the link_id which we need to ge the other link info
            involved_flows = []
            for f in l.flows:
                involved_flows.append(self.flows[f])
            if self.algo == 'sjf':
                involved_flows.sort(key=lambda x: x.remain_data, reverse=False)
            elif self.algo == 'ljf':
                involved_flows.sort(key=lambda x: x.remain_data, reverse=True)
            else:
                print "invalid algo"
                return 0
            for f in involved_flows:
                pi = self.topo.paths[(self.flows[f.flow_id].src,self.flows[f.flow_id].dst)]
                p_set = set(pi)
                if p_set.issubset(involved_links_set) and f.flow_id not in reshaped_flows:
                    # allocate more rate to f
                    reshaped_flows.append(f.flow_id)
                    path_Rresid = []
                    for i in pi:
                        l = self.topo.Link_set[i]
                        temp_sum = 0
                        for x in l.flows:
                            temp_sum = temp_sum + self.flows[x].Ralloc
                        l.Rresid = C - temp_sum
                        path_Rresid.append(l.Rresid)
                    Rresid = min(path_Rresid)
                    if (self.flows[f.flow_id].Ralloc + Rresid) <= self.flows[f.flow_id].Rmax and Rresid > 0:
                        self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Ralloc + Rresid
                        self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
                        self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch))
			if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
			    #print "true te < td" 
			    self.flows[f.flow_id].te = self.flows[f.flow_id].td
                        if int(self.flows[f.flow_id].te) == int(self.t_now):
                            print "te = t_now, te ="#,self.flows[f.flow_id.te,"t_now =",self.t_now,"Inside ceil",(self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch,"result of ceil",ceil( (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch)
                        #self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
			#print "link is ",l.link_id ," error, flow ",f.flow_id,"  size-sent ",self.flows[f.flow_id].size - self.flows[f.flow_id]    .sent_data," Ralloc ",self.flows[f.flow_id].Ralloc,"epoch ",epoch," t_now ",self.t_now," te ",self.flows[f.flow_id].te, " Rmin ",self.flows[f.flow_id].Rmin," flow path is ",p
                    elif (self.flows[f.flow_id].Ralloc + Rresid) > self.flows[f.flow_id].Rmax and Rresid > 0:
                        self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmax
                        self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
			self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch))
			if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
			    #print "true te < td"
			    self.flows[f.flow_id].te = self.flows[f.flow_id].td
                        if int(self.flows[f.flow_id].te) == int(self.t_now):
                            print "te = t_now, te ="#,self.flows[f.flow_id.te,"t_now =",self.t_now,"Inside ceil",(self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch,"result of ceil",ceil((self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc)/epoch)
			#self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin

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
            x = (self.sim_time/epoch) -1
            avg_utiliz = []
            if (self.t_now == x) :
                self.avg_utiliz.append(np.mean(l.utiliz))

