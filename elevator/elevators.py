from collections import deque

import simpy
from elevator.utils import print_status, bitify, UP, DOWN


class Elevator:
    """Continuously handle calls assigned to it by its Building.

    An Elevator follows the SCAN algorithm:
    1) While there are people in the elevator or calls waiting in the current
       direction of travel, keep heading in that direction and pick-up/drop-off
       as necessary.
    2) Once the elevator has serviced all calls in its current direction,
       reverse direction and go to step (1) if there are calls. Otherwise, stop
       and wait for a call (or move to a "waiting floor")

    An Elevator maintains all un-handled calls in a call queue (an instance
    of the CallQueue class, defined further below). The Elevator continuously
    handles calls while there are calls in the call queue.

    Whenever a call is assigned to an Elevator by a Building, the call is
    placed in the call pipe (a simple deque) to await further processing.
    """

    def __init__(self, building, env, id_num, capacity=simpy.core.Infinity):
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
        floor             -- current floor
        direction         -- current direction of service (1 denotes UP,
                             -1 denotes DOWN)
        curr capacity     -- current capacity
        upper bound       -- highest floor that is accessible (set by building
                             during runtime)
        lower bound       -- lowest floor that is accessible (set by building
                             during runtime)
        max capacity      -- maximum capacity
        pickup duration   -- time* it takes to pick up 1 passenger
        dropoff duration  -- time* it takes to drop off 1 passenger
        f2f time          -- time* it takes to travel between adjacent floors

        (*Unit is 0.1 seconds. Example: 75 -> 7.5 in-simulation seconds)

        """
        self.env = env
        self.id = id_num

        # Call-processing utilities
        self.call_handler = self.env.process(self._handle_calls())
        self.call_awaiter = self.env.process(self._await_calls())
        self.call_queue = CallManager(building.num_floors)
        self.call_pipe = simpy.Store(env)

        # Attributes that can change constantly
        self.floor = 1
        self.direction = UP
        self.curr_capacity = 0
        self.upper_bound = None
        self.lower_bound = None

        # Attributes that don't change
        self.max_capacity = capacity
        self.pickup_duration = 30
        self.dropoff_duration = 30
        self.f2f_time = 100

    def set_service_range(self, lower, upper):
        """Set upper and lower bound of travel."""
        if lower > upper:
            raise ServiceRangeError("Lower bound greater than upper bound.")
        self.upper_bound = upper
        self.lower_bound = lower

    def _handle_calls(self):
        """Continuously handle calls while there are calls to be handled."""
        while True:
            yield self.env.timeout(1)
            while True:
                next_stop = self.call_queue.next_stop(self.direction)
                if next_stop is None:
                    break
                self._move_to(next_stop)
                self._drop_off()
                self._pick_up()
            if self.call_queue.get_reachable_pickups(-self.direction):
                self.call_queue.swap_reachable(self.direction)
                self._switch_service_direction()
                start = self.call_queue.next_stop(-self.direction)
                if start:
                    self._move_to(start)

    def enqueue(self, call):
        """Enqueue the given call in the call pipe.

        Main public interface for receiving calls.
        Whenever this method is invoked (should be by building), the given
        call is placed into the call pipe to await further processing.
        """
        self.call_pipe.put(call)

    def _await_calls(self):
        """Wait for calls to be assigned and recalibrate as they arrive.

        Periodically check the call pipe for any assigned calls, and
        recalibrate the call queue when a call is found.
        """
        while True:
            call = yield self.call_pipe.get()
            print_status(self.env.now, f"Elevator {self.id} received call {call.id} at floor {self.floor}")
            self._recalibrate(call)

    def _recalibrate(self, call):
        """Add the given call to the call queue."""
        self.call_queue.add(call, self.direction, self.floor)

    def _switch_service_direction(self):
        """Switch service direction."""
        if self.direction == UP:
            self.direction = DOWN
        else:
            self.direction = UP

    def _move_to(self, target_floor):
        """Move to target floor."""
        if (target_floor is None
                or not (self.lower_bound <= target_floor <= self.upper_bound)):
            raise InvalidFloorError("Cannot move to specified floor.")
        print_status(self.env.now, f"Elevator {self.id} started moving to {target_floor}")
        n = target_floor - self.floor
        if n > 0:
            step = 1
        else:
            step = -1
        self.env.process(self._move_n_floors(abs(n), step))
        print_status(self.env.now, f"Elevator {self.id} is now at floor {self.floor}")

    def _pick_up(self):
        """Pick up as many passengers as possible on the current floor.

        Pick up as many passengers as the Elevator's capacity allows. If the
        Elevator reaches maximum capacity, passengers are left on the current
        floor to be handled at a later time.
        """
        while self.call_queue.get_pickups(self.direction, self.floor):
            if self.curr_capacity == self.max_capacity:
                print_status(self.env.now, f"Elevator {self.id} is full.")
                self.call_queue.reject_reachable(self.direction, self.floor)
                break
            call = self.call_queue.next_pickup(self.direction, self.floor)
            call.picked_up(self.env.now)
            self.env.process(self._pickup_single_passenger())
            self.curr_capacity += 1
            print_status(self.env.now,
                         f"(pick up) Elevator {self.id} at floor {self.floor}"
                         f", capacity now {self.curr_capacity}")

    def _drop_off(self):
        """Drop off all passengers waiting to get off at current floor."""
        while self.call_queue.get_dropoffs(self.floor):
            call = self.call_queue.next_dropoff(self.floor)
            call.completed(self.env.now)
            self.curr_capacity -= 1
            self.env.process(self._dropoff_single_passenger())
            print_status(self.env.now,
                         f"(drop off) Elevator {self.id} at floor "
                         f"{self.floor}, capacity now {self.curr_capacity}")

    def _move_n_floors(self, n, step):
        """Traverse n floors and elapse time accordingly."""
        for _ in range(n):
            self.floor += step
            yield self.env.timeout(self.f2f_time)

    def _move_one_floor(self):
        """Elapse time required to move one floor."""
        yield self.env.timeout(self.f2f_time)

    def _pickup_single_passenger(self):
        """Elapse time required to pick up one passenger."""
        yield self.env.timeout(self.pickup_duration)

    def _dropoff_single_passenger(self):
        """Elapse time required to drop off one passenger."""
        yield self.env.timeout(self.dropoff_duration)


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
        self._lower_bound = 1
        self._upper_bound = num_floors
        self._all_calls = {
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

    def get_pickups(self, direction, curr_floor):
        """Return pickups for given direction and floor."""
        try:
            return self._all_calls[1][bitify(direction)][1][curr_floor]
        except KeyError:
            return None

    def get_dropoffs(self, curr_floor):
        """Return dropoffs for given floor."""
        try:
            return self._all_calls[0][curr_floor]
        except KeyError:
            return None

    def get_all_dropoffs(self):
        """Return all dropoffs."""
        return self._all_calls[0]

    def get_reachable_pickups(self, direction):
        """Return all reachable pickups in given direction."""
        return self._all_calls[1][bitify(direction)][1]

    def _in_range(self, floor):
        """Return True if floor is maintained by self. False otherwise."""
        return self._lower_bound <= floor <= self._upper_bound

    def add(self, call, direction, curr_floor):
        """Add call to the CallManager tree.

        call       -- Call instance to be added
        direction  -- current direction of travel
        floor -- current floor
        """
        if direction is not UP and direction is not DOWN:
            raise InvalidCallError("Invalid direction. Call could not be "
                                   "added to CallManager.")
        if not self._in_range(call.source):
            raise InvalidCallError("Out of range. Call could not be added "
                                   "to CallManager.")
        if call.direction != direction:
            # add call to opposite direction, reachable
            tmp = self._all_calls[1][bitify(call.direction)][1]
            try:
                tmp[call.source].append(call)
            except KeyError:
                tmp[call.source] = deque([call])
        else:
            # add call to same direction, reachable or unreachable
            direction_bit = bitify(direction)
            if (call.source >= curr_floor and direction == UP
                    or call.source <= curr_floor and direction == DOWN):
                reachable_bit = 1
            else:
                reachable_bit = 0
            tmp = self._all_calls[1][direction_bit][reachable_bit]
            try:
                tmp[call.source].append(call)
            except KeyError:
                tmp[call.source] = deque([call])

    def _add_dropoff(self, call):
        """Adds given call to dropoffs."""
        try:
            self._all_calls[0][call.dest].append(call)
        except KeyError:
            self._all_calls[0][call.dest] = deque([call])

    def next_pickup(self, direction, curr_floor):
        """Pop and return the next pickup at given direction and floor.

        Poppped call is then placed in dropoffs. Return None if there are no
        calls left to pick up.
        """
        pickups = self.get_pickups(direction, curr_floor)
        try:
            call = pickups.popleft()
        except IndexError:
            return None
        if not ((call.dest - curr_floor) * direction > 0):
            raise InvalidCallError("Call destination was not in direction"
                                   " of travel.")
        if not pickups:
            del self._all_calls[1][bitify(direction)][1][curr_floor]
        self._add_dropoff(call)
        return call

    def next_dropoff(self, curr_floor):
        """Pop and return the next dropoff at given floor.

        Return None if there are no calls left to drop off.
        """
        dropoffs = self.get_dropoffs(curr_floor)
        try:
            call = dropoffs.popleft()
        except IndexError:
            return None
        if not dropoffs:
            del self._all_calls[0][curr_floor]
        return call

    def next_stop(self, direction):
        """Return the next floor that requires service."""
        pickups = self.get_reachable_pickups(direction)
        dropoffs = self.get_all_dropoffs()
        if not pickups and not dropoffs:
            return None
        else:
            if direction == UP:
                f = min
            elif direction == DOWN:
                f = max
            else:
                raise InvalidDirectionError("Invalid direction. "
                                            "Cannot find next floor.")
            all_floors = [flr for flr in pickups] + [flr for flr in dropoffs]
            return f(all_floors)

    def swap_reachable(self, direction):
        """Swap reachable and unreachable pickups for given direction.

        Called when elevator switches direction. For preparing reachable calls
        in advance for the next cycle."""
        d_bit = bitify(direction)
        self._all_calls[1][d_bit][1], self._all_calls[1][d_bit][0] \
            = self._all_calls[1][d_bit][0], self._all_calls[1][d_bit][1]

    def reject_reachable(self, direction, curr_floor):
        """Mark all reachable calls in direction and floor as unreachable.

        Called when elevator cannot accommodate reachable calls for whatever
        reason (usually when full) and postpones their service until the next
        cycle.
        """
        d_bit = bitify(direction)
        self._all_calls[1][d_bit][0][curr_floor] \
            .extend(self._all_calls[1][d_bit][1][curr_floor])
        del self._all_calls[1][d_bit][1][curr_floor]


# -- Custom Errors --
class ServiceRangeError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidCallError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidFloorError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidDirectionError(Exception):
    def __init__(self, message):
        super().__init__(message)
# ----
