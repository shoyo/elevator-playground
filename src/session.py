import simpy


class Session:
    def __init__(self, building):
        self.env = simpy.Environment()
        self.building = building
        self.building.set_env(self.env)
        for elevator in self.building.elevators:
            elevator.env = self.env
            elevator.cart = simpy.Resource(self.env, )

        self.total_runtime = 36000  # 1 hour (10 frames per second)

    def run(self):
        # TODO : Check conditions before starting
        print('BEGINNING SESSION')
        print('=================')
        self.env.run(until=self.total_runtime)
        print('=================')
        print('ENDING SESSION')

        print('\nRESULTS:')
        self.disp_metrics()

    def disp_metrics(self):
        # TODO: make this more efficient
        total_wait = sum(r.wait_time for r in self.building.all_calls if
                         r.done)
        avg_wait = total_wait / sum(1 for _ in (r for r in
                                                self.building.all_calls if r.done))
        max_wait = max(r.wait_time for r in self.building.all_calls if r.done)
        completed_invocs = sum(1 for _ in (r for r in self.building.all_calls if
                                           r.done))
        avg_pt = sum(r.process_time for r in self.building.all_calls if
                     r.done) / sum(1 for _ in (r for r in self.building.all_calls if r.done))

        print(f'Average wait time    = {avg_wait / 10} s')
        print(f'Maximum wait time    = {max_wait / 10} s')
        print(f'Completion rate      = {completed_invocs}/{len(self.building.all_calls)}')
        print(f'Average process time = {avg_pt / 10} s')
