from lib.di.ServiceManager import ServiceManager
from typing import List, Dict
import lxml.html
import os
import sys
import re
import json
from jinja2 import Template as jTemplate
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
        self.fl = sm.make("fileloader")
        
        # Determine the assets directory
        asset_dir = assets
        if asset_dir:
            if not os.path.isabs(asset_dir):
                docroot = settings.get("document_root", "")
                asset_dir = os.path.join(docroot, asset_dir.lstrip("/"))
        else:
            asset_dir = "/var/www/html/static/assets/enabled"
            
        self._log.info(f"The asset dir is: {asset_dir}")
        
        # Map the assets directory
        self.fl.map_directory("assets", asset_dir)
        
        # 1. Expand the extensions list to grab fonts and images
        target_extensions = [
            "css", "js", "mjs", 
            "jpg", "jpeg", "png", "gif", "svg", "webp", 
            "woff", "woff2", "ttf", "otf"
        ]
        assets_list: List = self.fl.find_files_by_extension(target_extensions)
        
        self.base_doc = lxml.html.fromstring(self.fl.read_file(base_layout))
        
        head = self.base_doc.xpath("//head")[0]
        body = self.base_doc.xpath("//body")[0]

        # Array to collect image/svg paths for the JSON preloader payload
        preload_images = []

        # 2. Categorize and inject
        for asset in assets_list:
            asset_sys_path = str(asset.resolve())
            web_path = asset_sys_path.replace("/var/www/html", "")
            ext = os.path.splitext(web_path)[1].lower()

            if ext == ".css":
                link = lxml.html.Element("link")
                link.set("rel", "stylesheet")
                link.set("type", "text/css")
                link.set("href", web_path)
                head.append(link)

            elif ext in [".js", ".mjs"]:
                script = lxml.html.Element("script")
                script.set("src", web_path)
                body.append(script)

            elif ext in [".woff", ".woff2", ".ttf", ".otf"]:
                # Web fonts require a specific preload directive to prevent FOIT (Flash of Invisible Text)
                link = lxml.html.Element("link")
                link.set("rel", "preload")
                link.set("as", "font")
                link.set("href", web_path)
                link.set("crossorigin", "anonymous")
                head.append(link)
                
            elif ext in [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]:
                # Collect images for the async JS preloader
                preload_images.append(web_path)

        # 3. Generate and append the Async Preloader Script
        if preload_images:
            # We dump the array to JSON so JS can parse it natively
            image_json = json.dumps(preload_images)
            
            preloader_code = f"""
            (async function initPreloader() {{
                const imageUrls = {image_json};
                
                const preloadImage = (url) => new Promise((resolve, reject) => {{
                    const img = new Image();
                    img.onload = () => resolve(url);
                    img.onerror = () => reject(new Error('Failed to load: ' + url));
                    img.src = url;
                }});

                try {{
                    await Promise.all(imageUrls.map(preloadImage));
                    console.log('[UI Preloader] All images and SVGs successfully cached.');
                    document.dispatchEvent(new CustomEvent('AssetsPreloaded', {{ 
                        detail: {{ count: imageUrls.length }} 
                    }}));
                }} catch (error) {{
                    console.error('[UI Preloader Error]', error);
                }}
            }})();
            """
            
            inline_script = lxml.html.Element("script")
            # Using .text ensures lxml handles the script content properly without escaping issues
            inline_script.text = preloader_code
            body.append(inline_script)
                
        self.content = lxml.html.tostring(self.base_doc).decode("utf-8")
        
    def add_var(self, key, value):
        self.vars[key] = value
        
    def insert_view(self, view):
        #get the content node via xpath using data-template="view"
        target = self.base_doc.xpath("//div[@data-template='view']")[0]
       
        #v = self.fl.read_file(f"/usr/lib/cgi-bin/app/views/routes/{view}")
        view = self.fl.read_file(view)
        fragment = lxml.html.fromstring(view)
        #self._log.info(fragment)
        target.append(fragment)
        self.render()
        
        
    def is_html(self, value):   
    
        # Simple check if the value is an lxml Element or a string containing tags
        if isinstance(value, lxml.html.HtmlElement):
            return True
        if isinstance(value, str) and re.search(r"<[a-z][\s\S]*>", value, re.IGNORECASE):
            return True
        return False
        """
        def render(self):
    rendered = self.content
    pattern = r"\{\{(\w+)\}\}"  # Matches {{variable_name}}

    # Search for all matches in the content
    while True:
        match = re.search(pattern, rendered)  # Find the first {{variable_name}}
        if not match:
            break  # Exit the loop if no more matches are found

        var_name = match.group(1)  # Extract the variable name inside {{ }}
        value = self.vars.get(var_name, "")  # Get the value from vars, default to empty string

        if self.is_html(value):  # Check if the value is HTML
            value = lxml.html.tostring(value).decode("utf-8")

        # Replace the first occurrence of {{var_name}} with the value
        rendered = rendered[:match.start()] + str(value) + rendered[match.end():]

    self.content = rendered
        """
    def render(self):
        content = lxml.html.tostring(self.base_doc).decode("utf-8")
        temp = jTemplate(content)
        self.content = temp.render(self.vars)
       