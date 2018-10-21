import simpy


class Session:
    def __init__(self, building):
        self.env = simpy.Environment()
        self.building = building
        self.building.set_env(self.env)
        for elevator in self.building.elevators:
            elevator.set_env(self.env)

        self.total_runtime = 36000  # 1 hour (10 frames per second)

    def run(self):
        # TODO : Check all conditions before starting
        print('BEGINNING SESSION')
        print('=================')
        self.env.run(until=self.total_runtime)
        print('=================')
        print('ENDING SESSION')

        print('\nRESULTS:')
        self.disp_metrics()

    def set_total_runtime(self, n):
        self.total_runtime = n

    def disp_metrics(self):
        total_wait = sum(r.wait_time for r in self.building.all_requests if
                r.done) 
        avg_wait = total_wait / len(self.building.all_requests)
        max_wait = max(r.wait_time for r in self.building.all_requests)
        print(f'Average wait time = {avg_wait / 10} s')
        print(f'Maximum wait time = {max_wait / 10} s')
