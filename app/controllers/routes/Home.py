from lib.http.Response import Response

class Home:
    def __init__(self, container, request, **params):
        pass
        
    def index(self, container, request, **paramms):
        try:
            sm = container.get_property("service_manager")
            view = sm.get_property("view")
         

            view.template.insert("home.html")
            view.template.render()
            view.res.set_body(view.template.content)
            view.res.send()
        except Exception as e:
            print(f"Error in Home@index: {e}")