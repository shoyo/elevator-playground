"""Utilities for running the elevator simulation."""


from random import sample


# -- Outputting simulation state --
def frame_to_time(frames):
    """Converts frames (10 fps) into corresponding string ' hh:mm:ss:msms'.

    Examples:
    >>> frame_to_time(100)
    '  0:00:10:00'
    >>> frame_to_time(72000)
    '  2:00:00:00'
    >>> frame_to_time(5235)
    '  0:08:43:30'
    """
    frames = int(frames)
    msec = frames % 10 * 6
    frames //= 10
    hour = frames // 3600
    frames %= 3600
    mins = frames // 60
    sec = frames % 60

    if mins // 10 == 0:
        mins = "0{}".format(mins)
    if sec // 10 == 0:
        sec = "0{}".format(sec)
    if msec // 10 == 0:
        msec = "0{}".format(msec)

    return "{:>3}:{}:{}:{}".format(hour, mins, sec, msec)


def print_status(time, status):
    print(f"{frame_to_time(time)} - {status}")
# ----


# -- Elevator travel directions --
UP = 1
DOWN = -1
IDLE = 0


def bitify(direction):
    """Return 1 if direction is UP (=1), 0 if direction is DOWN (=-1)."""
    if direction == UP:
        return 1
    elif direction == DOWN:
        return 0
    else:
        raise Exception("Can only bitify 1 or -1.")
# ----


# ---- Calls ----
# -- ID generator for Call class --
def id_generator():
    id = 1
    while True:
        yield id
        id += 1


id_gen = id_generator()
# ----


class Call:
    def __init__(self, source, destination, time):
        self.id = next(id_gen)
        self.source = source
        self.dest = destination
        if self.dest - self.source > 0:
            self.direction = UP
        elif self.dest - self.source < 0:
            self.direction = DOWN
        else:
            raise Exception("A call was generated with the same source and "
                            "destination.")
        self.orig_time = time
        self.wait_time = None
        self.process_time = None
        self.done = False

    def picked_up(self, pick_up_time):
        self.wait_time = pick_up_time - self.orig_time

    def completed(self, completion_time):
        self.done = True
        self.process_time = completion_time - self.orig_time


def rand_call(time, floor_upper_bound, floor_lower_bound=1):
    """Generates a random elevator call.

    The generated call is initialized at time "time", with the source floor
    and destination floors between the given upper and lower bound.
    The lower bound for the floors is set to 1 unless specified.
    """
    # TODO: Make floor choice between upper and lower bound dependent on given distribution.
    # TODO: (ex. uppeak/downpeak traffic, base floor congestion etc.).
    source, dest = sample([i for i in range(floor_lower_bound, floor_upper_bound + 1)], 2)
    return Call(source, dest, time)
# --------

