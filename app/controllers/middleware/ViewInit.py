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
        self.next = next
        view = container.make("View", container=container, request=request)
        container.add_property("view", view)
        self.next()

        