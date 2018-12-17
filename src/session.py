import simpy


class Session:
    """
    Responsible for setting up simulation environment for a Building
    containing Elevator(s) and calculating simulation results.
    """
    def __init__(self, building, runtime=36000):
        self.building = building
        self.total_runtime = runtime
        self.env = simpy.Environment()
        self.building.set_env(self.env)
        self.building.set_call_generator()
        self.building.set_call_handler()
        self.building.set_call_queue()
        self.building.assign_elevator_ids()
        for elevator in self.building.elevators:
            elevator.set_env(self.env)
            elevator.set_call_handler()
            elevator.init_service_maps()

    def run(self):
        if not self._valid_session():
            raise Exception("Session was not valid. Could not run Session.")
        else:
            print("BEGINNING SESSION")
            print("=================")
            self.env.run(until=self.total_runtime)
            print("=================")
            print("ENDING SESSION")
            # print("\nRESULTS:")
            # self._disp_metrics()

    def _valid_session(self):
        if self.total_runtime <= 0:
            print("Session has runtime less than or equal to 0.")
            return False
        if not self.env:
            print("Session does not has an environment.")
            return False
        if not self.building:
            print("Session does not have a building.")
            return False
        if not self.building.env:
            print("Building does not have an environment.")
            return False
        if not self.building.call_queue:
            print("Building does not have a call queue.")
            return False
        if not self.building.call_generator or not self.building.call_handler:
            print("Building does not have a call generator or handler.")
            return False
        if not self.building.elevators:
            print("Building does not have elevators.")
            return False
        for elevator in self.building.elevators:
            if not elevator.env or elevator.id is None:
                print("An Elevator does not have an environment or ID.")
                return False
            if not elevator.call_handler:
                print("An Elevator does not have a call handler.")
                return False
            if not elevator.service_range:
                print("An Elevator does not have a service range.")
                return False
            if not elevator.active_map or elevator.defer_map:
                print("An Elevator did not have its maps initialized.")
                return False
        return True

    def _view_state(self):
        """ Method for checking internal state of Session instance.
        For debugging purposes. """
        print(f"self.env = {self.env}")
        print(f"self.building = {self.building}")
        print(f"self.building.elevators = ")
        for elevator in self.building.elevators:
            print(f"elevator = {elevator}, id = {elevator.id}")

    def _disp_metrics(self):
        # TODO: Maybe make this more efficient
        total_wait = sum(r.wait_time for r in self.building.call_history if
                         r.done)
        avg_wait = total_wait / sum(1 for _ in (r for r in self.building.call_history if r.done))
        max_wait = max(r.wait_time for r in self.building.call_history if r.done)
        completed_invocs = sum(1 for _ in (r for r in self.building.call_history if
                                           r.done))
        avg_pt = sum(r.process_time for r in self.building.call_history if
                     r.done) / sum(1 for _ in (r for r in self.building.call_history if r.done))
        max_pt = max(r.process_time for r in self.building.call_history if r.done)

        print(f"Average wait time    = {avg_wait / 10} s")
        print(f"Maximum wait time    = {max_wait / 10} s")
        print(f"Completion rate      = {completed_invocs}/{len(self.building.call_history)}")
        print(f"Average process time = {avg_pt / 10} s")
        print(f"Maximum process time = {max_pt / 10} s")
