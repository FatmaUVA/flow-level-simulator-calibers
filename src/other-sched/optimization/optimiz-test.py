
import numpy as np
from scipy.optimize import minimize
from math import ceil

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


#x = [10000,10000,10000]
x = [10000,10000]
x = np.array(x)
#Rmin = [3000, 2000, 3000]
#Rmax = [10000, 10000, 10000]
#remain = [150000.0, 12000.0, 21000.0]
Rmin =  [ 67.9388535,   49.25333333]
Rmax =  [ 9950.74666667,  9932.0611465]
remain =  [13333,  5541]
Rmin = np.array(Rmin)
Rmax = np.array(Rmax)
x_Rmin_der = np.empty([x.size,x.size])
x_Rmax_der = np.empty([x.size,x.size])
for i in xrange(x.size):
    z = np.repeat(0,x.size)
    z[i] = 1
    x_Rmin_der[i] = z
remain = np.array(remain)

for i in xrange(x.size):
    z = np.repeat(0,x.size)
    z[i] = -1
    x_Rmax_der[i] = z

remain = np.array(remain)

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


res = minimize(func, x,args = (remain), jac=func_deriv,
constraints=cons, method='SLSQP', options={'disp': True}) #COBYLA SLSQP

print "res.x = ",res.x
print "With Rmin sum te = ",ceil(sum(remain/Rmin))
print "x_Rmax_der",x_Rmax_der
print " x_Rmin_der", x_Rmin_der

