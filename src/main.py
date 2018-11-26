from elevators import Elevator
from buildings import BasicBuilding
from session import Session
import random


def run_simulation():
    random.seed(1)
    elevator = Elevator(15)
    building = BasicBuilding(10, [elevator])
    session = Session(building)
    session.total_runtime = 36000
    session.run()
    return 0


if __name__ == '__main__':
    ret = run_simulation()

