from lib.http.Response import Response
from http.server import HTTPServer, BaseHTTPRequestHandler

class Services:
    def __init__(self, container, request, **params):
        pass
        
    def index(self, container, request, **params):
        sm = container.get_property("service_manager")
        view = sm.get_property("view")
    
        #here is will i will grab the unique view for this route
        #and then i will insert that as the param for a method called insert_view within the view class
        #also considering making all of these methods static mehtod
        #for a more flexible way to get the view init and then its not so tightly coupled to the rest of the class
        response = container.make("response")
        response.set_body(f"<h1>{response.get_body()}{request.get_params()}</h1>")
        response.send()