from elevators import BasicElevator
from buildings import BasicBuilding
from session import Session
import random


def run_simulation():
    random.seed(1)
    elevator = BasicElevator()
    building = BasicBuilding(10, [elevator])
    session = Session(building)
    session.set_total_runtime(36000)
    session.run()
    return 0

if __name__ == '__main__':
    run_simulation()
