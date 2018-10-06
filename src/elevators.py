class Elevator:
    def __init__(self):
        self.position = 1
        self.dest = None
        self.num_passengers = 0
        self.capacity = 10
        self.movement = 0  # 0 = stationary, 1 = moving up, -1 = moving down
        self.max_speed = None
        self.acceleration = None
        self.distance_traveled = 0
        self.requests = None            # List[tuple(start, dest)]
        self.pick_up_requests = {}      # {floor : passenger count}
        self.drop_off_requests = {}     # {floor : passenger count}
        self.month = None
        self.date = None
        self.time = 0

    def do_request(self, request):
        self.dest = request.dest


    def move_up(self, n=1):
        self.position += n

    def move_down(self, n=1):
        self.position -= n

    def pick_up(self, n=1):
        self.num_passengers += n

    def drop_off(self, n=1):
        if self.num_passengers < 0:
            raise Exception('There are no passengers to drop off.')
        self.num_passengers -= n

    def print_status(self):
        print(f'Floor { self.position }')
        if self.movement == 0:
            print('Stopped')
        elif self.movement == 1:
            print('Continuing up')
        else:
            print('Continuing down')
