"""
The View class represents the response. 
It will be the only class that will be tied to this response object
In the future all of the error handling will need to be routed through this class
first the response object instance is captured

"""
class View:
    def __init__(self, container, request, **params):
        self.app = container.get_property("app")
        self._settings = container.get_property("settings")
        self.c = container
        self.req = request
        self.res = self.c.make("response")
        self.prm = params
        self.initialize_view()
        
    def initialize_view(self):
        setttings = self.c.get_property("settings")
        sm = self.c.get_property("service_manager")
        template = sm.make("template")
        #self.init_template()
        self.res.set_header("X-view-init", "True")
        self.res.set_body("&nbsp;")