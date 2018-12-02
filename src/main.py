from elevators import Elevator
from buildings import BasicBuilding
from session import Session
import random

RANDOM_SEED = 1


def run_simulation():
    random.seed(RANDOM_SEED)
    elevator1, elevator2 = Elevator(15), Elevator(15)
    building = BasicBuilding(10, [elevator1, elevator2])
    session = Session(building, 36000)
    session.run()


if __name__ == '__main__':
    run_simulation()

