#import datetime
#from dateutil.relativedelta import relativedelta
#test commit
from library import time, datetime, np
from IoT import SerialCom
from client_mqtt import MQTTClient
from AI import AI
from library import relativedelta

relayON_array =     [[0, 0, 0, 0, 0, 0, 0, 0],
                    [1, 6, 0, 0, 0, 255, 201, 138],
                    [2, 6, 0, 0, 0, 255, 201, 185],
                    [3, 6, 0, 0, 0, 255, 200, 104],
                    [4, 6, 0, 0, 0, 255, 201, 223],
                    [5, 6, 0, 0, 0, 255, 200,  14],
                    [6, 6, 0, 0, 0, 255, 200,  61]]

relayOFF_array =    [[0, 0, 0, 0, 0, 0, 0, 0],
                    [1, 6, 0, 0, 0,  0, 137, 202],
                    [2, 6, 0, 0, 0,  0, 137, 249],
                    [3, 6, 0, 0, 0,  0, 136,  40],
                    [4, 6, 0, 0, 0,  0, 137, 159],
                    [5, 6, 0, 0, 0,  0, 136,  78],
                    [6, 6, 0, 0, 0,  0, 136, 125]]

relaySTATUS_array = [[0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 3, 0, 0, 0, 1, 132, 10],
                     [2, 3, 0, 0, 0, 1, 132, 57],
                     [3, 3, 0, 0, 0, 1, 133, 232],
                     [4, 3, 0, 0, 0, 1, 132, 95],
                     [5, 3, 0, 0, 0, 1, 133, 142],
                     [6, 3, 0, 0, 0, 1, 133, 189],
                     [7, 3, 0, 0, 0, 1, 132, 108],
                     [8, 3, 0, 0, 0, 1, 132, 147]]
class AgriSystem:
    def __init__(self, mqtt_broker, mqtt_username, mqtt_password, mqtt_topic, relay_on_array, relay_off_array, detectList, modelPath):
        self.__distance_calibration = np.asarray([ 2595, 2591, 2578, 2560, 2543, 2528, 2512, 2495, 2480, 2464, 2447, 2431, 2416, 2399, 2381, 2366, 2351, 2333, 2318,
                                       2301, 2283, 2271, 2255, 2238, 2223, 2194, 2177, 2160, 2144, 2129, 2114, 2099, 2082, 2068, 2054, 2038, 2024, 2010,
                                       1993, 1980, 1965, 1952, 1935, 1920, 1905, 1892, 1877, 1864, 1890, 1834, 1820])
        self.serial = SerialCom(relay_on_array, relay_off_array)
        self.mqttClient = MQTTClient(Broker=mqtt_broker, Username=mqtt_username, Password=mqtt_password,Topics=mqtt_topic)
        self.AI = AI( detectList, modelPath)
        ret = self.serial.initSerialport()
        if ret != 0:
            self.mqttClient.publish("error", ret)
        if self.AI.choose_and_load_model() == -1:
            self.mqttClient.publish("error", 301)
    
    """ GENERAL SUPPORT FUNCTIONS """
    def replace_AI_detectList(self, labelList):
        self.AI.replace_detectList(labelList.split(","))

    def add_command(self,command):
        self.mqttClient.add_command(command)
    
    def get_command(self):
        return self.mqttClient.get_command()
    
    def empty(self):
        return self.mqttClient.empty()

    def convert_datetime_to_sec(self,time_string = ""):
        try:
            if time_string == "" or time_string == "-----" or time_string == None:
                return datetime.datetime.now().timestamp()
            # "year-month-day-hour-minute-second"
            time_array = time_string.split('-')
            year,month,day,hour,minute,second = [int(i) for i in time_array]     
            event_time = datetime.datetime(year,month,day,hour,minute,second)
            return event_time.timestamp()
        except:
            print("ERROR WITH DATETIME IN COMMAND")
            return -1

    def convert_time_to_second(self, time_string = ""):
        try:
            # no delay
            if time_string == "":
                return 0
            timeDelay, timeUnit = time_string.split('-')
            timeDelay = int(timeDelay)
            # delay by seconds 
            if timeUnit in set(('s','S')):
                return timeDelay      
            # delay by minutes
            elif timeUnit in set(('m','M')):
                return timeDelay * 60
            # delay by hour
            elif timeUnit in set(('h','H')):
                return timeDelay * 3600
            # delay by days
            elif timeUnit in set(("ml","ML")):
                return timeDelay
            else:
                print("not support longer operation time")
                pass
        except:
            print("ERROR WITH TIME IN COMMAND")
            return -1

    def calculte_task_repeat_time(self, task_routine_time: str, date: datetime):
        routine_time, routine_type = task_routine_time.split('-')
        routine_time = int(routine_time)
        
        if routine_type in set(("s","S")):
            date = date + datetime.timedelta(seconds=routine_time)
        elif routine_type in set(("m","M")):
            date = date + datetime.timedelta(minutes=routine_time)
        elif routine_type in set(("h","H")):
            date = date + datetime.timedelta(hours=routine_time)
        elif routine_type in set(("d","D")):
            date = date + datetime.timedelta(days=routine_time)
        elif routine_type in set(("w","W")):
            date = date + datetime.timedelta(weeks=routine_time)
        elif routine_type in set(("mo","MO","Mo","mO")):
            date = date + relativedelta(months=routine_time)
        
        return date.strftime("%Y-%m-%d-%H-%M-%S")


    """ BELOW ARE FUNCTIONS TO READ SENSORS """

    def readSensor_at_PresetTime(self, attributes = "", command = ""):
        if attributes != "":
            # check if there are repeat command
            if command != "":
                self.add_command(command)
            sensors_data = [""] * 7
            attributes = attributes.split(",")
            for ele in attributes:
                res = self.serial.readSensorData(ele)
                if res < 0:
                    self.mqttClient.publish("error",-res + 100)
                    self.add_command(f"#1:{ele}::#")
                    continue
                try:
                    index = int(ele) - 1
                    sensors_data[index] = str(res)
                except:
                    continue
            
            # form a string: nito:photpho:kali:temperature:moisture:ph:ec
            buffer = ":".join(sensors_data)
            self.mqttClient.publish("sensors", buffer)
        else:
            self.mqttClient.publish("error", 103) # no attribute to read


    def stop_reading_sensor(self):
        self.mqttClient.rm_specific_command("#1:")
    

    def readSensor_at_PresetTime_and_repeat(self, attributes, preset_time, repeat_time_str):
        # calculate preset time of next reading task
        preset_time_date_format = datetime.datetime.fromtimestamp(preset_time)
        repeat_preset_time = self.calculte_task_repeat_time(repeat_time_str, preset_time_date_format)
        command = f"#1:{attributes}:{repeat_preset_time}:{repeat_time_str}#"

        self.readSensor_at_PresetTime(attributes, command)

    

    """ BELOW ARE FUNCTIONS TO CONTROL RELAYS """
    def turn_on_all_relay(self):
        self.serial.turn_on_all_relay()
        for ID in range(1, self.serial.MAX_RELAY_ID):
            self.mqttClient.publish(f"relay-{ID}",self.serial.relay_status[ID])
            

    def turn_off_all_relay(self):
        self.serial.turn_off_all_relay()
        for ID in range(1, self.serial.MAX_RELAY_ID):
            self.mqttClient.publish(f"relay-{ID}",self.serial.relay_status[ID])


    def turn_on_relay_0(self, relay_ID=None):
        if relay_ID != None:
            self.serial.turn_on_one_relay(relay_ID)
            self.mqttClient.publish(f"relay-{relay_ID}",self.serial.relay_status[relay_ID])


    def turn_off_relay_0(self, relay_ID=None):
        if relay_ID != None:
            self.serial.turn_off_one_relay(relay_ID)
            self.mqttClient.publish(f"relay-{relay_ID}",self.serial.relay_status[relay_ID])


    def turn_on_relay_2(self, relay_ID, command):
        if relay_ID != None:
            self.serial.turn_on_one_relay(relay_ID)
            self.mqttClient.publish(f"relay-{relay_ID}",self.serial.relay_status[relay_ID])
            self.add_command(command)


    def turn_off_relay_2(self, relay_ID):
        if relay_ID != None:
            self.serial.turn_off_one_relay(relay_ID)
            self.mqttClient.publish(f"relay-{relay_ID}",self.serial.relay_status[relay_ID])


    def pour_liquid(self,relay_ID, volume):
        # convert volume to water level
        volume_level = round(volume/100)

        # find current distance of water
        current_distance = self.serial.readDistance(relay_ID)
        print("First current_distance =", current_distance )
        # find closest water level of current distace
        current_volume_level = (np.abs(self.serial.distance_calibration - current_distance)).argmin()
        print("current level", current_volume_level)
        # calculate expect next water level after pour down
        next_volume_level = current_volume_level - volume_level
        print("next volume level: ", next_volume_level)
        if next_volume_level < 0:
            next_volume_level = 0
        next_distance = self.serial.distance_calibration[next_volume_level]
        print("next distance: ", next_distance)
        self.turn_on_relay_0(relay_ID)
        while True:
            current_distance = self.serial.readDistance(relay_ID)
            print("current_distance =", current_distance )
            if current_distance >= next_distance:
                self.turn_off_relay_0(relay_ID)
                break


    def operate_relay_for_duration_at_presetTime(self, relay_ID , preset_time, task_duration_str):
        task_duration = self.convert_time_to_second(task_duration_str)
        if task_duration == -1:
            return None
        
        if relay_ID in set((1,2,3)):
            task_args = (relay_ID, task_duration,)
            task_function = self.pour_liquid
            return [[preset_time, 0, task_function, task_args]]
        else:
            task_args = (relay_ID,)
            task_function_1 = self.turn_on_relay_0
            expect_complete_time = preset_time + task_duration
            #self.agri_system.mqttClient.add_command(f"#2:{relay_ID}:0:1:{complete_time}::#")

            task_function_2 = self.turn_off_relay_0

            return [[preset_time, 0, task_function_1, task_args],
                    [expect_complete_time, 0, task_function_2, task_args]]

    
    def operate_relay_for_duration_at_presetTime_and_repeat(self,relay_ID, preset_time, task_duration_str, repeat_time_str):
        #self.set_relay_repeat_flag(relay_ID, True)

        # calcute preset time of task's repeat
        task_duration = self.convert_time_to_second(task_duration_str)
        if task_duration == -1:
           return None
        preset_time_date_format = datetime.datetime.fromtimestamp(preset_time)
        repeat_preset_time = self.calculte_task_repeat_time(repeat_time_str, preset_time_date_format)
        # command to repeat task
        repeat_task_command = f"#2:{relay_ID}:1:2:{repeat_preset_time}:{task_duration_str}:{repeat_time_str}#"
        print(repeat_task_command)

        # argument of task turn on relay
        task_args_1 = (relay_ID, repeat_task_command,)
        task_function_1 = self.turn_on_relay_2
        
        # argument of task turn off relay
        task_args_2 = (relay_ID,)
        task_function_2 = self.turn_off_relay_2
        expect_complete_time = preset_time + task_duration

        return_args = [[preset_time, 0, task_function_1, task_args_1],
                        [expect_complete_time, 0, task_function_2, task_args_2]]
        return return_args  


    """ BELOW ARE FUNCTIONS TO CONTROL AI """
    def run_AI(self, URL, run_duration, repeat_command = ""):
        res = self.AI.run_AI_model_for_duration(URL, run_duration)

        # check if there is error when operate AI, publish to feed error
        if len(res) == 1:
            if res[0] == 1:
                self.mqttClient.publish("ai", "0:0")
            else:
                # update error code to error feed
                self.mqttClient.publish("error", -res[0] + 300)
        else:       
            if len(res) == 2:
                error_code, remain_duration_time = res
                remain_duration_time = round(remain_duration_time)
                self.mqttClient.publish("error", -error_code + 300)
            else:
                disease, percentage, remain_duration_time = res
                data = f"{disease}:{percentage}"
                self.mqttClient.publish("ai", data)

                # calculate shooting time for next frame and add AI command
                # if the AI operate is complete, check if AI operation has to repeat, add repeat command  
                remain_duration_time = round(remain_duration_time)

            if remain_duration_time > 0 and self.AI.stopFlag_val() == False:
                next_shoot_command = f"#3:{URL}:1:0::{remain_duration_time}-s:#"
                #print("next_shoot_command: ", next_shoot_command)
                self.add_command(next_shoot_command)
            else:
                if repeat_command != "":
                    self.add_command(repeat_command)
                else:
                    return


    def run_AI_for_duration_and_repeat(self, URL, preset_time, AI_run_duration_str, repeat_time_str):
        # calculate preset time of task's repeat
        if AI_run_duration_str != "":
            AI_duration = self.convert_time_to_second(AI_run_duration_str)
            if AI_duration == -1:
                return None
        else:
            AI_duration = 120

        preset_time_date_format = datetime.datetime.fromtimestamp(preset_time)
        repeat_preset_time = self.calculte_task_repeat_time(repeat_time_str, preset_time_date_format)
        # add command to repeat AI
        repeat_task_command = f"#3:{URL}:1:0:{repeat_preset_time}:{AI_run_duration_str}:{repeat_time_str}#"
        print("next AI cmd: ",repeat_task_command)
        # argument of task turn on relay
        task_args = (URL, AI_duration, repeat_task_command,)
        task_function = self.run_AI

        return_args = [[preset_time, 1, task_function, task_args]]
        return return_args

    
    def stop_AI(self):
        self.mqttClient.rm_specific_command("#3:")
        self.AI.set_stopFlag(True)
        self.add_command("3:URL:1:0:::#")