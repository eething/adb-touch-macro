# from typing import List
# import

import re

time_first = None
pattern = re.compile("(?:\\[\\s*(\\S*)\\] )?(/dev\\S*)\\s*(\\S*)\\s*(\\S*)\\s*(\\S*)")


class Slot:
    def __init__(self):
        self.x_start = None
        self.y_start = None
        self.x_end = None
        self.y_end = None
        self.x_diff = None
        self.y_diff = None

        self.time_start = None
        self.time_end = None
        self.time_diff = None

    def __repr__(self):
        return f"{self.x_start}, {self.y_start} -> {self.x_end}, {self.y_end}"

    def set_xy(self, x, y):
        if self.x_start is None:
            self.x_start = x
        else:
            self.x_end = x

        if self.y_start is None:
            self.y_start = y
        else:
            self.y_end = y

    def set_time(self, press_time, release_time):
        # print('set_time', press_time, release_time)
        if press_time is not None:
            self.time_start = press_time

        if release_time is not None:
            self.time_end = release_time

    def finalize(self):
        # print("Slot::finalize")
        # print(f"{self.x_start}, {self.y_start}, {self.x_end}, {self.y_end}")
        self.x_diff = self.x_start - self.x_end
        self.y_diff = self.y_start - self.y_end

        # print('finalize', self.time_start, self.time_end)
        self.time_diff = self.time_end - self.time_start

        # is_swipe = True if self.y_diff > 50 else False


class FinalEvent:
    def __init__(self):
        self.slots = []

    def set_slot_xy(self, slotid, x, y):
        while len(self.slots) <= slotid:
            self.slots.append(Slot())
        self.slots[slotid].set_xy(x, y)
        # print(*self.slots)

    def set_slot_time(self, slotid, press_time, release_time):
        while len(self.slots) <= slotid:
            self.slots.append(Slot())
        self.slots[slotid].set_time(press_time, release_time)

    def finalize(self):
        # print(f"FinalEvent::finalize")
        for slot in self.slots:
            slot.finalize()


class BundleEvent:
    def __init__(self):
        self.touch_up = False
        self.slotid = 0
        self.x = None
        self.y = None
        self.press_time = None
        self.release_time = None

    def set_touch_up(self):
        self.touch_up = True

    def is_touch_up(self):
        return self.touch_up

    def set_slotid(self, id):
        self.slotid = id

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def set_press_time(self, time):
        self.press_time = time

    def set_release_time(self, time):
        self.release_time = time

    def finalize(self, fe: FinalEvent):
        # print(f"BundleEvent::finalize", self.x, self.y)
        if self.x is not None and self.y is not None:
            fe.set_slot_xy(self.slotid, self.x, self.y)
        fe.set_slot_time(self.slotid, self.press_time, self.release_time)


class RawEvent:
    def __init__(self, matched):
        self.time, self.device, self.type, self.name, self.value = matched.groups()
        self.value_int = int(self.value, 16)

        # print(self.time, self.device, self.type, self.name, self.value)
        if self.time is not None:
            self.time = float(self.time)
            global time_first
            if time_first is None:
                time_first = self.time
            self.time -= time_first  # diff

        # self.result = down

    def analyze_to_bundle(self, be: BundleEvent):
        if self.type in ['0001', 'EV_KEY']:
            if self.name in ['014a', 'BTN_TOUCH']:
                if self.value in ['00000001', 'DOWN']:
                    # be.set_touch_down()
                    pass
                elif self.value in ['00000000', 'UP']:
                    # self.is_up = True
                    be.set_touch_up()

        elif self.type in ['0003', 'EV_ABS']:
            if self.name in ['0035', 'ABS_MT_POSITION_X']:
                be.set_x(self.value_int)
            elif self.name in ['0036', 'ABS_MT_POSITION_Y']:
                be.set_y(self.value_int)
            elif self.name in ['0039', 'ABS_MT_TRACKING_ID']:
                if self.value == 'ffffffff':  # 4294967295
                    #   this is end of TRACKING
                    be.set_release_time(self.time)
                else:
                    be.set_press_time(self.time)
            elif self.name == '002f':  # ABS_MT_SLOT
                be.set_slotid(self.value_int)

    def isSyn(self):  # EV_SYN, SYN_REPORT, 00000000
        return (self.type in ['0000'])


class Worker:
    def __init__(self):
        self.eof = False

        self.new_bundle: bool = True
        self.be: BundleEvent = None

        self.new_final: bool = True
        self.fe: FinalEvent = None
        self.cnt_final = 0
        self.final_list = []

    def bundle_to_final(self):
        if self.new_final:
            self.fe = FinalEvent()
            self.new_final = False

        self.be.finalize(self.fe)

        if self.be.is_touch_up():
            self.cnt_final += 1
            # print(f'New Final Event {self.cnt_final}')

            self.fe.finalize()
            self.final_list.append(self.fe)

            self.new_final = True
            self.fe = None

    def main(self):
        with open('record.txt') as f:
            while True:
                line = f.readline()
                if not line:
                    # print("End Of File")
                    break

                matched = pattern.match(line)
                if not matched:
                    continue

                if self.new_bundle:
                    self.be = BundleEvent()
                    self.new_bundle = False

                re = RawEvent(matched)
                re.analyze_to_bundle(self.be)

                if re.isSyn():
                    self.bundle_to_final()

                    self.new_bundle = True
                    self.be = None

        # 최종 체크
        for i, f in enumerate(self.final_list):
            # print(f"{i}: ...")
            for j, s in enumerate(f.slots):
                msg = f"Slot {j} : "
                msg += f"{s.x_start}, {s.y_start} -> {s.x_end}, {s.y_end} "
                msg += f"({s.x_diff}, {s.y_diff})"
                msg += f"// {s.time_end} - {s.time_start} = {s.time_diff}"
                print(msg)


w = Worker()
w.main()
