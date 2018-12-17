import sys

import simpy
from utils import print_status, UP, DOWN, IDLE


class ServiceMap:
    """
    Used by Elevator. Maps floors that require service with their corresponding
    calls. Calls are classified according to whether they require a pick-up or
    drop-off.
    """

    def __init__(self, service_range):
        self.pickups = {}
        self.dropoffs = {}
        self.service_range = service_range

    def __getitem__(self, floor):
        """
        Returns a dictionary where keys ["pickup"] and ["dropoff"] map
        to all the calls that require pick-up/drop-off on given floor,
        respectively. Note it returns a copy of data; editing returned
        dictionary will NOT change ServiceMap instance.
        """
        if not self._inrange(floor):
            raise Exception("Attempted to get a ServiceMap for a floor "
                            "outside of service range.")
        else:
            return {
                "pickup": self.pickups[floor],
                "dropoff": self.dropoffs[floor]
            }

    def set_pickup(self, call):
        if not self._inrange(call.origin):
            raise Exception("Attempted to give ServiceMap a pick-up call "
                            "for a floor outside of service range.")
        else:
            self.pickups[call.origin] = call

    def set_dropoff(self, call):
        if not self._inrange(call.dest):
            raise Exception("Attempted to give ServiceMap a drop-off call "
                            "for a floor outside of service range.")
        else:
            self.dropoffs[call.dest] = call

    def next_stop(self, curr_floor, direction):
        """
        Returns the next floor in the direction of travel that requires
        service if one exists. Returns None otherwise.
        """
        while True:
            next_floor = curr_floor + direction
            if not self._inrange(next_floor):
                return None
            if self._service_required(next_floor):
                return next_floor

    def _service_required(self, floor_num):
        """
        Returns a boolean denoting whether floor floor_num requires the
        Elevator to stop to pick-up or drop-off.
        """
        return self.pickups[floor_num] or self.dropoffs[floor_num]

    def _inrange(self, floor):
        """
        Returns whether floor is within service range.
        """
        return self.service_range[0] < floor < self.service_range[1]


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
        self.active_map = None
        self.defer_map = None

        self.curr_floor = 1
        self.dest_floor = None
        self.movement = IDLE
        self.service_direction = IDLE
        self.curr_capacity = 0

        self.max_capacity = capacity
        self.pickup_duration = 70
        self.dropoff_duration = 70
        self.f2f_time = 100
        self.service_range = None
        self.upper_bound = None
        self.lower_bound = None

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

    def set_call_handler(self):
        if not self.env:
            raise Exception("Attempted to assign a call handler to an "
                            "Elevator with no environment.")
        if self.call_handler:
            raise Exception("Attempted to assign a call handler to an "
                            "Elevator that already had a call handler.")
        else:
            self.call_handler = self.env.process(self._handle_calls())

    def _handle_calls(self):
        """
        Main, overarching Elevator operation method.
        Continuously handles calls while there are calls to be handled.
        """
        while True:
            try:
                print(f"Elevator {self.id} is handling calls...")
                while self.active_map:
                    if (self.curr_floor == self.upper_bound
                            or self.curr_floor == self.lower_bound):
                        print(f"Elevator {self.id} had unhandled call despite"
                              f"reaching its boundary. Are calls being handled"
                              f"properly?")
                        sys.exit(1)
                    next_stop = self.active_map.next_stop()
                    self._move_to(next_stop)
                    self._drop_off()
                    self._pick_up()
                if self.defer_map:
                    self.active_map = self.defer_map
                    self._switch_direction()
                else:
                    self._await_calls()

                # while self.active_map:
                #     # go to next target floor
                #     # pick up people that are waiting on that floor
                #     # drop off people that want to get off on that floor
                #     # remove served calls/ update active_map
                #     # update global state
                #     # if elevator is at building boundary and there are still
                #     #   calls that haven't been served, raise error and quit.
                #     # repeat
                # if not self.defer_map:
                #     # go idle OR go to a designated waiting floor
                # else:
                #     self.active_map = self.defer_map
                #     # switch service direction
                #     # update global state

            except simpy.Interrupt:
                print(f"Elevator {self.id} call-handling was interrupted.")

    def handle_call(self, call):
        """
        Main interface with Elevator for receiving assigned calls.
        """
        self.call_handler.interrupt()
        self._recalibrate(call)

    def _recalibrate(self, call):
        """
        Given a call, determines whether to add it to the active-map
        or defer-map.
        """
        print(f"Elevator {self.id} is recalibrating...")
        if call.direction == self.service_direction:
            if (self.service_direction == UP and call.origin > self.curr_floor
                    or self.service_direction == DOWN and call.origin < self.curr_floor):
                self.active_map.set_pickup(call)
        else:
            self.defer_map[call.origin]["pickup"] += call

    def process_call_or_something(self, call):
        # movement and pickup/dropoff logic
        # ...
        self._go_idle()

    def _start_moving(self, invoking_call):
        call_direction = invoking_call.origin - self.curr_floor
        self.movement = call_direction
        self.service_direction = call_direction
        self.dest_floor = invoking_call.origin
        print_status(self.env.now, f"Elevator {self.id} has starting moving"
                                   f"for call {invoking_call.id}")

    def _go_idle(self):
        self.movement = IDLE
        self.service_direction = IDLE
        self.dest_floor = None
        print_status(self.env.now, f"Elevator {self.id} is going idle at floor"
                                   f" {self.curr_floor}")

    def _move_to(self, target_floor):
        if target_floor > self.curr_floor:
            self.movement = UP
        elif target_floor < self.curr_floor:
            self.movement = DOWN
        try:
            while self.curr_floor != target_floor:
                self.env.run(self.env.process(self._move_one_floor()))
                self.curr_floor += self.movement
        except simpy.Interrupt:
            print("Elevator _move_to() was interrupted.")
            sys.exit(1)
        self.movement = IDLE

    def _move_one_floor(self):
        yield self.env.timeout(self.f2f_time)

    def _pick_up(self):
        if self.curr_capacity >= self.max_capacity:
            raise Exception("Elevator capacity exceeded.")
        self.curr_capacity += 1
        print_status(self.env.now,
                     f"(pick up) Elevator {self.id} at floor {self.curr_floor}, capacity now {self.curr_capacity}")

    def _drop_off(self):
        if self.curr_capacity == 0:
            raise Exception("Nobody on elevator to drop off")
        self.curr_capacity -= 1
        print_status(self.env.now,
                     f"(drop off) Elevator {self.id} at floor {self.curr_floor}, capacity now {self.curr_capacity}")
