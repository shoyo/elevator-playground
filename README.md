# Elevator Playground

## About
A simulation framework to measure the performance of various elevator dispatching strategies such as SCAN, CSCAN, RL-based approaches, and others.

## Getting Started
The environment has one dependency with SimPy, a Python simulation library that handles time-keeping and asynchronous actions within the simulation runtime. Create a virtual environment and install with

    (your-venv) $ pip install -r requirements.txt

The simulation parameters set from an external file, called `run.py`. Edit `run.py` in this repo or create your own in the same directory as the `elevator_playground` package.

Within `run.py`, initialize a custom `building` instance with the `elevator_playground.buildings` module, and set its parameters (number of floors, number of elevators, etc.). Initialize a `session` with the building instance, along with a total runtime (where 10 units = 1 in-simulation minute). Finally, let the simulation execute with `session.run()`.

From the command line, execute `run.py` with

    (your-venv) $ python run.py

## Package Structure
The `elevator_playground` is comprised of 4 components.
  * `buildings.py`: handles building initialization, call generation, and call assignment logic
  * `elevators.py`: handles call reception, priority recalibration, task management with `CallManager` class, floor-to-floor movement, and pick-up/drop-off logic
  * `sessions.py`: handles simulation runtime execution and performance metric calculation
  * `utils.py`: contains `Call` class various utilities for simulation environment
