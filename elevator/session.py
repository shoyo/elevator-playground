class Session:
    """A session that runs a simulation and outputs results. """
    def __init__(self, building, runtime=36000):
        self.env = building.env
        self.building = building
        self.total_runtime = runtime

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
        if self.env and self.building and self.total_runtime:
            return True
        else:
            return False

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
