"""Utility objects for running the elevator simulation."""


from random import sample


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


def id_generator():
    id = 1
    while True:
        yield id
        id += 1


id_gen = id_generator()

UP = 1
DOWN = -1
IDLE = 0


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
        print_status(pick_up_time, f"Call {self.id} was picked up")

    def completed(self, completion_time):
        self.done = True
        self.process_time = completion_time - self.orig_time
        print_status(completion_time, f"Call {self.id} is done")


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


# Deprecated
def merge(dict1, dict2):
    """Return a merged dictionary containing all items in dict1 and dict2.

    Keys can be any data type, values are assumed to be collections.deque
    instances.

    Example:
    >>> from collections import deque
    >>> a = {"a": deque([1]), "b": deque([4])}
    >>> b = {"b": deque([3]), "c": deque([2])}
    >>> merge(a, b)
    {"a": deque([1]), "b": deque([4, 3]), "c": deque([2])}
    """
    ret = {}
    for key in dict1:
        ret[key] = dict1[key]
    for key in dict2:
        if key in ret:
            ret[key].extend(dict2[key])
        else:
            ret[key] = dict2[key]
    return ret

