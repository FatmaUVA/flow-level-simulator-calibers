# this version uses optimization to settup Ralloc, note that when a flow is re moved, the code was not updated to use the optimization function
import time
import random
from math import *
import numpy as np
import operator 
from scipy.optimize import minimize, basinhopping

epoch = 100.0 #300.0 #1 #timeslot, periodic sceduling, unit seconds
C = 10000.0 #160000 # link capaacity in Mbps

class Link:
    def __init__(self,link_id):
        self.link_id=link_id #two tuples identifier
        self.flows = [] # list of flow id, flow info is stored in a dictionary in the Schedul class
        self.Rresid = C
        self.utiliz = []

    def utilization(self,flow_info):
        global C
        temp_sum = 0
        for f in self.flows:
            temp_sum = temp_sum + flow_info[f].Ralloc
        self.utiliz.append(temp_sum/C)
	#this could be due to floating-point operation depending on the platform where the simulator is running
	if temp_sum/C > 1:
	    self.utiliz.append(1)

class Topology:
    def __init__(self, links, paths):
        self.links=links
        self.paths=paths
        self.Link_set = dict()
        self.create_topo()

    def create_topo(self):
        #create the links and add them to a dictionary list
        for l in self.links:
            self.Link_set[l] = Link(l)

class flow:
    def __init__(self,flow_id,size,td,src,dst,t_now):
	global epoch
        self.t_now = t_now
        self.flow_id = flow_id
        self.src = src
        self.dst =dst
        self.size = size
        self.td = self.t_now + floor(td/epoch)  #how many time slots needed
        self.te = self.td #unit is in time slots
        self.Rmax = 10000 # unit Mbps, max rate the end points and the bottleneck link in the path can achieve
        self.Rmin = (self.size*8) / ((self.td - self.t_now)*epoch) #unit Mbps 
        self.Ralloc = 0
        self.slack = 0 
        self.sent_data = 0 #unit MB, data sent so far
	self.remain_data = int(self.size - self.sent_data)

    def update(self,t_now):
	global epoch
	global C
	self.t_now = t_now
        self.sent_data = self.sent_data + (self.Ralloc * epoch)/8 #in MB
	self.remain_data = int(((self.size - self.sent_data)*8) * 1e6) # to get preceision up to bytes
	self.remain_data = self.remain_data / 1.0e6 #unti Mbit
#	print "before update update flow ",self.flow_id," td ",self.td, "((td-t_now)*epoch) ", ((self.td-self.t_now)*epoch),"te ",self.te
	if ((self.td-self.t_now)*epoch) <= 0:
	    print "flow error, flow ",self.flow_id,"Rmin ",self.Rmin," size", self.size,"sent_data",self.sent_data," Ralloc",self.Ralloc,"self.size - self.sent_data",self.size - self.sent_data, "remain_data",self.remain_data,"td and tnow and te ",self.td," ",self.t_now," ",self.te
        #self.Rmin = ((self.size - self.sent_data)*8) / ((self.td-self.t_now)*epoch)
	self.Rmin = self.remain_data / ((self.td-self.t_now)*epoch)
        self.te = self.t_now + ceil((((self.remain_data) / self.Ralloc)/epoch))
	if self.te > self.td: #TODO check why is that happening
	    #print "true te > td"
	    self.te = self.td
        self.slack = self.Ralloc - self.Rmin
	#print "update flow ",self.flow_id," td ",self.td, "((td-t_now)*epoch) ", ((self.td-self.t_now)*epoch)
	#print "self.size-self.sent_data ",self.size-self.sent_data," update flow ",self.flow_id,"sent_data ",self.sent_data," te ",self.te, " ceil  ",((((self.size - self.sent_data)*8) / self.Ralloc)/epoch)," Ralloc ",self.Ralloc


class Scheduler:
    global C #link capacity
    global epoch
    
    def __init__ (self,topo,sim_time,epochx,log,debug = False):
	global epoch
        self.topo = topo
        self.no_accepted_flows = 0
        self.log = log
        self.debug = debug
        self.sim_time = sim_time
        epoch = float(epochx)
        self.pace_threshold = 100 # the maximum number of flow you can pace to accept new request
        self.success_count = 0
        self.reject_count = 0
	self.no_request = 0
        self.t_now = -1 # current timeslot (epoch)
        self.flows = dict() #indexed by the flow_id
        self.avg_utiliz = [] #for logging to keep track of link utilization


    def func(self,x,remain):
	global epoch
        return ( ceil(sum( (remain/x))/epoch ) )
    def func_deriv(self,x,remain):
        """ Derivative of objective function """
	global epoch
        return np.array(-1*remain*epoch/x**2)

    def reshape_optimize(self,l,involved_flows,slack_max , C_resid):
	global epoch
        #find the Rmin constrains
        Rmin = []
        Rmax = np.array(slack_max)
        remain = []
        #x = np.repeat(C_resid,len(involved_flows)) #initial Ralloc
        x = Rmax
        for f in involved_flows:
            Rmin.append(self.flows[f].Rmin)
            remain.append(self.flows[f].remain_data)
        Rmin = np.array(Rmin)
        remain = np.array(remain)

        x_Rmin_der = np.empty([x.size,x.size])
        x_Rmax_der = np.empty([x.size,x.size])
        for i in xrange(x.size):
            z = np.repeat(0,x.size)
            z[i] = 1
            x_Rmin_der[i] = z
        for i in xrange(x.size):
            z = np.repeat(0,x.size)
            z[i] = -1
            x_Rmax_der[i] = z
	print "Rmin = ",Rmin
	print "Rmax = ",Rmax
	print "remain = ",remain
	print "C_resid = ",C_resid
        #constraints
        cons = ({'type': 'ineq',
          'fun' : lambda x,Rmin,x_Rmin_der: x-Rmin,
          'jac' : lambda x,Rmin,x_Rmin_der: x_Rmin_der,
          'args': (Rmin,x_Rmin_der)},
        {'type': 'ineq',
          'fun' : lambda x,C_resid: np.array([C_resid - sum(x)]),
          'jac' : lambda x,C_resid: np.repeat(-1,x.size),
          'args': (C_resid,)},
        {'type': 'ineq',
          'fun' : lambda x,Rmax,x_Rmax_der: Rmax-x,
          'jac' : lambda x,Rmax,x_Rmax_der: x_Rmax_der,
          'args': (Rmax,x_Rmax_der)})

        #res = minimize(self.func, x,args = (remain,), jac=self.func_deriv,constraints=cons, method='SLSQP', options={'disp': True, 'eps' : 500})
        minimizer_kwargs = dict(method="SLSQP",args = (remain), jac=self.func_deriv,constraints=cons,options={'disp': False})
        res = basinhopping(self.func, x, minimizer_kwargs=minimizer_kwargs)
	
        print res
        count = 0
        #update the flows with the new optimized Ralloc
        for f in involved_flows:
            self.flows[f].Ralloc = res.x[count]
            count = count + 1
            self.flows[f].te = self.t_now + ceil( (self.flows[f].remain_data/self.flows[f].Ralloc) /epoch)
            if self.flows[f].te > self.flows[f].td:
                self.flows[f].te = self.flows[f].td
            self.flows[f].slack = self.flows[f].Ralloc - self.flows[f].Rmin
            if self.debug == True:
                print "flow",f ,"reshaped. Ralloc = ",self.flows[f].Ralloc," te = ",self.flows[f].te
 
    def pace(self,new_f,p):
        global epoch
	global C
        count_f =0 # counter for the number of flows involved in pacing
	involved_links = [] #used to sort based on te
	involved_flows = [] #involved flows considered for reshaping
        for i in p:
            l = self.topo.Link_set[i]
	    involved_links.append(l)
	    sum_slack = 0 
	    max_te_link = dict() # max te per link used for optimization (key:link_id, max_te)
	    max_te = 0
	    found_R = False # used to indicate if no rate was found
	    if len(l.flows) == 0: # if no flows in the link
		sum_slack = C 
	    else:
                for f in l.flows: #f holds only the flow id
                    involved_flows_id = [x.flow_id for x in involved_flows] #create a list of flow id to perform "not in "operation
                    if f not in involved_flows_id:
		        involved_flows.append(self.flows[f])
		    sum_slack = sum_slack + self.flows[f].slack
	 	    if self.flows[f].te > max_te:
		        max_te = self.flows[f].te
	        max_te_link[l.link_id] = max_te
	    if sum_slack < new_f.Rmin: #no enough rate to reach its deadline
		break
	    else:
		found_R = True

	if found_R == False:
	    if self.debug == True:
		print "Reject, no available bandwidth in link ",l.link_id," even with pacing"
	    self.reject_count = self.reject_count + 1
	    return 0 

	else: 
	    # Rmin found, optimiz to find the best rate to give to each flow
	    # first give it the minimum then optimize
	    new_f.Ralloc = new_f.Rmin
	    new_f.te = self.t_now + ceil( ((new_f.size*8)/new_f.Ralloc)/epoch)
	    if new_f.te > new_f.td:
		new_f.te = new_f.td
	    new_f.slack = new_f.Ralloc - new_f.Rmin
	    self.flows[new_f.flow_id] = new_f
	    self.success_count = self.success_count + 1
            involved_flows.append(self.flows[new_f.flow_id])
	    #update links with the new flow
	    for i in p:
		l = self.topo.Link_set[i]
		l.flows.append(new_f.flow_id)

            involved_links = [] #TODO maybe I should remove it formt he top
            max_te_link = dict()
            #find all involved links based on the other flows in the path of the new flow
	    for f in involved_flows:
		p = self.topo.paths[(self.flows[f.flow_id].src, self.flows[f.flow_id].dst)]
		for i in p: # go through each link (i holds link id)
                    l = self.topo.Link_set[i]
                    involved_links_id = [x.link_id for x in involved_links]
		    if l.link_id not in involved_links_id:
			max_te = 0
			involved_links.append(l)
			for j in l.flows:
			    if self.flows[j].te > max_te:
			        max_te = self.flows[j].te
			max_te_link[l.link_id] = max_te
 

	    #now optimizae
	    # start with link that will stay the busy the longest
	    # sort by te (we cannot sort a dictionary so sort the dict by te and add the sorted value to a list
	    sorted_te = sorted(max_te_link.items(), key=operator.itemgetter(1),reverse=True)
	    #sorted_te structure is as follows: [(link_id,max_te), (link_id,max_te)]
            print "sorted_te ",sorted_te
	    count = 0
	    reshaped_flows = [] # list of flows that have been reshaped ( no need to reshape them if found in another link)
	    for i in sorted_te:
                print "I'm in link" ,i[0]
		l = self.topo.Link_set[i[0]] # i[count][0] return the the link_id which we need to ge the other link info
		coun = count + 1
		involved_flows = []
		C_resid = C # the residual capacity after removing the reshaped flows
                slack_max = [] # the max value each flow can go up to based on the path
		for f in l.flows:
                    print "f in the path is ",f
                    #reshaped_flows_id = [x.flow_id for x in reshaped_flows]
		    if f not in reshaped_flows:
			involved_flows.append(f)
			reshaped_flows.append(f)
			#find max Rresid for each flow 
                        sum_slack = []
			p = self.topo.paths[(self.flows[f].src, self.flows[f].dst)]
			for j in p:
                            temp_sum_slack = 0
                            temp_sum_Ralloc = 0
			    l2 = self.topo.Link_set[j]
			    for x in l2.flows:
                                if x == f: #this is the flow that we want to find its Rmax so we don't consider what is already allocated to it
                                    continue
				else:
                                    temp_sum_slack = temp_sum_slack +  self.flows[x].slack
                                    temp_sum_Ralloc = temp_sum_Ralloc + self.flows[x].Ralloc
			    sum_slack.append( (C - temp_sum_Ralloc) + temp_sum_slack)
                            print "sum_slack.append ",sum_slack
			slack_max.append(min(sum_slack))
                        print "slack_max = ", slack_max
                        if slack_max == 0: #the flow cannot be assigned more than Rmin
                            involved_flows.remove(f) #we don't remove it from reshape because we know that we cannot reshape it so their is no point to let it be considered for reshaping
		    else: #if a flow already has been reshaped, then we don't touch it
			C_resid = C_resid - self.flows[f].Ralloc
                if len(involved_flows) == 0: #because the flows in this link has already been reshaped
                    continue
                
                #if len(involved_flows) == 1: #only one flow nothing we can do TODO: maybe give it its Rmax
                #    continue
                elif C_resid > 0:
		    #optimize for each link
		    self.reshape_optimize(l,involved_flows,slack_max,C_resid)
		
		 
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
            involved_flows.sort(key=lambda x: x.te, reverse=False)
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
                        self.flows[f.flow_id].te = self.t_now + ceil( (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch) #TODO check
			if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
			    #print "true te < td" 
			    self.flows[f.flow_id].te = self.flows[f.flow_id].td
                        self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
			#print "link is ",l.link_id ," error, flow ",f.flow_id,"  size-sent ",self.flows[f.flow_id].size - self.flows[f.flow_id]    .sent_data," Ralloc ",self.flows[f.flow_id].Ralloc,"epoch ",epoch," t_now ",self.t_now," te ",self.flows[f.flow_id].te, " Rmin ",self.flows[f.flow_id].Rmin," flow path is ",p
                    elif (f.Ralloc + Rresid) > f.Rmax and Rresid > 0:
                        self.flows[f.flow_id].Ralloc = f.Rmax
			self.flows[f.flow_id].te = self.t_now + ceil( (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch)
			if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
			    #print "true te < td"
			    self.flows[f.flow_id].te = self.flows[f.flow_id].td
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
                new_f.te = self.t_now + ceil( ((new_f.size*8)/new_f.Ralloc)/epoch )
		if new_f.te > new_f.td:
		    new_f.te = new_f.td
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

class Request:
    def __init__(self,src,dst,size,ts,td):
        self.ts = 0
        self.size = size # file size in MB
        self.td = td # deadline in seconds
        self.src = src
        self.dst = dst
