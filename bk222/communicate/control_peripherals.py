from bk222.communicate.SerialCommunicate import SerialPort
from bk222.communicate import SubFunctions as comFuncs

port = comFuncs.find_serial_port()
baudrate = comFuncs.find_serial_baudrate()
port_USB = comFuncs.find_serial_port_USB()
baudrate_USB = comFuncs.find_serial_baudrate_USB()
print("Find port {} - baudrate {}".format(port, baudrate))
print("Find port {} - baudrate {}".format(port_USB, baudrate_USB))
serial = SerialPort(port=port, baudrate=baudrate)
serial_USB = SerialPort(port=port_USB, baudrate=baudrate_USB)
serial.open()
serial_USB.open()

def readUSB():
    result = serial_USB.read_USB()
    return result

def readDistance(relay):
    sensor_distance = {
        'relay1': [0x09, 0x03, 0x00, 0x05, 0x00, 0x01, 149, 67],
        'relay2': [],
        'relay3': [0x0C, 0x03, 0x00, 0x05, 0x00, 0x01, 149, 22],
        'pump': [],
    }
    result = serial.read_distance(sensor_distance[relay])
    return result

def relay_1(state):
    relay1_ON = [1, 6, 0, 0, 0, 255, 200, 205]
    relay1_OFF = [1, 6, 0, 0, 0, 0, 200, 205]
    if state:
        return serial.control_relay(relay1_ON)
    else:
        return serial.control_relay(relay1_OFF)

def relay_2(state):
    relay2_ON = [2, 6, 0, 0, 0, 255, 200, 164]
    relay2_OFF = [2, 6, 0, 0, 0, 0, 136, 228]
    if state:
        return serial.control_relay(relay2_ON)
    else:
        return serial.control_relay(relay2_OFF)

def relay_3(state):
    relay3_ON = [3, 6, 0, 0, 0, 255, 200, 205]
    relay3_OFF = [3, 6, 0, 0, 0, 0, 200, 205]
    if state:
        return serial.control_relay(relay3_ON)
    else:
        return serial.control_relay(relay3_OFF)

def relay_4(state):
    relay4_ON = [4, 6, 0, 0, 0, 255, 200, 205]
    relay4_OFF = [4, 6, 0, 0, 0, 0, 200, 205]
    if state:
        return serial.control_relay(relay4_ON)
    else:
        return serial.control_relay(relay4_OFF)

def relay_5(state):
    relay5_ON = [5, 6, 0, 0, 0, 255, 200, 205]
    relay5_OFF = [5, 6, 0, 0, 0, 0, 200, 205]

    if state:
        return serial.control_relay(relay5_ON)
    else:
        return serial.control_relay(relay5_OFF)

def relay_6(state):
    relay6_ON = [6, 6, 0, 0, 0, 255, 200, 205]
    relay6_OFF = [6, 6, 0, 0, 0, 0, 200, 205]

    if state:
        return serial.control_relay(relay6_ON)
    else:
        return serial.control_relay(relay6_OFF)

def relay_7(state):
    relay7_ON = [7, 6, 0, 0, 0, 255, 200, 205]
    relay7_OFF = [7, 6, 0, 0, 0, 0, 200, 205]

    if state:
        return serial.control_relay(relay7_ON)
    else:
        return serial.control_relay(relay7_OFF)
    
def relay_8(state):
    relay8_ON = [8, 6, 0, 0, 0, 255, 200, 205]
    relay8_OFF = [8, 6, 0, 0, 0, 0, 200, 205]

    if state:
        return serial.control_relay(relay8_ON)
    else:
        return serial.control_relay(relay8_OFF)

def get_relay(relay):
    _name = {
        'relay1': relay_1,
        'relay2': relay_2,
        'relay3': relay_3,
        'relay4': relay_4,
        'relay5': relay_5,
        'relay6': relay_6,
        'relay7': relay_7,
        'relay8': relay_8,
        'readUSB': readUSB,
        'readDistance': readDistance,
    }
    return _name[relay]