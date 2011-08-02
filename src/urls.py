from django.conf.urls.defaults import *
from web.views import *
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^entry/(\w*)/delete/(\d*)', delete),
    #(r'^entry/(\w*):(\d*)/(\w*):(\d*)', entry),
    #(r'^entry/(\w*):(\d*)/(\w*)', subentry),
    (r'^entry/Trade/(\w*)/(\w*):(\d*)/delete:(\d*)', underlying_delete),
    (r'^entry/(\w*):(\d*)/(\w*)/delete:(\d*)-(\d*)-(\d*)', list_delete),
    (r'^entry/Trade/(\w*)/(\w*):(\d*)', trade_entry),
    (r'^entry/Trade:(?P<trade_id>\d*)', trade_entry),
    (r'^entry/Trade/(?P<derivative>\w*):(?P<trade_id>\d*)', trade_entry),
    (r'^entry/Trade:(?P<trade_id>\d*)', trade_entry),
    (r'^entry/Holiday:(?P<obj_id>\d*)', entry_list),
    #(r'^entry/Option:(\d*)', option_entry),
    (r'^entry/(\w*):(\d*)', entry),
    (r'^entry/(\w*)', list),
    (r'^risk/VaR', VaR),
    (r'^risk/FTR', transmission),
    (r'^import/prices/',import_prices),
    (r'^import',imports),
    (r'^script',script),
    (r'^cube',cube),
    #(r'^valuation:(\d*)',valuation),
    (r'^valuation/(.*)',valuation_engine),
    (r'^valuation',valuation_engine),
    (r'^market',market),
    (r'', welcome),
    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    
    #    (r'^(?i)trade', trade_entry),
)
