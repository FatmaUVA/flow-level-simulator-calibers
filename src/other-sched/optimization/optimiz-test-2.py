
import numpy as np
from scipy.optimize import minimize
from math import ceil

def func(x):
    remain = [15000.0, 12000.0, 21000.0]
    return ( ceil(remain[0]/x[0]) + ceil(remain[1]/x[1]) + ceil(remain[2]/x[2]) )

def func_deriv(x):
    """ Derivative of objective function """
    remain = [15000, 12000, 21000]
    df_x0 = -1*remain[0]/x[0]**2
    df_x1 = -1*remain[2]/x[1]**2
    df_x2 = -1*remain[1]/x[2]**2
  
    return np.array([ df_x0,df_x0,df_x0])

cons = ({'type': 'ineq',
          'fun' : lambda x: np.array([x[0]-3000,x[1]-2000,x[2]-3000]),
          'jac' : lambda x: np.array([[1,0,0],[0,1,0],[0,0,1]])},
        {'type': 'eq',
          'fun' : lambda x: np.array([10000 - (x[0]+x[1]+x[2])]),
          'jac' : lambda x: np.array([-1,-1,-1])})

x = [3000,2000,3000]
res = minimize(func, x, jac=func_deriv,
constraints=cons, method='SLSQP', options={'disp': True}) #'COBYLA'
#              method='SLSQP', options={'disp': True})

print res
