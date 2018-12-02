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
        self.call_buffer = None
        self.call_generator = None
        self.call_processor = None

        self.num_floors = num_floors
        self.elevators = elevators
        self.num_elevators = len(elevators)

        self.floor_queues = {}
        for i in range(1, num_floors + 1):
            self.floor_queues[i] = 0

        self.call_history = []

    def set_env(self, env):
        if self.env:
            raise Exception("Attempted to set environment for Building "
                            "which already had an environment.")
        else:
            self.env = env

    def set_call_buffer(self):
        if not self.env:
            raise Exception("Attempted to set call_queue for Elevator "
                            "with no environment.")
        if self.call_buffer:
            raise Exception("Attempted to set call_queue for Elevator "
                            "that already had a call_queue.")
        else:
            self.call_buffer = simpy.Store(self.env)


    def set_call_generator(self):
        if not self.env:
            raise Exception("Attempted to assign initial process to a Building " "with no environment.")
        if self.call_generator:
            raise Exception("Attempted to assign call_generator to a Building "
                            "that already had an call_generator.")
        else:
            self.call_generator = self.env.process(self.generate_calls())


    def set_call_processor(self):
        if not self.env:
            raise Exception("Attempted to assign initial process to a Building "
                            "with no environment.")
        if self.call_processor:
            raise Exception("Attempted to assign call_processor to a Building "
                            "that already had an call_processor.")
        else:
            self.call_processor = self.env.process(self.process_calls())


    def assign_elevator_ids(self):
        for i in range(self.num_elevators):
            self.elevators[i].set_id(i)


    def update_floor_queues(self):
        pass


    @abstractmethod
    def generate_calls(self):
        """ Periodically generates a call from an origin floor to a
        destination floor."""


    @abstractmethod
    def generate_single_call(self):
        """ Generates a single call."""
        pass


    @abstractmethod
    def process_calls(self):
        """ Continuously check call buffer for any queued calls and process them."""
        pass


    @abstractmethod
    def process_single_call(self, call, elevator):
        """ Process a single call given an elevator."""
        pass


    @abstractmethod
    def select_elevator(self, call):
        """ Judiciously selects an elevator to handle a generated call."""
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

    # TODO: DEPRECATING
    def run(self):
        while True:
            # TODO: handle specified distribution instead of simple random
            yield self.env.timeout(randint(30, 30))
            call = self.generate_single_call()

            elevator = self.select_elevator(call)
            self.process_call(call, elevator)

    def generate_calls(self):
        while True:
            yield self.env.timeout(randint(30, 30))
            call = self.generate_single_call()
            self.call_buffer.put(call)
            self.call_history.append(call)
            self.floor_queues[call.origin] += 1

    def generate_single_call(self):
        call = rand_call(self.env.now, self.num_floors)
        print_status(self.env.now, f'[Generate] call {call.id}: floor {call.origin} to {call.dest}')
        return call

    def process_calls(self):
        pass

    def process_single_call(self):

    def select_elevator(self, call):
        selected = self.elevators[randint(0, self.num_elevators - 1)]
        print_status(self.env.now,
                     f'[Select] call {call.id}: Elevator {selected.id}')
        return selected

    # TODO: DEPRECATING
    def process_call(self, call, elevator):
        # After call is processed, the following must be updated
        #    wait time, process time, "done"

        elevator.move_to(call.origin)
        elevator.pick_up()
        call.wait_time = self.env.now - call.orig_time
        print_status(self.env.now, f'call {call.id} waited {call.wait_time / 10} s')
        elevator.move_to(call.dest)
        elevator.drop_off()
        call.done = True
        call.process_time = self.env.now - call.orig_time

        print_status(self.env.now, f'[Done] call {call.id}')


class DeepReinforcementLearningBuilding:
    pass
