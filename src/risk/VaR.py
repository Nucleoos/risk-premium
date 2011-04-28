'''
Created on Mar 6, 2011

@author: t-bone
'''
import math
import random
from stats.general import percentile
from datastore import models

def VaR(portfolio,market):

    percent = .975
    
    market = Market()
    mtm = portfolio.eval(market)
    pnl = []    
    for i in range(nsim):
        sim_market = market.shock()
        portfolio.eval(sim_market)
        pnl.append(portfolio.mtm - mtm)
        
    VaR = -percentile(pnl,1-percent)
    
    
class Market(object):

    def __init__(self):

        forward_curve_query = models.ForwardCurve.all().filter

        self.curves = []
        for forward_curve in forward_curve_query:
            self.curves.append(ForwardCurve(forward_curve.name,forward_curve.structure))
        
    def shock(self):
        
        nrisk_factor = 2
        nsim = 100
        S0 = [50,10]
        sigma = [.5,.7]
    
        S = [[]]
        for irisk_factor in range(nrisk_factor):
            for isim in range(nsim):
                S[irisk_factor].append(random.gauss(0,1))
    
        for i in range(nrisk_factor):
            S[i][:]=S0[i]*math.exp(sigma[i]*S[i][:]-(sigma[i]**2)/2)
    
class ForwardCurve(object):

    def __init__(self,name,structure):
        self.name = name
        self.points = []
        for start_date,end_date in structure:
            self.points.append(CurvePoint(self,start_date,end_date))
       
class CurvePoint(object):
    
    def __init__(self,forward_curve,start_date,end_date,start_eod,end_eod):
        
        
        eod_query = models.EndOfDay.all(keys_only=True).filter('date >=',start_eod).filter('date <=',end_eod)

        market_query = models.Market.all().filter('forward_curve =',forward_curve.name)
        market_query.filter('eod in',[eod for eod in eod_query])

        self.price = [market.price.mid for market in market_query]