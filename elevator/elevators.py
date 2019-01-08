from collections import deque

import simpy
from elevator.utils import print_status, UP, DOWN, IDLE


class Elevator:
    """Continuously handles calls assigned to it by its Building.

    An Elevator follows the SCAN algorithm:
    1) While there are people in the elevator or calls waiting in the current
       direction of travel, keep heading in that direction and pick-up/drop-off
       as necessary.
    2) Once the elevator has serviced all calls in its current direction,
       reverse direction and go to step (1) if there are calls. Otherwise, stop
       and wait for a call (or move to another floor deemed more effective)

    An Elevator maintains all un-handled calls in a call queue (an instance
    of the CallQueue class, defined further below). The Elevator continuously
    handles calls while there are calls in the call queue.

    Whenever a call is assigned to an Elevator by a Building, the call is
    placed in the call pipe (a simple deque) to await further processing.
    """

    def __init__(self, building, env, id, capacity=simpy.core.Infinity):
        """
        Arguments:
        building -- Building instance that contains this elevator
        env      -- simpy.Environment instance that runs the simulation
        id       -- unique ID (given by building) to identify each elevator
        capacity -- total number of passengers that elevator can hold

        Attributes:
        call handler      -- simpy process for serving calls
        call awaiter      -- simpy process for awaiting calls to be placed in
                             call pipe
        call queue        -- structure for maintaining unhandled calls
        call pipe         -- queue that holds assigned calls
        curr floor        -- current floor
        dest floor        -- destination floor
        service direction -- current direction of service (1 denotes UP,
                             -1 denotes DOWN, 0 denotes IDLE)
        curr capacity     -- current capacity
        service range     -- range of floors that the elevator is expected to
                             serve
        upper bound       -- upper bound of service range
        lower bound       -- lower bound of service range
        max capacity      -- maximum capacity
        pickup duration   -- time* it takes to pick up 1 passenger
        dropoff duration  -- time* it takes to drop off 1 passenger
        f2f time          -- time* it takes to travel between adjacent floors
        directional pref  -- default direction of travel when IDLE and calls
                             exist above and below

        (*Unit is 0.1 seconds. Example: 75 -> 7.5 in-simulation seconds)

        """
        self.env = env
        self.id = id

        # Call-processing utilities
        self.call_handler = self.env.process(self._handle_calls())
        self.call_awaiter = self.env.process(self._await_calls())
        self.call_queue = CallManager(building.num_floors)
        self.call_pipe = simpy.Store()

        # Parameters that can change constantly
        self.curr_floor = 1
        self.dest_floor = None
        self.service_direction = IDLE
        self.curr_capacity = 0
        self.service_range = None
        self.upper_bound = None
        self.lower_bound = None

        # Parameters that don't change
        self.max_capacity = capacity
        self.pickup_duration = 30
        self.dropoff_duration = 30
        self.f2f_time = 100
        self.directional_pref = UP # preferred direction of travel when IDLE and requests exist above and below

    def _handle_calls(self):
        """Continuously handle calls while there are calls to be handled."""
        while True:
            print(f"Elevator {self.id} is handling calls...")
            yield self.env.timeout(0)
            while self.active_map and not self.active_map.is_empty():
                # if (self.curr_floor == self.upper_bound
                #         or self.curr_floor == self.lower_bound):
                #     raise Exception(f"Elevator {self.id} had unhandled "
                #                     f"calls despite reaching its boundary."
                #                     f" This may have been caused due to "
                #                     f"limited capacity of Elevator.")
                # TODO: Handle limited capacity instead of raising exception
                next_stop = self.active_map.next_stop(self.curr_floor,
                                                      self.service_direction,
                                                      self.directional_pref)
                self._move_to(next_stop)
                self._drop_off()
                self._pick_up()
            if not self.defer_map.is_empty():
                self.active_map = self.defer_map
                self._switch_direction()

    def enqueue(self, call):
        """Enqueue the given call in the Elevator's call pipe.

        Main public interface for receiving calls.
        Whenever this method is invoked (should be by Building), the given
        call is placed into the call pipe to await further processing.
        """
        self.call_queue.put(call)

    def _await_calls(self):
        """Awaits for calls to be assigned.

        Periodically checks the call pipe for any assigned calls, and
        recalibrates the call queue when a call is found.
        """
        while True:
            print(f"Elevator {self.id} is awaiting calls...")
            call = yield self.call_pipe.get()
            print(f"Elevator {self.id} was assigned a call!")
            self._recalibrate(call)

    def _recalibrate(self, call):
        """Recalibrates the call queue by adding the given call accordingly."""
        print(f"Elevator {self.id} is recalibrating...")
        if self.service_direction == IDLE:
            if call.direction == self.directional_pref:
                self.active_map.set_pickup(call)
            else:
                self.defer_map.set_pickup(call)
        else:
            if self.service_direction == call.direction:
                if (self.service_direction == UP and call.origin > self.curr_floor
                        or self.service_direction == DOWN and call.origin < self.curr_floor):
                    self.active_map.set_pickup(call)
            else:
                self.defer_map.set_pickup(call)

    def _start_moving(self, direction):
        self.service_direction = direction
        print_status(self.env.now, f"Elevator {self.id} has starting moving"
                                   f"for call {invoking_call.id}")

    def _go_idle(self):
        if self.service_direction != IDLE:
            self.service_direction = IDLE
            print_status(self.env.now, f"Elevator {self.id} is going idle at floor"
                                       f" {self.curr_floor}")

    def _move_to(self, target_floor):
        direction = target_floor - self.curr_floor
        if self.service_direction == IDLE:
            self._start_moving(direction)
        elif direction != self.service_direction:
            raise Exception("Attempted to move Elevator to a floor not in its"
                            "service direction.")
        while self.curr_floor != target_floor:
            self.env.run(self.env.process(self._move_one_floor()))
            self.curr_floor += self.service_direction

    def _move_one_floor(self):
        yield self.env.timeout(self.f2f_time)

    def _pickup_single_passenger(self):
        yield self.env.timeout(self.pickup_duration)

    def _dropoff_single_passenger(self):
        yield self.env.timeout(self.dropoff_duration)

    def _switch_direction(self):
        if self.service_direction == IDLE:
            raise Exception("Attempted to switch direction when Elevator was "
                            "idle.")
        if self.service_direction == UP:
            self.service_direction = DOWN
        elif self.service_direction == DOWN:
            self.service_direction = UP
        print_status(self.env.now, f"Elevator {self.id} switched directions.")

    def _pick_up(self):
        """Pick up as many passengers as possible on the current floor.

        Pick up as many passengers as the Elevator's capacity allows. If the
        Elevator reaches maximum capacity, passengers are left on the current
        floor to be handled at a later time.
        """
        if self.curr_capacity >= self.max_capacity:
            raise Exception("Elevator capacity exceeded.")

        while self.active_map.get_pickups(self.curr_floor):
            if self.curr_capacity == self.max_capacity:
                print_status(self.env.now, f"Elevator {self.id} is full. "
                                           f"Skipping call at floor "
                                           f"{self.curr_floor} ")
            call = self.active_map.pop_next_pickup(self.curr_floor)
            if call.origin != self.curr_floor:
                raise Exception(f"Attempted to pick up Call {call.id} at"
                                f"wrong source.")
            call.picked_up(self.env.now)
            self.curr_capacity += 1
            self.active_map.enqueue_dropoff(call)
            self.env.run(self.env.process(self._pickup_single_passenger()))
        print_status(self.env.now,
                     f"(pick up) Elevator {self.id} at floor {self.curr_floor}"
                     f", capacity now {self.curr_capacity}")

    def _drop_off(self):
        """Drops off all passengers waiting to get off at current floor."""
        if self.curr_capacity == 0:
            raise Exception("Nobody on elevator to drop off")

        while self.active_map.get_dropoffs(self.curr_floor):
            call = self.active_map.pop_next_dropoff(self.curr_floor)
            if call.dest != self.curr_floor:
                raise Exception(f"Attempted to drop off Call {call.id} at"
                                f"wrong destination.")
            call.completed(self.env.now)
            self.curr_capacity -= 1
            self.env.run(self.env.process(self._dropoff_single_passenger()))
        print_status(self.env.now,
                     f"(drop off) Elevator {self.id} at floor "
                     f"{self.curr_floor}, capacity now {self.curr_capacity}")


class CallManager:
    """Maintain unhandled calls of an elevator.

    Calls are organized as a tree shown below:

                        ALL CALLS
                        /      \
                  PICKUPS      DROP-OFFS
                 /       \
               UP         DOWN
             /   \       /    \
     REACHABLE    \  REACHABLE \
             UNREACHABLE    UNREACHABLE

    where:
    ALL CALLS   -- all calls assigned to the elevator
    PICKUPS     -- pickup requests to be handled by the elevator
    DROP-OFFS   -- drop-off requests to be handled by the elevator
    UP          -- upward-headed calls
    DOWN        -- downward-headed calls
    REACHABLE   -- calls that can be accessed without breaking SCAN*
    UNREACHABLE -- calls that cannot be accessed without breaking SCAN*

    Leaf nodes of the tree (DROP-OFFS, REACHABLE, UNREACHABLE) are implemented
    as dictionaries mapping floor number to a queue of Call instances.

    (* SCAN denotes the SCAN algorithm as explained in Elevator class
    documentation.)
    """
    def __init__(self, num_floors):
        """Create an empty CallManager.

        num_floors -- number of floors in building
        """
        self.all_calls = {
            "pickups": {
                "up": {
                    "reachable": {},
                    "unreachable": {},
                },
                "down": {
                    "reachable": {},
                    "unreachable": {},
                },
            },
            "dropoffs": {},
        }
        for i in range(1, num_floors + 1):
            self.all_calls["pickups"]["up"]["reachable"][i] = deque()
            self.all_calls["pickups"]["up"]["unreachable"][i] = deque()
            self.all_calls["pickups"]["down"]["reachable"][i] = deque()
            self.all_calls["pickups"]["down"]["unreachable"][i] = deque()
            self.all_calls["dropoffs"][i] = deque()






