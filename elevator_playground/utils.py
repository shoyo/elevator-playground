"""Utilities for running the elevator simulation."""


from random import sample


# -- Outputting simulation state --
def frame_to_time(frames):
    """Convert frames (10 fps) into corresponding string 'hh:mm:ss:msms'.

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
    """Print some status with a corresponding in-simulation time."""
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


def to_string(direction):
    """Return 'UP' if direction is 1, 'DOWN' if direction is -1."""
    if direction == UP:
        return "UP"
    elif direction == DOWN:
        return "DOWN"
    else:
        raise Exception("Can only convert to string 1 or -1.")
# ----


# ---- Calls ----

# -- ID generator for Call class --
def call_id_generator():
    """A generator to sequentially yield a unique value."""
    call_id = 1
    while True:
        yield call_id
        call_id += 1


id_gen = call_id_generator()
# ----


class Call:
    """An elevator call to go from one floor to another at a specific time."""
    def __init__(self, source, destination, time):
        """Create a new call.

        id           -- unique number to identify a call
        source       -- floor that requires pick-up
        dest         -- floor that requires drop-off (may or may not be
                        viewed by dispatching mechanism)
        direction    -- the direction
        orig time    -- time* that the call was initialized
        wait time    -- time* elapsed between initialization and pick-up
        process time -- time* elapsed between initialization and completion
        done         -- True if call has been completed, False otherwise

        (*Unit is 0.1 seconds. Example: 75 -> 7.5 in-simulation seconds)
        """
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
        """Set the wait time according to when call was picked up."""
        self.wait_time = pick_up_time - self.orig_time

    def completed(self, completion_time):
        """Mark the call as completed and calculate the total process time."""
        self.done = True
        self.process_time = completion_time - self.orig_time


def rand_call(time, floor_upper_bound, floor_lower_bound=1):
    """Generate a random elevator call.

    The generated call is initialized at time "time", with the source floor
    and destination floors between the given upper and lower bound.
    The lower bound for the floors is set to 1 unless specified.
    """
    # TODO: Make floor choice between upper and lower bound dependent on given distribution.
    # TODO: (ex. uppeak/downpeak traffic, base floor congestion etc.).
    source, dest = sample([i for i in range(floor_lower_bound, floor_upper_bound + 1)], 2)
    return Call(source, dest, time)
# --------

