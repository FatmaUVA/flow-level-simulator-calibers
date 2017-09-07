#most bottleneck first in pace and reshape
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
            self.flows[f].te = int(self.t_now + ceil( (self.flows[f].remain_data/(self.flows[f].Ralloc*1.0)) /epoch))
            if self.flows[f].te > self.flows[f].td:
                self.flows[f].te = self.flows[f].td
            if int(self.flows[f].te) == int(self.t_now):
                print "te < t_now te=",self.flows[f].te,"t_now =",self.t_now,"without ceil",(((self.flows[f].remain_data) / self.flows[f].Ralloc)/epoch)," result of ceil",ceil((((self.flows[f].remain_data) / self.flows[f].Ralloc)/epoch)),"remain data = ",self.flows[f].remain_data, "size =",self.flows[f].size,"Ralloc =",self.flows[f].Ralloc
            self.flows[f].slack = self.flows[f].Ralloc - self.flows[f].Rmin
            if self.debug == True:
                print "flow",f ,"reshaped. Ralloc = ",self.flows[f].Ralloc," te = ",self.flows[f].te
 
    def pace(self,new_f,p):
        global epoch
	global C
        count_f =0 # counter for the number of flows involved in pacing
	involved_flows = [] #involved flows considered for reshaping
        new_f_Rresid = [] # to find th emax rate new_f can go up to
        # first for each link find if Rmin is avilable by taking the slack
        for i in p:
            l = self.topo.Link_set[i]
	    sum_slack = 0 
	    max_te = 0
	    found_R = False # used to indicate if no rate was found
	    if len(l.flows) == 0: # if no flows in the link
		sum_slack = C 
	    else:
                for f in l.flows: #f holds only the flow id
                    involved_flows_id = [x.flow_id for x in involved_flows] #create a list of flow id to perform "not in "operation
		    sum_slack = sum_slack + self.flows[f].slack
            new_f_Rresid.append(sum_slack)
	    if sum_slack < new_f.Rmin: #no enough rate to reach its deadline
		break
	    else:
		found_R = True
        # Rresid available for the new flow across the entire path
        max_new_f_Rresid = min(new_f_Rresid)
	if found_R == False:
	    if self.debug == True:
		print "Reject, no available bandwidth in link ",l.link_id," even with pacing"
	    self.reject_count = self.reject_count + 1
	    return 0 

	else: 
            if self.debug == True:
                print "Success, reshaping will be done"
	    # Rmin found
	    # first give it the minimum then redistribute slack rate
	    new_f.Ralloc = new_f.Rmin
	    new_f.te = int(self.t_now + ceil( ((new_f.size)/new_f.Ralloc*1.0)/epoch))
	    if new_f.te > new_f.td:
		new_f.te = new_f.td
            if int(new_f.te) == int(self.t_now):
                print "te = t_now, te =",new_f.te,"t_now =",self.t_now,"Inside ceil",((new_f.size)/new_f.Ralloc)/epoch,"result of ceil",ceil( ((new_f.size)/new_f.Ralloc)/epoch)
	    new_f.slack = new_f.Ralloc - new_f.Rmin
	    self.flows[new_f.flow_id] = new_f
	    self.success_count = self.success_count + 1
            involved_flows.append(self.flows[new_f.flow_id])
	    #update links with the new flow
	    for i in p:
		l = self.topo.Link_set[i]
		l.flows.append(new_f.flow_id)

            involved_links = [] #to fond the most bottleneck link
            max_te_link = dict()
            for i in p: # go through each link (i holds link id)
                l = self.topo.Link_set[i]
                max_te = 0
                involved_links.append(l)
                for j in l.flows:
                    if self.flows[j].te > max_te:
                        max_te = self.flows[j].te
                max_te_link[l.link_id] = max_te

	    # now distribute residual rate
	    # start with link that will stay busy the longest
	    # sort by te (we cannot sort a dictionary so sort the dict by te and add the sorted value to a list
	    sorted_te = sorted(max_te_link.items(), key=operator.itemgetter(1),reverse=True)
	    # sorted_te structure is as follows: [(link_id,max_te), (link_id,max_te)]
	    count = 0
	    reshaped_flows = [] # list of flows that have been reshaped ( no need to reshape them if found in another link)
	    for i in sorted_te:
		l = self.topo.Link_set[i[0]] # i[count][0] return the the link_id which we need to ge the other link info
		coun = count + 1
		involved_flows = []
		C_resid = C # the residual capacity after removing the reshaped flows
                temp_sum_slack = 0
                temp_sum_Rmin = 0
		for f in l.flows:
		    if f not in reshaped_flows:
			involved_flows.append(self.flows[f])
			reshaped_flows.append(f)
                        temp_sum_Rmin = temp_sum_Rmin + self.flows[f].Rmin
                    else: #the flow already reshaped, we don't consider its slack
                        C_resid =  C_resid - self.flows[f].Ralloc

                l_slack = C_resid - temp_sum_Rmin # link slack capacity that we want to redistribute
                #print "C_resid =",C_resid,"temp_sum_Ramin",temp_sum_Rmin,"l_slack=",l_slack

                if len(involved_flows) == 0: #because the flows in this link has already been reshaped
                    continue
                
                elif l_slack > 0:
                    if self.algo == 'sjf':
                        involved_flows.sort(key=lambda x: x.remain_data, reverse=False)
                    elif self.algo == 'ljf':
                        involved_flows.sort(key=lambda x: x.remain_data, reverse=True)
                    else:
                        print "invalid algo"
                        return 0
                    for f in involved_flows:
                        if l_slack <= 0:
                            self.flows[f.flow_id].Ralloc = self.flows[f.flow_id].Rmin
                            self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc    *1.0)) /epoch))
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if int(self.flows[f.flow_id].te) == int(self.t_now):
                                print "te = t_now, inside ceil",(self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch,"results of ceil",ceil( (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc    ) /epoch)
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin 
                        
                        elif f.flow_id == new_f.flow_id:
                            self.flows[f.flow_id].Ralloc = min(max_new_f_Rresid, self.flows[f.flow_id].Rmin+l_slack)
                            self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch))
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if int(self.flows[f.flow_id].te) == int(self.t_now):
                                print "te = t_now, inside ceil",(self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch,"results of ceil",ceil( (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc    ) /epoch)
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin
                            l_slack = l_slack - self.flows[f.flow_id].Ralloc
                        else:
                            self.flows[f.flow_id].Ralloc = min(self.flows[f.flow_id].Ralloc, self.flows[f.flow_id].Rmin+l_slack) #you don't want to go beyond the flow Ralloc because then reshaping other flows in other links will be needed, anyway I don't think this will happen because a new flow is added, so we cannot really give more than Ralloc
                            self.flows[f.flow_id].te = int(self.t_now + ceil( (self.flows[f.flow_id].remain_data/(self.flows[f.flow_id].Ralloc*1.0)) /epoch))
                            if self.flows[f.flow_id].te > self.flows[f.flow_id].td:
                                self.flows[f.flow_id].te = self.flows[f.flow_id].td
                            if int(self.flows[f.flow_id].te) == int(self.t_now):
                                print "te = t_now, inside ceil",(self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc) /epoch,"results of ceil",ceil( (self.flows[f.flow_id].remain_data/self.flows[f.flow_id].Ralloc    ) /epoch)
                            self.flows[f.flow_id].slack = self.flows[f.flow_id].Ralloc - self.flows[f.flow_id].Rmin             
                            l_slack = l_slack - self.flows[f.flow_id].Ralloc
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
