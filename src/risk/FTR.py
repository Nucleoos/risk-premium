'''
Created on 2011-07-18

@author: t-bone
'''
from datastore.models import Trade, Derivatives, Underlying, Market, Period, Delivery, DeliveryPoint, Commodity, Profile, Calendar
from matrix.matrix import Matrix
from google.appengine.ext import db

def FTR():
    
    type = Derivatives.all().filter("name =",'FTR').get()
    trade_query = Trade.all().filter('derivative =',type)
    
    portfolio = Portfolio(trade_query)
    portfolio.sim()
    #portfolio.eval()
    result = portfolio.position
    
    return result


class Portfolio():
    
    def __init__(self,trade_query=[]):
 
        for trade in trade_query:
            for underlying_key in trade.underlying:
                underlying = Underlying.get_by_id(underlying_key.id_or_name())
                position = underlying.detailed_delivery()
            
        self.position = position
        #self.scenario = market
    
    def sim(self):
        
        scenario = []
        commodity = Commodity.all().filter("name =",'Electricity').get()
        delivery_point_query = DeliveryPoint.all().filter("commodity =",commodity)
        
        #market_query = Market.all().filter("delivery_point IN",[dp for dp in delivery_point_query])
        
        period_query = Period.all().filter("type =",'Hour')
        profile = Profile.all().filter("granularity =",'hourly').get()
        calendar = Calendar.all().filter("name =",'Base').get()
        
        delivery_query = Delivery.all().filter("profile =",profile).filter("calendar =",calendar)
        counter = 0
        for period in period_query:

            delivery = db.GqlQuery("SELECT * FROM Delivery " +
                                   "WHERE profile = :1 AND calendar = :2 " +
                                   "AND period = :3",
                                   profile,calendar,period).get()

            market = db.GqlQuery("SELECT * FROM Market " +
                                 "WHERE delivery_point = :1 " +
                                 "AND delivery = :3",
                                 [dp for dp in delivery_point_query], delivery)
            scenario.append(market)
            counter = counter + 1

        self.scenario = scenario
    
    def eval(self):
        pnl = Matrix()
        market_query = self.market[0]
        pnl.extend([market.price.day_ahead for market in market_query])
        pnl = pnl[1:]-pnl[0:-1]
            
        self.pnl = pnl #* self.price
