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
        self.building.set_call_buffer()
        for elevator in self.building.elevators:
            elevator.set_env(self.env)
            elevator.set_call_queue()
            elevator.set_call_handler()
        self.building.assign_elevator_ids()
        self.building.set_initial_process()

    def run(self):
        if self._valid_session():
            print("BEGINNING SESSION")
            print("=================")
            self.env.run(until=self.total_runtime)
            print("=================")
            print("ENDING SESSION")

            print("\nRESULTS:")
            self._disp_metrics()
        else:
            raise Exception("Session was not valid. Could not run Session.")

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
        if not self.building.call_buffer:
            print("Building does not have a call buffer.")
            return False
        if not self.building.call_generator or not self.building.call_processor:
            print("Building does not have a call generator or processor.")
            return False
        if not self.building.elevators:
            print("Building does not have elevators.")
            return False
        for elevator in self.building.elevators:
            if not elevator.env or elevator.id is None or not elevator.call_queue:
                print("An Elevator does not have an environment or ID or call queue.")
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
        avg_wait = total_wait / sum(1 for _ in (r for r in
                                                self.building.call_history if r.done))
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
