#!/usr/bin/python3
import time
import serial
from threading import Lock
from cm4.utils.logger import *


class SerialPort():
    def __init__(self, port, baudrate):
        self.temp = 0
        self._serial = None
        self._port = port
        self._baudrate = baudrate
        self.FAILED = -1
        self.SUCCESS = 0
        self.lock = Lock()
        self.logger = Logger(f'SERIALPORT {port}')

        self.logger.info(
            f"Config serial with Port {self._port} - Baudrate {self._baudrate}")
        try:
            self._serial = serial.Serial(self._port, self._baudrate)
        except Exception as e:
            self.logger.error(e)

    def open(self):
        self.logger.info(f"Opening port {self._port}...")
        try:
            if not self._serial.isOpen():
                self._serial.open()
            time.sleep(0.1)
            if self._serial.isOpen():
                self.logger.info(f"Port {self._port} is opened!")
        except:
            self.logger.error(f"Failed to open Serial port {self._port}")

    def close(self):
        self.logger.info(f"Closing port {self._port}")
        try:
            if self._serial.isOpen():
                self._serial.close()
            time.sleep(0.1)
            if not self._serial.isOpen():
                self.logger.info(f"Port {self._port} is closed!")
        except:
            self.logger.error(f"Failed to close Serial port {self._port}")

    def read_sensor(self, data, timeout=1000):
        value = self.FAILED

        if data is None or len(data) == 0:
            self.logger.error("Input data is empty")
            return self.FAILED

        self.logger.info(f"Getting sensor data from port {self._port}...")
        if self._serial != None and self._serial.isOpen():
            self._serial.write(serial.to_bytes(data))
            time.sleep(0.5)
            bytes_to_read = self._serial.inWaiting()
            if bytes_to_read > 0:
                out = self._serial.read(bytes_to_read)
                data_array = [b for b in out]
                if len(data_array) >= 7:
                    array_size = len(data_array)
                    value = data_array[array_size - 4] * \
                        256 + data_array[array_size - 3]
        else:
            self.logger.error(f"Port {self._port} is not opened.")
        return

    def read_distance(self, data, timeout=1000):
        value = 0

        if data is None or len(data) == 0:
            self.logger.error("Input data is empty")
            return self.FAILED

        if self._serial != None and self._serial.isOpen():
            self._serial.write(serial.to_bytes(data))
            time.sleep(0.1)
            bytes_to_read = self._serial.inWaiting()
            if bytes_to_read > 0:
                out = self._serial.read(bytes_to_read)
                data_array = [b for b in out]
                if len(data_array) >= 7:
                    array_size = len(data_array)
                    value = data_array[array_size - 4] * \
                        256 + data_array[array_size - 3]
                    return value/100
        else:
            self.logger.error(f"Port {self._port} is not opened.")
        return self.FAILED

    def control_relay(self, data, timeout=1000):
        if data is None or len(data) == 0:
            self.logger.error("Input data is empty")
            return self.FAILED

        if self._serial != None and self._serial.isOpen():
            with self.lock:
                try:
                    self._serial.write(serial.to_bytes(data))
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"Can not write serial! Error: {e}")

        else:
            self.logger.error(f"Port {self._port} is not opened.")
            return self.FAILED

        return self.SUCCESS

    def read_USB(self):
        parameter = ['#N#', '#P#', '#K#', '#PH#', '#EC#', '#T#', '#M#']
        data = [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
        if self._serial != None and self._serial.isOpen():
            try:
                for x in range(7):
                    self._serial.write(parameter[x].encode())
                    start = time.time()
                    while time.time() - start < 2:
                        bytes_to_read = self._serial.inWaiting()
                        if bytes_to_read > 0:
                            result = self._serial.read_until("\n", bytes_to_read).decode('utf-8')
                            result = result.replace('#', '')
                            self.logger.info(f"Read from esp32_2 with {parameter[x]}: {result}")
                            data[x] = float(result)
                            break
                        # time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Can not write serial! Error: {e}")
                return self.FAILED
            return data
        return self.FAILED
