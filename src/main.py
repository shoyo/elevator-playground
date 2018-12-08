from src.elevators import Elevator
from src.buildings import BasicBuilding
from src.session import Session
import random

RANDOM_SEED = 1


def run_simulation():
    random.seed(RANDOM_SEED)
    elevators = [
        Elevator(15),
        Elevator(15),
        Elevator(15),
    ]
    building = BasicBuilding(10, elevators)
    session = Session(building, 36000)
    session.run()


if __name__ == '__main__':
    run_simulation()

