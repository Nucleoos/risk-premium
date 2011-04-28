'''
Created on Nov 29, 2010

@author: t-bone
'''

import math
from stats.normal import cdf
# Black Merton Scholes Function

def bms(call_put,S,X,T,r,v,q):

    d1 = (math.log(S/X)+(r+v*v/2.)*T)/(v*math.sqrt(T))

    d2 = d1-v*math.sqrt(T)
    if call_put=='c':

        return S*math.exp(-q*T)*cdf(d1)-X*math.exp(-r*T)*cdf(d2)

    else:

        return X*math.exp(-r*T)*cdf(-d2)-S*cdf(-d1)
    
def black76(call_put,S,X,T,r,v):
    
    q = r
    return bms(call_put,S,X,T,r,v,q)
    
def bms_delta(call_put,S,X,T,r,v,q):

    d1 = (math.log(S/X)+(r+v*v/2.0)*T)/(v*math.sqrt(T))

    if call_put=='c':

        return cdf(d1)

    else:

        return cdf(-d1)
    
def black76_delta(call_put,S,X,T,r,v):
    
    d1 = math.exp(-r*T)*(math.log(S/X)+(v*v/2.0)*T)/(v*math.sqrt(T))

    if call_put=='c':
        return cdf(d1)

    else:
        return cdf(-d1)
    
def kirk95(call_put,F,K,T,r,vol,corr):
    
    v = math.sqrt( vol[0]**2
                   -2*F[1]/(F[1]+K)*corr*vol[0]*vol[1]
                   +(F[1]/(F[1]+K))**2*vol[1]*2
                   )
    d1 = (math.log(F[0]/(F[1]+K))+(v*v/2.0)*T)/(v*math.sqrt(T))

    d2 = d1-v*math.sqrt(T)
    
    if call_put=='c':

        return math.exp(-r*T)*(F[0]*cdf(d1)-(F[1]+K)*cdf(d2))

    else:

        return math.exp(-r*T)*((F[1]+K)*cdf(d2)-F[0]*cdf(d1))