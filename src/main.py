from elevators import Elevator
from buildings import BasicBuilding
from session import Session
import random


def run_simulation():
    random.seed(1)
    elevator1, elevator2 = Elevator(15), Elevator(15)
    building = BasicBuilding(10, [elevator1, elevator2])
    session = Session(building)
    session.total_runtime = 36000
    session.run()


if __name__ == '__main__':
    run_simulation()

