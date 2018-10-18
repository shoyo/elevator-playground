import simpy
from sim_utils import print_status


class Elevator:
    def __init__(self):
        self.env = None
        self.position = 1
        self.max_capacity = 0
        self.curr_capacity = 0
        self.pickup_duration = 70
        self.dropoff_duration = 70


class BasicElevator(Elevator):
    def __init__(self):
        super().__init__()
        self.max_capacity = 10
       
    def set_env(self, env):
        self.env = env

    def handle_req(self, request):
        print_status(self.env.now, f'Request {request.id} confirmed') 
