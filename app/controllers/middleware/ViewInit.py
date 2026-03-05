import os
import sys

import lxml.html
from typing import Callable
from lib.di.ServiceManager import ServiceManager
from lib.http.Response import Response
from lib.http.Request import Request
from lib.fs.files import FileSystem


class ViewInit:
    def __init__(self, container, request, next):
        pass
        

        
        
    def handle(self, container, request, next):
        # short-circuit static asset requests so they aren't wrapped in the view
        # helper.  the router strips the `/cgi-bin/public` prefix so a request
        # for `/cgi-bin/public/static/...` comes through as `/static/...`.
        # if you don't want any middleware applied to those URIs you can simply
        # forward the call immediately.
        uri = request.get_uri() or ''
        if uri.startswith('/static/'):
            # make sure we return whatever the next middleware/handler returns
            return next()

        # create a view helper and attach it to the container so controllers
        # can grab it later.  **always return the result of `next()`**; the
        # router relies on the value being bubbled back up.
        view = container.make("View", container=container, request=request)
        container.add_property("view", view)
        return next()

        