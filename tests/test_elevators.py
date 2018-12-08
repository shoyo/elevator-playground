import unittest
import random
from src.elevators import Elevator
from src.buildings import BasicBuilding
from src.session import Session


class ElevatorTests(unittest.TestCase):
    def setUp(self):
        random.seed(1)
        #elevator1, elevator2 = Elevator(15), Elevator(15)
        #building = BasicBuilding(10, [elevator1, elevator2])
        #session = Session(building, 36000)

    def testAssertTrue(self):
        self.assertTrue(True)

    def testAssertFalse(self):
        self.assertFalse(False)


if __name__ == '__main__':
    unittest.main()
