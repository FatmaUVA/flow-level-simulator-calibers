
import numpy as np
from scipy.optimize import minimize, basinhopping
from math import ceil
#from sklearn import preprocessing

epoch = 10
def func(x,remain):
#    return ( ceil(sum(remain/x)) )
    global epoch
    return ( ceil(sum( (remain/x))/epoch ) )

def func_deriv(x,remain):
    """ Derivative of objective function """
#    return np.array(-1*remain/x**2)
    global epoch
    return np.array(-1*remain*epoch/x**2)

def func2(x,remain):
    global epoch
    #find minimum te
    te_min_arr = (remain/x)/epoch
    te_min = ceil(min(te_min_arr))
    return sum( ((remain/x)/epoch) - te_min) 

def func2_deriv(x,remain):
    """ Derivative of objective function """
    global epoch
    return np.array(-1*remain*epoch/x**2)

#minimiza the average
def func3(x,remain):
    global epoch
    return ( ceil( (sum( (remain/x))/epoch)/x.size ) )

#Rmin =  [ 181.1093397  , 6.34716981,  72.34285714 , 215.24033613]
#Rmax =  [ 9706.06963691 ,9531.30746702 , 9597.30315435 , 9740.20063335]
#remain =  [  1.51769627e+06  ,1.68200000e+03, 6.33000000e+02,   3.20170000e+04]
Rmin =  [ 174.72240795 , 167.1009673 ,  288.83249216 ,  26.68388426,  398.71248711, 49.2024758,    46.27804878]
Rmax =  [ 9023.18964459,  9015.56820394,  9137.29972879,  8875.15112089 , 9247.17972375, 8897.66971243,  8894.74528541]
remain =  [ 1457184.882336,  950804.503965  , 788512.703591 ,  232950.309596, 362828.363274  ,109721.521024 ,   75433.219512]

Rmin = np.array(Rmin)
Rmax = np.array(Rmax)
x = Rmin
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

remain = np.array(remain)
count = 0
x = []
te_min_arr = (remain/Rmin)/epoch
te_min = ceil(min(te_min_arr))
for i in remain:
    if i/(epoch*10) > Rmax[count]:
        x.append(Rmax[count])
    else:
        x.append(i/(epoch*10))
    count = count + 1

x = (remain/1e5)*10000
x = (remain-min(remain))/(max(remain-min(remain)))*10000 #feature scaling, yield to zero
x = np.array((remain - np.mean(remain,axis = 0))/np.var(remain,axis=0)+0.5)*10000
x = np.array(x)
print "x0 = ",x
print "Rmax =",Rmax        
cons = ({'type': 'ineq',
          'fun' : lambda x,Rmin,x_Rmin_der: x-Rmin,
          #'jac' : lambda x,Rmin,x_Rmin_der: np.array([[1,0,0],[0,1,0],[0,0,1]]),
          'jac' : lambda x,Rmin,x_Rmin_der: x_Rmin_der,
          'args': (Rmin,x_Rmin_der)},
        {'type': 'ineq',
          'fun' : lambda x: np.array([10000 - sum(x)]),
          'jac' : lambda x: np.repeat(-1,x.size)},
        {'type': 'ineq',
          'fun' : lambda x,Rmax,x_Rmax_der: Rmax-x,
          'jac' : lambda x,Rmax,x_Rmax_der: x_Rmax_der,
          'args': (Rmax,x_Rmax_der)})


#res = minimize(func, x,args = (remain), jac=func_deriv,
#constraints=cons, method='SLSQP', options={'disp': True}) #COBYLA SLSQP

minimizer_kwargs = dict(method="SLSQP",args = (remain), jac=func_deriv,constraints=cons,options={'disp': False})
#res = basinhopping(func, x,stepsize=500, minimizer_kwargs=minimizer_kwargs)
res = basinhopping(func, x, minimizer_kwargs=minimizer_kwargs)
print "*******Minimiza Sum******"
print res 
Ralloc = np.array(res.x)
print "res.x = ",res.x
print "te = ",[ceil(y) for y in (((remain/Ralloc))/epoch)]

#res = basinhopping(func2, x, stepsize=500,minimizer_kwargs=minimizer_kwargs)
res = basinhopping(func2, x, minimizer_kwargs=minimizer_kwargs)
print "*******Minimiza difference******"
print res
Ralloc = np.array(res.x)
print "res.x = ",res.x
print "te = ",[ceil(y) for y in (((remain/Ralloc))/epoch)]

#res = basinhopping(func3, x, stepsize=500,minimizer_kwargs=minimizer_kwargs)
res = basinhopping(func3, x, minimizer_kwargs=minimizer_kwargs)
print "*******Minimiza Average******"
print res
Ralloc = np.array(res.x)
print "res.x = ",res.x
print "te = ",[ceil(y) for y in (((remain/Ralloc))/epoch)]

print "With Rmin sum te = ",ceil(sum(remain/Rmin))

