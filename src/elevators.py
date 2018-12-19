from collections import deque

import simpy
from utils import print_status, UP, DOWN, IDLE


class ServiceMap:
    """
    Used by Elevator. Maps floors that require service with their corresponding
    calls. Calls are classified according to whether they require a pick-up or
    drop-off.
    """

    def __init__(self, service_range):
        """
        :attrtype self.pickups: dict[int, List[Call]]
        :attr self.pickups: dictionary mapping floors to Calls that require a
                            pick-up

        :attrtype self.dropoffs: dict[int, deque[Call]]
        :attr self.dropoffs: dictionary mapping floors to Calls that require a
                            drop-off

        :attrtype self.service_range: tuple(int, int)
        :attr self.service_range: tuple where 0 indexes lower bound (inclusive)
                                  1 indexes upper bound (exclusive)
        """
        self._pickups = {}
        self._dropoffs = {}
        self._service_range = service_range
        self._upper_bound = service_range[1]
        self._lower_bound = service_range[0]
        for i in range(self._lower_bound, self._upper_bound):
            self._pickups[i] = deque()
            self._dropoffs[i] = deque()

    def get_pickups(self):
        return self._pickups

    def get_dropoffs(self):
        return self._dropoffs

    def is_empty(self):
        return not self._pickups and not self._dropoffs

    def pop_next_pickup(self, floor):
        call = self._pickups[floor].popleft()
        return call

    def pop_next_dropoff(self, floor):
        call = self._dropoffs[floor].popleft()
        return call

    def enqueue_dropoff(self, call):
        self._dropoffs[call.dest].append(call)

    def set_pickup(self, call):
        if not self._inrange(call.origin):
            raise Exception("Attempted to give ServiceMap a pick-up call "
                            "for a floor outside of service range.")
        else:
            self._pickups[call.origin].append(call)

    def _set_dropoff(self, call):
        if not self._inrange(call.dest):
            raise Exception("Attempted to give ServiceMap a drop-off call "
                            "for a floor outside of service range.")
        else:
            self._dropoffs[call.dest].append(call)

    def drop_off(self, floor):
        """
        Drops off a single passenger at given floor and returns the
        corresponding call.
        """
        return self._dropoffs[floor].popleft()

    def next_stop(self, curr_floor, direction, directional_pref):
        """
        :type curr_floor: int
        :param curr_floor: current location of Elevator

        :type direction: int
        :param direction: 1 denotes UP, -1 denotes DOWN
        
        :type directional_pref: int
        :param directional_pref: same as direction; default movement 
                                       when idle

        Returns the next floor in the direction of travel that requires
        service if one exists. Returns None otherwise.
        """
        # TODO: more robust checking for directional pref -- make sure it's
        # up or down
        if direction == IDLE and directional_pref == IDLE:
            raise Exception("Cannot find next stop if Elevator is idle "
                            "and does not have valid directional preference.")
        if direction == IDLE:
            direction = directional_pref
        next_floor = curr_floor
        while self._inrange(next_floor):
            next_floor = curr_floor + direction
            if self._service_required(next_floor):
                return next_floor
        return None

    def _service_required(self, floor):
        """
        Returns whether given floor requires a pick-up or drop-off.
        """
        return not not self._pickups[floor] or not not self._dropoffs[floor]

    def _inrange(self, floor):
        """
        Returns whether floor is within service range.
        """
        return self._lower_bound <= floor < self._upper_bound


class Elevator:
    """
    Elevator class. Responsible for handling calls assigned to it by its
    Building. Continuously handles calls while there are calls to be handled.

    This Elevator maintains 2 maps: active-map and defer-map. The former
    maintains all calls in the current direction of travel, and the latter
    maintains all calls in the opposite direction.

    Whenever this Elevator is assigned a call, its recalibration process is
    invoked. This Elevator then determines whether to put the call into its
    active-map or defer-map. The Elevator then proceeds to handle calls with
    the algorithm described below.

    Each elevator follows the SCAN algorithm:
    1) While there are people in the elevator or calls waiting in the
       current service direction, keep heading in that direction and
       pick-up/drop-off as necessary.
    2) Once the elevator has serviced all calls in its current direction,
       reverse direction and go to step (1) if there are calls. Else, stop
       and wait for a call (or move to another floor deemed more effective)
    """

    def __init__(self, capacity=simpy.core.Infinity):
        self.env = None
        self.id = None

        self.call_handler = None
        self.call_awaiter = None
        self.call_queue = None
        self.active_map = None
        self.defer_map = None

        self.curr_floor = 1
        self.dest_floor = None
        self.service_direction = IDLE
        self.curr_capacity = 0

        self.max_capacity = capacity
        self.pickup_duration = 30
        self.dropoff_duration = 30
        self.f2f_time = 100
        self.service_range = None
        self.upper_bound = None
        self.lower_bound = None
        self.directional_pref = UP
        # preferred direction of travel when IDLE and requests exist above and below

    def set_env(self, env):
        if self.env:
            raise Exception("Attempted to set environment for Elevator "
                            "which already had an environment.")
        else:
            self.env = env

    def set_id(self, id):
        if self.id:
            raise Exception("Attempted to set ID for Elevator which "
                            "already had an ID.")
        else:
            self.id = id

    def set_service_range(self, service_range):
        if service_range[0] > service_range[1]:
            raise Exception("Attempted to set an invalid service range for "
                            "Elevator")
        if self.service_range:
            raise Exception("Attempted to set Building for Elevator which"
                            "already had a Building.")
        else:
            self.service_range = service_range
            self.upper_bound = service_range[1]
            self.lower_bound = service_range[0]

    def init_service_maps(self):
        if not self.service_range:
            raise Exception("Attempted to initialize service maps for "
                            "Elevator with no service range.")
        if self.active_map or self.defer_map:
            raise Exception("Attempted to initialize service maps for "
                            "Elevator which already had service maps.")
        else:
            self.active_map = ServiceMap(self.service_range)
            self.defer_map = ServiceMap(self.service_range)

    def init_call_handler(self):
        if not self.env:
            raise Exception("Attempted to initialize a call handler to an "
                            "Elevator with no environment.")
        if self.call_handler:
            raise Exception("Attempted to initialize a call handler to an "
                            "Elevator that already had a call handler.")
        else:
            self.call_handler = self.env.process(self._handle_calls())

    def init_call_awaiter(self):
        if not self.env:
            raise Exception("Attempted to initialize a call awaiter to an "
                            "Elevator with no environment.")
        if self.call_awaiter:
            raise Exception("Attempted to initialize a call awaiter to an "
                            "Elevaotr that already had a call awaiter.")
        else:
            self.call_awaiter = self.env.process(self._await_calls())

    def init_call_queue(self):
        if not self.env:
            raise Exception("Attempted to initialize call queue for "
                            "Elevator with Environment.")
        if self.call_queue:
            raise Exception("Attempted to initialize call queue for "
                            "Elevator which already had a call queue.")
        else:
            self.call_queue = simpy.Store(self.env)

    def _handle_calls(self):
        """
        Main, overarching Elevator operation method.
        Continuously handles calls while there are calls to be handled.
        """
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
        """
        Main interface with Elevator for receiving calls.
        Puts given call into the Elevator's call queue. The Elevator
        recalibrates its active-map and defer-map with the calls in
        the call queue periodically.
        """
        self.call_queue.put(call)

    def _await_calls(self):
        """
        Constantly waits for calls to be assigned by the Building. If it
        receives a call, the Elevators service maps are recalibrated.
        """
        while True:
            print(f"Elevator {self.id} is awaiting calls...")
            call = yield self.call_queue.get()
            print(f"Elevator {self.id} was assigned a call!")
            self._recalibrate(call)

    def _recalibrate(self, call):
        """
        For a given call, determines whether to add it to the active-map or
        defer-map.
        """
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
        """
        Picks up all passengers waiting at current floor.
        :return:
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
                                f"wrong origin.")
            call.picked_up(self.env.now)
            self.curr_capacity += 1
            self.active_map.enqueue_dropoff(call)
            self.env.run(self.env.process(self._pickup_single_passenger()))
        print_status(self.env.now,
                     f"(pick up) Elevator {self.id} at floor {self.curr_floor}"
                     f", capacity now {self.curr_capacity}")

    def _drop_off(self):
        """
        Drops off all passengers waiting to get off at current floor.
        """
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
