import simpy
from random import randint
from sim_utils import print_status, rand_call
from abc import ABC, abstractmethod


class Building(ABC):
    def __init__(self, num_floors, elevators):
        """
        :param int num_floors: number of floors
        :param list[Elevator] elevators: all Elevators in this Building
        """
        self.env = None
        self.initial_process = None

        self.num_floors = num_floors
        self.elevators = elevators
        self.num_elevators = len(elevators)

        self.floor_queues = {}
        for i in range(1, num_floors + 1):
            self.floor_queues[i] = 0

        self.call_history = []

    def set_initial_process(self):
        if not self.env:
            raise Exception("Attempted to assign initial process to a Building "
                            "with no environment.")
        if self.initial_process:
            raise Exception("Attempted to assign initial process to a Building "
                            "that already had an initial process.")
        else:
            self.initial_process = self.env.process(self.start())

    def set_env(self, env):
        if self.env:
            raise Exception("Attempted to set environment for Building "
                            "which already had an environment.")
        else:
            self.env = env

    def assign_elevator_ids(self):
        for i in range(self.num_elevators):
            self.elevators[i].set_id(i + 1)

    def update_floor_queues(self):
        pass

    @abstractmethod
    def start(self):
        """ Start generating random elevator calls and dispatching elevators."""
        pass

    @abstractmethod
    def generate_call(self):
        """ Generates a call from an origin floor to a destination floor according to some distribution."""
        pass

    @abstractmethod
    def select_elevator(self, call):
        """ Judiciously selects an elevator to handle a generated call."""
        pass

    @abstractmethod
    def process_call(self, call, elevator):
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
    # def __init__(self, num_floors, elevators):
    #     super().__init__(num_floors, elevators)
    #     self.dispatcher = BasicDispatcher()
    #     self.dispatcher.start()

    def start(self):
        while True:
            # TODO: handle specified distribution instead of simple random
            yield self.env.timeout(randint(30, 30))
            call = self.generate_call()
            elevator = self.select_elevator(call)
            self.process_call(call, elevator)

    def generate_call(self):
        call = rand_call(self.env.now, self.num_floors)
        print_status(self.env.now, f'[Generate] call {call.id}: floor {call.origin} to {call.dest}')
        self.floor_queues[call.origin] += 1
        self.call_history.append(call)
        return call

    def select_elevator(self, call):
        selected = self.elevators[0]

        print_status(self.env.now,
                     f'[Select] call {call.id}: Elevator {selected.id}')
        return selected

    def new_process_call(self, call, elevator):
        elevator.queued_calls.append(call)

    def process_call(self, call, elevator):
        elevator.move_to(call.origin)
        elevator.pick_up()
        call.wait_time = self.env.now - call.orig_time
        print_status(self.env.now, f'call {call.id} waited {call.wait_time / 10} s')
        elevator.move_to(call.dest)
        elevator.drop_off()
        call.done = True
        call.process_time = self.env.now - call.orig_time

        print_status(self.env.now, f'[Done] call {call.id}')
