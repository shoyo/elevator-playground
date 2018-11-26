from random import randint
from sim_utils import print_status, rand_call
from collections import deque


class Building:
    def __init__(self, floors, elevators):
        self.env = None
        self.start = None
        self.floors = floors
        self.elevators = elevators
        self.num_elevators = len(elevators)
        for i in range(self.num_elevators):
            self.elevators[i].id = i
        self.all_calls = deque()

    def start_calls(self):
        """ Start generating random elevator calls."""
        pass

    def generate_call(self):
        """ Randomly generates an elevator call according to some distribution."""
        pass

    def select_elevator(self, call):
        """ Judiciously selects an elevator to handle a generated call."""
        pass

    def process_call(self, call):
        """ Tell selected elevator how to process the call."""
        pass


class BasicBuilding(Building):
    """
    A building with a basic dispatcher.

    Dispatches elevator calls according to basic elevator algorithm (SCAN):
         1) While there are people in the elevator or people waiting in the
             direction of the elevator, keep heading in that direction and
             pickup/dropoff as necessary.
         2) Once elevator has exhausted all requests in its current direction,
             reverse direction and go to step 1) if there are requests. Else, stop
             and wait for a call (or potentially move to another floor deemed more
             effective)
    """

    def __init__(self, floors, elevators):
        super().__init__(floors, elevators)

    def set_env(self, env):
        self.env = env
        self.start = env.process(self.generate_calls())

    def generate_calls(self):
        while True:
            yield self.env.timeout(randint(30, 30))
            call = rand_call(self.env.now, self.floors)
            print_status(self.env.now,
                         f'[Generate] call {call.id}: floor {call.origin} to {call.dest}')
            self.handle_call(call)

            self.all_calls.append(call)

            # while True:
            # if there exists a valid elevator:

            self.assign_call(call, randint(0, self.num_elevators - 1))

    # Copied over from elevators.py
    def handle_call(self, call):
        print_status(self.env.now,
                     f'[Confirm] call {call.id}: Elevator {self.id} at floor {self.position}')
        self.move_to(call.origin)
        self.pick_up()
        call.wait_time = self.env.now - call.orig_time

        print_status(self.env.now, f'call {call.id} waited {call.wait_time / 10} s')
        self.move_to(call.dest)
        self.drop_off()
        call.done = True
        call.process_time = self.env.now - call.orig_time
        print_status(self.env.now, f'[Done] call {call.id}')

    # REFACTOR
    def dispatch_calls(self):
        with self.elevators[elevator_index].request() as request:
            pass

    def assign_call(self, call, elevator_index):
        print_status(self.env.now,
                     f'[Assign] call {call.id}: Elevator {elevator_index}')
        self.elevators[elevator_index].handle_call(call)
