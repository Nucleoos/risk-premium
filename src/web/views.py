'''
Created on Dec 27, 2010

@author: t-bone
'''
from django.shortcuts import render_to_response
from django.forms import forms, fields, widgets
from google.appengine.api import taskqueue
#from google.appengine.ext import db
from django.http import HttpResponseRedirect, HttpResponse
from google.appengine.api import memcache
from datastore import models
from google.appengine.ext.db import djangoforms
from django.forms.extras.widgets import SelectDateWidget
from miscellaneous import data_loader
from google.appengine.api import users
import time, datetime
from risk.VaR import VaR


LEFT_KIND = [
('Book', 'Book'),
('Commodity', 'Commodity')]

TOP_KIND = [('Period','Period')]

PRODUCT = [('Forward','Forward'),
           ('Option','Option')]

PERIOD_TYPE = [('Week','Week'),
               ('Month','Month'),
               ('Year','Year')]

def entry(request,kind,obj_id = None):

    if request.method == 'POST':
        
        error = None
        if obj_id:
            db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
            form = eval(kind + 'Form(data=request.POST,instance=db_obj)')
        else:
            form = eval(kind + 'Form(data=request.POST)')
        
        form.set_choices()
        
        if form.is_valid():
            db_obj = form.save(commit=False)
            db_obj.put()
            obj_id = str(db_obj.key().id())
        else:
            error = form.errors

        if error:
            return render_to_response('entry.html',{'form' : form,
                                                'obj_id' : obj_id,
                                                'kind' : kind})
        else:
            return HttpResponseRedirect('/entry/' + kind)
    else:
        if obj_id:
            db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
            form = eval(kind + 'Form(instance = db_obj)')
            form.set_choices()
        else:
            form = eval(kind + 'Form()')
            form.set_choices()
            
        return render_to_response('entry.html',{'form' : form,
                                                'obj_id' : obj_id,
                                                'kind' : kind})

def entry_list(request,kind = 'Holiday',obj_id = None):

    if request.method == 'POST':
        
        entry_button = request.POST.get('entry')
        error = None
        if obj_id:
            db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
            form = eval(kind + 'Form(data=request.POST,instance=db_obj)')
        else:
            form = eval(kind + 'Form(data=request.POST)')
        
        form.set_choices()
        
        if form.is_valid():
            db_obj = form.save(commit=False)
            db_obj.put()
            obj_id = str(db_obj.key().id())
        else:
            error = form.errors

        if error:
            return render_to_response('entry_list.html',{'form' : form,
                                                'obj_id' : obj_id,
                                                'kind' : kind})
        elif entry_button == 'Add':
            return render_to_response('entry_list.html',{'form' : form,
                                                'obj_id' : obj_id,
                                                'kind' : kind,
                                                'list' : db_obj.date})
        else:
            return HttpResponseRedirect('/entry/' + kind)
    else:
        list = []
        if obj_id:
            db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
            form = eval(kind + 'Form(instance = db_obj)')
            form.set_choices()
        else:
            form = eval(kind + 'Form()')
            form.set_choices()
            
        return render_to_response('entry_list.html',{'form' : form,
                                                'obj_id' : obj_id,
                                                'kind' : kind,
                                                'list' : db_obj.date})

def trade_entry(request, derivative = 'Forward', basket = False, trade_id = None, underlying_id = None):
    
    if request.method == 'POST':
        
        entry_button = request.POST.get('entry')
        
        if trade_id:
            trade = models.Trade.get_by_id(int(trade_id))
            form = TradeForm(data=request.POST,instance=trade)
        else:
            form = TradeForm(data=request.POST)
        
        form.set_choices()
        
        if form.is_valid():
            trade = form.save(commit=False)
            trade.put()
        else:
            underlying_form = UnderlyingForm(data=request.POST)
            underlying_form.set_choices()
            delivery_form = DeliveryForm(data=request.POST)
            delivery_form.set_choices()
            return render_to_response('trade.html',{'form' : form,
                                                'obj_id' : trade_id,
                                                'kind' : derivative,
                                                'basket' : basket,
                                                'subform' : underlying_form,
                                                'subsubform' : delivery_form})
        
        #Underlying
        underlying = models.Underlying.all().filter('trade =',trade).get()
        if basket:
            if underlying and entry_button == 'Save':
                underlying_form = UnderlyingForm(trade = trade,data=request.POST,instance=underlying)
            else:
                underlying_form = UnderlyingForm(trade = trade,data=request.POST)
        else:
            if underlying:  
                underlying_form = SingleUnderlyingForm(trade = trade,data=request.POST,instance=underlying)
            else:
                underlying_form = SingleUnderlyingForm(trade = trade,data=request.POST)
                
        underlying_form.set_choices()
        
        if underlying_form.is_valid():
            underlying = underlying_form.save(commit=False)
            underlying.put()
        else:
            delivery_form = DeliveryForm(data=request.POST)
            delivery_form.set_choices()
            return render_to_response('trade.html',{'form' : form,
                                                'obj_id' : trade_id,
                                                'kind' : derivative,
                                                'basket' : basket,
                                                'subform' : underlying_form,
                                                'subsubform' : delivery_form})

        #Delivery term of the trade
        if underlying.delivery:
            delivery_form = DeliveryForm(underlying = underlying,data=request.POST,instance=underlying.delivery)
        else:
            delivery_form = DeliveryForm(underlying = underlying,data=request.POST)
        
        delivery_form.set_choices()
            
        if delivery_form.is_valid():
            delivery = delivery_form.save(commit=False)
            delivery.put()
            underlying.delivery = delivery
        else:
            return render_to_response('trade.html',{'form' : form,
                                                'obj_id' : trade_id,
                                                'kind' : derivative,
                                                'basket' : basket,
                                                'subform' : underlying_form,
                                                'subsubform' : delivery_form})
        
        #Saves the underlying key on the trade
        if underlying_form.is_valid():
            underlying.put()
            trade.underlying.append(underlying.key())
                #subobj_id = db_subobj.key().id()
        if form.is_valid():
            trade.put()
            
        if not(trade_id):
            trade_id = str(trade.key().id())
        
        if entry_button != "Save":
            request.method = 'GET'
            return HttpResponseRedirect('/entry/Trade/' + derivative + '/Basket:' + trade_id)
        else:
            return HttpResponseRedirect('/entry/Trade/')
    else:
        delivery_form = None
        underlying_form = None
        underlying_list = []
        
        if trade_id:
            trade = models.Trade.get_by_id(int(trade_id))
            form = TradeForm(instance = trade)
            form.set_choices()

            #subobj_id = trade.underlying.key().id()
            #underlying_keys = trade.underlying
            underlying_query = models.Underlying.all().filter('trade =',trade)
            underlying_instance = underlying_query.get()
            if underlying_instance:
                if basket:
                    underlying_form = UnderlyingForm(initial={"commodity" : underlying_instance.commodity.name,
                                                  "delivery_point" : underlying_instance.delivery_point.name,
                                                  "weight" : underlying_instance.weight,
                                                  "uom" : underlying_instance.uom.name})
                    for underlying in underlying_query:
                        underlying_list.append([str(underlying.weight) + ': ' + underlying.commodity.name + ' @ ' + underlying.delivery_point.name,underlying.key().id()])
                    
                    
                else:
                    underlying_form = SingleUnderlyingForm(initial={"commodity" : underlying_instance.commodity.name,
                                                                    "delivery_point" : underlying_instance.delivery_point.name,
                                                                    "uom" : underlying_instance.uom.name})
                
                delivery = underlying_instance.delivery
            else:
                underlying_form = UnderlyingForm()
                #underlying_list.append(['No underlying is set'])
                delivery = None
                 
            underlying_form.set_choices()
            
            if delivery:
                #delivery_id = delivery.key().id()
                delivery_form = DeliveryForm(initial={"period" : underlying_instance.delivery.period.name,
                                                      "calendar" : underlying_instance.delivery.calendar.name,
                                                      "profile" : underlying_instance.delivery.profile.name})
            else:
                delivery_form = DeliveryForm()
            
            delivery_form.set_choices()
            
        else:
            form = ForwardForm(data=request.GET)
            form.set_choices()

            if basket:
                underlying_form = UnderlyingForm()
            else:
                underlying_form = SingleUnderlyingForm()
            underlying_form.set_choices()
                
            delivery_form =DeliveryForm()
            delivery_form.set_choices()
            
        return render_to_response('trade.html',{'form' : form,
                                                'obj_id' : trade_id,
                                                'kind' : derivative,
                                                'basket' : basket,
                                                'list' : underlying_list,
                                                'subform' : underlying_form,
                                                'subsubform' : delivery_form})

def option_entry(request,obj_id = None,subkind = None,subobj_id = None):
    
    if request.method == 'POST':
        if obj_id:
            db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
            form = eval(kind + 'Form(data=request.POST,instance=db_obj)')
        else:
            form = eval(kind + 'Form(data=request.POST)')
        
        form.set_choices()
        
        if form.is_valid():
            db_obj = form.save(commit=False)
            db_obj.put()
        else:
            pass
        
        subkind = form.reference()
        if subkind:
            if db_obj.underlying:
                subform = eval(subkind + 'Form(trade = db_obj,data=request.POST,instance=db_obj.underlying)')
            else:
                subform = eval(subkind + 'Form(trade = db_obj,data=request.POST)')
            subform.set_choices()
            if subform.is_valid():
                underlying = subform.save(commit=False)
                underlying.put()
            else:
                print subform.errors()
            subsubkind = subform.reference()
            if subsubkind:
                if underlying.delivery:
                    subsubform = eval(subsubkind + 'Form(underlying = underlying,data=request.POST,instance=underlying.delivery)')
                else:
                    subsubform = eval(subsubkind + 'Form(underlying = underlying,data=request.POST)')
                if subsubform.is_valid():
                    subsubdb_obj = subsubform.save(commit=False)
                    subsubdb_obj.put()
                    underlying.delivery = subsubdb_obj
                else:
                    print subsubform.errors()
        
            if subform.is_valid():
                underlying.put()
                db_obj.underlying = underlying
                #subobj_id = db_subobj.key().id()
        if form.is_valid():
            db_obj.put()
            
        if not(obj_id):
            obj_id = str(db_obj.key().id())
        
        entry_button = request.POST.get('entry')
        if entry_button != "Save":
            request.method = 'GET'
            return HttpResponseRedirect('/entry/' + kind + ':' + obj_id + '/' + entry_button)
        else:
            return HttpResponseRedirect('/entry/' + kind)
    else:
        subsubform = None
        subform = None
        if obj_id:
            db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
            form = eval(kind + 'Form(instance = db_obj)')
            form.set_choices()
            subkind = form.reference()
            if subkind:
                subobj_id = eval('db_obj.' + subkind.lower() + '.key().id()')
                subform = eval(subkind + 'Form(initial={"commodity" : db_obj.underlying.commodity.name})')
                subform.set_choices()
                subsubkind = subform.reference()
                if subsubkind:
                    subsubdb_obj = eval('db_obj.' + subkind.lower() + '.'+ subsubkind.lower())
                    if subsubdb_obj:
                        subsubobj_id = subsubdb_obj.key().id()
                        #subsubdb_obj = eval('models.' + subsubkind + '.get_by_id(int(subsubobj_id))')
                        #db_obj.underlying = underlying
                        #db_obj.put()
                        subsubform = eval(subsubkind + 'Form(initial={"date" : db_obj.underlying.delivery.date,"quantity" : db_obj.underlying.delivery.quantity})')
                    else:
                        subsubform = eval(subsubkind + 'Form()')   
        else:
            form = TradeForm(data=request.GET)
            form.set_choices()
            subkind = form.reference()
            if subkind:
                subform = eval(subkind + 'Form()')
                subform.set_choices()
                subsubkind = subform.reference()
                if subsubkind:
                    subsubform = eval(subsubkind + 'Form()')
                    subsubform.set_choices()
        return render_to_response('trade.html',{'form' : form,
                                                'obj_id' : obj_id,
                                                'kind' : 'Trade',
                                                'subform' : subform,
                                                'subsubform' : subsubform})
    
def delete(request,kind,obj_id = None):
    
    if obj_id:
        db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
        db_obj.delete()
    else:
        pass
    return HttpResponseRedirect('/entry/' + kind)

def underlying_delete(request, derivative = 'Forward', basket = False, trade_id = None, underlying_id = None):
    
    if underlying_id:
        underlying = models.Underlying.get_by_id(int(underlying_id))
        underlying.trade.underlying.remove(underlying.key())
        underlying.trade.put()
        underlying.delete()
    else:
        pass
    return HttpResponseRedirect('/entry/Trade/' + derivative + '/Basket:' + trade_id)

def list_delete(request, kind = 'Holiday', obj_id = None,attribute = None, year = None, month = None, day =None):
    
    if year:
        date = datetime.datetime(int(year),int(month),int(day))
        
    if obj_id:
        db_obj = eval('models.' + kind + '.get_by_id(int(obj_id))')
        eval('db_obj.' + attribute + '.remove(date)')
        db_obj.put()
    else:
        pass
    return HttpResponseRedirect('/entry/' + kind + ':' + obj_id)

def list(request,kind):

    db_obj = eval('models.' + kind + '.all()')
    return render_to_response('list.html',{'list' : db_obj,'kind' : kind})

def imports(request):

    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        import_type = request.POST.get('import')
        if import_type == 'Import Prices':
            result = data_loader.price(request.FILES['file'])
        elif import_type == 'Import Volatilities':
            result = data_loader.volatility(request.FILES['file'])
        elif import_type == 'Import Interest Rate':
            result = data_loader.interest_rate(request.FILES['file'])
        else:
            result = False
        
        if result:
            done = 'Completed'
        else:
            done ='Failed'
        
    else:
        done = ''
        form = ImportForm()
    
    return render_to_response('import.html',{'form' : form,'done':done})

def import_prices(request):
    
    result = data_loader.price(request.FILES['file'])
    
    return HttpResponseRedirect('/')

def script(request):
    #trade_query = models.Trade.all()
    #derivative = models.Derivatives.all().filter("name =","Forward").get()
    
    #for trade in trade_query:
        #trade.derivative = derivative
        #trade.put()
            
    if request.method == 'POST':
        
        query = models.EndOfDay.all()
     
        for item in query:
            item.delete()
        
        query = models.Market.all()
            
        for item in query:
            item.delete()
            
        query = models.Price.all()
            
        for item in query:
            item.delete()  
    #    
    #    query = models.Volatility.all()
    #        
    #    for item in query:
    #        item.delete()
    #        
        query = models.Delivery.all()
            
        for item in query:
            item.delete()

        query = models.Underlying.all()
            
        for item in query:
            item.delete()
 
        query = models.Trade.all()
            
        for item in query:
            item.delete()   
        
           
        done = 'Completed'
    else:
        done = ""
        
    return render_to_response('script.html',{'done' : done})

def cube(request):

    trades = models.Trade.all()
    
    if trades.get():
    
        if request.method == 'POST':
            
            left_kind = request.POST.get('left_kind', '')
            left_obj = eval('models.' + left_kind + ".all().order('name')")
            left_ref = left_obj.get().reference()
            
            top_kind = request.POST.get('top_kind','')
            top_obj = eval('models.' + top_kind + ".all().order('first_date').filter('type =','Month')")
            top_ref = top_obj.get().reference()
            
            top = [top.name for top in top_obj]
            
            left = [left.name for left in left_obj]
            
            center = [[0 for element in top] for item in left]
            #for item in left:
            #    center[counter_left].append(left[counter_left])
            for trade in trades:
                for underlying_key in trade.underlying:
                    underlying = models.Underlying.get_by_id(underlying_key.id_or_name())
                    ix_top = eval('top.index(' + top_ref + '.' + top_kind.lower() + '.name)')
                    ix_left = eval('left.index(' +  left_ref + '.' + left_kind.lower() + '.name)')
                    center[ix_left][ix_top] = center[ix_left][ix_top] + trade.quantity
                
            form = CubeForm(request.POST)
            
        else:
            
            periods = models.Period.all().order('first_date').filter("type =", 'Month')
            commodity = models.Commodity.all().order('name')
            
            top = [period.name for period in periods]

            left = [com.name for com in commodity]
            
            center = [[0 for element in top] for item in left]
            #for item in left:
            #    center[counter_left].append(left[counter_left])
            for trade in trades:
                for underlying_key in trade.underlying:
                    underlying = models.Underlying.get_by_id(underlying_key.id_or_name())
                    ix_top = top.index(underlying.delivery.period.name)
                    ix_left = left.index(underlying.commodity.name)
                    center[ix_left][ix_top] = center[ix_left][ix_top] + trade.quantity
        
            form = CubeForm()
        
        center_temp = [[item] for item in left]
        for i in range(len(center)):
            center_temp[i].extend(center[i])
        center = center_temp
    
    else:
        center = None
        left = None
        form = CubeForm()
        top = 'No trade are saved. Please create a trade before using this tool.'
        
    return render_to_response('cube.html',{'center' : center,'left' : left, 'top' : top,'form' : form})

def VaR(request):
    
    user = users.get_current_user()
    
    if user:
        logout_url = users.create_logout_url("/")
        result = VaR()
        return render_to_response("VaR.html",{'user':user,'sign_out':logout_url,'result':result})
    else:
        return render_to_response("welcome.html")
        
def welcome(request):
    
    user = users.get_current_user()

    if user:
        loginout_url = users.create_logout_url("/")
    else:
        loginout_url = users.create_login_url("/")
    return render_to_response("welcome.html",{'user':user,'sign_in':loginout_url})

def valuation_engine(request,derivative = 'Option on Spot'):
    
    user = users.get_current_user()

    if user:
        login_url = users.create_logout_url("/valuation")
    else:
        login_url = users.create_login_url("/valuation")
    
    if request.method == 'POST':
        
        select_form = SelectDerivativeForm(request.POST)
        
        if derivative == 'Spread Option':
            form = ValuationParameterForm(request.POST)
            market_form = ValuationMarketForm(request.POST)
            
                        
            if form.is_valid() and select_form.is_valid() and market_form.is_valid():
                strike = form.cleaned_data['strike']
                expiry = form.cleaned_data['expiry_date']
                buy_sell = form.cleaned_data['buy_sell']
                call_put = form.cleaned_data['call_put']
                quantity = form.cleaned_data['quantity']
                date = form.cleaned_data['valuation_date']
                price = []
                price.append(market_form.cleaned_data['underlying_price'])
                price.append(market_form.cleaned_data['underlying_price_2'])
                vol=[]
                vol.append(market_form.cleaned_data['volatility'])
                vol.append(market_form.cleaned_data['volatility_2'])
                corr = market_form.cleaned_data['correlation']
                interest_rate = market_form.cleaned_data['interest_rate']
                derivative = select_form.cleaned_data['derivative']
            else:
                return render_to_response("valuation_engine.html",{'user':user,'sign_in':login_url,
                                                                   'form' : form,'select_form' : select_form,
                                                                   'market_form':market_form,
                                                                   'derivative':derivative})
                
            derivative_instance = models.Derivatives.all().filter('name =',derivative).get()
            
            eod = models.EndOfDay(date=date)
            eod.put()
            
            interest_rate = models.InterestRate(constant_maturity=interest_rate)
            interest_rate.put()    
                
            trade = models.Trade(derivative=derivative_instance,
                          strike=strike,
                          buy_sell=buy_sell,
                          call_put=call_put,
                          expiry=expiry,
                          quantity=quantity)
            
            price = [models.Price(mid=p) for p in price]
            [p.put() for p in price]

            volatility = [models.Volatility(mid=v) for v in vol]
            [v.put() for v in volatility]
            
            market = []
            for i in range(len(price)):
                market.append(models.Market(eod=eod,
                                            price=price[i],
                                            volatility=volatility[i],
                                            interest_rate=interest_rate,
                                            correlation=corr))
            
            trade.eval(market)
            results = {'MTM' : trade.mtm,'Delta' : trade.delta}                  
            
            [p.delete() for p in price]
            [v.delete() for v in volatility]
                            
        elif derivative == 'Forward':
            form = ForwardParameterForm(request.POST)
            market_form = ForwardMarketForm(request.POST)
            
            if form.is_valid() and select_form.is_valid() and market_form.is_valid():
                strike = form.cleaned_data['strike']
                expiry = form.cleaned_data['expiry_date']
                buy_sell = form.cleaned_data['buy_sell']
                quantity = form.cleaned_data['quantity']
                date = form.cleaned_data['valuation_date']
                price = market_form.cleaned_data['underlying_price']
                interest_rate = market_form.cleaned_data['interest_rate']
                derivative = select_form.cleaned_data['derivative']
            else:
                return render_to_response("valuation_engine.html",{'user':user,'sign_in':login_url,
                                                                   'form' : form,'select_form' : select_form,
                                                                   'market_form':market_form,
                                                                   'derivative':derivative})
                
            derivative_instance = models.Derivatives.all().filter('name =',derivative).get()
            
            eod = models.EndOfDay(date=date)
            eod.put()
            
            interest_rate = models.InterestRate(constant_maturity=interest_rate)
            interest_rate.put()
            
            trade = models.Trade(derivative=derivative_instance,
                          strike=strike,
                          buy_sell=buy_sell,
                          expiry=expiry,
                          quantity=quantity)
            
            price = models.Price(mid=price)
            price.put()
            
            market = models.Market(eod=eod,price=price,interest_rate=interest_rate)
            
            trade.eval(market)
            results = {'MTM' : trade.mtm,'Delta' : trade.delta}
            
            price.delete()
                     
        else:
            form = ValuationParameterForm(request.POST)
            market_form = OptionMarketForm(request.POST)
            
            if form.is_valid() and select_form.is_valid() and market_form.is_valid():
                strike = form.cleaned_data['strike']
                expiry = form.cleaned_data['expiry_date']
                buy_sell = form.cleaned_data['buy_sell']
                call_put = form.cleaned_data['call_put']
                quantity = form.cleaned_data['quantity']
                date = form.cleaned_data['valuation_date']
                price = market_form.cleaned_data['underlying_price']
                vol=market_form.cleaned_data['volatility']
                interest_rate = market_form.cleaned_data['interest_rate']
                derivative = select_form.cleaned_data['derivative']
            else:
                return render_to_response("valuation_engine.html",{'user':user,'sign_in':login_url,
                                                                   'form' : form,'select_form' : select_form,
                                                                   'market_form':market_form,
                                                                   'derivative':derivative})
        
        
            derivative_instance = models.Derivatives.all().filter('name =',derivative).get()
            
            eod = models.EndOfDay(date=date)
            eod.put()
            
            interest_rate = models.InterestRate(constant_maturity=interest_rate)
            interest_rate.put()

            trade = models.Trade(derivative=derivative_instance,
                          strike=strike,
                          buy_sell=buy_sell,
                          call_put=call_put,
                          expiry=expiry,
                          quantity=quantity)
            
            price = models.Price(mid=price)
            price.put() 

            volatility = models.Volatility(mid=vol)
            volatility.put()

            market = models.Market(eod=eod,price=price,volatility=volatility,interest_rate=interest_rate)
        
            trade.eval(market)
            results = {'MTM' : trade.mtm,'Delta' : trade.delta}
            
            price.delete()
            volatility.delete()
        
        eod.delete()
        interest_rate.delete()
        
        return render_to_response("valuation_engine.html",{'user':user,
                                                           'sign_in':login_url,
                                                           'form' : form,
                                                           'select_form':select_form,
                                                           'market_form':market_form,
                                                           'derivative':derivative,
                                                           'results': results})
        
    else:
        
        if derivative == 'Spread Option':
            form = ValuationParameterForm()
            market_form = ValuationMarketForm()
        elif derivative == 'Forward':
            form = ForwardParameterForm()
            market_form = ForwardMarketForm()
        else:
            form = ValuationParameterForm()
            market_form = OptionMarketForm()
            
        select_form = SelectDerivativeForm({'derivative':derivative})
        return render_to_response("valuation_engine.html",{'user':user,'sign_in':login_url,
                                                           'form' : form,'select_form':select_form,
                                                           'market_form':market_form,
                                                           'derivative':derivative})
    
    
def market(request):
    
    if request.method == 'POST':
        
        eod = time.strptime(request.POST.get('eod', ''),"%Y-%m-%d")
        eod = datetime.date(eod[0],eod[1],eod[2])
        eod = models.EndOfDay.all().filter("date =",eod).get()
        delivery_point = models.DeliveryPoint.all().filter("name =", request.POST.get('delivery_point', '')).get()
        
        market = models.Market.all()
        market.filter("eod =", eod)
        market.filter("delivery_point =", delivery_point)
        
        market_form = MarketForm(request.POST)
        market_form.set_choices()
        
        if request.POST.get('type', '')=='Price':
            table = [['Delivery','Mid','Bid','Offer']]
            for item in market:
                table.append([item.delivery.period.name,item.price.mid,item.price.bid,item.price.offer])
        elif request.POST.get('type', '')=='Volatility':
            table = [['Delivery','Mid','Moneyness']]
            for item in market:
                table.append([item.delivery.period.name,item.volatility.mid,item.volatility.moneyness])
        else:
            table = []
            pass
        
        return render_to_response("market.html",{'form':market_form,'table':table})
        
    else:
        market_form = MarketForm()
        market_form.set_choices()

        return render_to_response("market.html",{'form':market_form})
        
class CommodityForm(djangoforms.ModelForm):
    
    uom = fields.ChoiceField(label='Unit of Measure')
    name = fields.CharField()
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        
        if data:
            super(CommodityForm, self).__init__(data=data)
        elif self.instance:
            initial = {'uom':self.instance.uom.name,
                       'name':self.instance.name}
            super(CommodityForm, self).__init__(data=initial)
        else:
            super(CommodityForm, self).__init__(*args, **kwargs)
                    
    def set_choices(self):
        uom = models.UnitOfMeasure.all().order('name')
        self['uom'].field.choices = [(x.name,x.name) for x in uom]

    
    def save(self, commit=True):
        uom = models.UnitOfMeasure.all()
        uom.filter("name =", self.cleaned_data['uom'])
        
        if self.instance:
            
            instance = self.instance
            instance.uom = uom.get()
            instance.name = self.cleaned_data['name']
        else:
            instance = models.Commodity(uom = uom.get(), name = self.cleaned_data['name'])
        if commit:
            instance.put()
        return instance
        
    def reference(self): 
        return None

class DeliveryForm(forms.Form):
    
    period = fields.ChoiceField()
    calendar = fields.ChoiceField()
    profile = fields.ChoiceField()
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance =kwargs.get('instance',None)
        if data:
            super(DeliveryForm, self).__init__(data=data)
        elif self.instance:
            initial = {'period':self.instance.period,
                      'calendar':self.instance.calendar,
                      'profile':self.instance.profile}
            super(DeliveryForm, self).__init__(data=initial)
        else:
            super(DeliveryForm, self).__init__(*args, **kwargs)
        
    def set_choices(self):
        period = models.Period.all().order('name')
        self['period'].field.choices = [(x.name,x.name) for x in period]
        calendar = models.Calendar.all().order('name')
        self['calendar'].field.choices = [(x.name,x.name) for x in calendar]
        profile = models.Profile.all().order('name')
        self['profile'].field.choices = [(x.name,x.name) for x in profile]
    
    def save(self, commit=True):
        period = models.Period.all()
        period.filter("name =", self.cleaned_data['period'])
        calendar = models.Calendar.all()
        calendar.filter("name =", self.cleaned_data['calendar'])
        profile = models.Profile.all()
        profile.filter("name =", self.cleaned_data['profile'])
        if self.instance:
            instance = self.instance
            instance.period = period.get()
            instance.calendar = calendar.get()
            instance.profile = profile.get()
        else:
            instance = models.Delivery(period = period.get(),
                                       calendar = calendar.get(),
                                       profile = profile.get())
        if commit:
            instance.put()
        return instance
        
class UnderlyingForm(forms.Form):
    
    commodity = fields.ChoiceField(label='Commodity')
    delivery_point = fields.ChoiceField(label='Delivery Point')
    weight = fields.FloatField(label='Weight',initial=1.0,required=False)
    weight.default = 1.0
    uom = fields.ChoiceField(label='Unit of Measure')

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        self.trade = kwargs.get('trade',None)
        
        if data:
            super(UnderlyingForm, self).__init__(data=data)
        elif self.instance:
            initial = {'commodity':self.instance.commodity.name,
                       'delivery_point':self.instance.delivery_point.name,
                       'weight':self.instance.weight,
                       'uom':self.instance.uom.name}
            super(UnderlyingForm, self).__init__(data=initial)
        else:
            super(UnderlyingForm, self).__init__(*args, **kwargs)

    def set_choices(self):
        commodity = models.Commodity.all().order('name')
        self['commodity'].field.choices = [(com.name,com.name) for com in commodity]
        delivery_point = models.DeliveryPoint.all().order('name')
        self['delivery_point'].field.choices = [(dp.name,dp.name) for dp in delivery_point]
        uom = models.UnitOfMeasure.all().order('name')
        self['uom'].field.choices = [(x.name,x.name) for x in uom]
              
    def reference(self):

        return 'Delivery'

    def save(self, *args, **kwargs):
        
        commodity = models.Commodity.all()
        commodity.filter("name =", self.cleaned_data['commodity'])
        delivery_point = models.DeliveryPoint.all()
        delivery_point.filter("name =", self.cleaned_data['delivery_point'])
        uom = models.UnitOfMeasure.all()
        uom.filter("name =", self.cleaned_data['uom'])
        
        if self.instance:
            instance = self.instance
            instance.commodity = commodity.get()
            instance.delivery_point = delivery_point.get()
            instance.trade = self.trade
            instance.weight = self.cleaned_data['weight']
            instance.uom = uom.get()
        else:
            instance = models.Underlying(trade = self.trade,
                                         commodity = commodity.get(),
                                         delivery_point = delivery_point.get(),
                                         weight = self.cleaned_data['weight'],
                                         uom = uom.get())
        if kwargs.get('commit',True):
            instance.put()
        return instance

class SingleUnderlyingForm(UnderlyingForm):
    def __init__(self,*args,**kwargs):
        super(SingleUnderlyingForm, self).__init__(*args,**kwargs)
        self.fields['weight'].widget = fields.HiddenInput()
        #weight = self.fields['weight']
        #weight.widget = 'HiddenInput'
        #del self.fields['weight']
    
    #===========================================================================
    # def save(self, *args, **kwargs):
    #    instance = super(SingleUnderlyingForm, self).save(self, *args, **kwargs)
    #    instance.weight = 1.0 
    #    if kwargs.get('commit',True):
    #        instance.put()
    #    return instance
    #===========================================================================
        
        
class TradeForm(forms.Form):
    
    error_css_class = 'error'
    
    trade_date = fields.DateField(label = 'Trade Date',initial = datetime.date.today(),required = False)
    book = fields.ChoiceField(label='Book',required = False)
    derivative = fields.ChoiceField(label='Class of Derivatives',required = False)
    derivative.widget.attrs["onchange"]="changeForm(this)" 
    strike = fields.FloatField(label='Strike',required = False)
    buy_sell = fields.ChoiceField(label='Buy or Sell',choices=[('Buy','Buy'),('Sell','Sell')],required = False)
    call_put = fields.ChoiceField(label='Call or Put',choices=[('Call','Call'),('Put','Put')],required = False)
    trade_price = fields.FloatField(label='Premium',required = False)
    expiry_date = fields.DateField(label = 'Expiry Date',initial = datetime.date.today(),required = False)
    quantity = fields.FloatField(required = False)

    def __init__(self,*args, **kwargs):

        data = kwargs.get('data',None)
        self.instance =  kwargs.get('instance',None)
        #print instance.date
        if data:
            super(TradeForm, self).__init__(data = data)
        elif self.instance:
            initial = {'trade_date':self.instance.date,
                      'book':self.instance.book.name,
                      'derivative':self.instance.derivative.name,
                      'strike':self.instance.strike,
                      'buy_sell':self.instance.buy_sell,
                      'call_put':self.instance.call_put,
                      'trade_price':self.instance.trade_price,
                      'expiry_date':self.instance.expiry,
                      'quantity':self.instance.quantity}
            #initial = instance2
            #x = y
            super(TradeForm, self).__init__(data = initial)
        else:
            super(TradeForm, self).__init__(*args)

    def reference(self):
        return 'Underlying'
    
    def set_choices(self):
        book = models.Book.all().order('name')
        derivatives = models.Derivatives.all().order('name')
        self['book'].field.choices = [(b.name,b.name) for b in book]
        self['derivative'].field.choices = [(x.name,x.name) for x in derivatives]

    def save(self, commit=True):
        book = models.Book.all()
        book.filter("name =", self.cleaned_data['book'])
        derivatives = models.Derivatives.all()
        derivatives.filter("name =", self.cleaned_data['derivative'])
        
        if self.instance:
            instance = self.instance
            instance.date = self.cleaned_data['trade_date']
            instance.book = book.get()
            instance.derivative = derivatives.get()
            instance.srike = self.cleaned_data['strike']
            instance.buy_sell = self.cleaned_data['buy_sell']
            instance.call_put = self.cleaned_data['call_put']
            instance.trade_price = self.cleaned_data['trade_price']
            instance.expiry = self.cleaned_data['expiry_date']
            instance.quantity = self.cleaned_data['quantity']
        else:
            instance = models.Trade(date = self.cleaned_data['trade_date'],
                                    book = book.get(),
                                    derivative = derivatives.get(),
                                    strike = self.cleaned_data['strike'],
                                    buy_sell = self.cleaned_data['buy_sell'],
                                    call_put = self.cleaned_data['call_put'],
                                    trade_price = self.cleaned_data['trade_price'],
                                    expiry = self.cleaned_data['expiry_date'],
                                    underlying = [],
                                    quantity = self.cleaned_data['quantity'])
        
        if commit:
            instance.put()
        return instance

class ForwardForm(TradeForm):
    def __init__(self,*args,**kwargs):
        super(TradeForm, self).__init__(*args,**kwargs)
        del self.fields['call_put']
        self.fields['strike'].label = 'Forward Price'
    
class UnitOfMeasureForm(djangoforms.ModelForm):

    class Meta:
        model = models.UnitOfMeasure
        
    def set_choices(self):
        pass      

    def reference(self):   
        return None
    
class BookForm(djangoforms.ModelForm):
    
    class Meta:
        model = models.Book
        exclude = ['parent_book','child_book']
        
    def set_choices(self):
        pass
    
    def reference(self):   
        return None

class DerivativesForm(djangoforms.ModelForm):
    
    class Meta:
        model = models.Derivatives
        
    def set_choices(self):
        pass
    
    def reference(self):   
        return None
    
class CalendarForm(forms.Form):
    
    name = fields.CharField()
    holiday = fields.MultipleChoiceField(widget=widgets.CheckboxSelectMultiple(),required=False)
    weekend = fields.BooleanField(initial=True,required=False)

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        
        if data:
            super(CalendarForm, self).__init__(data=data)
        elif self.instance:
            initial = {'name':self.instance.name,
                       'weekend':self.instance.weekend,
                       'holiday':self.instance.holiday}
            super(CalendarForm, self).__init__(data=initial)
        else:
            super(CalendarForm, self).__init__(*args, **kwargs)

    def set_choices(self):
        holiday = models.Holiday.all().order('name')
        self['holiday'].field.choices = [(x.key(),x.name) for x in holiday]
        
    def reference(self):
        pass

    def save(self, commit=True):

        holiday = [models.Holiday.get(key).key() for key in self.cleaned_data['holiday']]
                
        if self.instance:
            instance = self.instance
            instance.name = self.cleaned_data['name']
            instance.weekend = (self.cleaned_data['weekend'])
            instance.holiday = holiday
        else:
            instance = models.Calendar(name = self.cleaned_data['name'],
                                            weekend = self.cleaned_data['weekend'],
                                            holiday = holiday)
        if commit:
            instance.put()
        return instance

class ProfileForm(forms.Form):
    
    name = fields.CharField()
    granularity = fields.ChoiceField()
#    field = (fields.FloatField(label='January'),
#            fields.FloatField(label='February'),
#            fields.FloatField(label='march'))
#    shape_factor = fields.MultiValueField(fields=field)

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        
        if data:
            super(ProfileForm, self).__init__(data=data)
        elif self.instance:
            initial = {'name':self.instance.name,
                       'granularity':self.instance.granularity,
                       'shape_factor':self.instance.shape_factor}
            super(ProfileForm, self).__init__(data=initial)
        else:
            super(ProfileForm, self).__init__(*args, **kwargs)

    def set_choices(self):
        choices=[('yearly','yearly'),('monthly','monthly'),('weekly','weekly'),('daily','daily'),('hourly','hourly')]
        self['granularity'].field.choices = choices
        
    def reference(self):
        pass

    def save(self, commit=True):

        if self.instance:
            instance = self.instance
            instance.name = self.cleaned_data['name']
            instance.granularity = (self.cleaned_data['granularity'])
        else:
            instance = models.Profile(name = self.cleaned_data['name'],
                                            granularity = self.cleaned_data['granularity'])
        if commit:
            instance.put()
        return instance
    
class HolidayForm(forms.Form):

    name = fields.CharField()
    date = fields.DateTimeField(initial = datetime.date.today())
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        
        if data:
            super(HolidayForm, self).__init__(data=data)
        elif self.instance:
            initial = {'name':self.instance.name,
                       'date':self.instance.date[-1]}
            super(HolidayForm, self).__init__(data=initial)
        else:
            super(HolidayForm, self).__init__(*args, **kwargs)

    def set_choices(self):
        pass
              
    def reference(self):
        pass

    def save(self, commit=True):

        if self.instance:
            instance = self.instance
            instance.name = self.cleaned_data['name']
            instance.date.append(self.cleaned_data['date'])
        else:
            instance = models.Holiday(name = self.cleaned_data['name'],
                                            date = [self.cleaned_data['date']])
        if commit:
            instance.put()
        return instance

class DeliveryPointForm(forms.Form):
    
    name = fields.CharField()
    nickname = fields.CharField()
    commodity = fields.ChoiceField(label='Commodity')

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        
        if data:
            super(DeliveryPointForm, self).__init__(data=data)
        elif self.instance:
            initial = {'commodity':self.instance.commodity.name,
                       'name':self.instance.name,
                       'nickname':self.instance.nickname}
            super(DeliveryPointForm, self).__init__(data=initial)
        else:
            super(DeliveryPointForm, self).__init__(*args, **kwargs)

    def set_choices(self):
        commodity = models.Commodity.all().order('name')
        self['commodity'].field.choices = [(com.name,com.name) for com in commodity]
              
    def reference(self):
        
        pass

    def save(self, commit=True):
        commodity = models.Commodity.all()
        commodity.filter("name =", self.cleaned_data['commodity'])
        if self.instance:
            instance = self.instance
            instance.commodity = commodity.get()
            instance.name = self.cleaned_data['name']
            instance.nickname = self.cleaned_data['nickname']
        else:
            instance = models.DeliveryPoint(commodity = commodity.get(),
                                            name = self.cleaned_data['name'],
                                            nickname = self.cleaned_data['nickname'])
        if commit:
            instance.put()
        return instance

class PeriodForm(forms.Form):
    
    name = fields.CharField()
    first_date = fields.DateField(label = 'Start Date')
    last_date = fields.DateField(label='End Date')
    type = fields.ChoiceField()

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',None)
        self.instance = kwargs.get('instance',None)
        
        if data:
            super(PeriodForm, self).__init__(data=data)
        elif self.instance:
            initial = {'name':self.instance.name,
                       'first_date':self.instance.first_date,
                       'last_date':self.instance.last_date,
                       'type':self.instance.type}
            super(PeriodForm, self).__init__(data=initial)
        else:
            super(PeriodForm, self).__init__(*args, **kwargs)

    def set_choices(self):
        self['type'].field.choices = PERIOD_TYPE
              
    def reference(self):
        
        pass

    def save(self, commit=True):

        if self.instance:
            instance = self.instance
            instance.name = self.cleaned_data['name']
            instance.first_date = self.cleaned_data['first_date']
            instance.last_date = self.cleaned_data['last_date']
            instance.type = self.cleaned_data['type']
        else:
            instance = models.Period(name = self.cleaned_data['name'],
                                     first_date = self.cleaned_data['first_date'],
                                     last_date = self.cleaned_data['last_date'],
                                     type = self.cleaned_data['type'])
        if commit:
            instance.put()
        return instance
    
class CubeForm(forms.Form):
    
    left_kind = fields.ChoiceField(choices=LEFT_KIND,label = 'Left')
    top_kind = fields.ChoiceField(choices=TOP_KIND,label = 'Top')
    
class SearchForm(forms.Form):
    
    commodity = fields.ChoiceField(label = 'Commodity')
    book = fields.ChoiceField(label = 'Book')
    derivative = fields.ChoiceField(label = 'Class of Derivatives')
    
    def set_choices(self):
        commodity = models.Commodity.all().order('name')
        commodity_list = [(None,'---')]
        commodity_list.extend([(com.name,com.name) for com in commodity])
        self['commodity'].field.choices = commodity_list
        
        book = models.Book.all().order('name')
        book_list = [(None,'---')]
        book_list.extend([(b.name,b.name) for b in book])
        self['book'].field.choices = book_list
        
        derivative = models.Derivatives.all().order('name')
        derivative_list = [(None,'---')]
        derivative_list.extend([(b.name,b.name) for b in derivative])
        self['derivative'].field.choices = derivative_list
        
        
class MarketForm(forms.Form):
    
    eod = fields.ChoiceField(label='End-of-Day')
    delivery_point = fields.ChoiceField(label='Delivery Point')
    type = fields.ChoiceField(label='Type')
    
    def set_choices(self):
        delivery_point = models.DeliveryPoint.all().order('name')
        eod = models.EndOfDay.all().order('-date')
        self['delivery_point'].field.choices = [(x.name,x.name) for x in delivery_point]
        self['eod'].field.choices = [(x.date,x.date) for x in eod]
        self['type'].field.choices = [('Price','Price'),('Volatility','Volatility'),('Interest Rate','Interest Rate')]
        
class ImportForm(forms.Form):

    file = forms.FileField()
    
class ValuationParameterForm(forms.Form):
    
    valuation_date = fields.DateField(label='Valuation_Date',initial = datetime.date.today(),widget=SelectDateWidget())
    buy_sell = fields.ChoiceField(label='Buy or Sell',choices=[('Buy','Buy'),('Sell','Sell')])
    call_put = fields.ChoiceField(label='Call or Put',choices=[('Call','Call'),('Put','Put')])
    quantity = fields.FloatField()
    strike = fields.FloatField(label='Strike')
    expiry_date = fields.DateField(label='Expiration Date',initial = datetime.date.today(),widget=SelectDateWidget())

class ValuationMarketForm(forms.Form):
    
    underlying_price = fields.FloatField(label='Underlying Price')
    underlying_price_2 = fields.FloatField(label='Second Underlying Price')
    volatility = fields.FloatField(label='Underlying Volatility (decimal)')
    volatility_2 = fields.FloatField(label='Second Underlying Volatility (decimal)')
    correlation = fields.FloatField(label='Correlation (decimal)')
    interest_rate = fields.FloatField(label='Risk-free rate (decimal)') 

class OptionMarketForm(ValuationMarketForm):
    def __init__(self,*args,**kwargs):
        super(ValuationMarketForm, self).__init__(*args,**kwargs)
        del self.fields['underlying_price_2'], self.fields['volatility_2'], self.fields['correlation']

class ForwardParameterForm(ValuationParameterForm):
    def __init__(self,*args,**kwargs):
        super(ValuationParameterForm, self).__init__(*args,**kwargs)
        del self.fields['call_put']
        self.fields['strike'].label = 'Trade Price'
        
class ForwardMarketForm(ValuationMarketForm):
    def __init__(self,*args,**kwargs):
        super(ValuationMarketForm, self).__init__(*args,**kwargs)
        del self.fields['underlying_price_2'], self.fields['volatility_2'], self.fields['correlation'], self.fields['volatility']
        self.fields['underlying_price'].label = 'Forward Price'
            
class SelectDerivativeForm(forms.Form):
    
    derivatives = models.Derivatives.all().order('name')
    derivative = fields.ChoiceField(choices = [(x.name,x.name) for x in derivatives],label='Type of Derivative')
    derivative.widget.attrs["onchange"]="changeForm(this)" 
    

        