from elevators import Elevator
from buildings import BasicBuilding
from session import Session
import random


def run_simulation():
    random.seed(1)
<<<<<<< HEAD
    elevator1, elevator2 = Elevator(15), Elevator(15)
    building = BasicBuilding(10, [elevator1, elevator2])
=======
    elevator = Elevator(15)
    building = BasicBuilding(10, [elevator])
>>>>>>> 7e7e1460220fce1892943e05ed0c7f2b9a503242
    session = Session(building)
    session.total_runtime = 36000
    session.run()


if __name__ == '__main__':
    run_simulation()

