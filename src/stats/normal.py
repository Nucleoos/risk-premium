'''
Created on Nov 29, 2010

@author: t-bone
'''
import math

def pdf(x, mu=0, sigma=1):
    u = (x-mu)/abs(sigma)
    y = (1/(math.sqrt(2*math.pi)*abs(sigma)))*math.exp(-u*u/2)
    return y

def erf(x):
    
    a = 0.140012

    if x == 0:
        y = 0
    else:
        y = x/abs(x) * math.sqrt(1 - math.exp(-x**2 * (4/math.pi+a*x**2)/(1+a*x**2)))
    return y

def erfc(x):

    y = 1.0 - erf(x)
    return y
    
def cdf(x, mu=0.0, sigma=1.0):
    t = x-mu
    y = 0.5 * (erfc(-t/( sigma * math.sqrt(2.0) )))
    if y>1.0:
        y = 1.0
    return y
    