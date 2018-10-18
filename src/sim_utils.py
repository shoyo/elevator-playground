from random import sample


class Request:

    global_id = 0
    
    def __init__(self, origin, destination, time):
        self.origin = origin
        self.dest = destination
        self.time = time
        self.id = self.generate_id() 

    def generate_id(self):
        yield global_id
        global_id += 1
    
    
def randreq(time, upper_bound, lower_bound=1):
    origin, dest = sample([i for i in range(lower_bound, upper_bound + 1)], 2)
    return Request(origin, dest, time)


def frameToTime(frames):
    """ Converts frames (10 fps) into corresponding formattted
    string 'hh:mm:ss:msms'.
    >>> frameToTime(100)
    '0:00:10:00'
    >>> frameToTime(72000)
    '2:00:00:00'
    """
    msec = frames % 10 * 6
    frames //= 10 
    hour = frames // 3600
    frames %= 3600 
    min = frames // 60
    sec = frames % 60
    
    if min // 10 == 0:
        min = f'0{min}'
    if sec // 10 == 0:
        sec = f'0{sec}'
    if msec // 10 == 0:
        msec = f'0{msec}'

    return f'{hour}:{min}:{sec}:{msec}'


def print_status(time, status):
    print(f'{frameToTime(time)} - {status}')

