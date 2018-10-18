from requests import Request


class Passenger:
    def __init__(self):
        self.request = None 

    def make_request(self, origin, destination, time):
       self.request = Request(origin, destination, time) 
        
        
