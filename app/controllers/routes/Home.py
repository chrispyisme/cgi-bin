from lib.http.Response import Response

class Home:
    def __init__(self, container, request, **params):
        pass
        
    def index(self, container, request, **params):
        try:
            sm = container.get_property("service_manager")
            view = sm.get_property("view")
            body = view.res.get_body()
            view.res.set_body(f"{body}<div>welcome to home page</div>")
            view.res.send()
        except Exception as e:
            print(f"Error in Home@index: {e}")