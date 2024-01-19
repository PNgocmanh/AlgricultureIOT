from library import sched, time, datetime
from system import AgriSystem

class AgriScheduler:
    def __init__(self, mqtt_broker, mqtt_username, mqtt_password, mqtt_topic, relay_on_array, relay_off_array, detectlist,modelPath):
        self.scheduler = sched.scheduler(timefunc=time.time, delayfunc=time.sleep)
        self.agri_system =AgriSystem(mqtt_broker, mqtt_username, mqtt_password, mqtt_topic, relay_on_array, relay_off_array, detectlist, modelPath)


    def __tokenize_command(self, command = ""):
        buffer_cmd = command
        command = command.replace('#','')
        cmd_elements = command.split(':')
        return cmd_elements, buffer_cmd
    

    def __search_RS485_task_and_delete(self, RS485_ID, cmd_opt):
        for task in self.scheduler.queue:
            if task.argument[0] == RS485_ID:
                if cmd_opt == 0 and ("turn_on_relay_0" in str(task.action) 
                                     or "turn_off_relay_0" in str(task.action)): 
                    self.cancel_task(task)
                elif cmd_opt == 1 and ("turn_on_relay_0" in str(task.action) 
                                     or "turn_off_relay_0" in str(task.action)):
                    self.cancel_task(task)
                elif cmd_opt == 2 and ("turn_on_relay_2" in str(task.action) 
                                     or "turn_off_relay_2" in str(task.action)):
                    self.cancel_task(task)
                self.agri_system.turn_off_relay_0(RS485_ID)


    def __search_AI_task_and_delete(self):
        for task in self.scheduler.queue:
            if ("run_AI" in str(task.action)) or ("run_AI_for_duration_and_repeat" in str(task.action)):
                self.cancel_task(task)
        print("DELETE AI TASKS IN SCHEDULER QUEUE")


    def __search_sensor_task_and_delete(self):
        for task in self.scheduler.queue:
            if ("readSensor_at_PresetTime" in str(task.action)) or ("readSensor_at_PresetTime_and_repeat" in str(task.action)):
                self.cancel_task(task)
        print("DELETE SENSOR TASKS IN SCHEDULER QUEUE")


    def __prepare_sensor_task_arguments(self, command):
        attributes = command[1]
        preset_time = self.agri_system.convert_datetime_to_sec(time_string=command[2])
        if preset_time == -1:
            return None 
        task_priority = 1
        task_args = ()
        task_routine_time = command[3]
        return_args = None
        if attributes == "0":
            self.__search_sensor_task_and_delete() # delete task in scheduler queue
            task_function = self.agri_system.stop_reading_sensor
            return_args = [[preset_time, 0, task_function, task_args]]
        else: 
            if task_routine_time == "":
                task_args = (attributes, )
                task_function = self.agri_system.readSensor_at_PresetTime
                return_args = [[preset_time, task_priority, task_function, task_args]]
            else:
                task_args = (attributes, preset_time, task_routine_time, )
                task_function = self.agri_system.readSensor_at_PresetTime_and_repeat
                return_args = [[preset_time, task_priority, task_function, task_args]]
        
        return return_args


    def __prepare_relay_task_arguments(self, command):
        relay_ID =int(command[1]) if command[1] != "" else 0
        cmd_opt = int(command[3]) if command[3] != "" else None
        preset_time = self.agri_system.convert_datetime_to_sec(time_string=command[4])
        if preset_time == -1:
            return None
        task_duration = command[5]
        task_priority = 0
        task_args = ()
        task_routine_time = command[6]
        return_args = None

        """ if relay_ID == 0 => control all relays
            if relay ID == (1,6) => control individual relay respect to user's condition (cmd_opt)       
                -cmd_opt = 0: turn ON/OFF relay at presest time and done
                -cmd_opt = 1: turn ON/OFF relay at preset time(empty mean turn on immediately) and  work in DURATION and NO REPEAT
                -cmd_opt = 2: task have DURATION to complete and repeat multple time (secondly, minutely, hourly, daily, weekly, monthly)
                *Note: for all cmd_opt if command[2] == 0 will cancel all that option task in waiting queue of that relay.
            
        """
        # control all relays
        if relay_ID == 0:
            if cmd_opt == 3:
                self.agri_system.update_relays_status()
            else:
                # reset all relay
                task_function = self.agri_system.turn_on_all_relay if int(command[2]) == 1 else self.agri_system.turn_off_all_relay         
                return_args = [[preset_time, task_priority, task_function, task_args]]
        # control delay individually
        else:
            if int(command[2]) == 1:
                if cmd_opt == 0:
                    task_args = (relay_ID,)
                    # Choose ON/OFF function
                    task_function = self.agri_system.turn_on_relay_0
                    return_args = [[preset_time, task_priority, task_function, task_args]]
                elif cmd_opt == 1:
                    return_args = self.agri_system.operate_relay_for_duration_at_presetTime(relay_ID, preset_time, task_duration)
                elif cmd_opt == 2:
                        return_args = self.agri_system.operate_relay_for_duration_at_presetTime_and_repeat(relay_ID, preset_time, 
                                                                                                           task_duration, 
                                                                                                          task_routine_time)
            else:
                if cmd_opt == 0:
                    task_args = (relay_ID,)
                    task_function = self.agri_system.turn_off_relay_0
                    return_args = [[preset_time, task_priority, task_function, task_args]]
                else:
                    self.__search_RS485_task_and_delete(relay_ID, cmd_opt)
        return return_args
    

    def __prepare_AI_task_arguments(self, command, command_str):
        cam_URL = command[1]
        cmd_opt = int(command[3]) if command[3] != "" else None
        preset_time = self.agri_system.convert_datetime_to_sec(time_string=command[4])
        if preset_time == -1:
            return None
        # operating_duration = self.agri_system.convert_time_to_second(command[5])
        # if operating_duration == -1:
        #     return None
        task_priority = 1
        task_args = ()
        task_routine_time = command[6]
        return_args = None
        """ choose method to run AI model to detect disease base on cmd_opt
                -cmd_opt = 0: run AI at preset time for duration(default = 120s)
                -cmd_opt = 1: run AI at preset time for duration and repeat (DURATION, ROUTINE is empty)
                *Note: command[2] == 0 will cancel all AI schedule of that option
        """
        if int(command[2]) == 1:
            if cmd_opt == 0:
                #buffer = ":".join(sensors_data)
                task_args = (cam_URL, command_str, "",)
                task_function = self.agri_system.run_AI
                return_args = [[preset_time, task_priority, task_function, task_args]]
            elif cmd_opt == 1:
                return_args = self.agri_system.run_AI_for_duration_and_repeat(cam_URL, preset_time, 
                                                                              command[5], task_routine_time)
        else:
            self.__search_AI_task_and_delete() # delete task in scheduler queue
            task_function = self.agri_system.stop_AI
            return_args = [[preset_time, 0, task_function, task_args]]
        return return_args


    def __prepare_status_task_arguments(self, command):
            relay_ID =int(command[1]) if command[1] != "" else 0
            #cmd_opt = int(command[3]) if command[3] != "" else None
            preset_time = self.agri_system.convert_datetime_to_sec(time_string=command[4])
            if preset_time == -1:
                return None
            task_duration = command[5]
            task_priority = 0
            task_args = ()
            task_routine_time = command[6]
            return_args = None

            """ if relay_ID == 0 => check status all relays 
                if relay ID == (1,8) => check status of relay ID (cmd_opt)       
                if relay ID == 9 or 12 => send water volume at the moment
                    
            """
            # control all relays
            if relay_ID == 0:
                if cmd_opt == 3:
                    self.agri_system.update_relays_status()
                else:
                    # reset all relay
                    task_function = self.agri_system.turn_on_all_relay if int(command[2]) == 1 else self.agri_system.turn_off_all_relay         
                    return_args = [[preset_time, task_priority, task_function, task_args]]
            # control delay individually
            else:
                if int(command[2]) == 1:
                    if cmd_opt == 0:
                        task_args = (relay_ID,)
                        # Choose ON/OFF function
                        task_function = self.agri_system.turn_on_relay_0
                        return_args = [[preset_time, task_priority, task_function, task_args]]
                    elif cmd_opt == 1:
                        return_args = self.agri_system.operate_relay_for_duration_at_presetTime(relay_ID, preset_time, task_duration)
                    elif cmd_opt == 2:
                            return_args = self.agri_system.operate_relay_for_duration_at_presetTime_and_repeat(relay_ID, preset_time, 
                                                                                                            task_duration, 
                                                                                                            task_routine_time)
                else:
                    if cmd_opt == 0:
                        task_args = (relay_ID,)
                        task_function = self.agri_system.turn_off_relay_0
                        return_args = [[preset_time, task_priority, task_function, task_args]]
                    else:
                        self.__search_RS485_task_and_delete(relay_ID, cmd_opt)
            return return_args

    def add_task(self, args):
        for arg in args:
            self.scheduler.enterabs(time=arg[0], priority=arg[1], action=arg[2], argument=arg[3])                


    def cancel_task(self, task):
        self.scheduler.cancel(task)


    def __categorize_command(self, command, command_str):
        cmd_type = command[0]
        """
            command have 3 type:
                1: sensor command
                2: relay command
                3: AI command
                4: status command
        """
        if cmd_type not in set(("0", "1", "2", "3","4")):
            print("INVALID COMMAND")
            return None

        if cmd_type == "0":
            self.agri_system.replace_AI_detectList(command[1])
        elif cmd_type == "1":
            # sensor task
            task_args = self.__prepare_sensor_task_arguments(command)
        elif cmd_type == "2":
            # relay task
            task_args = self.__prepare_relay_task_arguments(command)
        elif cmd_type == "3":
            # AI task 
            task_args = self.__prepare_AI_task_arguments(command, command_str)
        elif cmd_type == "4":
            # AI task 
            task_args = self.__prepare_status_task_arguments(command)
        else:
            # other configuration
            pass
        return task_args
  

    def run_scheduler(self):
        while True:
            # check if receive any mqtt command from server
            # then categorize and add task to queue and execute 
            if self.agri_system.empty() is False:
                command, command_str = self.__tokenize_command(self.agri_system.get_command())
                task_args = self.__categorize_command(command, command_str)
                if task_args != None:
                    self.add_task(args=task_args)
            if len(self.scheduler.queue) > 0:
                #task_funct_string = str(task_args[2])
                # AI will have a seperate thread due o it long execute run
                #print("scheduler queue before execute ", len(self.scheduler.queue))
                start = time.time()
                self.scheduler.run(blocking=False)
                print("burst time is: ",time.time()-start)
                #print("scheduler queue after ", len(self.scheduler.queue))
            

 
if __name__ == "__main__":
    relay_ON = [[0, 0, 0, 0, 0, 0, 0, 0],
                [1, 6, 0, 0, 0, 255, 201, 138],
                [2, 6, 0, 0, 0, 255, 201, 185],
                [3, 6, 0, 0, 0, 255, 200, 104],
                [4, 6, 0, 0, 0, 255, 201, 223],
                [5, 6, 0, 0, 0, 255, 200, 14],
                [6, 6, 0, 0, 0, 255, 200, 61],
                [7, 6, 0, 0, 0, 255, 201, 236],
                [8, 6, 0, 0, 0, 255, 201, 19]]

    relay_OFF = [[0, 0, 0, 0, 0, 0, 0, 0],
                 [1, 6, 0, 0, 0, 0, 137, 202],
                 [2, 6, 0, 0, 0, 0, 137, 249],
                 [3, 6, 0, 0, 0, 0, 136, 40],
                 [4, 6, 0, 0, 0, 0, 137, 159],
                 [5, 6, 0, 0, 0, 0, 136, 78],
                 [6, 6, 0, 0, 0, 0, 136, 125],
                 [7, 6, 0, 0, 0, 0, 137, 172],
                 [8, 6, 0, 0, 0, 0, 137, 83]]
    mqtt_broker = "io.adafruit.com"
    mqtt_username = "Thesis_SmartAgri"
    mqtt_password = "aio_HQLV330frfpmBwzKI76YlI0Z1DYh"
    # mqtt_broker = "broker1.hcmut.org"
    # mqtt_username = "vatserver"
    # mqtt_password = "vatserver123"
    mqtt_topic = ["message", "temperature", "relay-1", "relay-2", "relay-3", "relay-4", "relay-5", "relay-6", "relay-7", "relay-8", "error", "ai", "ai-img"]
    #detectList = ["healthy leaf", "wilting leaf","leaf spot","unhealthy leaf", "sick leaf"]
    detectList = ["healthy leaf", "unhealthy leaf"]
    #modelPath = "D:\SUBJECTS\Thesis\CLIP\clip\ViT-B-32.pt"
    modelPath = "opt"
    S = AgriScheduler(mqtt_broker,mqtt_username,mqtt_password,mqtt_topic, relay_ON, relay_OFF, detectList, modelPath )
    S.run_scheduler()