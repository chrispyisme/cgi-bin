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

app = App()
res = Response()
app.router.register_middleware("ViewInit", "ViewInit")

app._GET(uri="/", handler="Home@index", middleware=['ViewInit'])
app.run()
