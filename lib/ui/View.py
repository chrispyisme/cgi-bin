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
        self.sm = container.get_property("service_manager")
        self.prm = params
        self.initialize_view()
        
    def initialize_view(self):
        setttings = self.c.get_property("settings")
        sm = self.c.get_property("service_manager")
        template = sm.make("template")
        #self.init_template()
        self.res.set_header("X-view-init", "True")
        self.res.set_body(template.content)
      
      
    #we will need to open up the base document and read it into th tempate
    #from there we will need to get the assets appended
    #the logger is saying that im reaching?????rhe portion of code relevent  
    def init_template(self):
        self.fl = self.sm.make("fileloader")
        #get the base ytemplate
        
        #actually i think that i cn use kust one metgod cal to