
from ppadb.client import Client as AdbClient



#client = AdbClient(host="127.0.0.1", port=5037)


def init():
    client = AdbClient()
    version = client.version()
    print(f"ADB version is {version}")

    devices = client.devices()
    for device in devices:
        print(f"connected to {device.serial}")

    device = devices[0]    
    # device.shell("input keyevent KEYCODE_POWER")

    def handler(conn):
        i = 0
        while (True):
            recv = conn._recv(1000)
            print('====================')
            print(recv.decode('ascii'))
            i += 1
            if i > 10:
                break

    device.shell("getevent -l", handler)



def main():
    init()


main()

