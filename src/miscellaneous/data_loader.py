'''
Created on Feb 4, 2011

@author: t-bone
'''
#from google.appengine.api import urlfetch


#if result.status_code == 200:
#  parseCSV(result.content)
#import datetime
#from google.appengine.ext import db
#from google.appengine.tools import bulkloader
import csv
from datastore.models import Price, DeliveryPoint, Market, EndOfDay, Delivery, Volatility, Period, Profile, Calendar
import time
import datetime

def price(file):
    
    price_reader = csv.reader(file, delimiter=',', quotechar="'")
    #price_reader = csv.reader(open(file, 'rb'), delimiter=',', quotechar="'")
    #price_reader = file
   
    for row in price_reader:
        
        eod = time.strptime(row[0],"%m/%d/%Y")
        eod = datetime.date(eod[0],eod[1],eod[2])
        
        eod_query = EndOfDay.all()
        eod_instance = eod_query.filter("date =",eod).get()
        if not(eod_instance):
            eod_instance = EndOfDay(date=eod)
        
        delivery_point_query = DeliveryPoint.all()
        delivery_point_nickname = row[1]
        delivery_point_instance = delivery_point_query.filter("nickname =", delivery_point_nickname).get()
        
        period_start = time.strptime(row[2],"%m/%d/%Y")
        period_start = datetime.date(period_start[0],period_start[1],period_start[2])
        period_query = Period.all()
        period_instance = period_query.filter("first_date =",period_start).get()
        
        if period_instance:
                
            profile_query = Profile.all()
            profile_instance = profile_query.filter("name =",'Flat').get()
            
            calendar_query = Calendar.all()
            calendar_instance = calendar_query.filter("name =",'Base').get()
            
            delivery_query = Delivery.all()
            delivery_instance = delivery_query.filter("period =",period_instance).filter("calendar =",'Base').filter("profile =",profile_instance).get()
            if not(delivery_instance):
                delivery_instance = Delivery(period=period_instance,calendar=calendar_instance,profile=profile_instance)
                delivery_instance.put()
            
            price_instance = Price(mid=float(row[3]),
                            bid=float(row[4]),
                            offer=float(row[5]))
            price_instance.put()
            
            eod_instance.put()
            market_instance = Market(eod=eod_instance,
                                     delivery_point = delivery_point_instance,
                                     price = price_instance,
                                     delivery = delivery_instance)
            market_instance.put()
    
    return True

def volatility(file):
    
    reader = csv.reader(file, delimiter=',', quotechar="'")
   
    for row in reader:
        
        eod = time.strptime(row[0],"%m/%d/%Y")
        eod = datetime.date(eod[0],eod[1],eod[2])
        
        eod_query = EndOfDay.all()
        eod_instance = eod_query.filter("date =",eod).get()
        if not(eod_instance):
            eod_instance = EndOfDay(date=eod)
            eod_instance.put()
        
        delivery_point = DeliveryPoint.all()
        delivery_point_nickname = row[1]
        delivery_point.filter("nickname =", delivery_point_nickname)
        delivery_point_instance = delivery_point.get()
        
        volatility_instance = Volatility(mid=float(row[3]),
                        bid=float(row[4]),
                        offer=float(row[5]),
                        moneyness=0.0)
        volatility_instance.put()
        
        delivery = time.strptime(row[2],"%m/%d/%Y")
        delivery = datetime.date(delivery[0],delivery[1],delivery[2])
        delivery_query = Delivery.all().filter("date =",delivery).filter("volume =",1.0)
        delivery_instance = delivery_query.get()
        
        if not(delivery_instance):
            delivery_instance = Delivery(date=delivery,volume=1.0)
            delivery_instance.put()
        
        market = Market.all().filter("eod =",eod_instance)
        market.filter("delivery_point =",delivery_point_instance)
        market.filter("delivery =",delivery_instance)
        market_instance = market.get()
        
        if market_instance:
            market_instance.volatility = volatility_instance
        else:
            market_instance = Market(eod=eod_instance,
                                     delivery_point = delivery_point_instance,
                                     volatility = volatility_instance,
                                     delivery = delivery_instance)
        
        market_instance.put()
    
    return True

def interest_rate(file):
    pass
#price_loader()
#def prices():

    #result = urlfetch.fetch(url="ftp://ftp.cmegroup.com/datamine_sample_data/eod/ECLXF001.csv",)
    #print result.status_code