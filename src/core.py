
import time
import random
from math import *
import numpy as np

epoch = 100.0 #300.0 #1 #timeslot, periodic sceduling, unit seconds
C = int(10000 * 1e6) #160000 # link capaacity in bps

class Link:
    global C
    def __init__(self,link_id):
        self.link_id = link_id #two tuples identifier
        self.flows = [] # list of flow id, flow info is stored in a dictionary in the Schedul class
        self.Rresid = C
        self.utiliz = []

    def utilization(self,flow_info):
        global C
        temp_sum = 0
        for f in self.flows:
            temp_sum = temp_sum+ flow_info[f].Ralloc
        if len(self.flows) == 0:
            temp_sum = 0
        self.utiliz.append(temp_sum*1.0/C)
	#this could be due to floating-point operation depending on the platform where the simulator is running
	if temp_sum/C > 1:
	    self.utiliz.append(1)
            #if (temp_sum - C) >= 1e9:
            if  (temp_sum) > 10e9:
                print "util > 1!, temp_sum-C",temp_sum-C

class Topology:
    def __init__(self, links, paths,c,epochx):
        global C
        global epoch
        C = int(c * 1e6)
        epoch = float(epochx)
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
        #self.t_now = t_now
        self.flow_id = flow_id
        self.src = src
        self.dst =dst
        self.size = int(size*1e6*8) #unit bytes
        #self.td = int(self.t_now + floor(td/epoch))  #how many time slots needed
        self.td = t_now + td  #in sec
        self.te = self.td #unit is in time slots
        self.Rmax = int(10000*1e6) # unit Mbps, max rate the end points and the bottleneck link in the path can achieve
        self.Rmin = int((self.size*1.0) / (self.td - t_now)) #unit bps 
        self.Ralloc = 0
        self.slack = 0 
        self.sent_data = 0 #unit bytes, data sent so far
	self.remain_data = int(self.size - self.sent_data)

    def update(self,t_now):
	global epoch
	global C
        self.sent_data = int(self.sent_data + (self.Ralloc)) #in bits
	self.remain_data = int(((self.size - self.sent_data))) 

	if ((self.td-t_now)) <= 0:
	    print "flow error, flow ",self.flow_id,"Rmin ",self.Rmin," size", self.size,"sent_data",self.sent_data," Ralloc",self.Ralloc,"self.size - self.sent_data",self.size - self.sent_data, "remain_data",self.remain_data,"td and tnow and te ",self.td," ",t_now," ",self.te
	self.Rmin = int(self.remain_data*1.0 / ((self.td-t_now)))
        self.te = t_now + (self.remain_data / (self.Ralloc*1.0))
	if self.te > int(self.td):
	    #print "In update, true te > td,Ralloc =",self.Ralloc,"remain =",self.remain_data
	    self.te = self.td
        if  self.te == int(t_now):
            #print "In update te = t_now, flow",self.flow_id," Ralloc",self.Ralloc,"size",self.size,"remain =",self.remain_data,"sent_data",self.sent_data,"td and tnow and te ",self.td," ",t_now," ",self.te
            self.te = self.te + 1 
        self.slack = self.Ralloc - self.Rmin
        
        #print "In update: flow",self.flow_id," Ralloc",self.Ralloc,"size",self.size,"remain =",self.remain_data,"sent_data",self.sent_data,"td and tnow and te ",self.td," ",t_now," ",self.te,"ceil(self.remain_data / (self.Ralloc*1.0))",ceil(self.remain_data / (self.Ralloc*1.0)),"int(t_now + ceil(self.remain_data / (self.Ralloc*1.0)))",int(t_now + ceil(self.remain_data / (self.Ralloc*1.0)))


class Request:
    def __init__(self,src,dst,size,ts,td):
        self.ts = 0
        self.size = size # file size in MB
        self.td = td # deadline in seconds
        self.src = src
        self.dst = dst

