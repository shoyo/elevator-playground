from elevator.elevators import Elevator
from elevator.buildings import BasicBuilding
from elevator.session import Session
import random

RANDOM_SEED = 1


def run_simulation():
    """Set up simulation parameters and run the simulation."""
    random.seed(RANDOM_SEED)
    elevators = [
        Elevator(),
    ]
    building = BasicBuilding(10, elevators)
    session = Session(building, 36000)
    session.run()


if __name__ == '__main__':
    run_simulation()

