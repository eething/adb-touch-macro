# from typing import List
# import

class MyEvent:
    def __init__(self):
        self.down_time = None
        self.up_time = None
        self.x_start = None
        self.x_end = None
        self.y_start = None
        self.y_end = None

    def set_x(self, x):
        if self.x_start is None:
            self.x_start = x
        else:
            self.x_end = x

    def set_y(self, y):
        if self.y_start is None:
            self.y_start = y
        else:
            self.y_end = y

    def set_down(self):
        pass

    def set_up(self):
        pass

    def finalize(self):
        self.x_diff = self.x_start - self.x_end
        self.y_diff = self.y_start - self.y_end
        is_swipe = True if self.y_diff > 50 else False


class RawEvent:
    def __init__(self, line: str):
        a, b, c, d = line.split()
        self.device = a
        self.type = b
        self.name = c
        self.value = d
        self.value_int = int(d, 16)
        self.is_up = False
        # self.result = down

    def analyze(self, m: MyEvent):
        if self.type == '0001' and self.name == '014a':  # EV_KEY, BTN_TOUCH
            if self.value == '00000001':
                m.set_down()
            elif self.value == '00000000':
                self.is_up = True
                m.set_up()

        elif self.type == '0003':  # EV_ABS
            if self.name == '0035':  # ABS_MT_POSITION_X
                m.set_x(self.value_int)
            elif self.name == '0036':  # ABS_MT_POSITION_Y
                m.set_y(self.value_int)

    def isUp(self):
        return self.is_up

    def isSyn(self):
        return (self.type == '0000')  # EV_SYN, SYN_REPORT, 00000000


class Worker:
    def __init__(self):
        self.cnt_process = 0
        self.m_list = []

    def process(self, line: str, m: MyEvent):
        e: RawEvent = RawEvent(line)
        e.analyze(m)

        if e.isUp():
            self.cnt_process += 1
            print(f'end of event {self.cnt_process}')
            m.finalize()
            self.m_list.append(m)
            return True

        return False

    def main(self):
        with open('record.txt') as f:
            started = False
            while (True):
                line = f.readline()
                if not line:
                    print('ERROR: No lines...')
                    return

                if line.startswith("/dev"):
                    started = True
                    break

            if not started:
                return

            m = MyEvent()
            while (True):
                is_end = self.process(line, m)

                line = f.readline()
                if not line:
                    break
                elif is_end:
                    m = MyEvent()

        for i, m in enumerate(self.m_list):
            print(f"{i}: {m.x_start}, {m.y_start} -> {m.x_end}, {m.y_end} "
                  f"({m.x_diff}, {m.y_diff})")


w = Worker()
w.main()
