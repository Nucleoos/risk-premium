'''
Created on Nov 20, 2010

@author: t-bone
'''
import logging, os, sys

# Google App Engine imports.
from google.appengine.ext.webapp import util

# Remove the standard version of Django.
for k in [k for k in sys.modules if k.startswith('django')]:
    del sys.modules[k]

# Force sys.path to have our own directory first, in case we want to import
# from it.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Force Django to reload its settings.
#from django.conf import settings
#settings._target = None

# Must set this env var before importing any part of Django
# 'project' is the name of the project created with django-admin.py
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
import django.core.signals
import django.db
import django.dispatch.dispatcher

def log_exception(*args, **kwds):
    logging.exception('Exception in request:')

# Log errors.
django.dispatch.dispatcher.Signal.connect(
    django.core.signals.got_request_exception, log_exception)

# Unregister the rollback event handler.
django.dispatch.dispatcher.Signal.disconnect(
    django.core.signals.got_request_exception,
    django.db._rollback_on_exception)

def main():
    # Create a Django application for WSGI.
    application = django.core.handlers.wsgi.WSGIHandler()

    # Run the WSGI CGI handler with that application.
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
