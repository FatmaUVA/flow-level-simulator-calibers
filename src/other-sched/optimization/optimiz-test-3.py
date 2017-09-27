
import numpy as np
from scipy.optimize import minimize
from math import ceil

def func(x,remain):
    return ( ceil(sum(remain/x)) )

def func_deriv(x,remain):
    """ Derivative of objective function """
    #df_x0 = -1*remain[0]/x[0]**2
    #df_x1 = -1*remain[2]/x[1]**2
    #df_x2 = -1*remain[1]/x[2]**2
    return np.array(-1*remain/x**2)

Rmin = [3000, 2000, 3000]
cons = ({'type': 'ineq',
          'fun' : lambda x,Rmin: np.array([x[0]-Rmin[0],x[1]-Rmin[1],x[2]-Rmin[2]]),
          'jac' : lambda x,Rmin: np.array([[1,0,0],[0,1,0],[0,0,1]]),
          'args': (Rmin,)},
        {'type': 'eq',
          'fun' : lambda x: np.array([10000 - (x[0]+x[1]+x[2])]),
          'jac' : lambda x: np.array([-1,-1,-1])})


Rmin = [3000, 2000, 3000]
remain = [15000.0, 12000.0, 21000.0]
Rmin = np.array(Rmin)
remain = np.array(remain)
x = [3000,2000,3000]
x = np.array(x)
res = minimize(func, x,args = (remain), jac=func_deriv,
constraints=cons, method='SLSQP', options={'disp': True}) #'COBYLA'
#              method='SLSQP', options={'disp': True})

print res
