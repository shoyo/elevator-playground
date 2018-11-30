import sys
import simpy
from sim_utils import print_status
from collections import deque

UP = 1
DOWN = -1
IDLE = 0


class Elevator:
    def __init__(self, capacity):
        self.env = None
        self.id = None

        self.curr_floor = 1
        self.dest_floor = None
        self.movement = IDLE
        self.service_direction = IDLE

        self.max_capacity = capacity
        self.curr_capacity = 0
        self.pickup_duration = 70
        self.dropoff_duration = 70
        self.f2f_time = 100

        self.queued_calls = deque()

    def move_to(self, target_floor):
        if target_floor > self.curr_floor:
            self.movement = UP
        elif target_floor < self.curr_floor:
            self.movement = DOWN
        while self.curr_floor != target_floor:
            self.env.run(self.env.process(self._move_one_floor()))
            self.curr_floor += self.movement
        self.movement = IDLE

    def _move_one_floor(self):
        try:
            yield self.env.timeout(self.f2f_time)
        except simpy.Interrupt:
            print("Elevator movement was interrupted. Exiting for now...")
            sys.exit()

    def pick_up(self):
        if self.curr_capacity >= self.max_capacity:
            raise Exception('Elevator capacity exceeded.')
        self.curr_capacity += 1
        print_status(self.env.now,
                     f'(pick up) Elevator {self.id} at floor {self.curr_floor}, capacity now {self.curr_capacity}')

    def drop_off(self):
        if self.curr_capacity == 0:
            raise Exception('Nobody on elevator to drop off')
        self.curr_capacity -= 1
        print_status(self.env.now,
                     f'(drop off) Elevator {self.id} at floor {self.curr_floor}, capacity now {self.curr_capacity}')
