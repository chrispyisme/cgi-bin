import sys
import os
from unittest import case

from lib.fs.files import FileSystem
from lib.logging.Logger import Logger
from lib.di.Container import Container
from lib.di.Autoloader import Autoloader, AutoloaderException
from lib.di.ServiceManager import ServiceManager
from .config import settings, class_load, file_load
from lib.routing.Router import Router

class App:
   
    def __init__(self):
        self._settings = settings

        self.init_services_manager()
    
        self.load_base_services()

        # load any additional services defined via JSON
        self.router:Router = self.service_manager.make("router")
        self.fileloader = self.service_manager.make("fileloader")
        self.logger = self.service_manager.make("logger")

        
    def load_base_services(self):
        self.service_manager.add_property("settings", self._settings)
        self.service_manager.add_property("service_manager", self.service_manager)
        self.service_manager.add_property("app", self)
        self.service_manager.add(abstract='logger', concrete="lib.logging.Logger.Logger", 
                                 service_type="singleton", 
                                 params={"level":"INFO", "file":"/usr/lib/cgi-bin/app/logs/App.log", "name":"sm", "format":"%(asctime)s [%(levelname)8s] %(name)s:%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"})
        self.service_manager.add(abstract="response", concrete="lib.http.Response.Response", service_type="singleton")
        self.service_manager.add(abstract="Request", concrete="lib.http.Request.Request", service_type="factory")
        self.service_manager.add(abstract="router", concrete="lib.routing.Router.Router", service_type="singleton", params={"request":"Request"})
        self.service_manager.add(abstract="fileloader", concrete="lib.fs.files.FileSystem", service_type="singleton", 
                                 params={
                                     "directories":file_load
                                     })
        self.service_manager.add(abstract="template", concrete="lib.ui.Template.Template", service_type="factory",
                                 params={"base_layout":"base.html", "assets":"/static/assets/enabled"})
       

    def init_services_manager(self):
        
        self.container = Container()
        
        al = Autoloader(class_load)
        
        self.container.set_autoloader(al)
        
        self.service_manager = ServiceManager(self.container)
    
        #print(self.service_manager.list_services())
                
    def get_container(self):
        return self.container
    
    def _POST(self, uri, handler, middleware):
        self.router.add_route(uri=uri, method="POST", handler=handler, middleware=middleware)
        
    def _GET(self, uri, handler, middleware):
        self.router.add_route(uri=uri, method="GET", handler=handler, middleware=middleware)
        return self
    
    def run(self):
        self.router.dispatch(self.container)
        