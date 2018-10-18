from elevators import BasicElevator
from buildings import BasicBuilding
from session import Session


def run_simulation():
    elevator = BasicElevator()
    building = BasicBuilding(10, [elevator])
    session = Session(building)
    session.set_total_runtime(6000)
    session.run()


if __name__ == '__main__':
    run_simulation()
