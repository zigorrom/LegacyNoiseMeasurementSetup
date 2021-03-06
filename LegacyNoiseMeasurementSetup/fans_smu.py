﻿import time
import math
from fans_controller import FANS_controller, FANS_AI_channel,FANS_AO_channel,FANS_AO_Channel_Switch, FANS_CONTROLLER
from fans_constants import *
from agilent_u2542a_constants import *
from configuration import Configuration
import numpy as np
from hp34401a_multimeter import HP34401A,HP34401A_FUNCTIONS


MIN_MOVING_VOLTAGE = 0.3
MAX_MOVING_VOLTAGE = 6
VALUE_DIFFERENCE = MAX_MOVING_VOLTAGE-MIN_MOVING_VOLTAGE
FD_CONST = -0.1

FANS_VOLTAGE_SET_ERROR  = 0.002  #mV
FANS_VOLTAGE_FINE_TUNING_INTERVAL = 5*FANS_VOLTAGE_SET_ERROR  #### set here function for interval selection

A1 = 0.01
A2 = 0.002
X0 = 0.007
p = 3

FANS_VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION = lambda error: A2 + (A1 - A2)/(1+math.pow(error/X0,p))


FANS_ZERO_VOLTAGE_INTERVAL = 0.01#0.005

FANS_VOLTAGE_SET_MAXITER = 10000

FANS_POLARITY_CHANGE_VOLTAGE = (-5,5)
FANS_NEGATIVE_POLARITY,FANS_POSITIVE_POLARITY = FANS_POLARITY_CHANGE_VOLTAGE
 

X0_VOLTAGE_SET = 0.1
POWER_VOLTAGE_SET = 3


def voltage_setting_function(current_value, set_value, fine_tuning = False):
    # fermi-dirac-distribution
    sign = -1
    if current_value <0:
        if current_value > set_value:
            sign = -1   
        else:
            sign = +1
    else:
        if current_value > set_value:
            sign = +1
        else:
            sign = -1
    
    if fine_tuning:
        #return MIN_MOVING_VOLTAGE
        return sign*MIN_MOVING_VOLTAGE
    else:
        diff = math.fabs(current_value-set_value)
        return sign*(MAX_MOVING_VOLTAGE + (MIN_MOVING_VOLTAGE-MAX_MOVING_VOLTAGE)/(1+math.pow(diff/X0_VOLTAGE_SET,POWER_VOLTAGE_SET)))
        

        #try:
        #    exponent = math.exp(diff/FD_CONST)
        #except OverflowError:
        #    exponent = float("inf")
        
        #return (MIN_MOVING_VOLTAGE + VALUE_DIFFERENCE/(exponent+1))
        #return sign*(MIN_MOVING_VOLTAGE + VALUE_DIFFERENCE/(exponent+1))
        #return 


OUT_ENABLED_CH, OUT_CH, FEEDBACK_CH, POLARITY_RELAY_CH , CH_POLARITY = [0,1,2,3,4]
# output channel - A0_BOX_CHANNELS
# feedback_channel - AI_BOX_CHANNELS
def generate_state_dictionary(enabled, output_channel, feedback_channel, polarity_relay_channel):
    return {OUT_ENABLED_CH:enabled, OUT_CH:output_channel, FEEDBACK_CH:feedback_channel, POLARITY_RELAY_CH: polarity_relay_channel, CH_POLARITY:FANS_POSITIVE_POLARITY}



    




LOW_SPEED, FAST_SPEED = (1,5)
SHORT_TIME,LONG_TIME = (0.3,2)

class FANS_SMU:
    def __init__(self,fans_controller, drain_source_motor, drain_source_relay, drain_source_feedback,  gate_motor, gate_relay, gate_feedback, main_feedback, load_resistance  ):
        self._fans_controller = fans_controller #FANS_CONTROLLER("") #
        self._drain_source_motor = drain_source_motor
        self._gate_motor = gate_motor
        
        self._drain_source_relay = drain_source_relay
        self._gate_relay = gate_relay
        
        self._drain_source_feedback = drain_source_feedback
        self._gate_feedback = gate_feedback
        self._main_feedback = main_feedback

        self._load_resistance = load_resistance

        self._averageing_number = 100
        self._fans_controller.analog_read_averaging(self.smu_averaging_number)


    

    @property
    def smu_averaging_number(self):
        return self._averageing_number

    @smu_averaging_number.setter
    def smu_averaging_number(self,value):
        self._averageing_number = value

    @property
    def smu_load_resistance(self):
        return self._load_resistance

    @smu_load_resistance.setter
    def smu_load_resistance(self,value):
        self._load_resistance = value

    @property
    def smu_ds_motor(self):
        return self._drain_source_motor

    @smu_ds_motor.setter
    def smu_ds_motor(self,value):
        self._drain_source_motor = value

    @property
    def smu_gate_motor(self):
        return self._gate_motor

    @smu_gate_motor.setter
    def smu_gate_motor(self,value):
        self._gate_motor = value

    @property
    def smu_ds_relay(self):
        return self._drain_source_relay

    @smu_ds_relay.setter
    def smu_ds_relay(self,value):
        self._drain_source_relay = value

    @property
    def smu_gate_relay(self):
        return self._gate_relay

    @smu_gate_relay.setter
    def smu_gate_relay(self,value):
        self._gate_relay = value

    @property
    def smu_drain_source_feedback(self):
        return self._drain_source_feedback

    @smu_drain_source_feedback.setter
    def smu_drain_source_feedback(self,value):
        self._drain_source_feedback = value

    @property
    def smu_gate_feedback(self):
        return self._gate_feedback

    @smu_gate_feedback.setter
    def smu_gate_feedback(self,value):
        self._gate_feedback = value

    @property
    def smu_main_feedback(self):
        return self._main_feedback

    @smu_main_feedback.setter
    def smu_main_feedback(self,value):
        self._main_feedback = value

    def init_smu_mode(self):
        # here use multichannel !!!
        ai_feedback = self._fans_controller.get_ai_channel(self.smu_drain_source_feedback)
        ai_feedback.ai_mode = AI_MODES.DC
        ai_feedback.set_fans_ai_channel_params()

        ai_feedback = self._fans_controller.get_ai_channel(self.smu_gate_feedback)
        ai_feedback.ai_mode = AI_MODES.DC
        ai_feedback.set_fans_ai_channel_params()

        ai_feedback = self._fans_controller.get_ai_channel(self.smu_main_feedback)
        ai_feedback.ai_mode = AI_MODES.DC
        ai_feedback.set_fans_ai_channel_params()


   

    def __set_voltage_polarity(self, polarity, voltage_set_channel, relay_channel):
        rel_ch = self._fans_controller.fans_ao_switch.select_channel(relay_channel)
        rel_ch.ao_voltage = polarity
        time.sleep(0.5)
        rel_ch.ao_voltage = 0
        self._fans_controller.fans_ao_switch.select_channel(voltage_set_channel)

    def set_drain_source_polarity_positiv(self):
        self.__set_voltage_polarity(FANS_POSITIVE_POLARITY, self._drain_source_motor, self._drain_source_relay)

    def set_drain_source_polarity_negativ(self):
        self.__set_voltage_polarity(FANS_NEGATIVE_POLARITY, self._drain_source_motor, self._drain_source_relay)

    def set_gate_polarity_positiv(self):
        self.__set_voltage_polarity(FANS_POSITIVE_POLARITY, self._gate_motor, self._gate_relay)

    def set_gate_polarity_negativ(self):
        self.__set_voltage_polarity(FANS_NEGATIVE_POLARITY, self._gate_motor, self._gate_relay)

    def move_motor(self, voltage_set_channel, direction, speed, timeout = 0.1):
        output_channel = self._fans_controller.fans_ao_switch.select_channel(voltage_set_channel)
        output_channel.ao_voltage = direction*speed
        time.sleep(timeout)
        output_channel.ao_voltage = 0

    def move_ds_motor_left(self):
        self.move_motor(self._drain_source_motor, -1, LOW_SPEED, SHORT_TIME)

    def move_ds_motor_left_fast(self):
        self.move_motor(self._drain_source_motor, -1, FAST_SPEED, LONG_TIME)

    def move_ds_motor_right(self):
        self.move_motor(self._drain_source_motor, 1, LOW_SPEED, SHORT_TIME)

    def move_ds_motor_right_fast(self):
        self.move_motor(self._drain_source_motor, 1, FAST_SPEED, LONG_TIME)

    def move_gate_motor_left(self):
        self.move_motor(self._gate_motor, -1, LOW_SPEED,SHORT_TIME)

    def move_gate_motor_left_fast(self):
        self.move_motor(self._gate_motor, -1, FAST_SPEED, LONG_TIME)

    def move_gate_motor_right(self):
        self.move_motor(self._gate_motor, 1, LOW_SPEED, SHORT_TIME)

    def move_gate_motor_right_fast(self):
        self.move_motor(self._gate_motor, 1, FAST_SPEED, LONG_TIME)

    def set_analog_read_averaging(self,averaging):
         self._fans_controller.analog_read_averaging(averaging)

    def __set_voltage_for_function_new(self, voltage, voltage_set_channel, relay_channel, feedback_channel):
        raise NotImplementedError()
        self.init_smu_mode()
        
        output_channel = self._fans_controller.fans_ao_switch.select_channel(voltage_set_channel)
        prev_value = self.analog_read(feedback_channel)
        fine_tuning = False
        polarity_switched = False
        
        VoltageSetError = FANS_VOLTAGE_SET_ERROR

        condition_satisfied = False

        # READ CURRENT VALUE
        # IF DIFFERENT POLARITY - GO TO 0 AND SWITCH POLARITY
        
        # SWITCHING POLARITY
        #if current_value*voltage<0 and not polarity_switched:
        #        set_result = self.__set_voltage_for_function(0, voltage_set_channel, relay_channel, feedback_channel)
                 #if set_result:
                 #   polarity = FANS_NEGATIVE_POLARITY if voltage<0 else FANS_POSITIVE_POLARITY
                 #   self.__set_voltage_polarity(polarity, voltage_set_channel, relay_channel)
                 #   polarity_switched = True

        

        while not condition_satisfied:
            # using set voltage function to set voltage less than estimation error

            # move the motor with the smallest speed to the goal value

            # if the error is smaller than the final error 
            # check if it staus there for count times in a row.
            # otherwise correct the value
            # and repeat the correction
            
            pass


    def __set_voltage_for_function(self,voltage, voltage_set_channel, relay_channel, feedback_channel):
        
        self.init_smu_mode()

        #ai_feedback = self._fans_controller.get_ai_channel(feedback_channel)
        #ai_feedback.ai_mode = AI_MODES.DC
        #ai_feedback.set_fans_ai_channel_params()

        #
        #  TO IMPLEMENT: use here UNIPOLAR voltage read and select appropriate range
        #

        output_channel = self._fans_controller.fans_ao_switch.select_channel(voltage_set_channel)
        

        assert isinstance(output_channel, FANS_AO_channel)

        #set read averaging to small value for fast acquisition
        coarse_averaging = 1
        fine_averaging = 50
        stabilization_counter = 200

        self.set_analog_read_averaging(coarse_averaging)

        prev_value = self.analog_read(feedback_channel)
        fine_tuning = False
        polarity_switched = False
        
        VoltageSetError = FANS_VOLTAGE_SET_ERROR
        VoltageTuningInterval = FANS_VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION(VoltageSetError)

        if math.fabs(voltage) < FANS_ZERO_VOLTAGE_INTERVAL :
            VoltageSetError = FANS_ZERO_VOLTAGE_INTERVAL
            VoltageTuningInterval =  VoltageTuningInterval+VoltageSetError     #5*VoltageSetError   

        while True: #continue_setting:    
            current_value = self.analog_read(feedback_channel)
            if current_value*voltage<0 and not polarity_switched:
                set_result = self.__set_voltage_for_function(0, voltage_set_channel, relay_channel, feedback_channel)
        
                if set_result:
                    polarity = FANS_NEGATIVE_POLARITY if voltage<0 else FANS_POSITIVE_POLARITY
                    self.__set_voltage_polarity(polarity, voltage_set_channel, relay_channel)
                    polarity_switched = True
                else:
                    return set_result

            value_to_set = voltage_setting_function(current_value,voltage)
            abs_distance = math.fabs(current_value - voltage)

            if abs_distance < VoltageSetError and fine_tuning: #FANS_VOLTAGE_SET_ERROR and fine_tuning:
                # set high averaging, moving voltage to 0 and check condition again count times if is of return true if not repeat adjustment
                output_channel.ao_voltage = 0
                condition_sattisfied = True
                for i in range(fine_averaging):
                    current_value = self.analog_read(feedback_channel)
                    abs_distance = math.fabs(current_value - voltage)

                    print("current distanse: {0}, trust_error: {1}, count: {2}, value: {3}".format(abs_distance, VoltageSetError, i, current_value))
                    if abs_distance > VoltageSetError:
                        condition_sattisfied = False
                        break

                if condition_sattisfied:
                    return True
                #self.set_analog_read_averaging(fine_averaging)
                #current_value = self.analog_read(feedback_channel)
                #abs_distance = math.fabs(current_value - voltage)
                #if abs_distance < VoltageSetError:
                #    return True
                ##for i in range(stabilization_counter):
                ##    current_value = self.analog_read(feedback_channel)
                #self.set_analog_read_averaging(coarse_averaging)


            elif abs_distance < VoltageTuningInterval or fine_tuning: #FANS_VOLTAGE_FINE_TUNING_INTERVAL:
                fine_tuning = True
                value_to_set = voltage_setting_function(current_value,voltage,True)
            
            
            
            if polarity_switched:
                abs_value = math.fabs(value_to_set)
                if voltage * current_value < 0:
                    if voltage > 0:
                        value_to_set = abs_value
                    else:
                        value_to_set = -abs_value
            print("current: {0}; goal: {1};to set: {2};".format(current_value,voltage, value_to_set))    
            output_channel.ao_voltage = value_to_set 


    def smu_set_drain_source_voltage(self,voltage):
        self.__set_voltage_for_function(voltage, self.smu_ds_motor, self.smu_ds_relay, self.smu_drain_source_feedback)

    def smu_set_gate_voltage(self,voltage):
        self.__set_voltage_for_function(voltage, self.smu_gate_motor, self.smu_gate_relay, self.smu_gate_feedback)

    def analog_read(self,channels):
        return self._fans_controller.analog_read(channels)

    def read_all_parameters(self):
        # can be a problem with an order of arguments
        result = self.analog_read([self.smu_drain_source_feedback,self.smu_gate_feedback,self.smu_main_feedback])
        ds_voltage = result[self.smu_drain_source_feedback]
        main_voltage = result[self.smu_main_feedback]
        gate_voltage = result[self.smu_gate_feedback]


        ### fix divide by zero exception
        try:
            current = (main_voltage-ds_voltage)/self.smu_load_resistance
            resistance = ds_voltage/current
        except ZeroDivisionError:
            current = 0
            resistance = 0
        
        return {"Vds":ds_voltage,"Vgs":gate_voltage,"Vmain":main_voltage, "Ids":current,"Rs":resistance}




class HybridSMU_System(FANS_SMU):
    def __init__(self, fans_controller, drain_source_motor, drain_source_relay, drain_source_feedback_multimeter, gate_motor, gate_relay, gate_feedback_multimeter, main_feedback_multimeter, load_resistance):
        drain_source_feedback, gate_feedback, main_feedback = (0,1,2)
        super().__init__(fans_controller, drain_source_motor, drain_source_relay, drain_source_feedback, gate_motor, gate_relay, gate_feedback,main_feedback, load_resistance)
        assert isinstance(drain_source_feedback_multimeter, HP34401A) and isinstance(gate_feedback_multimeter, HP34401A) and isinstance(main_feedback_multimeter, HP34401A)
        self._multimeters = {
            drain_source_feedback:drain_source_feedback_multimeter,
            gate_feedback:gate_feedback_multimeter,
            main_feedback:main_feedback_multimeter
            }
        
        #self._voltage_measurement_switch = 

    def analog_read_channel(self, channel):
        return self._multimeters[channel].read_voltage()

    def analog_read_average_channel(self,channel):
        self._multimeters[channel].init_instrument()
        return self._multimeters[channel].read_average()

    def analog_read(self, channels):
        if isinstance(channels,int):
            return self.analog_read_channel(channels)

        elif isinstance(channels, list):
            return {ch: self.analog_read_channel(ch) for ch in channels}

    def set_analog_read_averaging(self, averaging):
        #raise BaseException("NotImplementedError")
        for k,v in self._multimeters.items():
            assert isinstance(v, HP34401A)
            v.set_averaging(averaging)

    def read_drain_source_voltage(self, read_average = False):
        if read_average:
            return self.analog_read_average_channel(0)
        else:
            return self.analog_read_channel(0)

    def read_gate_voltage(self, read_average = False):
        if read_average:
            return self.analog_read_average_channel(1)
        else:
            return self.analog_read_channel(1)

    def read_main_voltage(self, read_average = False):
        if read_average:
            return self.analog_read_average_channel(2)
        else:
            return self.analog_read_channel(2)


class ManualSMU(FANS_SMU):
    def __init__(self, fans_controller, drain_source_motor, drain_source_relay, gate_motor, gate_relay, load_resistance):
        super().__init__(fans_controller, drain_source_motor, drain_source_relay, None, gate_motor, gate_relay, None, None, load_resistance)

        


    
    






  


#    def set_fans_voltage(self, voltage,channel):
#        pass
#    


if __name__ == "__main__":
    f = FANS_CONTROLLER("ADC");   #USB0::0x0957::0x1718::TW52524501::INSTR")
    
    smu = FANS_SMU(f, AO_BOX_CHANNELS.ao_ch_1, AO_BOX_CHANNELS.ao_ch_4, AI_CHANNELS.AI_101, AO_BOX_CHANNELS.ao_ch_9, AO_BOX_CHANNELS.ao_ch_12, AI_CHANNELS.AI_102, AI_CHANNELS.AI_103, 5000)

    mult1 = HP34401A("GPIB0::23::INSTR")
    mult1.set_nplc(0.1)
    mult2 = HP34401A("GPIB0::22::INSTR")
    mult2.set_nplc(0.1)

    smu_h = HybridSMU_System(f, AO_BOX_CHANNELS.ao_ch_1, AO_BOX_CHANNELS.ao_ch_4, mult1, AO_BOX_CHANNELS.ao_ch_9, AO_BOX_CHANNELS.ao_ch_12, mult2, mult2, 5000)

    print(smu_h.analog_read([0,1,2]))

    #smu_h.set_drain_source_polarity_negativ()
    #time.sleep(1)
    #smu_h.set_drain_source_polarity_positiv()
    #time.sleep(1)

    #smu_h.set_gate_polarity_negativ()
    #time.sleep(1)
    #smu_h.set_gate_polarity_positiv()
    #time.sleep(1)


    try:
        smu_h.smu_set_drain_source_voltage(0.2)
        for vg in np.arange(-0.3,0.2,0.05):
          print("setting gate")
          smu_h.smu_set_gate_voltage(vg)
          print(smu_h.read_all_parameters())
          
       
    except Exception as e:
        raise
        print(str(e))
    finally:
        f.get_ao_channel(AO_CHANNELS.AO_201).ao_voltage = 0
        f.get_ao_channel(AO_CHANNELS.AO_202).ao_voltage = 0

   
    #try:
    #    smu.smu_set_drain_source_voltage(0.1)
    #    for vg in np.arange(0,3,0.2):
    #      print("setting gate")
    #      smu.smu_set_gate_voltage(vg)
    #      print(smu.read_all_parameters())
          
    #    #  time.sleep(2)

    #    #smu.smu_set_drain_source_voltage(1)
    #    #smu.smu_set_gate_voltage(1)
    #    #smu.smu_set_drain_source_voltage(-1)
    #    #smu.smu_set_gate_voltage(-1)

    #    #smu.smu_set_drain_source_voltage(0)
    #    #smu.smu_set_gate_voltage(0)


    #    #print("finish")
    #    #smu.smu_set_drain_source_voltage(-1)
    #    #print(smu.read_all_parameters())
    #except Exception as e:
    #    raise
    #    print(str(e))
    #finally:
    #    f.get_ao_channel(AO_CHANNELS.AO_201).ao_voltage = 0
    #    f.get_ao_channel(AO_CHANNELS.AO_202).ao_voltage = 0


    #cfg = Configuration()
    ##f = FANS_controller("ADC",configuration=cfg)
    #f = FANS_controller("USB0::0x0957::0x1718::TW52524501::INSTR",configuration=cfg)
    #smu = fans_smu(f)
    
    #smu.set_fans_ao_channel_for_function(FANS_AI_FUNCTIONS.DrainSourceVoltage, AO_BOX_CHANNELS.ao_ch_1,STATES.ON)
    ##smu.set_fans_ao_channel_for_function(FANS_AI_FUNCTIONS.DrainSourceVoltage, A0_BOX_CHANNELS.ao_ch_10,STATES.ON)
    #smu.set_fans_ao_channel_for_function(FANS_AI_FUNCTIONS.GateVoltage, AO_BOX_CHANNELS.ao_ch_9,STATES.ON)

    #smu.set_fans_ao_relay_channel_for_function(FANS_AI_FUNCTIONS.DrainSourceVoltage, AO_BOX_CHANNELS.ao_ch_4)
    ##smu.set_fans_ao_relay_channel_for_function(FANS_AI_FUNCTIONS.DrainSourceVoltage, A0_BOX_CHANNELS.ao_ch_11)
    #smu.set_fans_ao_relay_channel_for_function(FANS_AI_FUNCTIONS.GateVoltage,AO_BOX_CHANNELS.ao_ch_12)
     
    #smu.set_fans_ao_polarity_for_function(FANS_AI_FUNCTIONS.DrainSourceVoltage, FANS_POSITIVE_POLARITY )
    #smu.set_fans_ao_polarity_for_function(FANS_AI_FUNCTIONS.GateVoltage, FANS_POSITIVE_POLARITY)

    #smu.set_fans_ao_feedback_for_function(FANS_AI_FUNCTIONS.DrainSourceVoltage, AI_BOX_CHANNELS.ai_ch_1)    #ai_ch5
    #smu.set_fans_ao_feedback_for_function(FANS_AI_FUNCTIONS.GateVoltage, AI_BOX_CHANNELS.ai_ch_2)   #ai_ch6
    #smu.set_fans_ao_feedback_for_function(FANS_AI_FUNCTIONS.MainVoltage,AI_BOX_CHANNELS.ai_ch_3 )   #ai_ch7

    #smu.init_smu_mode()
    #smu._init_fans_ao_channels()
    
    #try:
    #  #smu.set_drain_voltage(0)
    #  #smu.set_gate_voltage(0)
    #  smu.set_drain_voltage(0.3)
    #  smu.set_drain_voltage(-0.1)
      
    #  #for vds in np.arange(5,-5,-0.2):
    #  #    #print("setting drain-source")
    #  #    smu.set_drain_voltage(vds)
    #  #    print("setting gate")
    #  #    smu.set_gate_voltage(vds)
        
    #  #    print("Vgs = {0}; Id = {1}".format(res["Vgs"],res["Ids"]))
    #  #    time.sleep(2)

    #  #smu.set_drain_voltage(-0.2)
    #  #smu.set_gate_voltage(-4)
    #  #res = smu.read_all_parameters()
    #  print(smu.read_all_parameters())

    #except Exception as e:
    #    raise
    #    print(str(e))
    #finally:
    #    smu.set_hardware_voltage_channels(0, AO_CHANNELS.indexes)


    ####
    #OLD VERSION
    ###
    #class fans_smu:
    #def __init__(self, fans_controller):
    #    self.fans_controller = fans_controller
    #    self.load_resistance = fans_controller.load_resistance

    #    self.state_dictionary = dict()
    #    self.state_dictionary[FANS_AI_FUNCTIONS.DrainSourceVoltage] = generate_state_dictionary(True,0,0,0) # {OUT_CH:0, FEEDBACK_CH:1}
    #    self.state_dictionary[FANS_AI_FUNCTIONS.MainVoltage]= generate_state_dictionary(True,None,0,0)
    #    self.state_dictionary[FANS_AI_FUNCTIONS.GateVoltage]=generate_state_dictionary(True, 0,0,0) #{OUT_CH:0, FEEDBACK_CH:1}

    #    #self.ao_ch1_hardware_voltage = 0
    #    #self.ao_ch2_hardware_voltage = 0
    #    #self.ao_ch1_enabled = True
    #    #self.ao_ch2_enabled = True
    #    #self.fans_drain_source_set_channel = 0
    #    #self.fans_drain_source_set_channel = 0


    #    #self._init_fans_ao_channels()
    #    #self.init_smu_mode()
        


    #def _init_fans_ao_channels(self):
    #    #self.fans_controller._set_output_channels(self.fans_drain_source_set_channel,self.ao_ch1_enabled,self.fans_drain_source_set_channel,self.ao_ch2_enabled)
    #    ao1_channel = self.state_dictionary[FANS_AI_FUNCTIONS.DrainSourceVoltage][OUT_CH]
    #    ao1_enabled = self.state_dictionary[FANS_AI_FUNCTIONS.DrainSourceVoltage][OUT_ENABLED_CH]
    #    ao2_channel = self.state_dictionary[FANS_AI_FUNCTIONS.GateVoltage][OUT_CH]
    #    ao2_enabled = self.state_dictionary[FANS_AI_FUNCTIONS.GateVoltage][OUT_ENABLED_CH]
    #    self.fans_controller._set_output_channels(ao1_channel,ao1_enabled,ao2_channel,ao2_enabled)

    #def init_smu_mode(self):
    #    for ch in [FANS_AI_FUNCTIONS.DrainSourceVoltage, FANS_AI_FUNCTIONS.GateVoltage, FANS_AI_FUNCTIONS.MainVoltage]:
    #        self.fans_controller.set_fans_ai_channel_mode(AI_MODES.DC,self.state_dictionary[ch][FEEDBACK_CH])
    #    #self.fans_controller.set_fans_ai_channel_mode(AI_MODES.DC,channel)
    #    #self.fans_controller.analog_read_averaging(1000)

   
    #def set_fans_ao_relay_channel_for_function(self,function, ao_channel):
    #    self.state_dictionary[function][POLARITY_RELAY_CH] = ao_channel
   
    #def set_fans_ao_channel_for_function(self,function, ao_channel,enabled):
    #    self.state_dictionary[function][OUT_CH] = ao_channel
    #    self.state_dictionary[function][OUT_ENABLED_CH] = enabled
    #    self.fans_controller.set_selected_output(ao_channel,enabled)
      
    #def set_fans_ao_polarity_for_function(self,function, polarity):
    #    self.state_dictionary[function][CH_POLARITY] = polarity

    #def set_fans_ao_feedback_for_function(self,function,feedback):
    #    self.state_dictionary[function][FEEDBACK_CH] = feedback

    #def set_hardware_voltage(self,voltage, channel):
    #    self.fans_controller.fans_output_channel_voltage(voltage, channel)

    #def set_hardware_voltage_channels(self, voltage, channels):
    #    self.fans_controller.fans_output_voltage_to_channels(voltage,channels)

    #def set_hardware_voltages(self,channel_voltage_pairs):
    #    for channel,voltage in channel_voltage_pairs:
    #        self.fans_controller.fans_output_channel_voltage(voltage, channel)

    #def analog_read(self,channels):
    #    return self.fans_controller.analog_read(channels)


    #def __start_polarity_change(self,function):
    #    box_ao_ch = self.state_dictionary[function][OUT_CH]
    #    ao_ch = BOX_AO_CHANNEL_MAP[box_ao_ch]
    #    switch_ch = self.state_dictionary[function][POLARITY_RELAY_CH]
        
    #    self.set_hardware_voltage(0,ao_ch)
    #    self.fans_controller._set_output_channel(switch_ch,STATES.ON)
        
    #    #self.fans_controller._set_output_channels(
    #def __stop_polarity_change(self,function):
    #    box_ao_ch = self.state_dictionary[function][OUT_CH]
    #    ao_ch = BOX_AO_CHANNEL_MAP[box_ao_ch]
    #    #out_ch = self.state_dictionary[function][POLARITY_RELAY_CH]
    #    self.set_hardware_voltage(0,ao_ch)
    #    self.fans_controller._set_output_channel(box_ao_ch,STATES.ON)


    #def set_fans_output_polarity(self,polarity,function):
    #    self.__start_polarity_change(function)
    #    box_ao_ch = self.state_dictionary[function][POLARITY_RELAY_CH]
    #    ao_ch = BOX_AO_CHANNEL_MAP[box_ao_ch]
    #    self.set_hardware_voltage(polarity,ao_ch)
    #    time.sleep(0.5)
    #    self.set_hardware_voltage(0,ao_ch)
    #    self.state_dictionary[function][CH_POLARITY] = polarity
    #    #self.set_hardware_voltage(0,hardware_relay_ch)

    #    self.__stop_polarity_change(function)



    #def set_fans_voltage_for_channel(self,voltage,function):

    #    ai_feedback = self.state_dictionary[function][FEEDBACK_CH]
    #    output_ch = self.state_dictionary[function][OUT_CH]

    #    hardware_feedback_ch = BOX_AI_CHANNELS_MAP[ai_feedback]["channel"]
    #    hardware_output_ch = BOX_AO_CHANNEL_MAP[output_ch]
       
    #    prev_value = self.analog_read(hardware_feedback_ch)[hardware_feedback_ch]
    #    fine_tuning = False
    #    polarity_switched = False
        
    #    VoltageSetError = FANS_VOLTAGE_SET_ERROR
    #    VoltageTuningInterval = FANS_VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION(VoltageSetError)

    #    if math.fabs(voltage) < FANS_ZERO_VOLTAGE_INTERVAL :
    #        VoltageSetError = FANS_ZERO_VOLTAGE_INTERVAL
    #        VoltageTuningInterval =  VoltageTuningInterval+VoltageSetError     #5*VoltageSetError   

    #    #VoltageSetError = FANS_ZERO_VOLTAGE_INTERVAL if math.fabs(voltage) < FANS_ZERO_VOLTAGE_INTERVAL else FANS_VOLTAGE_SET_ERROR
    #    #VoltageTuningInterval =  FANS_VOLTAGE_FINE_TUNING_INTERVAL_FUNCTION(VoltageSetError)   #5*VoltageSetError
    #    print("Voltage set error = {0}, Voltage Tuning Interval = {1}".format(VoltageSetError,VoltageTuningInterval))
        
    #    time.sleep(1)


    #    while True: #continue_setting:    
    #        values = self.analog_read(AI_CHANNELS.indexes)
    #        current_value = self.analog_read(hardware_feedback_ch)[hardware_feedback_ch]

    #        if current_value*voltage<0 and not polarity_switched:
    #            set_result = self.set_fans_voltage_for_channel(0,function)
    #            if set_result:
    #                polarity = FANS_NEGATIVE_POLARITY if voltage<0 else FANS_POSITIVE_POLARITY
    #                self.set_fans_output_polarity(polarity,function)
    #                polarity_switched = True
    #            else:
    #                return set_result

    #        print((FANS_AI_FUNCTIONS[function], current_value,voltage))
    #        value_to_set = voltage_setting_function(current_value,voltage)
    #        values["value_to_set"] = value_to_set

    #        abs_distance = math.fabs(current_value - voltage)
    #        if abs_distance < VoltageTuningInterval: #FANS_VOLTAGE_FINE_TUNING_INTERVAL:
    #            fine_tuning = True
    #            value_to_set = voltage_setting_function(current_value,voltage,True)
            
    #        if abs_distance < VoltageSetError and fine_tuning: #FANS_VOLTAGE_SET_ERROR and fine_tuning:
    #            self.set_hardware_voltage(0,hardware_output_ch)
    #            return True
            
    #        if polarity_switched:
    #            abs_value = math.fabs(value_to_set)
    #            if voltage * current_value < 0:
    #                if voltage > 0:
    #                    value_to_set = -abs_value
    #                else:
    #                    value_to_set = abs_value
                

    #        self.set_hardware_voltage(value_to_set,hardware_output_ch)



            

    #def _start_setting_voltage(self,function):
    #    box_ao_ch = self.state_dictionary[function][OUT_CH]
    #    ao_ch = BOX_AO_CHANNEL_MAP[box_ao_ch]
    #    #out_ch = self.state_dictionary[function][POLARITY_RELAY_CH]
    #    self.set_hardware_voltage(0,ao_ch)
    #    self.fans_controller._set_output_channel(box_ao_ch,STATES.ON)

    #def set_drain_voltage(self,voltage):
    #    #feedback_ch = self.state_dictionary[FANS_AI_FUNCTIONS.DrainSourceVoltage][FEEDBACK_CH]
    #    #output_ch = self.state_dictionary[FANS_AI_FUNCTIONS.DrainSourceVoltage][OUT_CH]
    #    self._start_setting_voltage(FANS_AI_FUNCTIONS.DrainSourceVoltage)
    #    self.set_fans_voltage_for_channel(voltage,FANS_AI_FUNCTIONS.DrainSourceVoltage) #feedback_ch,output_ch)
    #    #self.set_fans_voltage_for_channel(voltage,self.fans_drain_source_feedback)



    #def set_gate_voltage(self, voltage):
    #    #feedback_ch = self.state_dictionary[FANS_AI_FUNCTIONS.GateVoltage][FEEDBACK_CH]
    #    #output_ch = self.state_dictionary[FANS_AI_FUNCTIONS.GateVoltage][OUT_CH]
    #    self._start_setting_voltage(FANS_AI_FUNCTIONS.GateVoltage)
    #    self.set_fans_voltage_for_channel(voltage,FANS_AI_FUNCTIONS.GateVoltage) #feedback_ch,output_ch)
    #    #self.set_fans_voltage_for_channel(voltage, self.fans_gate_feedback)
    
    
    
    ##def read_drain_source_current(self):
    ##    pass    

    #def read_all_parameters(self):
    #    drain_feedback_ch = self.state_dictionary[FANS_AI_FUNCTIONS.DrainSourceVoltage][FEEDBACK_CH]
    #    gate_feedback_ch = self.state_dictionary[FANS_AI_FUNCTIONS.GateVoltage][FEEDBACK_CH]
    #    main_feedback_ch = self.state_dictionary[FANS_AI_FUNCTIONS.MainVoltage][FEEDBACK_CH]

    #    drain_hardware_ch = BOX_AI_CHANNELS_MAP[drain_feedback_ch]["channel"]
    #    gate_hardware_ch = BOX_AI_CHANNELS_MAP[gate_feedback_ch]["channel"]
    #    main_hardware_ch = BOX_AI_CHANNELS_MAP[main_feedback_ch]["channel"]
        
    #    # can be a problem with an order of arguments
    #    result = self.analog_read([drain_hardware_ch,main_hardware_ch,gate_hardware_ch])
    #    ds_voltage = result[drain_hardware_ch]
    #    main_voltage = result[main_hardware_ch]
    #    gate_voltage = result[gate_hardware_ch]


    #    ### fix divide by zero exception
    #    try:
    #        current = (main_voltage-ds_voltage)/self.load_resistance
    #        resistance = ds_voltage/current
    #    except ZeroDivisionError:
    #        current = 0
    #        resistance = 0
        
    #    return {"Vds":ds_voltage,"Vgs":gate_voltage,"Vmain":main_voltage, "Ids":current,"Rs":resistance}