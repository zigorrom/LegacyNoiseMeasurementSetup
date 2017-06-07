from arduino_controller import ArduinoController
from hp34401a_multimeter import HP34401A,HP34401A_FUNCTIONS
import math

MIN_MOVING_SPEED = 5
MAX_MOVING_SPEED = 255
VALUE_DIFFERENCE = MAX_MOVING_SPEED - MIN_MOVING_SPEED
FD_CONST = -0.1

ZERO_VOLTAGE_INTERVAL = 0.02

VOLTAGE_SET_ERROR = 0.005
VOLTAGE_FINE_TUNING_INTERVAL  = 5*VOLTAGE_SET_ERROR

A1 = 0.05#0.006
A2 = 0.002
X0 = 0.01
p = 3

VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION = lambda error: A2 + (A1 - A2)/(1+math.pow(error/X0,p))

def speed_setting_function(current_value, set_value, fine_tuning = False):
    # fermi-dirac-distribution
    sign = 1
    if current_value <0:
        if current_value > set_value:
            sign = +1   
        else:
            sign = -1
    else:
        if current_value > set_value:
            sign = -1
        else:
            sign = +1
    
    if fine_tuning:
        #return MIN_MOVING_VOLTAGE
        return sign*MIN_MOVING_SPEED
    else:
        diff = math.fabs(current_value-set_value)
        try:
            exponent = math.exp(diff/FD_CONST)
        except OverflowError:
            exponent = float("inf")
        
        #return (MIN_MOVING_VOLTAGE + VALUE_DIFFERENCE/(exponent+1))
        return int(sign*(MIN_MOVING_SPEED + VALUE_DIFFERENCE/(exponent+1)))



class MotorizedPotentiometer():
    def __init__(self, motor_controller, motor_channel, multimeter):
        assert isinstance(motor_controller, ArduinoController) and isinstance(multimeter,HP34401A)
        self.__motor_controller = motor_controller
        self.__motor_channel = motor_channel
        self.__multimiter = multimeter

    def measure_voltage(self):
        pass

    def __set_voltage_polarity(polarity, channel):
        pass

    def set_voltage(self, voltage):
        multimeter = self.__multimiter
        motor = self.__motor_controller
        motor_ch = self.__motor_channel

        prev_value = multimeter.read_voltage()

        fine_tuning = False
        polarity_switched = False
        
        VoltageSetError = VOLTAGE_SET_ERROR
        VoltageTuningInterval = VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION(VoltageSetError)

        if math.fabs(voltage) < ZERO_VOLTAGE_INTERVAL :
            VoltageSetError = ZERO_VOLTAGE_INTERVAL
            VoltageTuningInterval =  VoltageTuningInterval+VoltageSetError     #5*VoltageSetError   

        while True: #continue_setting:    
            current_value = multimeter.read_voltage()
            if current_value*voltage<0 and not polarity_switched:
                set_result = self.set_voltage(voltage)
        
                if set_result:
                    polarity = FANS_NEGATIVE_POLARITY if voltage<0 else FANS_POSITIVE_POLARITY
                    self.__set_voltage_polarity(polarity, motor_ch)
                    polarity_switched = True
                else:
                    return set_result

            speed_to_set = speed_setting_function(current_value,voltage)
            abs_distance = math.fabs(current_value - voltage)
            if abs_distance < VoltageTuningInterval: #FANS_VOLTAGE_FINE_TUNING_INTERVAL:
                fine_tuning = True
                speed_to_set = speed_setting_function(current_value,voltage,True)
            
            if abs_distance < VoltageSetError and fine_tuning: #FANS_VOLTAGE_SET_ERROR and fine_tuning:
                motor.set_motor_speed(motor_ch,0)

                counts_to_trust = 5
                current_counts = 0
                ## stabilize
                #while current_counts < counts_to_trust:
                #    if current5

                return True
            
            if polarity_switched:
                abs_value = math.fabs(speed_to_set)
                if voltage * current_value < 0:
                    if voltage > 0:
                        speed_to_set = abs_value
                    else:
                        speed_to_set = -abs_value
            print("current: {0}; goal: {1};to set: {2};".format(current_value,voltage, speed_to_set))    
            motor.set_motor_speed(motor_ch,speed_to_set)
            #output_channel.ao_voltage = value_to_set 

    def set_average(self,average):
        pass



if __name__ == "__main__":
    ard = ArduinoController("COM27", 115200)


    m1 = HP34401A("GPIB0::23::INSTR")
    m1.clear_status()
    m1.reset()
    
    m2 = HP34401A("GPIB0::22::INSTR")
    m2.clear_status()
    m2.reset()
    #m1.switch_beeper(False)
    #m1.set_nplc(0.1)
    #m1.set_trigger_count(1)
    #m1.switch_high_ohmic_mode(False)
    #m1.set_function(HP34401A_FUNCTIONS.AVER)

    ch1 = 1
    ch2 = 2
    potenz1 = MotorizedPotentiometer(ard,ch1,m1)
    potenz1.set_voltage(-0.5)
    
    potenz2 = MotorizedPotentiometer(ard,ch2,m2)
    potenz2.set_voltage(-0.5)
    pass


#import time
#import math
#from fans_controller import FANS_controller, FANS_AI_channel,FANS_AO_channel,FANS_AO_Channel_Switch, FANS_CONTROLLER
#from fans_constants import *
#from agilent_u2542a_constants import *
#from node_configuration import Configuration
#import numpy as np

#MIN_MOVING_VOLTAGE = 0.5
#MAX_MOVING_VOLTAGE = 6
#VALUE_DIFFERENCE = MAX_MOVING_VOLTAGE-MIN_MOVING_VOLTAGE
#FD_CONST = -0.1

#FANS_VOLTAGE_SET_ERROR  = 0.001  #mV
#FANS_VOLTAGE_FINE_TUNING_INTERVAL = 5*FANS_VOLTAGE_SET_ERROR  #### set here function for interval selection

#A1 = 0.006
#A2 = 0.002
#X0 = 0.01
#p = 3

#FANS_VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION = lambda error: A2 + (A1 - A2)/(1+math.pow(error/X0,p))


#FANS_ZERO_VOLTAGE_INTERVAL = 0.02#0.005

#FANS_VOLTAGE_SET_MAXITER = 10000

#FANS_POLARITY_CHANGE_VOLTAGE = (-5,5)
#FANS_NEGATIVE_POLARITY,FANS_POSITIVE_POLARITY = FANS_POLARITY_CHANGE_VOLTAGE
 


#def voltage_setting_function(current_value, set_value, fine_tuning = False):
#    # fermi-dirac-distribution
#    sign = -1
#    if current_value <0:
#        if current_value > set_value:
#            sign = -1   
#        else:
#            sign = +1
#    else:
#        if current_value > set_value:
#            sign = +1
#        else:
#            sign = -1
    
#    if fine_tuning:
#        #return MIN_MOVING_VOLTAGE
#        return sign*MIN_MOVING_VOLTAGE
#    else:
#        diff = math.fabs(current_value-set_value)
#        try:
#            exponent = math.exp(diff/FD_CONST)
#        except OverflowError:
#            exponent = float("inf")
        
#        #return (MIN_MOVING_VOLTAGE + VALUE_DIFFERENCE/(exponent+1))
#        return sign*(MIN_MOVING_VOLTAGE + VALUE_DIFFERENCE/(exponent+1))

#OUT_ENABLED_CH, OUT_CH, FEEDBACK_CH, POLARITY_RELAY_CH , CH_POLARITY = [0,1,2,3,4]
## output channel - A0_BOX_CHANNELS
## feedback_channel - AI_BOX_CHANNELS
#def generate_state_dictionary(enabled, output_channel, feedback_channel, polarity_relay_channel):
#    return {OUT_ENABLED_CH:enabled, OUT_CH:output_channel, FEEDBACK_CH:feedback_channel, POLARITY_RELAY_CH: polarity_relay_channel, CH_POLARITY:FANS_POSITIVE_POLARITY}



    





#class FANS_SMU:
#    def __init__(self,fans_controller, drain_source_motor, drain_source_relay, drain_source_feedback,  gate_motor, gate_relay, gate_feedback, main_feedback, load_resistance  ):
#        self._fans_controller = fans_controller #FANS_CONTROLLER("") #
#        self._drain_source_motor = drain_source_motor
#        self._gate_motor = gate_motor
        
#        self._drain_source_relay = drain_source_relay
#        self._gate_relay = gate_relay
        
#        self._drain_source_feedback = drain_source_feedback
#        self._gate_feedback = gate_feedback
#        self._main_feedback = main_feedback

#        self._load_resistance = load_resistance

#        self._averageing_number = 100
#        self._fans_controller.analog_read_averaging(self.smu_averaging_number)


    

#    @property
#    def smu_averaging_number(self):
#        return self._averageing_number

#    @smu_averaging_number.setter
#    def smu_averaging_number(self,value):
#        self._averageing_number = value

#    @property
#    def smu_load_resistance(self):
#        return self._load_resistance

#    @smu_load_resistance.setter
#    def smu_load_resistance(self,value):
#        self._load_resistance = value

#    @property
#    def smu_ds_motor(self):
#        return self._drain_source_motor

#    @smu_ds_motor.setter
#    def smu_ds_motor(self,value):
#        self._drain_source_motor = value

#    @property
#    def smu_gate_motor(self):
#        return self._gate_motor

#    @smu_gate_motor.setter
#    def smu_gate_motor(self,value):
#        self._gate_motor = value

#    @property
#    def smu_ds_relay(self):
#        return self._drain_source_relay

#    @smu_ds_relay.setter
#    def smu_ds_relay(self,value):
#        self._drain_source_relay = value

#    @property
#    def smu_gate_relay(self):
#        return self._gate_relay

#    @smu_gate_relay.setter
#    def smu_gate_relay(self,value):
#        self._gate_relay = value

#    @property
#    def smu_drain_source_feedback(self):
#        return self._drain_source_feedback

#    @smu_drain_source_feedback.setter
#    def smu_drain_source_feedback(self,value):
#        self._drain_source_feedback = value

#    @property
#    def smu_gate_feedback(self):
#        return self._gate_feedback

#    @smu_gate_feedback.setter
#    def smu_gate_feedback(self,value):
#        self._gate_feedback = value

#    @property
#    def smu_main_feedback(self):
#        return self._main_feedback

#    @smu_main_feedback.setter
#    def smu_main_feedback(self,value):
#        self._main_feedback = value

#    def init_smu_mode(self):
#        # here use multichannel !!!
#        ai_feedback = self._fans_controller.get_ai_channel(self.smu_drain_source_feedback)
#        ai_feedback.ai_mode = AI_MODES.DC
#        ai_feedback.set_fans_ai_channel_params()

#        ai_feedback = self._fans_controller.get_ai_channel(self.smu_gate_feedback)
#        ai_feedback.ai_mode = AI_MODES.DC
#        ai_feedback.set_fans_ai_channel_params()

#        ai_feedback = self._fans_controller.get_ai_channel(self.smu_main_feedback)
#        ai_feedback.ai_mode = AI_MODES.DC
#        ai_feedback.set_fans_ai_channel_params()




#    def __set_voltage_polarity(self, polarity, voltage_set_channel, relay_channel):
#        rel_ch = self._fans_controller.fans_ao_switch.select_channel(relay_channel)
#        rel_ch.ao_voltage = polarity
#        time.sleep(0.5)
#        rel_ch.ao_voltage = 0
#        self._fans_controller.fans_ao_switch.select_channel(voltage_set_channel)


#    def __set_voltage_for_function(self,voltage, voltage_set_channel, relay_channel, feedback_channel):
#        self.init_smu_mode()

#        #ai_feedback = self._fans_controller.get_ai_channel(feedback_channel)
#        #ai_feedback.ai_mode = AI_MODES.DC
#        #ai_feedback.set_fans_ai_channel_params()

#        #
#        #  TO IMPLEMENT: use here UNIPOLAR voltage read and select appropriate range
#        #

#        output_channel = self._fans_controller.fans_ao_switch.select_channel(voltage_set_channel)
       
#        prev_value = self.analog_read(feedback_channel)
#        fine_tuning = False
#        polarity_switched = False
        
#        VoltageSetError = FANS_VOLTAGE_SET_ERROR
#        VoltageTuningInterval = FANS_VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION(VoltageSetError)

#        if math.fabs(voltage) < FANS_ZERO_VOLTAGE_INTERVAL :
#            VoltageSetError = FANS_ZERO_VOLTAGE_INTERVAL
#            VoltageTuningInterval =  VoltageTuningInterval+VoltageSetError     #5*VoltageSetError   

#        while True: #continue_setting:    
#            current_value = self.analog_read(feedback_channel)
#            if current_value*voltage<0 and not polarity_switched:
#                set_result = self.__set_voltage_for_function(0, voltage_set_channel, relay_channel, feedback_channel)
        
#                if set_result:
#                    polarity = FANS_NEGATIVE_POLARITY if voltage<0 else FANS_POSITIVE_POLARITY
#                    self.__set_voltage_polarity(polarity, voltage_set_channel, relay_channel)
#                    polarity_switched = True
#                else:
#                    return set_result

#            value_to_set = voltage_setting_function(current_value,voltage)
#            abs_distance = math.fabs(current_value - voltage)
#            if abs_distance < VoltageTuningInterval: #FANS_VOLTAGE_FINE_TUNING_INTERVAL:
#                fine_tuning = True
#                value_to_set = voltage_setting_function(current_value,voltage,True)
            
#            if abs_distance < VoltageSetError and fine_tuning: #FANS_VOLTAGE_SET_ERROR and fine_tuning:
#                output_channel.ao_voltage = 0
#                return True
            
#            if polarity_switched:
#                abs_value = math.fabs(value_to_set)
#                if voltage * current_value < 0:
#                    if voltage > 0:
#                        value_to_set = abs_value
#                    else:
#                        value_to_set = -abs_value
#            print("current: {0}; goal: {1};to set: {2};".format(current_value,voltage, value_to_set))    
#            output_channel.ao_voltage = value_to_set 


#    def smu_set_drain_source_voltage(self,voltage):
#        self.__set_voltage_for_function(voltage, self.smu_ds_motor, self.smu_ds_relay, self.smu_drain_source_feedback)

#    def smu_set_gate_voltage(self,voltage):
#        self.__set_voltage_for_function(voltage, self.smu_gate_motor, self.smu_gate_relay, self.smu_gate_feedback)

#    def analog_read(self,channels):
#        return self._fans_controller.analog_read(channels)

#    def read_all_parameters(self):
#        # can be a problem with an order of arguments
#        result = self.analog_read([self.smu_drain_source_feedback,self.smu_gate_feedback,self.smu_main_feedback])
#        ds_voltage = result[self.smu_drain_source_feedback]
#        main_voltage = result[self.smu_main_feedback]
#        gate_voltage = result[self.smu_gate_feedback]


#        ### fix divide by zero exception
#        try:
#            current = (main_voltage-ds_voltage)/self.smu_load_resistance
#            resistance = ds_voltage/current
#        except ZeroDivisionError:
#            current = 0
#            resistance = 0
        
#        return {"Vds":ds_voltage,"Vgs":gate_voltage,"Vmain":main_voltage, "Ids":current,"Rs":resistance}


    
