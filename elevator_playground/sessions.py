class Session:
    """A wrapper for the SimPy library for simulation execution.

    A session runs a simulation for a given building containing elevators
    and outputs the corresponding results.
    """
    def __init__(self, building, runtime=36000):
        """Create a new simulation session for a given building.

        env      -- simpy.Environment instance that runs the simulation
        building -- buildings.Building subclass instance for conducting the
                    simulation
        runtime  -- total time* for running the simulation
        (*Unit is 0.1 seconds. Example: 75 -> 7.5 in-simulation seconds)
        """
        self.env = building.env
        self.building = building
        self.total_runtime = runtime

    def run(self):
        """Run the session."""
        print("BEGINNING SESSION")
        print("=================")
        self.env.run(until=self.total_runtime)
        print("=================")
        print("ENDING SESSION")
        print("\nRESULTS:")
        self._disp_metrics()

    def _disp_metrics(self):
        """Calculate and print simulation results."""
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
