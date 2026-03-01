from lib.di.Container import Container
from typing import List
import os
import lxml.etree
import lxml.html

class Template:
    """Template middleware - adds custom header"""
    
    def add_var(self, name, value):
        self.vars.update({name:value})
        
    def add_routine(self, ns, routine, params):
        self.routines.update({ns:{"routine":routine, "params":params}})
          
    def __init__(self, c, base_layout, assets):
        self.base_layout = base_layout
        self.assets = assets
        self.vars = {}
        self.routines = {}
        self.container = c
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
        asset_dir = asset_dir or "/usr/lib/cgi-bin/static/assets/enabled"

        # map the assets directory
        try:
            fl.map_directory("assets", asset_dir)
        except Exception:
            # fall back to known location if mapping fails
            fl.map_directory("assets", "/usr/lib/cgi-bin/static/assets/enabled")

        # find css/js files inside the mapped assets directory
        assets_list = fl.find_files_by_extension([".css", ".js"], "assets")
        self.base_doc = lxml.html.fromstring(fl.read_file(base_layout))
        self.content = lxml.html.tostring(self.base_doc).decode("utf-8")
        

