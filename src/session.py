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
        print('BEGINNING SESSION')
        print('=================')
        self.env.run(until=self.total_runtime)
        print('=================')
        print('ENDING SESSION')

    def set_total_runtime(self, n):
        self.total_runtime = n
