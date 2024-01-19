from library import Serial, time, np
#import serial.tools.list_ports
#import time
import array
class SerialCom:
    def __init__(self, relayON_array, relayOFF_array,RSPort="/dev/ttyAMA2", UARTPort="/dev/ttyUSB0", Signal_time_delay_ms=120 ):
        self.__RSPort = RSPort
        self.__UARTPort = UARTPort
        self.relay_ON = relayON_array
        self.relay_OFF = relayOFF_array
        self.relay_status_format = [[0, 0, 0, 0, 0,  0,   0,   0],
                     [1, 3, 0, 0, 0, 1, 132, 10],
                     [2, 3, 0, 0, 0, 1, 132, 57],
                     [3, 3, 0, 0, 0, 1, 133, 232],
                     [4, 3, 0, 0, 0, 1, 132, 95],
                     [5, 3, 0, 0, 0, 1, 133, 142],
                     [6, 3, 0, 0, 0, 1, 133, 189],
                     [7, 3, 0, 0, 0, 1, 132, 108],
                     [8, 3, 0, 0, 0, 1, 132, 147]]
        self.relay_status= [
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False  ]
        self.distance_sensors =[[0, 0, 0, 0, 0, 0, 0, 0], #Same ID with relay
                                [9, 3, 0, 5, 0, 1, 149, 67],# Relay ID 1 to have sensor ID 9
                                [10, 3, 0, 5, 0, 1, 149, 112], # Not install 
                                [12, 3, 0, 5, 0, 1, 149, 22]] # Relay ID 3 have sensor ID 12
        
        self.distance_calibration = np.asarray([ 2595, 2591, 2578, 2560, 2543, 2528, 2512, 2495, 2480, 2464, 2447, 2431, 2416, 2399, 2381, 2366, 2351, 2333, 2318,
                                       2301, 2283, 2271, 2255, 2238, 2223, 2194, 2177, 2160, 2144, 2129, 2114, 2099, 2082, 2068, 2054, 2038, 2024, 2010,
                                       1993, 1980, 1965, 1952, 1935, 1920, 1905, 1892, 1877, 1864, 1890, 1834, 1820])
        self.signalTimeDelay = Signal_time_delay_ms
        self.MAX_RELAY_ID = len(self.relay_ON)
        #self.relay_status = [False] * (self.MAX_RELAY_ID)
        self.serUART = UARTPort
        self.serRS = RSPort
        # Reset all relay to OFF state

    def initSerialport(self):
        #initialize serial connection
        try:
            self.serUART = Serial(self.__UARTPort, 115200)
        except:
            return 101
        
        try:
            self.serRS = Serial(self.__RSPort, 9600)
        except:
            return 201
        self.turn_off_all_relay()
        #self.read_status_initial()
        #self.read_status_initial()
        # Log for status Input 
        return 0


    def read_sensor_status(self, relay_ID):
        try:
            #print("Run read sensor status with ID =", relay_ID)
            self.serRS.write(self.relay_status_format[relay_ID])
            time.sleep(100/1000)
            bytesToRead = self.serRS.inWaiting()
            #print("Byte to read :",bytesToRead)
            if bytesToRead > 0:
                out = self.serRS.read(bytesToRead)
                data_array = [b for b in out]
                #print("Data array =",data_array)
                if len(data_array) >= 7:
                    array_size = len(data_array)
                    value = data_array[4]
                    return value
                else:
                    return -1
        except:
            return -1

    def read_status_initial(self):
        status = [0,0,0,0,0,0,0,0]
        for rl_ID in range(1, self.MAX_RELAY_ID):
            time.sleep(100/1000)
            try:
                #print("Run read sensor status with ID =", relay_ID)
                self.serRS.write(self.relay_status_format[rl_ID])
                time.sleep(self.signalTimeDelay/1000)
                bytesToRead = self.serRS.inWaiting()
                #print("Byte to read :",bytesToRead)
                if bytesToRead > 0:
                    out = self.serRS.read(bytesToRead)
                    data_array = [b for b in out]
                    #print("Data array =",data_array, len(data_array))
                    if len(data_array) >= 7:
                        array_size = len(data_array)
                        value = data_array[4]
                        if value == 255:
                            status[rl_ID-1] = 1
                        elif value == 0:
                            status[rl_ID-1] = 0
                else:
                    #print("Relay problem is ID", rl_ID)
                    status[rl_ID-1] = -1
                #print(status[rl_ID-1])        
            except:
                status[rl_ID-1] = -1
        return status

    def turn_on_one_relay(self, relay_ID):
        if self.relay_status[relay_ID] is False:
            self.serRS.write(self.relay_ON[relay_ID])
            print(f"{relay_ID}-ON")
            self.relay_status[relay_ID] = True

            time.sleep(self.signalTimeDelay/1000)
            self.serial_read_data() # Clear buffer


    def turn_off_one_relay(self, relay_ID):
        if self.relay_status[relay_ID] is True:
            self.serRS.write(self.relay_OFF[relay_ID])
            print(f"{relay_ID}-OFF")
            self.relay_status[relay_ID] = False
            time.sleep(self.signalTimeDelay/1000)
            self.serial_read_data() # Clear buffer 


    
    def turn_on_all_relay(self):
        for ID in range(1,self.MAX_RELAY_ID):
            self.serRS.write(self.relay_ON[ID])
            print(f"{ID}-ON-ALL")
            self.relay_status[ID] = True
            time.sleep(self.signalTimeDelay/1000)
            self.serial_read_data()# Clear buffer 



    def turn_off_all_relay(self):
        for ID in range(1,self.MAX_RELAY_ID):
            self.serRS.write(self.relay_OFF[ID])
            print(f"{ID}-OFF-ALL")
            self.relay_status[ID] = False
            time.sleep(self.signalTimeDelay/1000)
            self.serial_read_data()# Clear buffer 
   
    
    def serial_read_data(self):                                                                                                                                         
        bytesToRead = self.serRS.inWaiting()
        if bytesToRead > 0:
            out = self.serRS.read(bytesToRead)
            data_array = [b for b in out]                                                                                                                              
            #print(data_array)                                                                                                                                         
            if len(data_array) >= 7:                                                                                                                                
                array_size = len(data_array)                                                                                                                           
                value = data_array[array_size - 4] * 256 + data_array[array_size - 3]                                                                                  
                return value                                                                                                                                           
            else:                                                                                                                                                      
                return -1                                                                                                                                              
        return 0


    def readDistance(self, ID):
        self.serRS.write(self.distance_sensors[ID])
        time.sleep(self.signalTimeDelay/1000)
        bytesToRead = self.serRS.inWaiting()
        if bytesToRead > 0:
            out = self.serRS.read(bytesToRead)
            data_array = [b for b in out]
            if len(data_array) >= 7:
                array_size = len(data_array)
                current_distance = data_array[array_size - 4] * 256 + data_array[array_size - 3]
                return current_distance
            else:
                return -1
        else:
            return 0


    def readSensorData(self, attribute):
        """
            cmdType from 0-7:
                1: read N
                2: read P
                3: read K
                4: read soil Temperature
                5: read soil moisture 
                6: read PH
                7: read EC
                
        """
        start = time.time()
        if attribute == '1':
            self.serUART.write(f"#N#".encode())
        elif attribute == '2':
            self.serUART.write(f"#P#".encode())
        elif attribute == '3':
            self.serUART.write(f"#K#".encode())
        elif attribute == '4':
            self.serUART.write(f"#T#".encode())
        elif attribute == '5':
            self.serUART.write(f"#M#".encode())
        elif attribute == '6':
            self.serUART.write(f"#PH#".encode())
        elif attribute == '7':
            self.serUART.write(f"#EC#".encode())
        else:
            return -4

        while time.time() - start <=6:
            try:
                bytesToRead = self.serUART.inWaiting()
                if bytesToRead > 0:
                    output = self.serUART.read(bytesToRead)
                    output = output.decode("utf-8")
                    start = output.find('#')
                    end = output.rfind('#')
                    if start != -1 and end!= -1:
                       print(f"read from esp32 attribute {attribute}: {output}")
                       output = output[start+1:end]
                       time.sleep(self.signalTimeDelay/1000)
                       return float(output)
                    else:
                       return -6
            except:
                continue
        return -5


if __name__ == "__main__":
    relayON_array = [[0, 0, 0, 0, 0,   0,   0,   0],
                     [1, 6, 0, 0, 0, 255, 201, 138],
                     [2, 6, 0, 0, 0, 255, 201, 185],
                     [3, 6, 0, 0, 0, 255, 200, 104],
                     [4, 6, 0, 0, 0, 255, 201, 223],
                     [5, 6, 0, 0, 0, 255, 200,  14],
                     [6, 6, 0, 0, 0, 255, 200,  61]]

    relayOFF_array = [[0, 0, 0, 0, 0,  0,   0,   0],
                      [1, 6, 0, 0, 0,  0, 137, 202],
                      [2, 6, 0, 0, 0,  0, 137, 249],
                      [3, 6, 0, 0, 0,  0, 136,  40],
                      [4, 6, 0, 0, 0,  0, 137, 159],
                      [5, 6, 0, 0, 0,  0, 136,  78],
                      [6, 6, 0, 0, 0,  0, 136, 125]]

    ser = SerialCom(relayON_array, relayOFF_array)
    ser.initSerialport()
    # start = time.monotonic()
    # print("start ",start)
    # while time.monotonic() - start < 4:
    #     pass
    # print(time.monotonic())
    # start = time.monotonic()
    # print("start ",start)
