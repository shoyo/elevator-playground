from elevator.buildings import BasicBuilding
from elevator.session import Session
import random

RANDOM_SEED = 1


def run_simulation():
    """Set up simulation parameters and run the simulation."""
    random.seed(RANDOM_SEED)

    num_floors = 10
    num_elevators = 1
    total_runtime = 36000

    building = BasicBuilding(num_floors, num_elevators)
    session = Session(building, total_runtime)

    session.run()


if __name__ == '__main__':
    run_simulation()

