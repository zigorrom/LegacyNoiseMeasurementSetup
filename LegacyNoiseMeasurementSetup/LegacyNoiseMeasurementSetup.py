﻿import sys
import visa
import time
import serial
import base64
import PyCmdMessenger
from n_enum import enum
from PyQt4 import uic, QtGui, QtCore

def instrument_await_function(func):
        def wrapper(self,*args,**kwargs):
            prev_timeout = self.instrument.timeout
            self.instrument.timeout = None
            result = func(self,*args,**kwargs)
            self.instrument.timeout = prev_timeout 
            return result
        return wrapper


class SerialInstrument:
    def __init__(self, resource, baud_rate = 9600):
        self.__port = serial.Serial(
            port = resource, 
            baudrate = baud_rate
            )
        self.__termination_char = "\n"
        self.__port.flushInput()
        self.__port.flushOutput()

    @property
    def termination_char(self):
        return self.__termination_char
    
    @termination_char.setter
    def termination_char(self,value):
        self.__termination_char = value

    def open(self):
        if not self.isOpen():
            self.__port.open()

    def close(self):
        self.__port.close()

    def isOpen(self):
        return self.__port.isOpen()

    def write(self, string):
        #assert self.isOpen()
        print("sending to device: {0}".format(string))
        self.__port.write(string.encode('ascii'))   #base64.b64encode(bytes(string, 'utf-8')))   #string.encode('')
                          

    def read(self, num_of_bytes = 1):
        #assert self.isOpen()
        return self.__port.read(num_of_bytes).decode()

    def read_until_termination(self):
        #assert self.isOpen()
        read_chars = []
        current_char = None
        while current_char != self.termination_char:
            current_char = self.read()
            read_chars.append(current_char)

        return "".join(read_chars)

    def query(self,string):
        #assert self.isOpen()
        self.write(string)
        return self.read_until_termination()

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
        
  
class MotorizedPotentiometer():
    def __init__(self, motor_controller, motor_channel, multimeter):
        self.__motor_controller = motor_controller
        self.__motor_channel = motor_channel
        self.__multimiter = multimeter

    def measure_voltage(self):
        pass

    def set_voltage(self):
        pass

    def set_average(self,average):
        pass



class VisaInstrument:
    def __init__(self, resource):
        rm = visa.ResourceManager()
        self.__instrument = rm.open_resource(resource, write_termination = '\n',read_termination='\n')

    def write(self,string):
        assert isinstance(string, str)
        print("writing to device: {0}".format(string))
        self.__instrument.write(string)

    def query(self,string):
        assert isinstance(string, str)
        print("querying from device: {0}".format(string))
        return self.__instrument.ask(string)

    def read(self):
        return self.__instrument.read()


HP34401A_FUNCTIONS = enum("AVER")

class HP34401A(VisaInstrument):
    def __init__(self, resource):
        super().__init__(resource)

    def reset(self):
        self.write("*RST")

    def clear_status(self):
        self.write("*CLS")

    def query_operation_completed(self):
        return self.query("*OPC?")

    def set_nplc(self,nplc):
        assert isinstance(nplc, float)or isinstance(nplc, int)
        assert nplc > 0, "nplc should be greater than 0"
        self.write("VOLT:DC:NPLC {0}".format(nplc))

    def set_trigger_count(self,count):
        assert  isinstance(count, int)
        self.write("TRIG:COUN {0}".format(count))

    def switch_beeper(self,state):
        self.write("SYST:BEEP:STAT {0}".format("ON" if state else "OFF"))

    def switch_high_ohmic_mode(self,state):
        self.write("INP:IMP:AUTO {0}".format("ON" if state else "OFF"))

    def set_function(self,func):
        assert func in HP34401A_FUNCTIONS.indexes
        self.write("CALC:FUNC {0}".format(HP34401A_FUNCTIONS[func]))

    def switch_stat(self,state):
        self.write("CALC:STAT {0}".format("ON" if state else "OFF"))

    def switch_autorange(self,state):
        self.write("SENS:VOLT:DC:RANG:AUTO {0}".format("ON" if state else "OFF"))

    def init_instrument(self):
        self.write("INIT")

    @instrument_await_function
    def read_voltage(self):
        return float(self.query("MEAS:VOLTAGE:DC?")) #"CALC:AVER:AVER?"))

    @instrument_await_function
    def read_average(self):
        return float(self.query("CALC:AVER:AVER?"))


HP35670A_MODES = enum("FFT", "OCT", "ORD", "SINE", "HIST", "CORR")
HP35670A_INPUTS = enum("INP1","INP2")
HP35670A_CALC = enum("CALC1","CALC2","CALC3","CALC4")
HP35670A_TRACES = enum("A","B","C","D")

class HP3567A(VisaInstrument):
    def __init__(self, resource):
        super().__init__(resource)
   
    def initialize_instrument(self):
        raise NotImplementedError()

    def output_state(self, state):
        self.write("OUTPUT:STAT {0}".format("ON" if state else "OFF"))

    def set_source_voltage(self,voltage):
        assert isinstance(voltage, float) or isinstance(voltage, int), "Houston, we`ve got a problem"
        self.write("SOUR:VOLTAGE:OFFS {0}".format(voltage))

    def remove_time_capture_data(self):
        self.write(":TCAP:DEL")

    def select_instrument_mode(self,mode):
        """ mode can be FFT|OCTave|ORDer|SINE|HISTogram|CORRelation"""
        assert mode in HP35670A_MODES.indexes
        #print(HP35670A_MODES[mode])
        self.write("INST:SEL {0}".format(HP35670A_MODES[mode]))

    def switch_input(self,input,state):
        assert input in HP35670A_INPUTS.indexes
        self.write(":{0} {1}".format(HP35670A_INPUTS[input], "ON" if state else "OFF"))

    def select_active_traces(self, calc, trace):
        assert calc in HP35670A_CALC.indexes
        assert trace in HP35670A_TRACES.indexes
        self.write(":{0}:ACTIVE {1}".format(HP35670A_CALC[calc],HP35670A_TRACES[trace]))

    def select_real_format(self, bit_number):
        assert bit_number is 32 or bit_number is 64
        self.write("FORM:DATA REAL, {0}".format(bit_number))

    def select_ascii_format(self):
        self.write("FORM:DATA ASC, 12")

    def select_power_spectrum_function(self,calc):
        assert calc in HP35670A_CALC.indexes
        self.write("{0}:FEED '{1}'".format(HP35670A_CALC[calc], "XFR:POW {0}".format(calc+1)))

    def select_voltage_unit(self,calc):
        assert calc in HP35670A_CALC.indexes
        self.write("{0}:UNIT:VOLT 'V2/Hz'".format(HP35670A_CALC[calc]))

    def switch_calibration(self,state):
        self.write("CAL:AUTO {0}".format("ON" if state else "OFF"))

    def set_frequency_resolution(self,value):
        assert isinstance(value,int)
        self.write("FREQ:RES {0}".format(value))

    def switch_averaging(self,state):
        self.write(":AVER {0}".format("ON" if state else "OFF"))

    def set_display_update_rate(self, rate):
        assert isinstance(rate,int) and rate > 0
        self.write("SENS:AVERAGE:IRES:RATE {0}".format(rate))

    def set_average_count(self,count):
        assert isinstance(count,int) and count > 0
        self.write("SENS:AVERAGE:COUNT {0}".format(count))

    def switch_overload_rejection(self,state):
        self.write("SENS:REJ:STAT {0}".format("ON" if state else "OFF"))

    def get_points_number(self,calc):
        assert calc in HP35670A_CALC.indexes
        return self.query("{0}:DATA:HEAD:POIN?".format(HP35670A_CALC[calc]))

    def set_frequency_start(self, value):
        assert isinstance(value, float) or isinstance(value,int)
        self.write("SENS:FREQ:STAR {0}".format(value))

    def set_frequency_stop(self,value):
        assert isinstance(value, float) or isinstance(value, int)
        self.write("SENS:FREQ:STOP {0}".format(value))

    @instrument_await_function
    def get_data(self,calc):
        assert calc in HP35670A_CALC.indexes
        return self.query("{}:DATA?".format(HP35670A_CALC[calc]) )


    def abort(self):
        self.write("ABORT");

    def init_instrument(self):
        self.write(":INIT");

    def clear_status(self):
        self.write("*CLS")

    @instrument_await_function
    def calibrate(self):
        return self.query("*CAL?")
     
    @instrument_await_function
    def wait_operation_complete(self):
        self.write("*WAI")


class ExperimentSettingsViewModel(QtCore.QAbstractListModel):
    def __init__(self, settings = None, parent = None):
        super(ExperimentSettingsViewModel,self).__init__(parent)#,parent)
        self.__settings = settings #ExperimentSettings() #settings

    def rowCount(self,index):
        #return 1
        if self.__settings:# amount of properties in ExperimentSettings class
            return self.__settings.get_column_count()

    #def columnCount(self, index):
    #    if self.__settings:# amount of properties in ExperimentSettings class
    #        return self.__settings.get_column_count()

    """INPUTS: QModelIndex"""
    """OUTPUT: int (flag)"""
    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    """INPUTS: QModelIndex, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""
    def data(self, index, role):
        if not index.isValid():
            return None
        if not self.__settings:
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.__settings.data(index.row()) #.column())

    def setData(self, index, value,role = QtCore.Qt.EditRole):
        if not index.isValid():
            return False

        if role == QtCore.Qt.EditRole:
            self.__settings.setData(index.row(),value)#.column(),value)
            self.dataChanged.emit(index,index)
            return True




class ExperimentSettings:
    def __init__(self):
        #this settings - separate class. shoy\uld be saved to file

        self.__working_directory = None
        self.__expeiment_name = None
        self.__measurement_name = None
        self.__measurement_count  = 0
        
        self.__calibrate_before_measurement = False
        self.__overload_rejecion = False

        self.__display_refresh = 10
        self.__averages = 100

        self.__use_homemade_amplifier = True
        self.__homemade_amp_coeff = 178
        self.__use_second_amplifier = True
        self.__second_amp_coeff = 100

        self.__load_resistance = 5000
        
        self.__need_measure_temperature = False
        self.__meas_gated_structure = True
        self.__meas_characteristic_type = 0; # 0 is output 1 is transfer


        self.__use_transistor_selector = False
        self.__transistor_list = None

        self.__use_set_vds_range = False
        self.__vds_range = None

        self.__use_set_vfg_range = False
        self.__vfg_range = None

        self.__front_gate_voltage = 0
        self.__drain_source_voltage = 0

    def get_column_count(self):
       return 24  # amount of properties in ExperimentSettings class

    def data(self,column):
        #self.__working_directory = None
        if column is 0: return self.working_directory
        #self.__expeiment_name = None
        elif column is 1: return self.expeiment_name
        #self.__measurement_name = None
        elif column is 2: return self.measurement_name
        #self.__measurement_count  = 0
        elif column is 3: return self.measurement_count

        
        #self.__calibrate_before_measurement = False
        elif column is 4: return self.calibrate_before_measurement
        #self.__overload_rejecion = False
        elif column is 5: return self.overload_rejecion

        #self.__display_refresh = 10
        elif column is 6: return self.display_refresh
        #self.__averages = 100
        elif column is 7: return self.averages

        #self.__use_homemade_amplifier = True
        elif column is 8: return self.use_homemade_amplifier
        #self.__homemade_amp_coeff = 178
        elif column is 9: return self.homemade_amp_coeff


        #self.__use_second_amplifier = True
        elif column is 10: return self.use_second_amplifier
        #self.__second_amp_coeff = 100
        elif column is 11: return self.second_amp_coeff

        #self.__load_resistance = 5000
        elif column is 12: return self.load_resistance

        #self.__need_measure_temperature = False
        elif column is 13: return self.need_measure_temperature

        #self.__meas_gated_structure = True
        elif column is 14: return self.meas_gated_structure
        #self.__meas_characteristic_type = 0; # 0 is output 1 is transfer
        elif column is 15: return self.meas_characteristic_type

        #self.__use_transistor_selector = False
        elif column is 16: return self.use_transistor_selector
        #self.__transistor_list = None
        elif column is 17: return self.transistor_list

        #self.__use_set_vds_range = False
        elif column is 18: return self.use_set_vds_range
        #self.__vds_range = None
        elif column is 19: return self.vds_range

        #self.__use_set_vfg_range = False
        elif column is 20: return self.use_set_vfg_range
        #self.__vfg_range = None
        elif column is 21: return self.vfg_range

        #self.__front_gate_voltage = 0
        elif column is 22: return self.front_gate_voltage
        #self.__drain_source_voltage = 0
        elif column is 23: return self.drain_source_voltage
        else:
            return None

    def setData(self,column, value):
         #self.__working_directory = None
        if column is 0: self.working_directory = value
        #self.__expeiment_name = None
        elif column is 1:  self.expeiment_name= value
        #self.__measurement_name = None
        elif column is 2:  measurement_name= value
        #self.__measurement_count  = 0
        elif column is 3:  measurement_count= value

        
        #self.__calibrate_before_measurement = False
        elif column is 4:  self.calibrate_before_measurement= value
        #self.__overload_rejecion = False
        elif column is 5:  self.overload_rejecion= value

        #self.__display_refresh = 10
        elif column is 6:  self.display_refresh= value
        #self.__averages = 100
        elif column is 7:  self.averages= value

        #self.__use_homemade_amplifier = True
        elif column is 8:  self.use_homemade_amplifier= value
        #self.__homemade_amp_coeff = 178
        elif column is 9:  self.homemade_amp_coeff= value


        #self.__use_second_amplifier = True
        elif column is 10:  self.use_second_amplifier= value
        #self.__second_amp_coeff = 100
        elif column is 11:  self.second_amp_coeff= value

        #self.__load_resistance = 5000
        elif column is 12:  self.load_resistance= value

        #self.__need_measure_temperature = False
        elif column is 13:  self.need_measure_temperature= value

        #self.__meas_gated_structure = True
        elif column is 14:  self.meas_gated_structure= value
        #self.__meas_characteristic_type = 0; # 0 is output 1 is transfer
        elif column is 15:  self.meas_characteristic_type= value

        #self.__use_transistor_selector = False
        elif column is 16:  self.use_transistor_selector= value
        #self.__transistor_list = None
        elif column is 17:  self.transistor_list= value

        #self.__use_set_vds_range = False
        elif column is 18:  self.use_set_vds_range= value
        #self.__vds_range = None
        elif column is 19:  self.vds_range= value

        #self.__use_set_vfg_range = False
        elif column is 20:  self.use_set_vfg_range= value
        #self.__vfg_range = None
        elif column is 21:  self.vfg_range= value

        #self.__front_gate_voltage = 0
        elif column is 22:  self.front_gate_voltage= value
        #self.__drain_source_voltage = 0
        elif column is 23:  self.drain_source_voltage= value

    @property
    def vds_range(self):
        return self.__vds_range

    @vds_range.setter
    def vds_range(self,value):
        self.__vds_range = value

    @property
    def vfg_range(self):
        return self.__vfg_range

    @vfg_range.setter
    def vfg_range(self,value):
        self.__vfg_range = value

    @property
    def front_gate_voltage(self):
        return self.__front_gate_voltage

    @front_gate_voltage.setter
    def front_gate_voltage(self,value):
        self.__front_gate_voltage = value

    @property
    def drain_source_voltage(self):
        return self.__drain_source_voltage

    @drain_source_voltage.setter
    def drain_source_voltage(self,value):
        self.__drain_source_voltage = value

    @property
    def working_directory(self):
        return self.__working_directory

    @working_directory.setter
    def working_directory(self,value):
        self.__working_directory = value

    #self.__expeiment_name = None
    @property
    def expeiment_name(self):
        return self.__expeiment_name

    @expeiment_name.setter
    def expeiment_name(self,value):
        self.__expeiment_name = value

    #self.__measurement_name = None
    @property
    def measurement_name(self):
        return self.__measurement_name

    @measurement_name.setter
    def measurement_name(self,value):
        self.__measurement_name = value

    #self.__measurement_count  = 0
    @property
    def measurement_count(self):
        return self.__measurement_count

    @measurement_count.setter
    def measurement_count(self,value):
        self.__measurement_count = value    


    #self.__calibrate_before_measurement = False
    @property
    def calibrate_before_measurement(self):
        return self.__calibrate_before_measurement

    @calibrate_before_measurement.setter
    def calibrate_before_measurement(self,value):
        self.__calibrate_before_measurement= value    

    #self.__overload_rejecion = False
    @property
    def overload_rejecion(self):
        return self.__overload_rejecion

    @overload_rejecion.setter
    def overload_rejecion(self,value):
        self.__overload_rejecion= value    

    #self.__display_refresh = 10
    @property
    def display_refresh(self):
        return self.__display_refresh

    @display_refresh.setter
    def display_refresh(self,value):
        self.__display_refresh= value    
    #self.__averages = 100
    @property
    def averages(self):
        return self.__averages

    @averages.setter
    def averages(self,value):
        self.__averages= value  

    #self.__use_homemade_amplifier = True
    @property
    def use_homemade_amplifier(self):
        return self.__use_homemade_amplifier

    @use_homemade_amplifier.setter
    def use_homemade_amplifier(self,value):
        self.__use_homemade_amplifier= value  


    #self.__homemade_amp_coeff = 178
    @property
    def homemade_amp_coeff(self):
        return self.__homemade_amp_coeff

    @homemade_amp_coeff.setter
    def homemade_amp_coeff(self,value):
        self.__homemade_amp_coeff= value  

    #self.__use_second_amplifier = True
    @property
    def use_second_amplifier(self):
        return self.__use_second_amplifier

    @use_second_amplifier.setter
    def use_second_amplifier(self,value):
        self.__use_second_amplifier= value 


    #self.__second_amp_coeff = 100
    @property
    def second_amp_coeff(self):
        return self.__second_amp_coeff

    @second_amp_coeff.setter
    def second_amp_coeff(self,value):
        self.__second_amp_coeff= value 

    #self.__load_resistance = 5000
    @property
    def load_resistance(self):
        return self.__load_resistance

    @load_resistance.setter
    def load_resistance(self,value):
        self.__load_resistance= value 
        
    #self.__need_measure_temperature = False
    @property
    def need_measure_temperature(self):
        return self.__need_measure_temperature

    @need_measure_temperature.setter
    def need_measure_temperature(self,value):
        self.__need_measure_temperature= value 

    #self.__meas_gated_structure = True
    @property
    def meas_gated_structure(self):
        return self.__meas_gated_structure

    @meas_gated_structure.setter
    def meas_gated_structure(self,value):
        self.__meas_gated_structure= value 
   
    #self.__meas_characteristic_type = 0; # 0 is output 1 is transfer
    @property
    def meas_characteristic_type(self):
        return self.__meas_characteristic_type

    @meas_characteristic_type.setter
    def meas_characteristic_type(self,value):
        self.__meas_characteristic_type= value

    #self.__use_transistor_selector = False
    @property
    def use_transistor_selector(self):
        return self.__use_transistor_selector

    @use_transistor_selector.setter
    def use_transistor_selector(self,value):
        self.__use_transistor_selector= value

    #self.__transistor_list = None
    @property
    def transistor_list(self):
        return self.__transistor_list

    @transistor_list.setter
    def transistor_list(self,value):
        self.__transistor_list= value

    #self.__use_set_vds_range = False
    @property
    def use_set_vds_range(self):
        return self.__use_set_vds_range

    @use_set_vds_range.setter
    def use_set_vds_range(self,value):
        self.__use_set_vds_range= value
    #self.__use_set_vfg_range = False
    @property
    def use_set_vfg_range(self):
        return self.__use_set_vfg_range

    @use_set_vfg_range.setter
    def use_set_vfg_range(self,value):
        self.__use_set_vfg_range= value




class Experiment:
    def __init__(self):
        self.__hardware_settings = None
        self.__exp_settings = ExperimentSettings()
        self.__initialize_hardware()

        self._measured_temp_start = 0;
        self._measured_temp_end = 0;

        self._measured_main_voltage_start = 0;
        self._measured_main_voltage_end = 0;

        self._measured_sample_voltage_start = 0;
        self._measured_samole_voltage_end = 0;
        
        self._measured_gate_voltage_start = 0;
        self._measured_gate_voltage_end = 0;

        self._sample_current_start = 0;
        self._sample_current_end = 0;

        self._sample_resistance_start = 0;
        self._sample_resistance_end = 0;

        self._equivalent_resistance_start = 0;
        self._equivalent_resistance_end = 0;


    def __initialize_hardware(self):
        self.__dynamic_signal_analyzer = HP3567A(self.__hardware_settings["analyzer"])
        self.__arduino_controller = ArduinoController(self.__hardware_settings["arduino_controller"])
        self.__drain_multimeter = HP34401A(self.__hardware_settings["drain_multimeter"])
        self.__main_gate_multimeter = HP34401A(self.__hardware_settings["main_gate_multimeter"])


    def output_curve_measurement_function(self):
        if self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            for vfg in self.__exp_settings.vfg_range:
                for vds in self.__exp_settings.vds_range:
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in self.__exp_settings.vds_range:
                    self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
             for vfg in self.__exp_settings.vfg_range:
                    self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        #foreach vfg_voltage in Vfg_range 
        #    foreach vds_voltage in Vds_range
        #       single_value_measurement(vds_voltage,vfg_voltage)
        

    def transfer_curve_measurement_function(self):
        if self.__exp_settings.use_set_vds_range and self.__exp_settings.use_set_vfg_range:
            for vds in self.__exp_settings.vds_range:
                for vfg in self.__exp_settings.vfg_range:
                    self.single_value_measurement(vds, vfg)
           
        elif not self.__exp_settings.use_set_vfg_range:
            for vds in self.__exp_settings.vds_range:
                    self.single_value_measurement(vds, self.__exp_settings.front_gate_voltage)
                    
        elif not self.__exp_settings.use_set_vds_range:
             for vfg in self.__exp_settings.vfg_range:
                    self.single_value_measurement(self.__exp_settings.drain_source_voltage, vfg)
        else:
            self.single_value_measurement(self.__exp_settings.drain_source_voltage,self.__exp_settings.front_gate_voltage)

        # foreach vds_voltage in Vds_range
        #     foreach vfg_voltage in Vfg_range 
        #       single_value_measurement(vds_voltage,vfg_voltage)
    
    def set_front_gate_voltage(self,voltage):
        pass

    def set_drain_source_voltage(self,voltage):
        pass

    def set_voltage(self, voltage):
        pass   

    def single_value_measurement(self, drain_source_voltage, gate_voltage):
        self.set_drain_source_voltage(drain_source_voltage)
        self.set_front_gate_voltage(gate_voltage)
        self.set_drain_source_voltage(drain_source_voltage) ## specifics of the circuit!!! to correct the value of dropped voltage on opened channel
        self.perform_single_measurement()
        #set vds_voltage
        # set vfg voltage
        # stabilize voltage
        # perform_single_measurement()
        

    def non_gated_structure_meaurement_function(self):
        if self.__exp_settings.use_set_vds_range:
             for vds in self.__exp_settings.vds_range:
                    self.non_gated_single_value_measurement(vds)
        else:
            self.non_gated_single_value_measurement(self.__exp_settings.drain_source_voltage)

        # foreach vds_voltage in Vds_range
        #  non_gated_single_value_measurement(vds)

    def non_gated_single_value_measurement(self, drain_source_voltage):
        self.set_drain_source_voltage(drain_source_voltage)
        self.perform_non_gated_single_measurement()
        #set vds_voltage
        # stabilize voltage
        # perform_single_measurement()
        pass

   

    def generate_experiment_function(self):
        func = None
        if not self.__exp_settings.meas_gated_structure:# non gated structure measurement
            func = self.non_gated_structure_meaurement_function
        elif self.__meas_characteristic_type == 0: #output curve
            func = self.output_curve_measurement_function
        elif self.__meas_characteristic_type == 1: #transfer curve
            func = self.transfer_curve_measurement_function
        else: 
            raise AssertionError("function was not selected properly")

        if self.__exp_settings.use_transistor_selector:
            def execution_function(self):
                for transistor in self.__exp_settings.transistor_list:
                    func()
            return execution_function

        return func






    def perform_non_gated_single_measurement(self):
        #set overload_rejection
        #self.__dynamic_signal_analyzer.switch_overload_rejection(self.__exp_settings.overload_rejecion)
        #calibrate
        #if self.__exp_settings.calibrate_before_measurement:
        #    self.__dynamic_signal_analyzer.calibrate()
        
        #set averaging
        #self.__dynamic_signal_analyzer.set_average_count(self.__exp_settings.averages)

        #set display updates
        #self.__dynamic_signal_analyzer.set_display_update_rate(self.__exp_settings.display_refresh)

        #measure_temperature
        #if self.__exp_settings.need_measure_temperature:
        #    raise NotImplementedError()

        #switch Vfg to Vmain


        #measure Vmain
        #calculate Isample ,Rsample
        #measure spectra 
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #calculate resulting spectra
        #write data to measurement file and experiment file
        print("performing perform_non_gated_single_measurement")
        #pass
        

    def perform_single_measurement(self):
        #calibrate
        #set overload_rejection
        #set averaging
        #measure_temperature
        #measure Vds, Vfg
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #measure spectra 
        #measure Vds, Vfg
        #switch Vfg to Vmain
        #measure Vmain
        #calculate Isample ,Rsample
        #calculate resulting spectra
        #write data to measurement file and experiment file
        print("performing perform_single_measurement")
        #pass


    def perform_experiment(self):
        function_to_execute = self.generate_experiment_function()
        function_to_execute()







mainViewBase, mainViewForm = uic.loadUiType("UI_NoiseMeasurement.ui")
class MainView(mainViewBase,mainViewForm):
    def __init__(self, parent = None):
       super(mainViewBase,self).__init__(parent)
       self.setupUi(self)
       self._settings = ExperimentSettings()
       self.setModel(ExperimentSettingsViewModel(self._settings))
       #self._viewModel = ExperimentSettingsViewModel(self._settings)
       #self._dataMapper = QtGui.QDataWidgetMapper()

    def setModel(self, model):
       self._viewModel = model
       
       

       self._dataMapper = QtGui.QDataWidgetMapper()
       self._dataMapper.setModel(self._viewModel)
       print(self._dataMapper.rootIndex())
        #self._dataMapper.addMapping(self. ,0)
       self._dataMapper.addMapping(self.ui_experimentName ,1)
       self._dataMapper.addMapping(self.ui_measurementName ,2)
       self._dataMapper.addMapping(self.ui_measurementCount ,3)
       self._dataMapper.addMapping(self.ui_calibrate ,4)
       self._dataMapper.addMapping(self.ui_overload_reject ,5)
       self._dataMapper.addMapping(self.ui_display_refresh ,6)
       self._dataMapper.addMapping(self.ui_averages ,7)
       self._dataMapper.addMapping(self.ui_use_homemade_amplifier ,8)
       #self._dataMapper.addMapping(self. ,9)
       #self._dataMapper.addMapping(self. ,10)
       self._dataMapper.addMapping(self.ui_second_amp_coeff ,11)
       self._dataMapper.addMapping(self.ui_load_resistance ,12)
       self._dataMapper.addMapping(self.ui_need_meas_temp ,13)
       self._dataMapper.addMapping(self.ui_meas_gated_structure ,14)
       self._dataMapper.addMapping(self.ui_meas_characteristic_type ,15,"currentIndex")
       self._dataMapper.addMapping(self.ui_use_dut_selector ,16)
       #self._dataMapper.addMapping(self. ,17)
       self._dataMapper.addMapping(self.ui_use_set_vds_range ,18)
       #self._dataMapper.addMapping(self. ,19)
       self._dataMapper.addMapping(self.ui_use_set_vfg_range ,20)
       #self._dataMapper.addMapping(self. ,21)
       self._dataMapper.addMapping(self.ui_front_gate_voltage ,22)
       self._dataMapper.addMapping(self.ui_drain_source_voltage ,23)
       
       QtCore.QObject.connect(self._viewModel, QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), self.on_data_changed)
        

    def on_data_changed(self):
        print("view model changed")

    @QtCore.pyqtSlot()
    def on_startButton_clicked(self):
        print("start")

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        print("stop")

    def show_range_selector(self,model):
        dialog = RangeSelectorView(model)
        result = dialog.exec_()
        print(result)

    @QtCore.pyqtSlot()
    def on_VdsRange_clicked(self):
        print("Vds range")
        self.show_range_selector(None)

    @QtCore.pyqtSlot()
    def on_VfgRange_clicked(self):
        print("Vfg range")
        self.show_range_selector(None)

    @QtCore.pyqtSlot()
    def on_transistorSelector_clicked(self):
        dialog = DUTselectorView()
        result = dialog.exec_()
        print("Select transistors")

    @QtCore.pyqtSlot()
    def on_folderBrowseButton_clicked(self):
        print("Select folder")
        folder_name = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder")
        
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setText("This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText(folder_name)
        msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        retval = msg.exec_()
    
    @QtCore.pyqtSlot()
    def on_selectVoltageChangeOrder_clicked(self):
        print("selectVoltageChangeOrder")
        
  

    


DUTselectorViewBase, DUTselectorViewForm = uic.loadUiType("UI_TransistorSelector.ui")
class DUTselectorView(DUTselectorViewBase,DUTselectorViewForm):
    def __init__(self,parent = None):
        super(DUTselectorViewBase,self).__init__(parent)
        self.setupUi(self)


rangeSelectorBase, rangeSelectorForm = uic.loadUiType("UI_RangeSelector.ui")
class RangeSelectorView(rangeSelectorBase,rangeSelectorForm):
    def __init__(self,parent = None):
        super(rangeSelectorBase,self).__init__(parent)
        self.setupUi(self)

    #def set


 
if __name__== "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("LegacyNoiseMeasurementSetup")
    app.setStyle("cleanlooks")

    #listView = QtGui.QListView()
    #settings = ExperimentSettings()
    #vm = ExperimentSettingsViewModel(settings)
    
    #listView.setModel(vm)
    
    #listView.show()
       

    wnd = MainView()
    wnd.show()

    sys.exit(app.exec_())



    #ard = ArduinoController("COM4", 115200)
    ##ard.open();
    ##var = ard.read_idn()
    ##print(var)
    #time.sleep(2)
    #for i in range(1,33,1):
    #    ard.switch_channel(i,True)
    #    time.sleep(0.3)
    #    ard.switch_channel(i,False)
    #var = ard.read_idn()
    #print(var)

    #ard.set_motor_speed(1,200)
    #ard.set_motor_speed(1 ,0)


    #ard.close()
    #    time.sleep(1)
    #    print(i)
    #    ard.write("2,{0},1;".format(i).encode())


    #m1 = HP34401A("GPIB0::23::INSTR")
    #m1.clear_status()
    #m1.reset()
    
    #m1.switch_beeper(False)
    #m1.set_nplc(0.1)
    #m1.set_trigger_count(10)
    #m1.switch_high_ohmic_mode(False)
    #m1.set_function(HP34401A_FUNCTIONS.AVER)
    
    #m1.switch_stat(True)
    #m1.switch_autorange(True)
    #m1.init_instrument()
    #print(m1.read_average())
    #m1.switch_stat(False)
    #print(m1.read_voltage())
    

    #res = "GPIB0::6::INSTR"
    #dev = HP3567A(res)
    #dev.abort()
    #dev.calibrate()
    #dev.set_source_voltage(6.6)
    #dev.output_state(True)
    #time.sleep(2)
    #dev.output_state(False)
    #print(HP35670A_MODES.FFT)
    #dev.select_instrument_mode(HP35670A_MODES.FFT)
    #dev.switch_input(HP35670A_INPUTS.INP2, False)
    #dev.select_active_traces(HP35670A_CALC.CALC1, HP35670A_TRACES.A)
    ##dev.select_real_format(64)
    #dev.select_ascii_format()
    #dev.select_power_spectrum_function(HP35670A_CALC.CALC1)
    #dev.select_voltage_unit(HP35670A_CALC.CALC1)
    #dev.switch_calibration(False)
    #dev.set_average_count(10)
    #dev.set_display_update_rate(2)
    #dev.set_frequency_resolution(1600)
    #dev.set_frequency_start(64.0)
    #dev.set_frequency_stop(102.4e3)

    #print(dev.get_points_number(HP35670A_CALC.CALC1))


    #dev.init_instrument()
    #dev.wait_operation_complete()

    #print(dev.get_data(HP35670A_CALC.CALC1))
