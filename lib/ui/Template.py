from lib.di.Container import Container
from typing import List
import os
from typing import Dict, List, Union, Optional, Callable
import lxml.etree
import lxml.html
from pathlib import Path
from pathlib import PosixPath

class Template:
    """Template middleware - adds custom header"""
    
    def add_var(self, name, value):
        self.vars.update({name:value})
        
    def add_routine(self, ns, routine, params):
        self.routines.update({ns:{"routine":routine, "params":params}})
    def add_function(self, namespace, callable_function):
          self.routines[namespace] = callable_function
    def __init__(self, c, base_layout, assets):
        self.base_layout = base_layout
        self.assets = assets
        self.vars = {}
        self.routines = {}
        self.container = c
        self._log = c.make("logger")
        
        sm = self.container.get_property("service_manager")
        settings = sm.get_property("settings")
        fl = sm.make("fileloader")
        # determine the assets directory (allow relative paths)
        asset_dir = assets
        if asset_dir:
            # if not absolute, prefix with configured document_root
            if not os.path.isabs(asset_dir):
                docroot = settings.get("document_root", "")
                asset_dir = os.path.join(docroot, asset_dir.lstrip("/"))
        # default fallback
        asset_dir =  "/usr/lib/cgi-bin/static/assets/enabled"
        self._log.info(f"the asset dir is the {asset_dir}")
        # map the assets directory
        document_root = settings.get("document_root", "/usr/lib/cgi-bin")
        
        fl.map_directory("assets", asset_dir)
        #print(fl._mapped_directories)
        # find css/js files inside the mapped assets directory
        assets_list:List = fl.find_files_by_extension(["css", "js"])
        self._log.info(f"the assets list is {assets_list}")
        self.base_doc = lxml.html.fromstring(fl.read_file(base_layout))
        for asset in assets_list:
            asset_path = asset.resolve()
            #print(type(asset_path))
            if isinstance(asset_path, str):
                domObject = None
                if(asset.resolve().endswith(".css")):
                    domObject = lxml.html.fromstring(f"<link href='/cgi-bin{asset.resolve()}' rel='stylesheet' type='text/css' />")
                else:
                    domObject = lxml.html.fromstring(f"<script src='{asset.resolve()}'></script>")
            #print(type(domObject))
            self.base_doc.get_element_by_id("assets").append(domObject)
        self.content = lxml.html.tostring(self.base_doc).decode("utf-8")
        
