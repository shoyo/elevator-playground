from buildings import BasicBuilding
from elevators import Elevator
from requests import Request
from session import Session


def run_simulation():
    elevator = Elevator()
    building = BasicBuilding([elevator])
    building.set_floor_count(10)
    building.set_requests([Request(5, 2, 1000), Request(4, 1, 2500), Request(10, 7, 5000)])

    session = Session(building)
    session.set_total_time(36000)  # 1 hour = 0.1 s / frame * 36000 frames
    session.run()


if __name__ == '__main__':
    run_simulation()
