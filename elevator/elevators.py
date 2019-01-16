from collections import deque

import simpy
from elevator.utils import print_status, UP, DOWN, IDLE, merge


# -- Custom Errors --
class ServiceRangeError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidCallError(Exception):
    def __init__(self, message):
        super().__init__(message)


# ----


class Elevator:
    """Continuously handle calls assigned to it by its Building.

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
        upper bound       -- highest floor that is accessible (set by building
                             during runtime)
        lower bound       -- lowest floor that is accessible (set by building
                             during runtime)
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

        # Attributes that can change constantly
        self.curr_floor = 1
        self.service_direction = IDLE
        self.curr_capacity = 0
        self.upper_bound = None
        self.lower_bound = None

        # Attributes that don't change
        self.max_capacity = capacity
        self.pickup_duration = 30
        self.dropoff_duration = 30
        self.f2f_time = 100
        self.directional_pref = UP

    def set_service_range(self, lower, upper):
        """Set upper and lower bound of travel."""
        if lower > upper:
            raise ServiceRangeError("Lower bound greater than upper bound.")
        self.upper_bound = upper
        self.lower_bound = lower

    def _handle_calls(self):
        """Continuously handle calls while there are calls to be handled."""
        while True:
            print(f"Elevator {self.id} is handling calls...")
            yield self.env.timeout(0)
            while (self.call_queue.get_reachable_pickups(self.service_direction)
                   or self.call_queue.get_dropoffs()):


    def enqueue(self, call):
        """Enqueue the given call in the call pipe.

        Main public interface for receiving calls.
        Whenever this method is invoked (should be by building), the given
        call is placed into the call pipe to await further processing.
        """
        self.call_pipe.put(call)

    def _await_calls(self):
        """Await for calls to be assigned.

        Periodically check the call pipe for any assigned calls, and
        recalibrate the call queue when a call is found.
        """
        while True:
            print(f"Elevator {self.id} is awaiting calls...")
            call = yield self.call_pipe.get()
            print(f"Elevator {self.id} was assigned a call!")
            self._recalibrate(call)

    def _recalibrate(self, call):
        """Add the given call to the call queue."""
        print(f"Elevator {self.id} is recalibrating...")
        self.call_queue.add(call, self.service_direction, self.curr_floor)

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
        """Switch direction of travel."""
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
        """Drop off all passengers waiting to get off at current floor."""
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

        num_floors -- number of floors in building (range assumed to be 1 to
                      num_floors)
        """
        self.lower_bound = 1
        self.upper_bound = num_floors
        self.all_calls = {
            # pickups
            1: {
                # upward-headed
                1: {
                    # reachable
                    1: {},
                    # unreachable
                    0: {},
                },
                # downward-headed calls
                0: {
                    # reachable
                    1: {},
                    # unreachable
                    0: {},
                },
            },
            # dropoffs
            0: {},
        }
        for i in range(1, num_floors + 1):
            self.all_calls[1][1][1][i] = deque()
            self.all_calls[1][1][0][i] = deque()
            self.all_calls[1][0][1][i] = deque()
            self.all_calls[1][0][0][i] = deque()
            self.all_calls[0][i] = deque()

    def get_reachable_pickups(self, direction):
        """Return all reachable pickups."""
        return self.all_calls[1][self._bitify(direction)][1]

    def get_dropoffs(self):
        """Return all dropoffs."""
        return self.all_calls[0]

    def get_reachable_calls(self, direction):
        """Return all reachable pickups and dropoffs as a merged dictionary."""
        pickups = self.get_reachable_pickups(direction)
        dropoffs = self.get_dropoffs()
        return merge(pickups, dropoffs)

    def _in_range(self, floor):
        """Return True if floor is maintained by self. False otherwise."""
        return self.lower_bound <= floor <= self.upper_bound

    def _bitify(self, direction):
        """Return 1 if direction is UP (=1), 0 if direction is DOWN (=-1)."""
        if direction == UP:
            return 1
        elif direction == DOWN:
            return 0
        else:
            raise Exception("Can only bitify 1 or -1.")

    def add(self, call, direction, curr_floor):
        """Add call to the CallManager tree.

        call       -- Call instance to be added
        direction  -- current direction of travel
        curr_floor -- current floor
        """
        if (direction is not UP or direction is not DOWN
                or not self._in_range(call.origin)):
            raise InvalidCallError("Call could not be added to CallManager.")
        direction_bit = self._bitify(direction)
        if (call.origin > curr_floor and direction == UP
                or call.origin < curr_floor and direction == DOWN):
            reachable_bit = 1
        else:
            reachable_bit = 0
        self.all_calls[1][direction_bit][reachable_bit][call.origin] = call
