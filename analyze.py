# from typing import List
# import

class Slot:
    def __init__(self):
        self.x_start = None
        self.y_start = None

        self.x_end = None
        self.y_end = None

        self.x_diff = None
        self.y_diff = None

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

    def finalize(self):
        # print("Slot::finalize")
        # print(f"{self.x_start}, {self.y_start}, {self.x_end}, {self.y_end}")

        self.x_diff = self.x_start - self.x_end
        self.y_diff = self.y_start - self.y_end
        # is_swipe = True if self.y_diff > 50 else False


class FinalEvent:
    def __init__(self):
        self.down_time = None
        self.up_time = None
        self.slots = []

    def set_down(self):
        pass

    def set_up(self):
        pass

    def set_slot(self, slotid, x, y):
        while len(self.slots) <= slotid:
            self.slots.append(Slot())

        self.slots[slotid].set_x(x)
        self.slots[slotid].set_y(y)

    def finalize(self):
        for slot in self.slots:
            slot.finalize()


class BundleEvent:
    def __init__(self):
        self.up = False
        self.slotid = 0
        self.x = None
        self.y = None

    def set_up(self):
        self.up = True

    def is_up(self):
        return self.up

    def set_slotid(self, id):
        self.slotid = id

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def finalize(self, fe: FinalEvent):
        if self.x is not None and self.y is not None:
            fe.set_slot(self.slotid, self.x, self.y)


class RawEvent:
    def __init__(self, line: str):
        a, b, c, d = line.split()
        self.device = a
        self.type = b
        self.name = c
        self.value = d
        self.value_int = int(d, 16)
        # self.result = down

    def analyze_to_bundle(self, be: BundleEvent):
        if self.type == '0001' and self.name == '014a':  # EV_KEY, BTN_TOUCH
            if self.value == '00000001':
                # be.set_down()
                pass
            elif self.value == '00000000':
                # self.is_up = True
                be.set_up()
        elif self.type == '0003':  # EV_ABS
            if self.name == '0035':  # ABS_MT_POSITION_X
                be.set_x(self.value_int)
            elif self.name == '0036':  # ABS_MT_POSITION_Y
                be.set_y(self.value_int)

            # elif self.name == '0039':  # ABS_MT_TRACKING_ID
            # if self.value == 'ffffffff' // 4294967295
            #   this is end of TRACKING

            elif self.name == '002f':  # ABS_MT_SLOT
                be.set_slotid(self.value_int)

    def isSyn(self):
        return (self.type == '0000')  # EV_SYN, SYN_REPORT, 00000000


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

        if self.be.is_up():
            self.cnt_final += 1
            print(f'New Final Event {self.cnt_final}')

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

                if not line.startswith("/dev"):
                    continue

                if self.new_bundle:
                    self.be = BundleEvent()
                    self.new_bundle = False

                re = RawEvent(line)
                re.analyze_to_bundle(self.be)

                if re.isSyn():
                    self.bundle_to_final()

                    self.new_bundle = True
                    self.be = None

        # 최종 체크
        for i, f in enumerate(self.final_list):
            print(f"{i}: ...")
            for j, s in enumerate(f.slots):
                msg = f"Slot {j} : "
                msg += f"{s.x_start}, {s.y_start} -> {s.x_end}, {s.y_end} "
                msg += f"({s.x_diff}, {s.y_diff})"
                print(msg)


w = Worker()
w.main()
