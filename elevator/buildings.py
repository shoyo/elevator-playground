import simpy
from random import randint
from elevator.elevators import Elevator
from elevator.utils import print_status, rand_call
from abc import ABC, abstractmethod


class Building(ABC):
    """A building containing elevators that handles randomly generated calls.

    (more documentation)
    """
    def __init__(self, env, num_floors, num_elevators):
        """
        Create a building with a
        """
        self.env = env
        self.call_generator = self.env.process(self._generate_calls())
        self.call_assigner = self.env.process(self._assign_calls())
        self.call_queue = simpy.Store(self.env)
        self.call_history = []
        self.num_floors = num_floors
        self.elevators = self._init_elevators(num_elevators)
        self.service_ranges = self._init_service_ranges()

        self.floor_queues = self._init_floor_queues()

    def _init_elevators(self, num_elevators):
        elevators = []
        for i in range(num_elevators):
            elevators.append(Elevator(self, self.env, i))
        return elevators

    def _init_floor_queues(self):
        queues = {}
        for i in range(1, self.num_floors + 1):
            queues[i] = 0
        return queues

    def _init_service_ranges(self):
        ranges = {}
        for i in range(self.num_elevators):
            service_range = (1, self.num_floors + 1)
            ranges[self.elevators[i]] = service_range
            self.elevators[i].set_service_range(service_range)
        return ranges

    def _assign_elevator_ids(self):
        """Give a unique ID number to each elevator."""
        for i in range(self.num_elevators):
            self.elevators[i].set_id(i)

    @abstractmethod
    def _generate_calls(self):
        """Periodically generate a call and place it into the call queue."""
        pass

    @abstractmethod
    def _generate_single_call(self):
        """Generate a random call."""
        pass

    @abstractmethod
    def _assign_calls(self):
        """Periodically check the call queue for any calls and assign them."""
        pass

    @abstractmethod
    def _select_elevator(self, call):
        """Judiciously select an elevator to handle a call."""
        pass


class BasicBuilding(Building):
    """A building that assigns calls randomly."""

    def _generate_calls(self):
        print("Building has started generating calls...")
        while True:
            yield self.env.timeout(randint(30, 30))
            call = self._generate_single_call()
            self.call_queue.put(call)
            self.call_history.append(call)
            self.floor_queues[call.origin] += 1

    def _generate_single_call(self):
        call = rand_call(self.env.now, self.num_floors)
        print_status(self.env.now, f"[Generate] call {call.id}: floor {call.source} to {call.dest}")
        return call

    def _assign_calls(self):
        print("Building has started assigning calls...")
        while True:
            call = yield self.call_queue.get()
            elevator = self._select_elevator(call)
            elevator.enqueue(call)

    def _select_elevator(self, call):
        # I probably want an efficient way of checking global state -- where each
        # elevator is, where they're headed, their capacities etc.
        # Ultimately, this method is the bulk of the thinking
        selected = self.elevators[randint(0, self.num_elevators - 1)]
        print_status(self.env.now,
                     f"[Select] call {call.id}: Elevator {selected.id}")
        return selected


class BasicSectorBuilding:
    pass


class DynamicLoadBalancingBuilding:
    pass


class DeepReinforcementLearningBuilding:
    pass
