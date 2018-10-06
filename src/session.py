class Session:
    def __init__(self, building):
        self.building = building
        self.clock = 0
        self.total_time = 0

    def set_total_time(self, time):
        if time < 1:
            raise Exception('Total time must be positive')
        self.total_time = time

    def run(self):
        if not self.building.elevators or not self.building.floors:
            raise Exception('Insufficient building. Cannot start session.')

        print('==== Beginning Session ====')
        while self.clock < self.total_time:
            try:
                self.building.operate(self.clock)
            except:
                print('Unexpected error occurred during session. Ending session.')
                raise
            self.clock += 1
        print('===== Ending Session ======')
