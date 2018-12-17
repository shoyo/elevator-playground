import simpy
from random import randint
from utils import print_status, rand_call
from abc import ABC, abstractmethod


class Building(ABC):
    """
    Building class. Responsible for generating random elevator calls and
    assigning them to appropriate Elevator given its strategy.

    Contains a call-generating process and a call-handling process, both of
    which asynchronously put/get calls respectively to the call queue.
    """
    def __init__(self, num_floors, elevators):
        """
        :param int num_floors: number of floors
        :param list[Elevator] elevators: all Elevators in this Building
        """
        self.env = None
        self.call_generator = None
        self.call_handler = None
        self.call_queue = None
        self.call_history = []

        if num_floors < 1:
            raise Exception("Building was initialized with less than 1 floor.")
        self.num_floors = num_floors
        self.elevators = elevators
        self.num_elevators = len(elevators)

        self.floor_queues = {}
        for i in range(1, num_floors + 1):
            self.floor_queues[i] = 0

        self.service_ranges = {}
        for i in range(len(elevators)):
            service_range = (1, self.num_floors)
            self.service_ranges[elevators[i]] = service_range
            self.elevators[i].set_service_range(service_range)

    def set_env(self, env):
        if self.env:
            raise Exception("Attempted to set environment for Building "
                            "which already had an environment.")
        else:
            self.env = env

    def init_call_queue(self):
        if not self.env:
            raise Exception("Attempted to initialize call queue for Elevator "
                            "with no environment.")
        if self.call_queue:
            raise Exception("Attempted to initialize call queue for Elevator "
                            "that already had a call queue.")
        else:
            self.call_queue = simpy.Store(self.env)

    def init_call_generator(self):
        if not self.env:
            raise Exception("Attempted to initialize call generator to a "
                            "Building with no environment.")
        if self.call_generator:
            raise Exception("Attempted to initialize call generator to a "
                            "Building that already had a call generator.")
        else:
            self.call_generator = self.env.process(self._generate_calls())

    def init_call_handler(self):
        if not self.env:
            raise Exception("Attempted to initialize call handler to a "
                            "Building with no environment.")
        if self.call_handler:
            raise Exception("Attempted to initialize call handler to a "
                            "Building that already had an call handler.")
        else:
            self.call_handler = self.env.process(self._handle_calls())

    def assign_elevator_ids(self):
        for i in range(self.num_elevators):
            self.elevators[i].set_id(i)

    @abstractmethod
    def _generate_calls(self):
        """ Periodically generates a random call from an origin floor to a
        destination floor and places call into the call queue. """

    @abstractmethod
    def _generate_single_call(self):
        """ Generates a single call. """
        pass

    @abstractmethod
    def _handle_calls(self):
        """ Periodically check the call queue for any queued calls and process them. """
        pass

    @abstractmethod
    def _delegate_call(self, call, elevator):
        """ Process a single call given an elevator. """
        pass

    @abstractmethod
    def _select_elevator(self, call):
        """ Judiciously selects an elevator to handle a generated call. """
        pass


class BasicBuilding(Building):
    """ A building with a basic dispatcher. """

    def _generate_calls(self):
        while True:
            yield self.env.timeout(randint(30, 30))
            call = self._generate_single_call()
            self.call_queue.put(call)
            self.call_history.append(call)
            self.floor_queues[call.origin] += 1

    def _generate_single_call(self):
        call = rand_call(self.env.now, self.num_floors)
        print_status(self.env.now, f"[Generate] call {call.id}: floor {call.origin} to {call.dest}")
        return call

    def _handle_calls(self):
        while True:
            call = yield self.call_queue.get()
            elevator = self._select_elevator(call)
            self._delegate_call(call, elevator)

    def _delegate_call(self, call, elevator):
        elevator.handle_call(call)

    def _select_elevator(self, call):
        # I probably want an efficient way of checking global state -- where each
        # elevator is, where they're headed, their capacities etc.
        # Ultimately, this method is the bulk of the thinking
        selected = self.elevators[randint(0, self.num_elevators - 1)]
        print_status(self.env.now,
                     f"[Select] call {call.id}: Elevator {selected.id}")
        return selected

    # TODO: DEPRECATING
    def _process_call(self, call, elevator):
        elevator.move_to(call.origin)
        elevator.pick_up()
        call.wait_time = self.env.now - call.orig_time
        print_status(self.env.now, f"call {call.id} waited {call.wait_time / 10} s")
        elevator.move_to(call.dest)
        elevator.drop_off()
        call.done = True
        call.process_time = self.env.now - call.orig_time

        print_status(self.env.now, f"[Done] call {call.id}")


class BasicSectorBuilding:
    pass


class DynamicLoadBalancingBuilding:
    pass


class DeepReinforcementLearningBuilding:
    pass
