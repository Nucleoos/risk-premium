'''
Created on Dec 18, 2010

@author: t-bone
'''
from google.appengine.ext import db
from pricing import option
import datetime


class UnitOfMeasure(db.Model):

    name = db.StringProperty()
    type = db.StringProperty(choices=set(['Energy','Volume']))
    joules_con_factor = db.FloatProperty(verbose_name='Conversion factor to joule')

class Commodity(db.Model):
    
    name = db.StringProperty()
    uom =  db.ReferenceProperty(UnitOfMeasure,verbose_name='Unit of Measure',collection_name='commodity_uom')
    
    def reference(self):
        return 'trade.underlying'

class Holiday(db.Model):
    
    name = db.StringProperty()
    date = db.ListProperty(datetime.datetime)

class Calendar(db.Model):
    
    name = db.StringProperty()
    holiday = db.ListProperty(db.Key)
    weekend = db.BooleanProperty()
    
class Profile(db.Model):
    
    name = db.StringProperty()
    granularity = db.StringProperty()
    shape_factor = db.ListProperty(float)

class Delivery(db.Model):

    name = db.StringProperty()
    first_date = db.DateProperty()
    last_date = db.DateProperty()
    calendar = db.ReferenceProperty(collection_name='delivery_cal')
    profile = db.ReferenceProperty(collection_name='delivery_profile')
    
    def reference(self):
        return 'trade.underlying'

class Underlying(db.Model):
    
    commodity = db.ReferenceProperty(Commodity,collection_name='underlyings_com')
    delivery_point = db.ReferenceProperty(collection_name='underlyings_dp')
    delivery = db.ReferenceProperty(Delivery,collection_name='underlyings')
    quantity = db.FloatProperty()
    trade = db.ReferenceProperty(collection_name='underlyings_trade')
    weight = db.FloatProperty()
    uom = db.ReferenceProperty(UnitOfMeasure,collection_name='underlyings_uom')

class Book(db.Model):
    
    name = db.StringProperty()
    parent_book = db.SelfReferenceProperty(collection_name='child_books')
    child_book = db.SelfReferenceProperty(collection_name='parent_books')
    
    def reference(self):
        return 'trade'

class Trade(db.Model):
    
    book = db.ReferenceProperty()
    date = db.DateProperty()
    derivative = db.ReferenceProperty(collection_name='trade_derivative')
    strike = db.FloatProperty()
    buy_sell = db.StringProperty(verbose_name='Buy or Sell',choices=set(["Buy", "Sell"]))
    call_put = db.StringProperty(verbose_name='Call or Put',choices=set(["Call", "Put"]))
    trade_price = db.FloatProperty()
    expiry = db.DateProperty()
    underlying = db.ListProperty(db.Key)
    #uom = db.ReferenceProperty(UnitOfMeasure,collection_name='trades')
    
    def eval(self,market):
        
        time_to_expiry = (self.expiry - market.eod.date)
        time_to_expiry = float(time_to_expiry.days)/360

        if self.buy_sell == 'Buy':
            buy_sell = 1 
        else: 
            buy_sell = -1
            
        if self.derivative.name == 'Forward':
            
            self.MTM = (market.price.mid - self.strike) * self.underlying.delivery.volume * buy_sell
            
        elif self.derivative.name == 'Option':
            mtm = option.black76(self.call_put,
                                       market.price.mid,
                                       self.strike,
                                       time_to_expiry,
                                       #market.irate.constant_maturity,
                                       0.0,
                                       market.volatility.mid)
            delta = option.black76_delta(self.call_put,
                                           market.price.mid,
                                           self.strike,
                                           time_to_expiry,
                                           #market.irate.constant_maturity,
                                           0.0,
                                           market.volatility.mid)
            self.mtm = mtm * self.underlying.delivery.volume * buy_sell
            self.delta = delta * self.underlying.delivery.volume * buy_sell
        #=======================================================================
        else:
            self.MTM = self.derivative.name + ' is an unknown valuation model.'

class DeliveryPoint(db.Model):
    
    name = db.StringProperty(db.Model)
    nickname = db.StringProperty(db.Model)
    commodity = db.ReferenceProperty(Commodity)
    
class Market(db.Model):
    
    eod = db.ReferenceProperty(collection_name='market_eod')
    price = db.ReferenceProperty(collection_name='market_prices')
    volatility = db.ReferenceProperty(collection_name='market_volatilities')
    delivery_point = db.ReferenceProperty(DeliveryPoint,collection_name='markets')
    delivery = db.ReferenceProperty(Delivery,collection_name='market_delivery')
    
class Price(db.Model):
    
    mid = db.FloatProperty()
    bid = db.FloatProperty()
    offer = db.FloatProperty()
    
class Volatility(db.Model):
    
    historical = db.FloatProperty()
    mid = db.FloatProperty()
    bid = db.FloatProperty()
    offer = db.FloatProperty()
    moneyness = db.FloatProperty()
    
class Analytic(db.Model):
    
    date = db.ReferenceProperty(collection_name='analytics_eod')
    trade = db.ReferenceProperty(Trade,collection_name='analytics')
    MTM = db.FloatProperty()
    
class EndOfDay(db.Model):
    
    date = db.DateProperty()
    
class Derivatives(db.Model):
    
    name = db.StringProperty()
    algorythm = db.StringProperty()
    
class Exchanges(db.Model):
    
    name = db.StringProperty()
    
class Products(db.Model):
    
    name = db.StringProperty
    exchange = db.ReferenceProperty(collection_name='products_ex')
    code = db.StringProperty()
    size = db.FloatProperty()
    uom = db.ReferenceProperty(UnitOfMeasure,collection_name='products_uom')
    currency = db.ReferenceProperty(collection_name='products_currency')
    payment_date = db.ReferenceProperty(collection_name='products_payment')
    settlement = db.StringProperty()