from random import randint
from sim_utils import print_status, randreq


class Building:
    def __init__(self, floors, elevators):
        self.env = None
        self.action = None
        self.floors = floors
        self.elevators = elevators
        self.num_elevators = len(elevators)
        for i in range(self.num_elevators):
            self.elevators[i].set_id(i)
        self.all_requests = []
 
    def make_reqs(self):
        pass


class BasicBuilding(Building):
    def __init__(self, floors, elevators):
        super().__init__(floors, elevators)

    def set_env(self, env):
        self.env = env
        self.action = env.process(self.make_reqs())

    def make_reqs(self):
        while True:
            yield self.env.timeout(randint(6000, 9000))
            request = randreq(self.env.now, self.floors)    
            print_status(self.env.now,
                    f'[Generate] Req {request.id}: floor {request.origin} to {request.dest}')
            self.all_requests.append(request)
            self.assign_req(request, randint(0, self.num_elevators - 1))

    def assign_req(self, request, elevator_index):
        print_status(self.env.now,
                f'[Assign] Req {request.id}: Elevator {elevator_index}')    
        self.elevators[elevator_index].handle_req(request)

