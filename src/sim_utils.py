from random import sample


def frame_to_time(frames):
    """ Converts frames (10 fps) into corresponding formattted
    string 'hh:mm:ss:msms'.
    >>> frame_to_time(100)
    '0:00:10:00'
    >>> frame_to_time(72000)
    '2:00:00:00'
    """
    frames = int(frames)
    msec = frames % 10 * 6
    frames //= 10
    hour = frames // 3600
    frames %= 3600
    mins = frames // 60
    sec = frames % 60

    if mins // 10 == 0:
        mins = '0{}'.format(mins)
    if sec // 10 == 0:
        sec = '0{}'.format(sec)
    if msec // 10 == 0:
        msec = '0{}'.format(msec)

    return '{:>4}:{}:{}:{}'.format(hour, mins, sec, msec)


def print_status(time, status):
    print(f'{frame_to_time(time)} - {status}')


def id_generator():
    id = 1
    while True:
        yield id
        id += 1


id_gen = id_generator()


class Call:
    def __init__(self, origin, destination, time):
        self.id = next(id_gen)
        self.origin = origin
        self.dest = destination
        self.orig_time = time
        self.wait_time = None
        self.process_time = None
        self.done = False


# TODO: (maybe) create call generator class in order to control call arrival distributions
class CallGenerator:
    """ Generates elevator calls according to Poisson distribution. """

    def __init___(self, arrival_dist, floor_dist):
        pass


def rand_call(time, floor_upper_bound, floor_lower_bound=1):
    """ Generates a random elevator call at time 'time' from floors between lower and upper bound.
    """
    # TODO: Make floor choice between upper and lower bound dependent on given distribution.
    # TODO: (ex. upstream/downstream traffic, base floor congestion etc.).
    origin, dest = sample([i for i in range(floor_lower_bound, floor_upper_bound + 1)], 2)
    return Call(origin, dest, time)
