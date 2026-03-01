from lib.http.Response import Response

class Services:
    def __init__(self, container, request, **params):
        pass
        
    def index(self, container, request, **params):
        response = container.make("response")
        response.set_body(f"<h1>{response.get_body()}{request.get_params()}</h1>")
        response.send()