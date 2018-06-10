# this a fixed scheduler which gives each flow Rmin, and it doesn't dynamixally change rates

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
        self.paths_involved = [] #when a flow completed
        self.missed_td = 0
        


    def delete_completed_flows(self):
        global epoch
        self.t_now = self.t_now + 1
        current_flows = dict() #need to make a copy to delete
        for f in self.flows:
            if self.flows[f].te <= int(self.t_now):
                p = self.topo.paths[(self.flows[f].src, self.flows[f].dst)]
                if self.debug == True:
                    print "flow",f, " finished"
                #delete the flow id from the links involved
                for i in p:
                    l = self.topo.Link_set[i]
                    l.flows.remove(f)
                    if self.debug == True:
                        print "flow",f, "deleted from link ",l.link_id
            else:
                current_flows[f] = self.flows[f]
                current_flows[f].update(self.t_now)
        self.flows = current_flows #current_flow does not include the finished flows



    def sched(self,requests):
        global epoch
        global C

        if self.debug == True:
            print "\nt_now = ", self.t_now


        if self.debug == True:
    	    for f in self.flows:
                p = self.topo.paths[(self.flows[f].src,self.flows[f].dst)]
                print "flow",f," with links :",p," Ralloc, te: ",self.flows[f].Ralloc, " ", self.flows[f].te

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
                print "new request: flow",new_f.flow_id," size ",req.size," td ", req.td," src,dst ",req.src,req.dst

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
                #reject flow:
                self.reject_count = self.reject_count + 1
                if self.debug == True:
                    print "request ",new_f.flow_id," is rejected, Rmin not available"
            else:
                new_f.Ralloc =new_f.Rmin
                #new_f.update()
                new_f.te = self.t_now + (new_f.size/(new_f.Ralloc*1.0))
                if new_f.te > new_f.td:
                    new_f.te = new_f.td
                if new_f.te == int(self.t_now):
                    new_f.te = new_f.te + 1
                new_f.slack = new_f.Ralloc - new_f.Rmin 
                
                self.flows[new_f.flow_id] = new_f
                
                if self.debug == True:
                    print "Success, flow has been scheduled with rate ",new_f.Ralloc," te = ",new_f.te
                self.success_count = self.success_count + 1
                #update links with new flow
                for i in p:
                    l = self.topo.Link_set[i]
                    l.flows.append(new_f.flow_id) 

    def log_link_utilization(self):
	global epoch
        for i in self.topo.links:
            l = self.topo.Link_set[i]
            l.utilization(self.flows)

    def stop_simulation(self):
        for i in self.topo.links:
            l = self.topo.Link_set[i]
            self.avg_utiliz.append(np.mean(l.utiliz))
