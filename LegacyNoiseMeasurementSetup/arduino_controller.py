import time
from n_enum import enum
import PyCmdMessenger

ARDUINO_FUNCTIONS = enum("Watchdog","Acknowledge","SwitchChannel", "Error", "MotorCommand")

class ArduinoController():
    def __init__(self, resource, baud_rate = 9600):
        self.__arduino = PyCmdMessenger.ArduinoBoard(resource, baud_rate,10)
        self.__commands = [
            [ARDUINO_FUNCTIONS.Watchdog,"s"],
            [ARDUINO_FUNCTIONS.Acknowledge, "s*"],
            [ARDUINO_FUNCTIONS.SwitchChannel,"i?"],
            [ARDUINO_FUNCTIONS.Error,"s"],
            [ARDUINO_FUNCTIONS.MotorCommand,"ii"]
            ]
        self.__messenger = PyCmdMessenger.CmdMessenger(self.__arduino, self.__commands)
        self.read_idn()

        
    def read_idn(self):
        self.__messenger.send(ARDUINO_FUNCTIONS.Watchdog)
        msg = self.__messenger.receive()
        return msg

        #return self.query("{0};".format(ARDUINO_FUNCTIONS.Watchdog))

    def switch_channel(self, channel, state):
        assert isinstance(channel, int)and isinstance(state, bool)
        self.__messenger.send(ARDUINO_FUNCTIONS.SwitchChannel,channel,state)
        print("channel: {0}, state: {1}".format(channel, state))
        response= self.__messenger.receive()
        self._parse_response(response)

    
    def set_motor_speed(self, channel, speed):
        assert isinstance(channel, int)and isinstance(speed, int)
        self.__messenger.send(ARDUINO_FUNCTIONS.MotorCommand,channel,speed)
        print("channel: {0}, speed: {1}".format(channel, speed))
        response = self.__messenger.receive()
        self._parse_response(response)

    def _parse_response(self,response):
        cmd,val,t = response
        print("response: {0}, value: {1}".format(ARDUINO_FUNCTIONS[cmd], val))
        assert cmd !=  ARDUINO_FUNCTIONS.Error, "Error while handling request on the controller"
        

if __name__=="__main__":
    ard = ArduinoController("COM7", 115200)
    
    var = ard.read_idn()
    print(var)
    time.sleep(2)
    for i in range(1,33,1):
        ard.switch_channel(i,True)
        time.sleep(0.3)
        ard.switch_channel(i,False)
    var = ard.read_idn()
    print(var)

    ard.set_motor_speed(1,200)
    ard.set_motor_speed(1 ,0)


    ard.close()
    
    pass