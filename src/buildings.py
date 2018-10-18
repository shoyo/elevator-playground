from random import randint
from sim_utils import print_status, randreq


class Building:
    def __init__(self, floors, elevators):
        self.env = None
        self.action = None
        self.floors = 0
        self.elevators = None
        self.num_elevators = None

    def make_reqs(self):
        pass


class BasicBuilding(Building):
    def __init__(self, floors, elevators):
        super().__init__(floors, elevators)
        self.floors = floors
        self.elevators = elevators
        self.num_elevators = len(self.elevators)

    def set_env(self, env):
        self.env = env
        self.action = env.process(self.make_reqs())

    def make_reqs(self):
        while True:
            yield self.env.timeout(randint(100, 500))
            request = randreq(self.env.now, self.floors)    
            print_status(self.env.now,
                    f'Generated request {request.id} from floor {request.origin} to {request.dest}')
            self.assign_req(request, randint(0, self.num_elevators - 1))

    def assign_req(self, request, elevator_index):
        print_status(self.env.now,
                f'Assigning request {request.id} to Elevator {elevator_index}')    
        self.elevators[elevator_index].handle_req(request)
