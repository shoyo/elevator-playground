import sys
import simpy
from utils import print_status

UP = 1
DOWN = -1
IDLE = 0

PICKING_UP = 2
# consider the case when elevator is picking up, and call is generated on that floor.


class Elevator:
    """
    Each elevator follows the SCAN algorithm.
    1) While there are people in the elevator or people waiting in the
       direction of the elevator, keep heading in that direction and
       pickup/dropoff as necessary.
    2) Once elevator has exhausted all requests in its current direction,
       reverse direction and go to step 1) if there are requests. Else, stop
       and wait for a call (or potentially move to another floor deemed more
       effective)
    """
    def __init__(self, capacity):
        self.env = None
        self.id = None
        self.call_queue = None
        self.call_handler = None

        self.curr_floor = 1
        self.dest_floor = None
        self.movement = IDLE
        self.service_direction = IDLE
        self.action = IDLE

        self.max_capacity = capacity
        self.curr_capacity = 0
        self.pickup_duration = 70
        self.dropoff_duration = 70
        self.f2f_time = 100

    def set_env(self, env):
        if self.env:
            raise Exception("Attempted to set environment for Elevator "
                            "which already had an environment.")
        else:
            self.env = env

    def set_call_queue(self):
        if not self.env:
            raise Exception("Attempted to set call_queue for Elevator "
                            "with no environment.")
        if self.call_queue:
            raise Exception("Attempted to set call_queue for Elevator "
                            "that already had a call_queue.")
        else:
            self.call_queue = simpy.Store(self.env)

    def set_id(self, id):
        if not self.id:
            self.id = id
        else:
            raise Exception("Attempted to set ID for Elevator which "
                            "already had an ID.")

    def set_call_handler(self):
        if not self.env:
            raise Exception("Attempted to assign call_handler to an Elevator "
                            "with no environment.")
        if self.call_handler:
            raise Exception("Attempted to assign call_handler to an Elevator "
                            "that already had an call_handler.")
        else:
            self.call_handler = self.envj.process(self.handle_calls())

    def handle_calls(self):
        while True:
            call = self.call_queue.get()
            if

            pass

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
            raise Exception("Elevator capacity exceeded.")
        self.curr_capacity += 1
        print_status(self.env.now,
                     f"(pick up) Elevator {self.id} at floor {self.curr_floor}, capacity now {self.curr_capacity}")

    def drop_off(self):
        if self.curr_capacity == 0:
            raise Exception("Nobody on elevator to drop off")
        self.curr_capacity -= 1
        print_status(self.env.now,
                     f"(drop off) Elevator {self.id} at floor {self.curr_floor}, capacity now {self.curr_capacity}")
