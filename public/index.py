#!/usr/bin/python3

import os
import sys
import re




sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.di.Autoloader import Autoloader, AutoloaderException
from lib.di.Container import Container
from lib.http.Request import Request
from lib.http.Response import Response
from app.App import App

def authenticate_user(c, request, next):
    """simple middleware example that checks for an authenticated user.

    - `c` is the DI container, `request` is the Request instance.
    - if the check fails we redirect to '/register' (or '/login'), otherwise we
      continue the chain by calling and returning ``next()``.

    If you don't want the middleware to execute for static asset requests you
    can either register it only on routes that need it, or inspect the URI
    here and call ``next()`` immediately.
    """

    uri = request.get_uri() or ''
    if uri.startswith('/static/'):
        # ignore assets - just call the callback
        return next()

    # this assumes you have an Auth service bound in the container; adjust as
    # needed for your application.
    try:
        auth = c.make('Auth')
        if not auth.is_authenticated():
            resp = c.make('response')
            resp.redirect('/register')
            return resp
    except Exception:
        # if the auth service is missing just continue
        pass

    # continue to the next middleware or handler; return its result
    return next()



app = App()
res = Response()
app.router.register_middleware("ViewInit", "ViewInit")
app.router.register_middleware("Authenticate", authenticate_user)
app._GET(uri="/", handler="Home@index", middleware=['ViewInit'])
app._GET(uri="/register", handler="Register@auth", middleware=['ViewInit', 'Authenticate'])
app._GET(uri="/services", handler="Services@index", middleware=["ViewInit"])
app.run()
