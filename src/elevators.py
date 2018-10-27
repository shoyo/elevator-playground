import simpy
from sim_utils import print_status


class Elevator:
    def __init__(self):
        self.env = None
        self.id = None
        self.position = 1
        self.dest = None
        self.movement = 0   # 0: stationary, 1: up, -1: down
        self.max_capacity = 0
        self.curr_capacity = 0
        self.pickup_duration = 70
        self.dropoff_duration = 70
       
    def set_env(self, env):
        self.env = env

    def set_id(self, id):
        self.id = id

class BasicElevator(Elevator):
    def __init__(self):
        super().__init__()
        self.max_capacity = 10
        self.f2f_time = 100     # 10 seconds

    def handle_req(self, request):
        print_status(self.env.now, 
                f'[Confirm] Req {request.id}: Elevator {self.id} at floor {self.position}') 
        self.move_to(request.origin)
        self.pick_up()
        request.wait_time = self.env.now - request.time
        print_status(self.env.now, f'Req {request.id} waited {request.wait_time / 10} s')
        self.move_to(request.dest)
        self.drop_off()
        request.done = True
        print_status(self.env.now, f'[Done] Req {request.id}')

    def move_to(self, target_floor):
        if target_floor > self.position:
            self.movement = 1
        elif target_floor < self.position:
            self.movement = -1
        while self.position != target_floor:
            self.env.run(self.env.process(self.move_one_floor()))
            self.position += self.movement
        self.movement = 0

    def move_one_floor(self):
        yield self.env.timeout(self.f2f_time)

    def pick_up(self):
        if self.curr_capacity >= self.max_capacity:
            raise Exception('Elevator capacity exceeded. Dispatcher gotta git gud')
        self.curr_capacity += 1
        print_status(self.env.now,
                f'(pick up) Elevator {self.id} at floor {self.position}, capacity now {self.curr_capacity}')

    def drop_off(self):
        if self.curr_capacity == 0:
            raise Exception('Nobody on elevator to drop off')
        self.curr_capacity -= 1
        print_status(self.env.now,
                f'(drop off) Elevator {self.id} at floor {self.position}, capacity now {self.curr_capacity}')

