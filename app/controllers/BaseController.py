from abc import ABC, abstractmethod
class BaseController(ABC):
    
    @abstractmethod
    def __init__(self):
        pass
    @abstractmethod
    def index(self, container, request, params=None)->None:
        pass