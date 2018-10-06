from random import randint


class Building:
    def __init__(self, elevators):
        self.elevators = elevators  # list[Elevator]
        self.num_elevators = len(elevators)
        self.floors = 0
        self.requests = None    # {time : (origin, dest)}

    def set_floor_count(self, floors):
        if floors < 1:
            raise Exception('Floor count must be positive')
        self.floors = floors

    def set_requests(self, requests):
        for request in requests:
            if 1 > request.origin > self.floors or 1 > request.dest > self.floors:
                raise Exception('Request out of bounds')
            self.requests[request.time] = (request.origin, request.dest)

    def operate(self, time):
        pass


class BasicBuilding(Building):
    def operate(self, time):
        if time in self.requests:




