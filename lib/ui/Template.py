from lib.di.ServiceManager import ServiceManager
from typing import List, Dict
import lxml.html
import os
import sys


class Template:
    def __init__(self, c, base_layout, assets):
            self.base_layout = base_layout
            self.assets = assets
            self.vars = {}
            self.routines = {}
            self.container = c
            self._log = c.make("logger")
            
            sm: ServiceManager = self.container.get_property("service_manager")
            settings = sm.get_property("settings")
            fl = sm.make("fileloader")
            
            # Determine the assets directory
            asset_dir = assets
            if asset_dir:
                if not os.path.isabs(asset_dir):
                    docroot = settings.get("document_root", "")
                    asset_dir = os.path.join(docroot, asset_dir.lstrip("/"))
            else:
                # ONLY use the fallback if 'assets' wasn't provided
                asset_dir = "/usr/lib/cgi-bin/static/assets/enabled"
                
            self._log.info(f"The asset dir is: {asset_dir}")
            
            # Map the assets directory
            fl.map_directory("assets", asset_dir)
            assets_list: List = fl.find_files_by_extension(["css", "js"])
            
            
            self.base_doc = lxml.html.fromstring(fl.read_file(base_layout))
            
           
            head = self.base_doc.xpath("//head")[0]
            body = self.base_doc.xpath("//body")[0]

            for asset in assets_list:

                asset_sys_path = str(asset.resolve())
                web_path = asset_sys_path.replace("/usr/lib", "")

                if asset_sys_path.endswith(".css"):

                    link = lxml.html.Element("link")
                    link.set("rel", "stylesheet")
                    link.set("type", "text/css")
                    link.set("href", web_path)

                    head.append(link)

                elif asset_sys_path.endswith(".js"):

                    script = lxml.html.Element("script")
                    script.set("src", web_path)

                    body.append(script)

            self.content = lxml.html.tostring(self.base_doc).decode("utf-8")
            #dstop = True