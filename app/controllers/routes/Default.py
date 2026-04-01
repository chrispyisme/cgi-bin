import os
import sys
from lib.di.Container import Container
from lib.db.Database import Database
from lib.http.Request import Request

class Default:
    def __init__(self):
        pass
    
    def home(self, c:Container, request:Request, ):
        pass