import sys
import simpy
from sim_utils import print_status


class Elevator:
    def __init__(self, capacity):
        self.env = None
        self.cart = None
        self.id = None
        self.position = 1
        self.dest = None
        self.movement = 0  # 0: stationary, 1: up, -1: down
        self.direction = 0  # 0: idle, 1: servicing up, 2: servicing down
        self.max_capacity = capacity
        self.curr_capacity = 0
        self.pickup_duration = 70
        self.dropoff_duration = 70
        self.max_capacity = capacity
        self.f2f_time = 100  # 10 seconds

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
        try:
            yield self.env.timeout(self.f2f_time)
        except simpy.Interrupt:
            print("Elevator movement was interrupted. Exiting for now...")
            sys.exit()

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
