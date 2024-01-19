#import IoT as basicFunct 
import paho.mqtt.client as mqtt
import time
class MQTTClient:
    def __init__(self, Broker, Username, Password, Topics):
        self.__broker = Broker
        #self.__topics = Topics
        self.__command_array = []
        self.__username = Username
        # initialize mqtt client connection
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect

        self.client.username_pw_set(Username, Password)
        self.connect()
        self.client.loop_start()
        
    def connect(self):
        self.client.connect(self.__broker, port=1883)
        print(f"CONNECTED TO {self.__broker}")

    def publish(self, topic, payload, qos=0, retain=False):
        self.client.publish(f"{self.__username}/feeds/{topic}", payload, qos, retain)
        print(f"\nSEND {payload} -TO- {topic}\n")

    def on_connect(self, client, userdata, flags, rc):
        # handle connection logic here
        if rc == 0:
            if self.__broker == "io.adafruit.com": 
                self.client.subscribe(f"{self.__username}/feeds/message",qos=0)
                #self.client.subscribe(f"{self.__username}/feeds/relay-2",qos=0)
            elif self.__broker == "broker1.hcmut.org":
                self.client.subscribe(f"/bkiot/QThai/message", qos=0)
        else:
            print("COULDN'T SUBSCRIBE TO FEED message")
            
    
    def on_message(self, client, userdata, message):
        print(f"Received message on topic {message.topic}: {message.payload.decode()}")
        self.add_command(message.payload.decode())

    def add_command(self,command):
        self.__command_array.append(command)
    
    def rm_specific_command(self, phrase):
        queue_len = self.get_cmd_queue_len()
        if queue_len <= 0:
            return
        
        for idx in range(0,queue_len):
            if phrase in self.__command_array[idx]:
                self.__command_array.pop(idx)
        print("DELETE IN COMMAND QUEUE")

    def get_command(self):
        return self.__command_array.pop(0)
    
    def get_cmd_queue_len(self):
        return len(self.__command_array)

    def empty(self):
        return True if len(self.__command_array) == 0 else False

    def disconnect(self):
        self.client.disconnect()


    
# Connect to MQTT broker
if __name__ == "__main__":
    mqtt_broker = "io.adafruit.com"
    #mqtt_broker = "broker1.hcmut.org"
    mqtt_username = "Thesis_SmartAgri"
    mqtt_password = "aio_HQLV330frfpmBwzKI76YlI0Z1DYh"
    mqtt_topic = ["moisture", "temperature", "relay-1","relay-2","ai","ai-img"]
    client = MQTTClient(Broker=mqtt_broker, Username=mqtt_username, Password=mqtt_password,Topics=mqtt_topic)
    
    while True:
        client.publish("moisture",10)
        client.publish("temperature",20)
        time.sleep(10)
